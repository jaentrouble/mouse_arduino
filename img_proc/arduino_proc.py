import pyfirmata as pf
from pyfirmata import util
from pyfirmata import ArduinoMega
import time
from threading import Thread, Lock
import random
import datetime

ARD_DIR = '/dev/ttyACM0'
JACKPOT_PROB = 0.05
JACKPOT_COOLTIME = 0
JACKPOT_BURSTS = 20
NORMAL_BURSTS = 3
NORMAL_COOLTIME = 0

BURST_INTERVAL = 0.2
BURST_DURATION = 0.05

TARGET_HOURS = list(range(0,7)) + list(range(22,24))
TARGET_MINS = list(range(0,60,20))
TEST_TIME = 120
INTER_BUTTON = 3

class ArduProc():
    """ArduProc
    Wrapper around Arduino
    """
    def __init__(self, frame_res=(640,480)):
        print('initializing board...')
        self._board = ArduinoMega(ARD_DIR)
        self._pos = (0,0)
        self._frame_res = frame_res
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
        self._pos_lock = Lock()
        self._jackpot_prob = JACKPOT_PROB
        self._jackpot_delay = 600
        self._waiting = False
        # Just in case test finishes within 1 min
        self._test_finished=False
        self._last_test = 0
        self._last_button = 0
        self._target_rooms = []

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
        now = datetime.datetime.now()
        with self._pos_lock:
            y, x = self._pos
        if x>self._frame_res[0]/2 and y>self._frame_res[1]/2:
            cur_room = 1
        elif x<=self._frame_res[0]/2 and y>self._frame_res[1]/2:
            cur_room = 0
        elif x>self._frame_res[0]/2 and y<=self._frame_res[1]/2:
            cur_room = 2
        elif x<=self._frame_res[0]/2 and y<=self._frame_res[1]/2:
            cur_room = 3


        if (now.hour in TARGET_HOURS) and (now.minute in TARGET_MINS) \
            and not self._test_finished:
            if not self._waiting:
                self.led_all_off()
                self._waiting = True
                self._last_test = time.time()
                self._target_rooms = []
                clock_wise = random.random()<0.5
                if clock_wise:
                    # Target room, target button
                    self._target_rooms.append(
                        (self._rooms[(cur_room-2)%4], random.randint(0,1)))
                    self._target_rooms.append(
                        (self._rooms[(cur_room-1)%4], random.randint(0,1)))
                    self.turn_on(self._target_rooms[1][0]['corridor_leds'][0])
                    self.turn_on(self._rooms[cur_room]['corridor_leds'][0])
                else:
                    self._target_rooms.append(
                        (self._rooms[(cur_room+2)%4], random.randint(0,1)))
                    self._target_rooms.append(
                        (self._rooms[(cur_room+1)%4], random.randint(0,1)))
                    self.turn_on(self._target_rooms[1][0]['corridor_leds'][1])
                    self.turn_on(self._rooms[cur_room]['corridor_leds'][1])
                for tr, tb in self._target_rooms:
                    self.turn_on(tr['button_leds'][tb])

        if self._waiting:
            target_room = self._target_rooms[-1][0]
            target_idx = self._target_rooms[-1][1]
            target_button = target_room['buttons'][target_idx]
            if not target_button.read() and \
                time.time()-self._last_button>INTER_BUTTON:
                self._last_button = time.time()
                self._target_rooms.pop()
                if len(self._target_rooms)>0:
                    self.turn_off(target_room['button_leds'][target_idx])
                    self.normal_reward(target_room)
                else:
                    self.led_all_off()
                    self.jackpot(target_room)
                    self._waiting = False
                    self._test_finished = True
        if time.time()- self._last_test>TEST_TIME:
            self._waiting = False
            self.led_all_off()
            self._test_finished = False

    def update_pos(self, pos):
        with self._pos_lock:
            self._pos = pos
    
    def jackpot(self, room):
        """jackpot
        Things to do when jackpot happens
        """
        self._last_jackpot = time.time()
        for cl in room['corridor_leds']:
            self.turn_on_timer(cl, 0.5)
        self.valve_timer(room, BURST_DURATION, BURST_INTERVAL,
                         JACKPOT_COOLTIME, JACKPOT_BURSTS)

    def normal_reward(self,room):
        self.valve_timer(room, BURST_DURATION, BURST_INTERVAL,
                         NORMAL_COOLTIME,NORMAL_BURSTS)


    def valve_timer(self, room, open_time:float, interval_time:float,
                    cool_time:float, count:int):
        """valve_shot
        Open valve for a short time, count times
        While the valve is open, or is in cool time,
        additional method calls will be ignored

        Parameters
        ----------
        room : Dict
            room dictionary

        open_time : float
            the time the valve be stayed open, in seconds

        interval_time : float
            the time between each burst (if count > 1)

        cool_time : float
            the time the valve stays closed after open_time

        count : int
            number of bursts
        """
        if room['valve_avail']:
            Thread(
                target=self._valve_timer_thread,
                args=(room, open_time, interval_time, cool_time, count),
                daemon=True,
            ).start()


    def _valve_timer_thread(self, room, open_time, interval_time,
                             cool_time, count):
        room['valve_avail'] = False
        for c in range(count):
            self.turn_on(room['valve'])
            time.sleep(open_time)
            self.turn_off(room['valve'])
            if c < count-1:
                time.sleep(interval_time)
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
    
        
