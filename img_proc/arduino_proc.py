import pyfirmata as pf
from pyfirmata import util
from pyfirmata import ArduinoMega
import time
from threading import Thread, Lock

ARD_DIR = '/dev/ttyACM0'

class ArduProc():
    """ArduProc
    Wrapper around Arduino
    """
    def __init__(self):
        print('initializing board...')
        self._board = ArduinoMega(ARD_DIR)
        util.Iterator(self._board).start()
        self._leds = [
            self._board.digital[i] for i in range(22,54,2)
        ]
        self._valves = [
            self._board.digital[i] for i in range(47,55,2)
        ]

        self._buttons = [
            self._board.digital[i] for i in range(23,39,2)
        ]
        for b in self._buttons:
            b.mode = pf.INPUT

        #TODO: check buttons number
        self._room1 = {
            'corridor_leds' : [
                self._leds[14],
                self._leds[9],
            ],
            'button_leds' : [
                self._leds[1],
                self._leds[2],
            ],
            'buttons' : [
                self._buttons[],
                self._buttons[],
            ],
            'valve' : self._valves[4]
        }

        self._room2 = {
            'corridor_leds' : [
                self._leds[16],
                self._leds[11],
            ],
            'button_leds' : [
                self._leds[3],
                self._leds[4],
            ],
            'buttons' : [
                self._buttons[],
                self._buttons[],
            ],
            'valve' : self._valves[1]
        }

        self._room3 = {
            'corridor_leds' : [
                self._leds[10],
                self._leds[13],
            ],
            'button_leds' : [
                self._leds[5],
                self._leds[6],
            ],
            'buttons' : [
                self._buttons[],
                self._buttons[],
            ],
            'valve' : self._valves[2]
        }

        self._room4 = {
            'corridor_leds' : [
                self._leds[12],
                self._leds[15],
            ],
            'button_leds' : [
                self._leds[7],
                self._leds[8],
            ],
            'buttons' : [
                self._buttons[],
                self._buttons[],
            ],
            'valve' : self._valves[4]
        }

        print('board initialized')
        self._lock = Lock()

    def led_all_off(self):
        """led_all_off
        Turn off all LEDs

        """
        with self._lock:
            for l in self._leds:
                l.write(0)

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
