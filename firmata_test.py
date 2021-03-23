import pyfirmata
from pyfirmata import util
import time

board = pyfirmata.ArduinoMega('COM4')
util.Iterator(board).start()
led = board.digital[22]
led.mode = pyfirmata.OUTPUT

button = board.digital[34]
button.mode = pyfirmata.INPUT

sol = board.digital[40]
sol.mode = pyfirmata.OUTPUT

while True:
    if button.read():
        led.write(1)
        sol.write(1)
    else:
        led.write(0)
        sol.write(0)