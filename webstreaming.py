from imutils.video import VideoStream
import flask
from flask import Flask, render_template, Response
import cv2
import argparse
import tflite_runtime.interpreter as tflite
import numpy as np
FRAME_RES = (640,480)
FRAME_RES_HW = (FRAME_RES[1],FRAME_RES[0])

vs = VideoStream(usePiCamera=True, resolution=FRAME_RES,framerate=10).start()

app = Flask(__name__)

interpreter = tflite.Interpreter('savedmodels/mobv3_small_head_quan.tflite')
interpreter.allocate_tensors()

input_idx = interpreter.get_input_details()[0]['index']
input_size_wh = (interpreter.get_input_details()[0]['shape'][2],
                 interpreter.get_input_details()[0]['shape'][1],)

output_idx = interpreter.get_output_details()[0]['index']
output_size_wh = (interpreter.get_output_details()[0]['shape'][2],
                  interpreter.get_output_details()[0]['shape'][1],)
output_size_hw = (output_size_wh[1], output_size_wh[0])

resize_ratio = np.divide(FRAME_RES_HW,output_size_hw)

@app.route('/')
def index():
    return render_template('index.html')

def generator():
    global vs, interpreter
    while True:
        frame = vs.read().copy()
        resized_frame = cv2.resize(frame, dsize=input_size_wh)
        interpreter.set_tensor(input_idx,resized_frame[np.newaxis,...])
        interpreter.invoke()
        heatmap = np.squeeze(interpreter.get_tensor(output_idx))
        pos = np.unravel_index(heatmap.flatten().argmax(),output_size_hw)
        pos = np.multiply(pos, resize_ratio).astype(np.int)
        r, c = pos
        r_min = max(r-10,0)
        r_max = r+10
        c_min = max(c-10,0)
        c_max = c+10
        frame[r_min:r_max,c_min:c_max] = [0,255,0]
        flag, encoded_image = cv2.imencode('.jpg',frame)
        if not flag:
            continue
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n'+
               bytearray(encoded_image) +
               b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generator(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i','--ip',dest='ip', default='127.0.0.1')
    parser.add_argument('-p','--port', type=int,dest='port')
    args = parser.parse_args()

    app.run(host=args.ip, port=args.port, debug=True, threaded=True, use_reloader=False)

vs.stop()