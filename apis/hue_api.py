from datetime import datetime
from typing import List

import requests
from colorsys import rgb_to_hsv

from apis.basic_api import BasicApi


def create_new_user(ip):
    """
    This will register a new User in the Hue-Bridge with the given ip.

    :param ip:  the IP-Address of the Hue-Bridge
    :return:    the new username
    """
    response = requests.post("http://" + ip + "/api", """{"devicetype":"WaylandHue"}""").json()[0]
    user = None
    if response.keys().__contains__("success"):
        user = response["success"]["username"]
    return user


def ip_cleaner(ip):
    """
    Cleans unwanted chars like spaces from the IP

    :param ip:  IP input string
    :return:    cleaned ip string
    """
    return ip.replace(" ", "")


def configure():
    ip = input("Please Enter The IP-Address of your Hue-Bridge.\n")

    user = None
    while True:
        input("Please press the big Button on your PhilipsHue Bridge.\nThen press Enter to proceed.")
        user = create_new_user(ip)

        if user is not None:
            break

    bridge = HueBridge(ip, user)

    groups = bridge.get_groups()
    target = -1

    print("\n".join([str(g) for g in groups]))
    while True:
        val = input("Please chose a target Group.\n")

        try:
            target = int(val)
        except ValueError:
            targets = [g.id for g in groups if g.name == val]
            if len(targets) > 0:
                target = targets[0]

        if [g.id for g in groups].__contains__(target):
            break
        print("Enter a valid Group Id or Name!")
    return {"ip": ip, "user": user, "target_group": target, "restore_to_zero": False}


class HueBridge(object):

    def __init__(self, ip, username=None):
        self.ip = ip_cleaner(ip)
        self.username = username
        if self.username is None:
            self.username = create_new_user(self.ip)

        self.base_url = "http://" + self.ip + "/api/" + self.username

    def get_groups(self):
        lights = {light.id: light for light in self.get_lights()}
        response = requests.get(self.base_url+"/groups").json()
        groups = [HueGroup(self, int(id), response[id]["name"], [lights[int(lid)] for lid in response[id]["lights"]
                                                          if lights.keys().__contains__(int(lid))]) for id in response.keys()]
        return groups

    def get_lights(self):
        response = requests.get(self.base_url + "/lights").json()
        lights = [HueLight(self, int(id), response[id]["name"]) for id in response.keys()
                                     if response[id]["state"].keys().__contains__("hue")]
        return lights

    def get_light_states(self, lights):
        out = {}
        response = requests.get(self.base_url + "/lights").json()

        for l in lights:
            id = l.id
            out[l] = response[str(id)]["state"]
        return out


class HueLight:

    def __init__(self, bridge: HueBridge, id: int, name: str):
        self.bridge = bridge
        self.id = id
        self.name = name

    def get_state(self):
        response = requests.get(self.bridge.base_url + "/lights/" + str(self.id) + "/state").json()
        return response

    def set_state(self, state: dict):
        requests.put(self.bridge.base_url + "/lights/" + str(self.id) + "/state", json=state)

    def __str__(self):
        out = str(self.id)
        while len(out) < 3:
            out = " " + out
        out = "Light:" + out + ": " + self.name
        return out


class HueGroup(object):

    def __init__(self, bridge: HueBridge, id: int, name: str, lights: List[HueLight]):
        self.bridge = bridge
        self.id = id
        self.name = name
        self.lights = lights

    def set_state(self, state: dict):
        for light in self.lights:
            light.set_state(state)

    def __str__(self):
        out = str(self.id)
        while len(out) < 3:
            out = " " + out
        out = "Group:" + out + ": " + self.name
        out += "".join(["\n\t"+str(l) for l in self.lights])
        return out


class HueAPI(BasicApi):

    def __init__(self, conf):
        super().__init__(conf)
        self.main_bridge = HueBridge(conf.get("ip"), conf.get("user"))
        self.target_group = [g for g in self.main_bridge.get_groups() if g.id == int(conf.get("target_group"))][0]
        if not self.restore_to_zero:
            self.restore_data = self.main_bridge.get_light_states(self.target_group.lights)

    def set_color(self, rgb):
        h, s, v = rgb_to_hsv(*rgb)
        self.target_group.set_state({"on": True, "sat": int(s * 256), "bri": int(v * 256), "hue": int(h * 65536)})

    def restore_data(self):
        if self.restore_to_zero:
            self.set_color((0, 0, 0))
        else:
            for light in self.restore_data.keys():
                light.set_state(self.restore_data.get(light))


api = {"hue": (HueAPI, configure)}
