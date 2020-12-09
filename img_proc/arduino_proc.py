import pyfirmata as pf
from pyfirmata import Arduino
import time

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
                'R' : self._board.digital[5],
                'G' : self._board.digital[3],
                'B' : self._board.digital[4]
            },
            {
                'R' : self._board.digital[8],
                'G' : self._board.digital[9],
                'B' : self._board.digital[10],
            }
        ]
        print('board initialized')

    def turn_on(self, set_num, color):
        """turn_on
        Turn on specified LED
        
        Parameter
        ---------
        set_num : int
        
        color : str
            One of 'R','G','B'
        """
        self._rgb[set_num][color].write(1)
    
    def turn_off(self, set_num, color) :
        """turn_on
        Turn off specified LED
        
        Parameter
        ---------
        set_num : int
        
        color : str
            One of 'R','G','B'
        """
        self._rgb[set_num][color].write(0)
    
    def drop_food(self):
        """drop_food
        1. Turn servo to 140 degree
        2. Wait 3 seconds
        3. Turn servo back to 10 degree
        """
        self._servo.write(140)
        time.sleep(3)
        self._servo.write(10)
