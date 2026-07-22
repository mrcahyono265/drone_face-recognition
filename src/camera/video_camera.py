import cv2
import os
import glob


class VideoStream:
    def __init__(self, video_dir="test"):
        self.video_dir = video_dir

        video_files = set()
        for ext in ('*.mp4', '*.avi', '*.mov', '*.mkv'):
            video_files.update(glob.glob(os.path.join(video_dir, ext)))
        self.video_files = sorted(video_files)

        if not self.video_files:
            raise FileNotFoundError(f"No video files found in '{video_dir}'")

        names = [os.path.basename(f) for f in self.video_files]
        print(f"[INFO] Found {len(self.video_files)} video(s): {names}")

        self.current_index = 0
        self.current_video_name = os.path.basename(self.video_files[0])
        self.stopped = False
        self.exhausted = False

        self.stream = cv2.VideoCapture(self.video_files[0])

    def start(self):
        return self

    def read(self):
        if self.stopped or self.exhausted:
            return None

        while True:
            grabbed, frame = self.stream.read()
            if not grabbed:
                self.stream.release()
                self.current_index += 1
                if self.current_index >= len(self.video_files):
                    self.exhausted = True
                    return None
                path = self.video_files[self.current_index]
                self.current_video_name = os.path.basename(path)
                print(f"[INFO] Playing: {self.current_video_name}")
                self.stream = cv2.VideoCapture(path)
                continue
            return frame

    def stop(self):
        self.stopped = True
        if self.stream is not None:
            self.stream.release()
