import datetime
import logging
import os
import time
from threading import Thread, Lock

import cv2

from stream_web_provider.interruptable_thread import InterruptableThread


class CameraStream:

    def __init__(self, camera_index: int = 0, resolution: tuple[int, int] = None):
        self._camera_index: int = camera_index

        self._with: int = resolution[0] if resolution is not None else 1280
        self._height: int = resolution[1] if resolution is not None else 720

        self._camera: cv2.VideoCapture | None = None
        self._camera_lock: Lock = Lock()

        self._stream_end: datetime.datetime = datetime.datetime.now()
        self._is_stopped: bool = True

        file_directory = os.path.dirname(os.path.realpath(__file__))

        self._connecting_frame_bytes = self._load_image_frame(
            os.path.join(file_directory, "templates/connecting_camera.png"))

        self._stopped_frame_bytes = self._load_image_frame(
            os.path.join(file_directory, "templates/stream_stopped.png"))

    def _load_image_frame(self, image_path: str, size: tuple[int, int] = None):
        image = cv2.imread(image_path, cv2.IMREAD_COLOR)

        if size is None:
            height, width = image.shape[:2]
            percentage = self._with / width if width > height else self._height / height
            new_size = (int(width * percentage), int(height * percentage))

        else:
            new_size = size

        image = cv2.resize(image, new_size)
        _, buffer = cv2.imencode(".jpg", image)

        return buffer.tobytes()

    def start(self, stream_duration: float):
        logging.info(f"Start camera stream with duration: {stream_duration}")

        self._stream_end = datetime.datetime.now() + datetime.timedelta(seconds=stream_duration)
        self._is_stopped = False

        if self._camera is None:
            Thread(target=self._start_camera).start()

    def _open_camera(self, *args):
        try:
            self._camera = cv2.VideoCapture(self._camera_index, *args)
        except KeyboardInterrupt:
            pass

    def _start_camera(self):
        try:
            logging.info("Try to open camera")

            start_time = time.time()
            end_time = start_time + 2

            with self._camera_lock:
                open_camera_thread = InterruptableThread(target=self._open_camera)
                open_camera_thread.start()

                while time.time() < end_time and open_camera_thread.is_alive():
                    time.sleep(0.05)

                if open_camera_thread.is_alive():
                    logging.error("Failed to open camera with default setting, trying with DSHOW")

                    open_camera_thread.interrupt()
                    open_camera_thread = InterruptableThread(target=self._open_camera, args=(cv2.CAP_DSHOW,))
                    open_camera_thread.start()

                open_camera_thread.join()

                self._camera.set(cv2.CAP_PROP_FRAME_WIDTH, float(self._with))
                self._camera.set(cv2.CAP_PROP_FRAME_HEIGHT, float(self._height))

                # read first frame from camera, otherwise the capturing mechanism cannot access the camera stream
                success, frame = self._camera.read()

                if not success:
                    logging.error(f"Cannot open camera stream - success: {success} - frame: {frame}")
                    raise RuntimeError

            logging.info("Camera is opened")

        # pylint: disable=broad-exception-caught
        except Exception as e:
            logging.error(f"Failed to open camera: {e}")

            self._is_stopped = True

    def stop(self):
        if self._camera is None:
            return

        self._camera.release()
        self._camera = None
        self._is_stopped = True

        cv2.destroyAllWindows()

    def get_frames(self):
        while True:
            if self._is_stopped:
                yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + self._stopped_frame_bytes + b"\r\n"  # noqa

                continue

            if self._camera is None or not self._camera.isOpened():
                # wait until the camera is ready
                yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + self._connecting_frame_bytes + b"\r\n"  # noqa

                continue

            logging.info("Camera is active")

            if datetime.datetime.now() > self._stream_end:
                logging.info(f"Stream duration is expired: {self._stream_end}")

                self.stop()
                continue

            try:
                with self._camera_lock:
                    success, frame = self._camera.read()

            # pylint: disable=broad-exception-caught
            except Exception as e:
                logging.error(f"Cannot read frame from camera: {e}")

                success = False
                frame = None

            if not success:
                logging.error(f"Cannot read frame from camera - success: {success} - frame: {frame}")
                self.stop()
                continue

            _, buffer = cv2.imencode(".jpg", frame)
            frame_bytes = buffer.tobytes()

            # concat frame one by one and show result
            yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"  # noqa
