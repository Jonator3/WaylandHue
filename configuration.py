import sys
import os
from configparser import ConfigParser
from argparse import ArgumentParser
from apis import pipe_api, hue_api, udp_api

base_path = "/".join(sys.argv[0].split("/")[:-1])
if base_path == "":
    base_path = "./"
elif not base_path.endswith("/"):
    base_path += "/"
raw_args = sys.argv[1:]

apis = {
    "hue": hue_api,
    "pipe": pipe_api,
    "udp": udp_api
}

arg_par = ArgumentParser()
arg_par.add_argument("--api_mode", type=str, choices=apis, default=list(apis.keys())[0], help="Specify in with way the Programm will output the Colour-Values.")
arg_par.add_argument("--silence", "-s", default=False, action='store_true', help="Disable STD_IN and STD_OUT. (api_mode Pipe will automaticly set this)")

args = arg_par.parse_args(raw_args)

config = ConfigParser()
if not os.path.exists(base_path + "config.ini"):
    print("No Config File Found!\n")
    print("Starting First Time Setup.")

    api_conf = apis.get(args.api_mode).configure()

    config["API"] = {"mode": args.api_mode}
    for key in list(api_conf.keys()):
        config["API"][str(key)] = str(api_conf.get(key))
    config["Colouring"] = {"brightness_modifier": "1.0", "saturation_modifier": "1.0", "min_difference": "0.01"}
    config.write(open(base_path + "config.ini", "w+"))
else:
    config.read(base_path + "config.ini")

apis.get(config["API"]["mode"]).start_up(config["API"])

old_rgb = (-1, -1, -1)


def reset():
    apis.get(config["API"]["mode"]).restore()


def set_rgb(rgb):
    global old_rgb
    r, g, b = rgb
    diff = sum([abs(rgb[i]-old_rgb[i]) for i in range(3)])
    if diff < float(config["Colouring"]["min_difference"]):
        return
    old_rgb = rgb
    if not (args.silence or args.api_mode == "pipe"):
        print("RGB:\t", round(r, 3), "\t", round(g, 3), "\t", round(b, 3))
    apis.get(config["API"]["mode"]).set_rgb(rgb)
