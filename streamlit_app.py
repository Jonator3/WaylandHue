import os

import streamlit as st
from apis import hue_api
from configparser import ConfigParser
import sys
import subprocess


base_path = "/".join(sys.argv[0].split("/")[:-1])
if base_path == "":
    base_path = "./"
elif not base_path.endswith("/"):
    base_path += "/"


def write_conf(ip: str, user: str, target: int, brightness: float):

    config = ConfigParser()
    config["API"] = {
        "mode": "hue",
        "ip": ip,
        "user": user,
        "target_group": str(target)
    }
    config["Colouring"] = {
        "brightness_modifier": str(brightness),
        "saturation_modifier": "1.0",
        "min_difference": "0.01"
    }
    config.write(open(base_path + "config.ini", "w+"))


def is_valid_ip(ip: str):
    parts = ip.split(".")
    if len(parts) != 4:
        return False
    for P in parts:
        if not P.isnumeric():
            return False
        elif not (0 <= int(P) <= 255):
            return False
    return True


# init session variables
if "wh_pid" not in st.session_state:
    st.session_state.wh_pid = None  # None indicating that WaylandHue is not running
if "hue_user" not in st.session_state:
    st.session_state.hue_user = None


st.markdown('# WaylandHue')

if st.session_state.wh_pid is not None:
    if st.button("Stop WaylandHue Desktop sync"):
        os.kill(st.session_state.wh_pid, 9)
        st.session_state.wh_pid = None
        st.rerun()
else:
    hue_bridge_ip = st.text_input("Bridge IP:", "192.168.x.x")
    if is_valid_ip(hue_bridge_ip):
        st.text("After updating the Bridge IP,\npress the big button on your Hue-Bridge\nand then press the \"Link\" button below.")
        if st.button("Link HUE-Bridge"):
            st.session_state.hue_user = hue_api.create_new_user(hue_bridge_ip)
            if st.session_state.hue_user is None:  #create user failed!
                st.warning("Failed to link Hue-Bridge, please check the IP and try again.")
        if st.session_state.hue_user is not None:
            hue_bridge = hue_api.HueBridge(hue_bridge_ip, st.session_state.hue_user)
            groups = hue_bridge.get_groups()
            target_name = st.selectbox("Light Group to be controlled:", [g.name for g in groups])
            target_id = [g.id for g in groups if g.name == target_name][0]

            brightness_factor = st.slider("Brightness factor:", 0.0, 1.0, step=0.01)

            if st.button("Start WaylandHue Desktop sync"):
                write_conf(hue_bridge_ip, st.session_state.hue_user, target_id, brightness_factor)
                st.session_state.wh_pid = subprocess.Popen(["python3", base_path+"main.py"]).pid
