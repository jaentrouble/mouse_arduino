import pyfirmata as pf
from pyfirmata import Arduino
import time
from threading import Thread, Lock

ARD_DIR = '/dev/ttyACM0'

class ArduProc():
    """ArduProc
    Wrapper around Arduino
    """
    def __init__(self):
        print('initializing board...')
        self._board = Arduino(ARD_DIR)
        self._servo = self._board.digital[2]
        self._servo.mode = pf.SERVO
        self._rgb = [
            {
                'R' : self._board.digital[8],
                'G' : self._board.digital[9],
                'B' : self._board.digital[10],
            },
            {
                'R' : self._board.digital[5],
                'G' : self._board.digital[3],
                'B' : self._board.digital[4]
            },
        ]
        print('board initialized')
        self._lock = Lock()

    def turn_on(self, set_num, color):
        """turn_on
        Turn on specified LED
        
        Parameter
        ---------
        set_num : int
        
        color : str
            One of 'R','G','B'
        """
        with self._lock:
            self._rgb[set_num][color].write(1)

    def turn_on_timer(self, set_num, color, sleep_time=1):
        """turn_on_timer
        Turn on specified LED for specified time (in seconds)

        Parameter
        ---------
        set_num : int
        
        color : str
            One of 'R','G','B'
        sleep_time : float
            Time to turn on in seconds
        """
        Thread(
            target=self._turn_on_timer, 
            args=(set_num,color,sleep_time),
            daemon=True,
        ).start()

    def _turn_on_timer(self, set_num, color, sleep_time):
        """Thread function for turn_on_timer()
        """
        self.turn_on(set_num, color)
        time.sleep(sleep_time)
        self.turn_off(set_num, color)
    
    def turn_off(self, set_num, color) :
        """turn_on
        Turn off specified LED
        
        Parameter
        ---------
        set_num : int
        
        color : str
            One of 'R','G','B'
        """
        with self._lock:
            self._rgb[set_num][color].write(0)

    def turn_off_all(self):
        """turn_off_all
        Turn off every LEDs
        """
        with self._lock:
            for pinset in self._rgb:
                for color, pin in pinset.items():
                    pin.write(0)
        
    def drop_food(self):
        """drop_food
        1. Turn servo to 140 degree
        2. Wait 3 seconds
        3. Turn servo back to 10 degree
        """
        Thread(target=self._drop_food,daemon=True).start()

    def _drop_food(self):
        """drop_food()'s thread function
        Do not call this directly - It sleeps 3 seconds
        """
        with self._lock:
            self._servo.write(140)
        time.sleep(3)
        with self._lock:
            self._servo.write(10)
