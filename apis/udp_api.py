from colorsys import rgb_to_hsv
import socket


def configure():
    ip = input("Please Enter the IP-Address of the UDP-Endpoint.\n")
    port = int(input("Please Enter the Port of the UDP-Endpoint.\n"))
    return {"ip": ip, "port": port, "restore_to_zero": False}


ip = ""
port = -1
restore_to_zero = False

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP


def start_up(conf):
    global ip, port, restore_to_zero
    ip = conf.get("ip")
    port = int(conf.get("port"))
    restore_to_zero = conf.get("restore_to_zero").lower() == "true"


def set_rgb(rgb):
    h, s, v = rgb_to_hsv(*rgb)
    r, g, b = rgb
    json = '{"r":'+str(int(r*255))+', "g":'+str(int(g*255))+', "b":'+str(int(b*255))+', "h":'+str(int(h*65536))+', "s":'+str(int(s*255))+', "v":'+str(int(v*255))+'}'
    sock.sendto(bytes(json, "utf-8"), (ip, port))


def restore():
    if restore_to_zero:
        json = '{"r":0, "g":0, "b":0, "h":0, "s":0, "v":0}'
        sock.sendto(bytes(json, "utf-8"), (ip, port))
