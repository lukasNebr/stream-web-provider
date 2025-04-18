import platform
from argparse import ArgumentParser

from flask import Flask, render_template, Response, redirect, url_for, request

from stream_web_provider.camera_stream import CameraStream

arg_parser = ArgumentParser()

arg_parser.add_argument(
    "--port",
    type=int,
    help="Port for the web application",
    default=5000
)

arg_parser.add_argument(
    "--camera-index",
    type=int,
    help="Index of the camera of the system",
    default=0
)

arg_parser.add_argument(
    "--resolution",
    type=str,
    help="Resolution of the camera stream as tuple: width,height",
    default="1280,720"
)

arg_parser.add_argument(
    "--stream-duration",
    type=int,
    help="Default stream duration in seconds",
    default=120
)

arguments, _ = arg_parser.parse_known_args()

port = arguments.port
camera_index = arguments.camera_index
resolution = tuple(int(x.strip()) for x in arguments.resolution.split(","))
stream_duration_default = arguments.stream_duration

camera = CameraStream(camera_index, )

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html", stream_duration=stream_duration_default, system_name=platform.node())


@app.route("/cameraStream")
def camera_stream():
    return Response(camera.get_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/startStream", methods=["POST"])
def start_stream():
    stream_duration = request.form.get("stream_duration")

    if stream_duration:
        try:
            duration = float(stream_duration)
        except ValueError:
            duration = stream_duration_default

        camera.start(duration)

    return redirect(url_for("index"))


@app.route("/stopStream")
def stop_stream():
    camera.stop()

    return redirect(url_for("index"))


def run_app():
    app.run(host="0.0.0.0", port=port)
