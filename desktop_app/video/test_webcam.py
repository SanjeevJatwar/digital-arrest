import time
from desktop_app.video.webcam_monitor import WebcamMonitor

monitor = WebcamMonitor()

monitor.start()

try:
    for i in range(20):
        result = monitor.analyze_frame()
        print(result)
        time.sleep(0.5)

finally:
    monitor.stop()