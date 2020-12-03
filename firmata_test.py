import pyfirmata
import time

board = pyfirmata.Arduino('COM3')
servo = board.digital[7]
servo.mode = pyfirmata.SERVO

for _ in range(10):
    servo.write(100)
    time.sleep(2)
    servo.write(20)
    time.sleep(2)