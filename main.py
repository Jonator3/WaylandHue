import os.path
import sys
import time
from colorsys import rgb_to_hsv
import requests as re

import hue_api.exceptions
import pyscreenshot as ImageGrab
from hue_api import HueApi

from argparse import ArgumentParser


arg_pars = ArgumentParser()

arg_pars.add_argument("--bridge_ip", type=str, default=None, metavar="IP-Address", help="The IP-Address of your PhilipsHue Bridge")
arg_pars.add_argument("--interval", type=float, default=1.0, metavar="time", help="Time interval between screenshots")
arg_pars.add_argument("--bbox", nargs=4, type=int, default=None, metavar="time", help="Bounding-Box for the screenshot")

args = arg_pars.parse_args(sys.argv[1:])


interval = args.interval
bbox = args.bbox
bridge_ip = args.bridge_ip

api = HueApi()
api_key_path = "/".join(sys.argv[0].split("/")[:-1]) + "hue_api_user"

if not os.path.exists(api_key_path):
    if bridge_ip is None:
        print("Please specify an IP for the Bridge at first usage.")
        sys.exit(1)
    keep_trying = True
    while keep_trying:
        input("Please press the big Button on your PhilipsHue Bridge.\nThen press Enter to proceed.")
        try:
            api.create_new_user(bridge_ip)
            keep_trying = False
        except hue_api.exceptions.ButtonNotPressedException:
            pass
    api.save_api_key(api_key_path)
else:
    api.load_existing(api_key_path)

api.print_debug_info()

api.fetch_lights()
api.fetch_groups()

# select target group
target_group = api.groups[int(input("\nPleas select a Group to control:\n" + " ".join([str(i)+":"+g.name for i, g in enumerate(api.groups)])+"\n"))]


print("You selected:", target_group.name)
print(target_group.lights)


while True:
    time.sleep(interval)
    # grab fullscreen
    im = ImageGrab.grab(bbox)
    im = im.resize((1, 1))

    r, g, b = tuple(list(im.getpixel((0, 0)))[:3])
    print(r, "\t", g, "\t", b)

    h, s, v, = rgb_to_hsv(r/256, g/256, b/256)

    for light in target_group.lights:

        """state_url = light.light_url + "state/"
        response = re.put(state_url, json={'hue': int(h*(2**16)), 'sat': int(s*(2**8)), 'bri': int(b*(2**8))})
        print(response)"""
        light.set_color(int(h*(2**16)), int(s*(2**8)))
        light.set_brightness(int(b*(2**8)))

