import cv2
import numpy as np
from insightface.app import FaceAnalysis


class Models:
    def __init__(self, provider="cuda", model_name="buffalo_sc", det_size=(320, 320)):
        print("[INFO] Loading model...")
        providers = (['CUDAExecutionProvider', 'CPUExecutionProvider'] if provider == "cuda"
                     else ['CPUExecutionProvider'])
        self.face_app = FaceAnalysis(name=model_name, allowed_modules=['detection', 'recognition'], providers=providers)
        self.face_app.prepare(ctx_id=0, det_size=det_size)

    def detect_and_recognize(self, frame_bgr):
        rgb_frame = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        faces = self.face_app.get(rgb_frame)
        return faces
