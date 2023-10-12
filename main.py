import signal
from datetime import datetime
import cv2
import configuration
import screen_grab
import os
import json


def signal_handler(sig, frame):
    print("\nSignal Interrupt received, closing now!")
    configuration.reset()
    exit(0)


def get_mean_rgb(img):
    img = cv2.resize(img, (1, 1), interpolation=cv2.INTER_AREA)
    b, g, r = img[0, 0]
    return int(r), int(g), int(b)


class ScreenRGBGraber(object):

    def __init__(self, on_new_frame=lambda rgb: None, fps=20):
        self.delta = 1/fps
        self.last_frame = datetime.now()
        self.on_new_frame = on_new_frame
        pipe_r, pipe_w = os.pipe()

        pid = os.fork()
        if pid == 0:  # child
            self.__write_loop(pipe_w)
        else:  # parent
            self.__read_loop(pipe_r)

    def __write_loop(self, pipe_w):
        def write(frame):
            now = datetime.now()
            if (now - self.last_frame).total_seconds() < self.delta:
                return
            self.last_frame = now
            r, g, b = get_mean_rgb(frame)
            s = '\n{"r":'+str(r)+', "g":'+str(g)+', "b":'+str(b)+'}'
            os.write(pipe_w, s.encode("utf-8"))
        screen_grab.run_screencast(write)

    def __read_loop(self, pipe_r):
        while True:
            json_str = os.read(pipe_r, 256).decode("utf-8").split("\n")[-1]
            data = json.loads(json_str)
            rgb = data["r"]/255, data["g"]/255, data["b"]/255
            self.on_new_frame(rgb)


if __name__ == "__main__":
    on_new_frame = lambda rgb: configuration.set_rgb(rgb)

    signal.signal(signal.SIGINT, signal_handler)
    ScreenRGBGraber(on_new_frame)
