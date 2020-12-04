from imutils.video import VideoStream
import flask
from flask import Flask, render_template, Response
import cv2
import argparse

vs = VideoStream(usePiCamera=True, resolution=(384,256),framerate=10).start()

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')

def generator():
    while True:
        global vs
        frame = vs.read()
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

    app.run(host=args.ip, port=args.port, debug=True, threaded=False)

vs.stop()