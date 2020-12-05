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
parser.add_argument('-p','--port', type=int,dest='port')
parser.add_argument('-v','--viddir', type=str, dest='vid_dir')
args = parser.parse_args()

FRAME_RES = (640,480)
model_path = 'savedmodels/mobv3_small_head.tflite'
imgproc = ImageProcessor(FRAME_RES, args.vid_dir, model_path).start()

# FRAME_RES = (640,480)
# FRAME_RES_HW = (FRAME_RES[1],FRAME_RES[0])

# vs = VideoStream(usePiCamera=True, resolution=FRAME_RES,framerate=10).start()

app = Flask(__name__)

# interpreter = tflite.Interpreter('savedmodels/mobv3_small_head.tflite')
# interpreter.allocate_tensors()

# input_idx = interpreter.get_input_details()[0]['index']
# input_size_wh = (interpreter.get_input_details()[0]['shape'][2],
#                  interpreter.get_input_details()[0]['shape'][1],)

# output_idx = interpreter.get_output_details()[0]['index']
# output_size_wh = (interpreter.get_output_details()[0]['shape'][2],
#                   interpreter.get_output_details()[0]['shape'][1],)
# output_size_hw = (output_size_wh[1], output_size_wh[0])

# resize_ratio = np.divide(FRAME_RES_HW,output_size_hw)

@app.route('/')
def index():
    return render_template('index.html')

def generator():
    global imgproc
    while True:
        # frame = vs.read().copy()
        # resized_frame = cv2.resize(frame, dsize=input_size_wh)
        # interpreter.set_tensor(input_idx,resized_frame[np.newaxis,...])
        # interpreter.invoke()
        # heatmap = np.squeeze(interpreter.get_tensor(output_idx))
        # pos = np.unravel_index(heatmap.flatten().argmax(),output_size_hw)
        # pos = np.multiply(pos, resize_ratio).astype(np.int)
        # r, c = pos
        # r_min = max(r-5,0)
        # r_max = r+5
        # c_min = max(c-5,0)
        # c_max = c+5
        # frame[r_min:r_max,c_min:c_max] = [0,255,0]
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