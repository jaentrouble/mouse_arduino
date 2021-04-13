from imutils.video import VideoStream
import flask
from flask import Flask, render_template, Response
import cv2
import argparse
import tflite_runtime.interpreter as tflite
import numpy as np
from img_proc.detector import ImageProcessor

parser = argparse.ArgumentParser()
parser.add_argument('-i','--ip',dest='ip', default='127.0.0.1')
parser.add_argument('-p','--port', type=int,dest='port', default=9999)
args = parser.parse_args()

FRAME_RES = (640,480)
_vs = VideoStream(
    usePiCamera=True,
    resolution=FRAME_RES,
    framerate=20
).start()


app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')

def generator():
    global _vs
    while True:
        new_frame = _vs.read().copy()
        flag, encoded_image = cv2.imencode('.jpg',frame)
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n'+
               bytearray(encoded_image) +
               b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generator(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


app.run(host=args.ip, port=args.port, debug=True, threaded=True, use_reloader=False)

imgproc.stop()