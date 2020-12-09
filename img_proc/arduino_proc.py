import pyfirmata as pf
from pyfirmata import Arduino

ARD_DIR = '/dev/ttyACM0'

class ArduProc():
    """ArduProc
    Wrapper around Arduino
    """
    def __init__(self):
        self.board = Arduino(ARD_DIR)
        self.servo = 
        self.rgb = [
            {
                'R' : self.board.digital[3],
                'G' : self.board.digital[4],
                'B' : self.board.digital[5]
            },
            {
                'R' : self.board.digital[8],
                'G' : self.board.digital[9],
                'B' : self.board.digital[10],
            }
        ]