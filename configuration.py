import sys
import os
from configparser import ConfigParser
from argparse import ArgumentParser
from api_manager import apis

base_path = "/".join(sys.argv[0].split("/")[:-1])
if base_path == "":
    base_path = "./"
elif not base_path.endswith("/"):
    base_path += "/"
raw_args = sys.argv[1:]


arg_par = ArgumentParser()

args = arg_par.parse_args(raw_args)

config = ConfigParser()
if not os.path.exists(base_path + "config.ini"):
    print("No Config File Found!\n")
    print("Starting First Time Setup.")

    make_new_api = True
    api_index = 1

    while make_new_api:
        api_mode = input("please enter your desired API:\n"+"\n".join([k for k in apis.keys()])+"\n")

        while api_mode not in apis.keys():
            api_mode = input("please enter your desired API:\n" + "\n".join([k for k in apis.keys()]) + "\n")

        api_conf = apis.get(api_mode)[1]()

        config["API_"+str(api_index)] = {"mode": api_mode}
        for key in list(api_conf.keys()):
            config["API_"+str(api_index)][str(key)] = str(api_conf.get(key))
        config["Colouring"] = {"brightness_modifier": "1.0", "saturation_modifier": "1.0", "min_difference": "0.01"}
        config.write(open(base_path + "config.ini", "w+"))

        if input("Do you want too add another API? (y/n) ").lower() == "y":
            api_index += 1
        else:
            make_new_api = False
else:
    config.read(base_path + "config.ini")

api_list = []
for api in [sec for sec in config.sections() if sec.startswith("API")]:
    api_obj = apis.get(config[api]["mode"])[0](config[api])
    api_list.append(api_obj)

old_rgb = (-1, -1, -1)


def reset():
    for api in api_list:
        api.restore()


def set_rgb(rgb):
    global old_rgb
    r, g, b = rgb
    diff = sum([abs(rgb[i]-old_rgb[i]) for i in range(3)])
    if diff < float(config["Colouring"]["min_difference"]):
        return
    old_rgb = rgb
    if not (args.silence or args.api_mode == "pipe"):
        print("RGB:\t", round(r, 3), "\t", round(g, 3), "\t", round(b, 3))
    for api in api_list:
        api.set_color(rgb)
