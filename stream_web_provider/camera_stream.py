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
        file_directory = os.path.dirname(os.path.realpath(__file__))

        while True:
            if self._is_stopped:
                image = cv2.imread(os.path.join(file_directory, "templates/stream_stopped.png"), cv2.IMREAD_COLOR)

                ret, buffer = cv2.imencode(".jpg", image)
                frame_bytes = buffer.tobytes()

                yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"  # noqa

                continue

            if self._camera is None or not self._camera.isOpened():
                # wait until camera is ready
                image = cv2.imread(os.path.join(file_directory, "templates/connecting_camera.png"), cv2.IMREAD_COLOR)

                ret, buffer = cv2.imencode(".jpg", image)
                frame_bytes = buffer.tobytes()

                yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"  # noqa

                continue

            if datetime.datetime.now() > self._stream_end:
                self.stop()
                continue

            success, frame = self._camera.read()

            if not success:
                break

            else:
                ret, buffer = cv2.imencode(".jpg", frame)
                frame_bytes = buffer.tobytes()

                # concat frame one by one and show result
                yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"  # noqa
