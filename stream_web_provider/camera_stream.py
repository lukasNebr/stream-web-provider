import datetime
import os
from threading import Thread

import cv2


class CameraStream:

    def __init__(self, camera_index: int = 0, resolution: tuple[int, int] = None):
        self._camera_index: int = camera_index

        self._with: int = resolution[0] if resolution is not None else 1280
        self._height: int = resolution[1] if resolution is not None else 720

        self._camera: cv2.VideoCapture | None = None

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
        self._stream_end = datetime.datetime.now() + datetime.timedelta(seconds=stream_duration)
        self._is_stopped = False

        if self._camera is None:
            Thread(target=self._start_camera).start()

    def _start_camera(self):
        self._camera = cv2.VideoCapture(self._camera_index)

        self._camera.set(cv2.CAP_PROP_FRAME_WIDTH, self._with)
        self._camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self._height)

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
                # wait until camera is ready
                yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + self._connecting_frame_bytes + b"\r\n"  # noqa

                continue

            if datetime.datetime.now() > self._stream_end:
                self.stop()
                continue

            success, frame = self._camera.read()

            if not success:
                self.stop()
                continue

            _, buffer = cv2.imencode(".jpg", frame)
            frame_bytes = buffer.tobytes()

            # concat frame one by one and show result
            yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"  # noqa
