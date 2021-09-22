from imutils.video import VideoStream
import cv2
import ffmpeg
import tflite_runtime.interpreter as tflite
import numpy as np
from pathlib import Path
from datetime import datetime
import time
from threading import Thread, Lock
from img_proc import tools


VID_TIME = 1800

class ImageProcessor():
    """ImageProcessor
    Constantly grabs frames from picamera and do some things with them
    It uses a thread to process frames in the background.
    It also saves processed frames into a video file.
    Use read() to get current frame.
    """
    def __init__(
            self,
            frame_resolution,
            vid_dir,
            model_path,
            framerate=10,
        ):
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
        self.frame_count = 0
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

        self._video_writer = None

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

        # Start arduino (lazy start)
        from img_proc import arduino_proc as ap
        self.arduproc = ap.ArduProc(self, self.frame_res).loop()

        print('initiating...')
        time.sleep(2)

        Thread(target=self.update, daemon=True).start()

        return self

    def reset_writer(self):
        self._rec_start = time.time()
        # Reset frame counting
        self.frame_count = 0

        if self._video_writer is not None:
            self._video_writer.stdin.close()
        
        now = datetime.now()
        rec_dir = self.vid_dir/now.strftime('%m_%d')
        if not rec_dir.exists():
            rec_dir.mkdir(parents=True)
        rec_name = now.strftime('%m_%d_%H_%M.ts')
        log_name = now.strftime('%m_%d_%H_%M.log')

        # For logging
        self.rec_path = str(rec_dir/rec_name)
        self.log_path = str(rec_dir/log_name)

        self._video_writer = (
            ffmpeg
            .input('pipe:', format='rawvideo', pix_fmt='rgb24', 
                    s=f'{self.frame_res[0]}x{self.frame_res[1]}',
                    loglevel='panic', framerate=self.framerate)
            .output(self.rec_path,pix_fmt='yuv420p',
                    video_bitrate='0.8M')
            .overwrite_output()
            .run_async(pipe_stdin=True)
        )


    def update(self):
        while True:

            if self._stopped:
                self._vs.stop()
                if self._video_writer is not None:
                    self._video_writer.release()
                return

            new_frame = self._vs.read().copy()
            
            with self._lock:
                self.frame_count += 1
                self._video_writer.stdin.write(new_frame[...,2::-1].tobytes())

                # TODO: if too laggy, delete
                r, c = self.get_pos(img=new_frame)
                new_frame[r:r+5,c:c+5] = (0,255,255)
                self.frame = new_frame
                self._updated = True

            # Reset writer every 30 mins
            if (time.time() - self._rec_start) > VID_TIME:
                self.reset_writer()

    def write_log(self, event_type, event_content):
        with open(self.log_path,'a') as log_writer:
            now = datetime.now()
            log_list = [
                self.frame_count,
                now.month,
                now.day,
                now.hour,
                now.minute,
                now.second,
                event_type,
                event_content,
            ]
            log_str = ','.join([str(s) for s in log_list])+'\n'
            print(self.log_path)
            print(log_str)
            log_writer.write(log_str)

    def get_pos(self, img = None):
        """get_pos
        Detect head and return current position
        """
        if img is not None:
            new_frame = img
        else:
            new_frame = self._vs.read().copy()

        resized_frame = cv2.resize(new_frame, dsize=self.input_size_wh)
        self.interpreter.set_tensor(
            self.input_idx,
            resized_frame[np.newaxis,...].astype(np.float32).copy()
        )
        self.interpreter.invoke()
        heatmap = np.squeeze(self.interpreter.get_tensor(
            self.output_idx
        ))
        pos = np.unravel_index(heatmap.flatten().argmax(),
                               self.output_size_hw)
        pos = np.multiply(pos, self.resize_ratio).astype(np.int)
        return pos


    def draw_area(self, frame, area, color):
        r0 = area[0][0]
        r1 = area[1][0]
        c0 = area[0][1]
        c1 = area[1][1]
        frame[r0:r1,c0] = color
        frame[r0:r1,c1] = color
        frame[r0,c0:c1] = color
        frame[r1,c0:c1] = color
        return frame

    def is_updated(self):
        return self._updated

    def read(self):
        with self._lock:
            self._updated = False
            return self.frame

    def stop(self):
        self._stopped = True
