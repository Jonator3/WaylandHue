from colorsys import rgb_to_hsv


class BasicApi(object):

    def __init__(self, conf):
        self.restore_to_zero = conf.get("restore_to_zero").lower() == "true"

    def set_color(self, rgb):
        h, s, v = rgb_to_hsv(*rgb)
        r, g, b = rgb
        print('{"r":'+str(int(r*255))+', "g":'+str(int(g*255))+', "b":'+str(int(b*255))+', "h":'+str(int(h*65536))+', "s":'+str(int(s*255))+', "v":'+str(int(v*255))+'}')

    def restore(self):
        if self.restore_to_zero:
            self.set_color((0, 0, 0))


def configure():
    return {"restore_to_zero": False}


api = {"basic": (BasicApi, configure)}
