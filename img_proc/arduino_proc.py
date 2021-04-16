import pyfirmata as pf
from pyfirmata import util
from pyfirmata import ArduinoMega
import time
from threading import Thread, Lock
import random
import datetime

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

        self._rooms = [
            # Room 0
            {
                'corridor_leds' : [
                    self._leds[13],
                    self._leds[8],
                ],
                'button_leds' : [
                    self._leds[0],
                    self._leds[1],
                ],
                'buttons' : [
                    self._buttons[1],
                    self._buttons[0],
                ],
                'valve' : self._valves[3],
                'valve_avail' : True,
            },
            # Room 1
            {
                'corridor_leds' : [
                    self._leds[15],
                    self._leds[10],
                ],
                'button_leds' : [
                    self._leds[2],
                    self._leds[3],
                ],
                'buttons' : [
                    self._buttons[7],
                    self._buttons[6],
                ],
                'valve' : self._valves[0],
                'valve_avail' : True,
            },
            # Room 2
            {
                'corridor_leds' : [
                    self._leds[9],
                    self._leds[12],
                ],
                'button_leds' : [
                    self._leds[4],
                    self._leds[5],
                ],
                'buttons' : [
                    self._buttons[5],
                    self._buttons[4],
                ],
                'valve' : self._valves[1],
                'valve_avail' : True,
            },
            # Room 3
            {
                'corridor_leds' : [
                    self._leds[11],
                    self._leds[14],
                ],
                'button_leds' : [
                    self._leds[6],
                    self._leds[7],
                ],
                'buttons' : [
                    self._buttons[3],
                    self._buttons[2],
                ],
                'valve' : self._valves[2],
                'valve_avail' : True,
            },
        ]

        time.sleep(2)

        print('board initialized')

        self._lock = Lock()
        self._jackpot_prob = 0.05
        self._last_jackpot = 0
        self._jackpot_delay = 600

        self.led_all_off()

    def led_all_off(self):
        """led_all_off
        Turn off all LEDs

        """
        for l in self._leds:
            self.turn_off(l)
    
    def loop(self):
        Thread(target=self._loop_thread, daemon=True).start()
        return self

    def _loop_thread(self):
        while True:
            self.update()

    def update(self):
        """update
        This function is called every loop
        """
        for i, room in enumerate(self._rooms):
            button_pressed = False
            for b, bl in zip(room['buttons'], room['button_leds']):
                if b.read() and i != 2:
                    self.turn_on(bl)
                    button_pressed = True
                else:
                    self.turn_off(bl)
            if button_pressed and i != 2:
                if room['valve_avail']:
                    now = datetime.datetime.now()
                    print(f'room{i} button pressed'+now.strftime('%m%d%H%M%S'))
                if (room['valve_avail'] and 
                    random.random() < self._jackpot_prob and
                    time.time() - self._last_jackpot > self._jackpot_delay):
                    self.jackpot(room)
                else:
                    self.valve_timer(room, 0.05)
    
    def jackpot(self, room):
        """jackpot
        Things to do when jackpot happens
        """
        for cl in room['corridor_leds']:
            self.turn_on_timer(cl, 0.5)
        self.valve_timer(room, 0.5, 10)


    def valve_timer(self, room, open_time=0.05, cool_time=0.2):
        """valve_shot
        Open valve for a short time
        While the valve is open, or is in cool time,
        additional method calls will be ignored

        Parameters
        ----------
        room : Dict
            room dictionary

        open_time : the time the valve be stayed open, in seconds

        cool_time : the time the valve stays closed after open_time
        """
        if room['valve_avail']:
            Thread(
                target=self._valve_timer_thread,
                args=(room, open_time, cool_time),
                daemon=True,
            ).start()


    def _valve_timer_thread(self, room, open_time, cool_time):
        room['valve_avail'] = False
        self.turn_on(room['valve'])
        time.sleep(open_time)
        self.turn_off(room['valve'])
        time.sleep(cool_time)
        room['valve_avail'] = True


    def turn_on(self, pin:pf.Pin):
        """turn_on
        Turn on specified pin

        Parameter
        ---------
        pin : Pin
            pin to turn on. Expected to be 'OUTPUT' mode
        """

        with self._lock:
            pin.write(1)

    def turn_off(self, pin:pf.Pin):
        """turn_off
        Turn off specified pin

        Parameter
        ---------
        pin : Pin
            pin to turn off. Expected to be 'OUTPUT' mode
        """
        with self._lock:
            pin.write(0)


    def turn_on_timer(self, pin, sleep_time):
        """turn_on_timer
        Turn on specified Pin for specified time (in seconds)

        Parameter
        ---------
        pin : Pin
        
        sleep_time : float
            Time to turn on in seconds
        """
        Thread(
            target=self._turn_on_timer_thread, 
            args=(pin,sleep_time),
            daemon=True,
        ).start()

    def _turn_on_timer_thread(self, pin, sleep_time):
        """Thread function for turn_on_timer()
        """
        self.turn_on(pin)
        time.sleep(sleep_time)
        self.turn_off(pin)
    
        
