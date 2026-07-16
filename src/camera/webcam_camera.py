import cv2
import platform
import time
import threading

class cameraDroneThread:
    def __init__(self, src=0):
        print(f"[INFO]: Connecting to camera {src}...")

        if platform.system() == "Windows":
            self.stream = cv2.VideoCapture(src, cv2.CAP_DSHOW)
        else:
            self.stream = cv2.VideoCapture(src)
        self.stream.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        (self.grabbed, self.frame) = self.stream.read()
        self.stopped = False

    def start(self):
        threading.Thread(target=self.update, args=(), daemon=True).start()
        return self

    def update(self):
        while True:
            if self.stopped:
                self.stream.release()
                return
            self.grabbed, self.frame = self.stream.read()
            time.sleep(0.001)

    def read(self):
        if self.frame is not None:
            return self.frame
        return None

    def stop(self):
        self.stopped = True
