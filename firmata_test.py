import pyfirmata
from pyfirmata import util
import time

board = pyfirmata.ArduinoMega('/dev/cu.usbmodem141101')
util.Iterator(board).start()
pumps = [
    board.digital[47],
    board.digital[51]
]
for pump in pumps:
    pump.mode = pyfirmata.OUTPUT

leds = [
    board.digital[50],
    board.digital[52]
]
for led in leds:
    led.mode = pyfirmata.OUTPUT

buttons = [
    board.digital[35],
    board.digital[37]
]
for button in buttons:
    button.mode = pyfirmata.INPUT

while True:
    leds[0].write(1)
    leds[1].write(0)
    time.sleep(0.5)
    leds[0].write(0)
    leds[1].write(1)
    time.sleep(0.5)
# while True:
#     for i, button in enumerate(buttons):
#         pumps[i].write(button.read())
#         leds[i].write(button.read())
