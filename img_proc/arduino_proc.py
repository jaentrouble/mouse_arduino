import pyfirmata as pf
from pyfirmata import util
from pyfirmata import ArduinoMega
import time
from threading import Thread, Lock
import random
import datetime
from .detector import ImageProcessor
import numpy as np

BUT_PRS = 'button_pressed'
CUR_POS = 'pos(x_y)'
CUR_ROOM = 'current_room'
PIN_ON = 'pin_on'
PIN_OFF = 'pin_off'
NOR_REW = 'normal_reward'
FAILED = 'failed'
TIME_OVR = 'time_over'
TEST_ST = 'test_start'

ARD_DIR = '/dev/ttyACM0'
JACKPOT_PROB = 0.05
JACKPOT_COOLTIME = 0
JACKPOT_BURSTS = 20
NORMAL_BURSTS = 3
NORMAL_COOLTIME = 300

BURST_INTERVAL = 0.2
BURST_DURATION = 0.05

# TARGET_HOURS = list(range(0,7)) + list(range(22,24))
TARGET_HOURS = list(range(7,19))
TARGET_MINS = list(range(0,60,10))
TEST_TIME = 120
INTER_BUTTON = 3


class ArduProc():
    """ArduProc
    Wrapper around Arduino
    """
    def __init__(self, detector:ImageProcessor, frame_res=(640,480), passive_mode=False):
        self._detector = detector
        self.button_detected_reset()
        self._button_log = np.zeros((4,2))

        print('initializing board...')
        self._board = ArduinoMega(ARD_DIR)
        self._frame_res = frame_res
        self._passive_mode = passive_mode
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
                'valve' : [self._valves[3],],
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
                'valve' : [self._valves[0],],
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
                'valve' : [self._valves[1],],
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
                'valve' : [self._valves[2],],
                'valve_avail' : True,
            },
        ]

        time.sleep(2)

        print('board initialized')

        self._lock = Lock()
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
        for r in range(4):
            for l in range(2):
                self.turn_off(r, 'corridor_leds', l)
                self.turn_off(r, 'button_leds', l)

    def _button_detect_loop_thread(self):
        while True:
            self.button_detection()
    
    def button_detection(self):
        for i, room in enumerate(self._rooms):
            for j, button in enumerate(room['buttons']):
                if button.read():
                    self._buttons_detected[i,j] = True


    def button_detected_reset(self):
        self._buttons_detected = np.zeros((4,2),dtype=bool)

    def loop(self):
        Thread(target=self._loop_thread, daemon=True).start()
        Thread(target=self._button_detect_loop_thread, daemon=True).start()
        return self

    def _loop_thread(self):
        while True:
            self.update()

    def update(self):
        """update
        This function is called every loop
        """
        time.sleep(0.1)
        now = datetime.datetime.now()

        
        # Log when any button is pressed
        detection_hold =  self._buttons_detected.copy()
        self.button_detected_reset()
        button_pressed = np.any(detection_hold)
        if button_pressed:
            rooms, buttons = np.where(detection_hold)
            for room,button in zip(rooms,buttons):
                self._detector.write_log(BUT_PRS, str(room)+'/'+str(button))


        if button_pressed:
            y, x = self._detector.get_pos()
            if x>self._frame_res[0]/2 and y>self._frame_res[1]/2:
                cur_room = 1
            elif x<=self._frame_res[0]/2 and y>self._frame_res[1]/2:
                cur_room = 0
            elif x>self._frame_res[0]/2 and y<=self._frame_res[1]/2:
                cur_room = 2
            elif x<=self._frame_res[0]/2 and y<=self._frame_res[1]/2:
                cur_room = 3
            self._detector.write_log(CUR_POS, str(x)+'/'+str(y))
            self._detector.write_log(CUR_ROOM, str(cur_room))

        # Sanity check
        # Turn on leds when button is pressed
        # for r in range(4):
        #     for b in range(2):
        #         if detection_hold[r,b]:
        #             self.turn_on(r, 'button_leds', b)
        #             self.normal_reward(r)
        #         else:
        #             self.turn_off(r,'button_leds', b, no_log=True)
                        


        if (now.hour in TARGET_HOURS) and (now.minute in TARGET_MINS) \
            and not self._test_finished:
            if not self._waiting:
                self.led_all_off()
                self._waiting = True
                self._last_test = time.time()
                self._target_room = (cur_room+2)%4
                self._target_button = random.randint(0,1)
                self._detector.write_log(
                    TEST_ST,
                    str(self._target_room)+'/'+str(self._target_button)
                )
                # Both way
                self.turn_on(cur_room,'corridor_leds',0)
                self.turn_on(cur_room,'corridor_leds',1)
                self.turn_on((cur_room+1)%4,'corridor_leds',1)
                self.turn_on((cur_room-1)%4,'corridor_leds',0)

        if self._waiting:
            # target_room = self._target_rooms[-1][0]
            # target_idx = self._target_rooms[-1][1]
            # target_button = target_room['buttons'][target_idx]
            if button_pressed:
                if detection_hold[self._target_room,self._target_button]:
                    self.normal_reward(self._target_room)
                    self._detector.write_log(NOR_REW, 
                        str(self._target_room)+'/'+str(self._target_button))
                else:
                    self._detector.write_log(FAILED, 
                        str(self._target_room)+'/'+str(self._target_button))
                self.led_all_off()
                self._waiting = False
                self._test_finished = True


        if time.time()- self._last_test>TEST_TIME:
            if self._waiting:
                self._detector.write_log(
                    TIME_OVR,
                    str(self._target_room)+'/'+str(self._target_button)
                )
            self._waiting = False
            self.led_all_off()
            self._test_finished = False


    
    def jackpot(self, room):
        """jackpot
        Things to do when jackpot happens
        """
        self._last_jackpot = time.time()
        for i in range(2):
            self.turn_on_timer(room, 'corridor_leds', i, 0.5)
        self.valve_timer(room, BURST_DURATION, BURST_INTERVAL,
                         JACKPOT_COOLTIME, JACKPOT_BURSTS)

    def normal_reward(self,room):
        self.valve_timer(room, BURST_DURATION, BURST_INTERVAL,
                         NORMAL_COOLTIME,NORMAL_BURSTS)


    def valve_timer(self, room:int, open_time:float, interval_time:float,
                    cool_time:float, count:int):
        """valve_shot
        Open valve for a short time, count times
        While the valve is open, or is in cool time,
        additional method calls will be ignored

        Parameters
        ----------
        room : int
            room index

        open_time : float
            the time the valve be stayed open, in seconds

        interval_time : float
            the time between each burst (if count > 1)

        cool_time : float
            the time the valve stays closed after open_time

        count : int
            number of bursts
        """
        if self._rooms[room]['valve_avail']:
            Thread(
                target=self._valve_timer_thread,
                args=(room, open_time, interval_time, cool_time, count),
                daemon=True,
            ).start()


    def _valve_timer_thread(self, room, open_time, interval_time,
                             cool_time, count):
        self._rooms[room]['valve_avail'] = False
        for c in range(count):
            self.turn_on(room,'valve')
            time.sleep(open_time)
            self.turn_off(room,'valve')
            if c < count-1:
                time.sleep(interval_time)
        time.sleep(cool_time)
        self._rooms[room]['valve_avail'] = True


    def turn_on(self, room, pin_type:str, index=0):
        """turn_on
        Turn on specified pin

        Parameter
        ---------
        room : int
            target room index
        pin_type : str
            target pin type
        index : int
            index of target pin (of the room)
        """

        with self._lock:
            self._rooms[room][pin_type][index].write(1)
            self._detector.write_log(PIN_ON,
                '/'.join([str(room),pin_type,str(index)]))

    def turn_off(self, room, pin_type:str, index=0, no_log=False):
        """turn_off
        Turn off specified pin

        Parameter
        ---------
        room : int
            target room index
        pin_type : str
            target pin type
        index : int
            index of target pin (of the room)
        """
        with self._lock:
            self._rooms[room][pin_type][index].write(0)
            if not no_log:
                self._detector.write_log(PIN_OFF,
                    '/'.join([str(room),pin_type,str(index)]))


    def turn_on_timer(self, room, pin_type:str, index, sleep_time):
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
            args=(room, pin_type, index,sleep_time),
            daemon=True,
        ).start()

    def _turn_on_timer_thread(self, room, pin_type:str, index, sleep_time):
        """Thread function for turn_on_timer()
        """
        self.turn_on(room, pin_type, index)
        time.sleep(sleep_time)
        self.turn_off(room, pin_type, index)
    
        
