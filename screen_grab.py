import re
import dbus
from jeepney import DBusAddress, new_method_call
from jeepney.bus_messages import MatchRule, message_bus
from jeepney.io.blocking import Proxy, open_dbus_connection
import cv2
import os
from gi.repository import GLib
from dbus.mainloop.glib import DBusGMainLoop
import numpy as np
import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstApp', '1.0')
from gi.repository import GObject, Gst, GstApp


def grab():

    portal = DBusAddress(
        object_path="/org/freedesktop/portal/desktop",
        bus_name="org.freedesktop.portal.Desktop",
    )
    screenshot = portal.with_interface("org.freedesktop.portal.Screenshot")
    connection = open_dbus_connection()
    sender_name = connection.unique_name[1:].replace(".", "_")

    handle = f"/org/freedesktop/portal/desktop/request/{sender_name}/WaylandHue"
    response_rule = MatchRule(type="signal", interface="org.freedesktop.portal.Request", path=handle)
    Proxy(message_bus, connection).AddMatch(response_rule)

    with connection.filter(response_rule) as responses:
        req = new_method_call(
            screenshot,
            "Screenshot",
            "sa{sv}",
            ("", {"handle_token": ("s", "WaylandHue"), "interactive": ("b", False)}),
        )
        connection.send_and_get_reply(req)
        response_msg = connection.recv_until_filtered(responses).body

    response, results = response_msg

    img = None
    if response == 0:
        filename = results["uri"][1].split("file://", 1)[-1]
        if os.path.isfile(filename):
            img = cv2.imread(filename)
            os.remove(filename)

    connection.close()

    return img


class DBusError(BaseException):

    def __init__(self, msg):
        super().__init__(msg)


should_stop = False


def stop():
    global should_stop
    should_stop = True


def run_screencast(on_new_frame=lambda img: None, on_start=lambda: None):
    DBusGMainLoop(set_as_default=True)
    Gst.init(None)

    loop = GLib.MainLoop()

    bus = dbus.SessionBus()
    request_iface = 'org.freedesktop.portal.Request'
    screen_cast_iface = 'org.freedesktop.portal.ScreenCast'
    sender_name = re.sub(r'\.', r'_', bus.get_unique_name()[1:])

    request_token_counter = 0
    session_token_counter = 0

    pipeline = None
    appsrc = None
    session = None


    def terminate():
        if pipeline is not None:
            pipeline.set_state(Gst.State.NULL)
        loop.quit()


    def get_appsink(pipeline):
        elements = pipeline.iterate_elements()
        if isinstance(elements, Gst.Iterator):
            # Patch "TypeError: ‘Iterator’ object is not iterable."
            _elements = []
            while True:
                ret, el = elements.next()
                if ret == Gst.IteratorResult(1):  # GST_ITERATOR_OK
                    _elements.append(el)
                else:
                    break
            elements = _elements

        return [e for e in elements if isinstance(e, GstApp.AppSink)]


    def on_new_sample(sample):
        buffer = sample.get_buffer()
        caps = sample.get_caps()
        width = caps.get_structure(0).get_value("width")
        height = caps.get_structure(0).get_value("height")

        retval, map_info = buffer.map(Gst.MapFlags.READ)
        if retval:
            frame_data = map_info.data

            frame = np.ndarray(shape=(height, width, 3), dtype=np.uint8, buffer=frame_data)

            on_new_frame(frame)

            buffer.unmap(map_info)


    def on_gst_message(bus, message):
        type = message.type
        if type == Gst.MessageType.EOS or type == Gst.MessageType.ERROR:
            terminate()


    def play_pipewire_stream(node_id):
        empty_dict = dbus.Dictionary(signature="sv")
        fd_object = portal.OpenPipeWireRemote(session, empty_dict,
                                              dbus_interface=screen_cast_iface)
        fd = fd_object.take()
        pipeline = Gst.parse_launch(f"pipewiresrc fd={fd} path={node_id} ! videoconvert ! video/x-raw,format=BGR ! appsink name=sink")
        pipeline.set_state(Gst.State.PLAYING)
        pipeline.get_bus().connect('message', on_gst_message)

        appsinks = get_appsink(pipeline)
        sink = appsinks[0]
        sink.set_max_buffers(1)

        while True:
            sample = sink.pull_sample()
            if should_stop:
                terminate()
                os.kill(os.getpid(), 9)
            on_new_sample(sample)


    def new_request_path():
        nonlocal request_token_counter
        request_token_counter = request_token_counter + 1
        token = 'u%d'%request_token_counter
        path = '/org/freedesktop/portal/desktop/request/%s/%s'%(sender_name, token)
        return (path, token)


    def new_session_path():
        nonlocal session_token_counter
        session_token_counter = session_token_counter + 1
        token = 'u%d'%session_token_counter
        path = '/org/freedesktop/portal/desktop/session/%s/%s'%(sender_name, token)
        return (path, token)


    def screen_cast_call(method, callback, *args, options={}):
        (request_path, request_token) = new_request_path()
        bus.add_signal_receiver(callback,
                                'Response',
                                request_iface,
                                'org.freedesktop.portal.Desktop',
                                request_path)
        options['handle_token'] = request_token
        method(*(args + (options, )),
               dbus_interface=screen_cast_iface)


    def on_start_response(response, results):
        if response != 0:
            raise DBusError("Failed to start: %s"%response)
            terminate()
            return

        for (node_id, stream_properties) in results['streams']:
            on_start()
            play_pipewire_stream(node_id)


    def on_select_sources_response(response, results):
        if response != 0:
            raise DBusError("Failed to select sources: %d"%response)
            terminate()
            return

        nonlocal session
        screen_cast_call(portal.Start, on_start_response,
                         session, '')


    def on_create_session_response(response, results):
        if response != 0:
            raise DBusError("Failed to create session: %d"%response)
            terminate()
            return

        nonlocal session
        session = results['session_handle']

        screen_cast_call(portal.SelectSources, on_select_sources_response,
                         session,
                         options={ 'multiple': False,
                                   'types': dbus.UInt32(1|2) })

    portal = bus.get_object('org.freedesktop.portal.Desktop',
                                 '/org/freedesktop/portal/desktop')

    (session_path, session_token) = new_session_path()
    screen_cast_call(portal.CreateSession, on_create_session_response,
                     options={ 'session_handle_token': session_token })

    loop.run()

