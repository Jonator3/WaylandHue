from colorsys import rgb_to_hsv


def configure():
    return {"restore_to_zero": False}


def start_up(conf):
    global restore_to_zero
    restore_to_zero = conf.get("restore_to_zero").lower() == "true"


def set_rgb(rgb):
    h, s, v = rgb_to_hsv(*rgb)
    r, g, b = rgb
    print('{"r":'+str(int(r*255))+', "g":'+str(int(g*255))+', "b":'+str(int(b*255))+', "h":'+str(int(h*65536))+', "s":'+str(int(s*255))+', "v":'+str(int(v*255))+'}')


def restore():
    if restore_to_zero:
        json = '{"r":0, "g":0, "b":0, "h":0, "s":0, "v":0}'
        print(json)


restore_to_zero = False
