from colorsys import rgb_to_hsv
import socket
from apis.basic_api import BasicApi


def configure_udp():
    ip = input("Please Enter the IP-Address of the UDP-Endpoint.\n")
    port = int(input("Please Enter the Port of the UDP-Endpoint.\n"))
    return {"ip": ip, "port": port, "restore_to_zero": False}


class UDPApi(BasicApi):

    def __init__(self, conf):
        super().__init__(conf)
        self.ip = conf.get("ip")
        self.port = int(conf.get("port"))
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP

    def set_color(self, rgb):
        h, s, v = rgb_to_hsv(*rgb)
        r, g, b = rgb
        json = '{"r":' + str(int(r * 255)) + ', "g":' + str(int(g * 255)) + ', "b":' + str(
            int(b * 255)) + ', "h":' + str(int(h * 65536)) + ', "s":' + str(int(s * 255)) + ', "v":' + str(
            int(v * 255)) + '}'
        self.sock.sendto(bytes(json, "utf-8"), (self.ip, self.port))


api = {"udp": (UDPApi, configure_udp)}
