import pyfirmata
import time

board = pyfirmata.ArduinoMega('COM4')
d = board.digital[32]
d.mode = pyfirmata.OUTPUT

for _ in range(10):
    d.write(1)
    time.sleep(0.5)
    d.write(0)
    time.sleep(0.5)