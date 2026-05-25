import cv2
import time


class WebcamMonitor:
    def __init__(self, camera_index=0):
        self.camera_index = camera_index
        self.cap = None
        self.is_running = False

        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades +
            "haarcascade_frontalface_default.xml"
        )

        self.last_result = {
            "face_detected": False,
            "stress_level": "UNKNOWN",
            "attention_status": "UNKNOWN",
            "face_confidence": 0.0,
            "timestamp": None,
        }

    def start(self):
        if self.is_running:
            return

        self.cap = cv2.VideoCapture(self.camera_index)

        if not self.cap.isOpened():
            raise RuntimeError("Could not open webcam.")

        self.is_running = True

        print("Webcam monitoring started.")

    def stop(self):
        self.is_running = False

        if self.cap:
            self.cap.release()
            self.cap = None

        print("Webcam monitoring stopped.")

    def analyze_frame(self):
        if not self.is_running or self.cap is None:
            return self.last_result

        ret, frame = self.cap.read()

        if not ret:
            return self.last_result

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(80, 80)
        )

        if len(faces) == 0:
            self.last_result = {
                "face_detected": False,
                "stress_level": "UNKNOWN",
                "attention_status": "FACE_NOT_VISIBLE",
                "face_confidence": 0.0,
                "timestamp": time.time(),
            }

            return self.last_result

        largest_face = max(faces, key=lambda f: f[2] * f[3])

        x, y, w, h = largest_face

        frame_center_x = frame.shape[1] / 2
        face_center_x = x + (w / 2)

        center_offset = abs(frame_center_x - face_center_x)

        attention_score = max(
            0,
            1 - (center_offset / frame_center_x)
        )

        face_area = w * h
        frame_area = frame.shape[0] * frame.shape[1]

        face_ratio = face_area / frame_area

        stress_score = 0

        if attention_score < 0.5:
            stress_score += 20

        if face_ratio > 0.20:
            stress_score += 20

        if stress_score >= 30:
            stress_level = "HIGH"
        elif stress_score >= 15:
            stress_level = "MEDIUM"
        else:
            stress_level = "LOW"

        if attention_score >= 0.5:
            attention_status = "LOOKING_AT_SCREEN"
        else:
            attention_status = "DISTRACTED"

        self.last_result = {
            "face_detected": True,
            "stress_level": stress_level,
            "attention_status": attention_status,
            "face_confidence": round(attention_score, 2),
            "face_ratio": round(face_ratio, 3),
            "timestamp": time.time(),
        }

        return self.last_result