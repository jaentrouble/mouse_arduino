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
parser.add_argument('-v','--viddir', type=str,required=True, dest='vid_dir')
args = parser.parse_args()

FRAME_RES = (640,480)
model_path = 'savedmodels/mobv3_small_07_head_q3q_quan.tflite'
imgproc = ImageProcessor(FRAME_RES, args.vid_dir, model_path).start()


app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')

def generator():
    global imgproc
    while True:
        if imgproc.is_updated():
            frame = imgproc.read()
            flag, encoded_image = cv2.imencode('.jpg',frame)
            if not flag:
                continue
        else: continue
        
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