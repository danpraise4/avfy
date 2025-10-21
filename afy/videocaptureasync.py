# https://github.com/gilbertfrancois/video-capture-async

import threading
import cv2
import time


WARMUP_TIMEOUT = 30.0


class VideoCaptureAsync:
    def __init__(self, src=0, width=640, height=480):
        self.src = src

        self.cap = cv2.VideoCapture(self.src, cv2.CAP_AVFOUNDATION)
        if not self.cap.isOpened():
            raise RuntimeError("Cannot open camera")

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.grabbed, self.frame = self.cap.read()
        self.started = False
        self.read_lock = threading.Lock()

    def set(self, var1, var2):
        self.cap.set(var1, var2)

    def isOpened(self):
        return self.cap.isOpened()

    def start(self):
        if self.started:
            print('[!] Asynchronous video capturing has already been started.')
            return None
        self.started = True
        self.thread = threading.Thread(target=self.update, args=(), daemon=True)
        self.thread.start()

        # (warmup) wait for the first successfully grabbed frame
        warmup_start_time = time.time()
        print(f"Starting camera warmup (timeout: {WARMUP_TIMEOUT}s)...")
        while not self.grabbed:
            warmup_elapsed_time = (time.time() - warmup_start_time)
            if warmup_elapsed_time > WARMUP_TIMEOUT:
                print(f"Camera warmup timeout after {WARMUP_TIMEOUT}s. Camera may need permissions or be in use by another application.")
                print("Please check:")
                print("1. Camera permissions in System Preferences > Security & Privacy > Camera")
                print("2. No other applications are using the camera")
                print("3. Try restarting the application")
                raise RuntimeError(f"Failed to succesfully grab frame from the camera (timeout={WARMUP_TIMEOUT}s). Try to restart.")

            if int(warmup_elapsed_time) % 5 == 0:  # Print every 5 seconds
                print(f"Waiting for camera... {warmup_elapsed_time:.1f}s elapsed")
            time.sleep(0.5)

        return self

    def update(self):
        while self.started:
            grabbed, frame = self.cap.read()
            if not grabbed or frame is None or frame.size == 0:
                print(f"Camera read failed: grabbed={grabbed}, frame is None={frame is None}, frame size={frame.size if frame is not None else 'None'}")
                time.sleep(0.1)
                continue
            with self.read_lock:
                self.grabbed = grabbed
                self.frame = frame
                print(f"Successfully grabbed frame: {frame.shape}")

    def read(self):
        while True:
            with self.read_lock:
                frame = self.frame.copy()
                grabbed = self.grabbed
            break
        return grabbed, frame

    def stop(self):
        self.started = False
        self.thread.join()

    def __exit__(self, exec_type, exc_value, traceback):
        self.cap.release()
