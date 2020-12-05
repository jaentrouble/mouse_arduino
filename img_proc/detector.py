from imutils.video import VideoStream
import cv2
import ffmpeg
import tflite_runtime.interpreter as tflite
import numpy as np
from pathlib import Path
from datetime import datetime
import time
from threading import Thread, Lock

VID_TIME = 1800

class ImageProcessor():
    """ImageProcessor
    Constantly grabs frames from picamera and do some things with them
    It uses a thread to process frames in the background.
    It also saves processed frames into a video file.
    Use read() to get a frame which has a head pointer drawn on.
    """
    def __init__(self, frame_resolution, vid_dir, model_path, framerate=10):
        """
        Parameters
        ----------
        frame_resolution : tuple
            Size of a frame to take from camera
            read() method will return frames in this size.
            (Width, Height)
        vid_dir : str
            Directory to save processed videos
        model_path : str
            Path to load Interpreter model
        framerate : int
            imutils.video.VideoStream option
        """
        self.vid_dir = Path(vid_dir)
        self.framerate = framerate
        self.frame_res = frame_resolution
        self.frame_res_hw = (self.frame_res[1],self.frame_res[0])

        self.interpreter = tflite.Interpreter(model_path)
        self.interpreter.allocate_tensors()
        input_details = self.interpreter.get_input_details()[0]
        output_details = self.interpreter.get_output_details()[0]
        self.input_idx = input_details['index']
        self.input_size_wh = (
            input_details['shape'][2],
            input_details['shape'][1],
        )
        self.output_idx = output_details['index']
        self.output_size_wh = (
            output_details['shape'][2],
            output_details['shape'][1],
        )
        self.output_size_hw = (self.output_size_wh[1], self.output_size_wh[0])
        self.resize_ratio = np.divide(self.frame_res_hw, self.output_size_hw)

        # self._fourcc = cv2.VideoWriter_fourcc(*'MPEG')
        self._writer = None

        # Dummy frame
        self.frame = np.zeros((100,100,3),dtype=np.uint8)

        self._lock = Lock()
        self._updated = False
        self._stopped = False

    def start(self):
        self.reset_writer()
        self._vs = VideoStream(
            usePiCamera=True,
            resolution=self.frame_res,
            framerate=self.framerate,
        ).start()
        print('initiating...')
        time.sleep(2)

        t = Thread(target=self.update, args=())
        t.daemon = True
        t.start()

        return self

    def reset_writer(self):
        self._rec_start = time.time()
        if self._writer is not None:
            self._writer.stdin.close()
        now = datetime.now()
        rec_dir = self.vid_dir/now.strftime('%m_%d')
        if not rec_dir.exists():
            rec_dir.mkdir(parents=True)
        rec_name = now.strftime('%m_%d_%H_%M.ts')
        # self._writer = cv2.VideoWriter(
        #     str(rec_dir/rec_name),
        #     self._fourcc,
        #     self.framerate,
        #     self.frame_res,
        # )
        self._writer = (
            ffmpeg
            .input('pipe:', format='rawvideo', pix_fmt='rgb24', 
                    s=f'{self.frame_res[0]}x{self.frame_res[1]}',
                    loglevel='panic', framerate=self.framerate)
            .output(str(rec_dir/rec_name),pix_fmt='yuv420p')
            .overwrite_output()
            .run_async(pipe_stdin=True)
        )

    def update(self):
        while True:

            if self._stopped:
                self._vs.stop()
                if self._writer is not None:
                    self._writer.release()
                return

            new_frame = self._vs.read().copy()
            resized_frame = cv2.resize(new_frame, dsize=self.input_size_wh)
            self.interpreter.set_tensor(
                self.input_idx,
                resized_frame[np.newaxis,...]
            )
            self.interpreter.invoke()
            heatmap = np.squeeze(self.interpreter.get_tensor(
                self.output_idx
            ))
            pos = np.unravel_index(heatmap.flatten().argmax(),
                                   self.output_size_hw)
            pos = np.multiply(pos, self.resize_ratio).astype(np.int)
            r,c = pos
            r_min = max(r-5,0)
            r_max = r+5
            c_min = max(c-5,0)
            c_max = c+5
            new_frame[r_min:r_max,c_min:c_max] = [0,255,0]
            
            with self._lock:
                self._writer.stdin.write(new_frame.tobytes())
                self.frame = new_frame
                self._updated = True

            # Reset writer every 30 mins
            if (time.time() - self._rec_start) > VID_TIME:
                self.reset_writer()

    def is_updated(self):
        return self._updated

    def read(self):
        with self._lock:
            return self.frame

    def stop(self):
        self._stopped = True
