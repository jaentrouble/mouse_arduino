from .arduino_proc import ArduProc
from datetime import datetime
import time
import numpy as np

AREA0 = [[0,440],[200,639]]
AREA1 = [[290,0],[479,210]]
AREA = [
    AREA0,
    AREA1,
]
TARGET_HOURS = list(range(0,8)) + list(range(21,24))
TARGET_MINS = range(0,60,10)
# WAIT_TIME should not exceed 60 seconds
WAIT_TIME = 30
STAY_TIME = 3

class PosProc():
    """PosProc
    Gets current position of the mouse, and determines what to do.
    """
    def __init__(self):
        self.arduino = ArduProc()
        self.reward_given = False
        self.waiting = False
        self.waiting_start = None
        self.waited = False
        self.target_area = None
        self.target_idx = None

        self.inside_start = None
        self.was_inside = False

        self.rewarded_time = None

        self._center0 = np.mean(AREA0,axis=0)
        self._center1 = np.mean(AREA1,axis=0)

    def update_pos(self, pos):
        """update_pos
        
        Parameter
        ---------
        pos : (Row, Col)

        Return
        ------
        Tuple of three bools:
            (self.waiting, self.was_inside, self.reward_given)
        """
        # Do nothing if there's no reward left to give
        if self.reward_given:
            # If it is the first time after the reward was given
            # And at least a second has passed
            if self.waiting and (time.time()-self.rewarded_time)>1:
                self.arduino.turn_off_all()
                self.waiting = False
                self.waited = False
                self.waiting_start = None
                self.target_idx = None
                self.rewarded_time = None
        else:
            now = datetime.now()
            # If it is time to test
            if (now.hour in TARGET_HOURS) and (now.minute in TARGET_MINS) :
                # If not waiting (Red LED off)
                if not self.waiting:
                    # If it is the first call after becoming target time
                    if not self.waited:
                        self.waiting = True
                        self.waited = True
                        self.waiting_start = time.time()
                        # Select area which is farther away
                        dist0 = np.linalg.norm(self._center0-pos)
                        dist1 = np.linalg.norm(self._center1-pos)
                        if dist0 > dist1 : 
                            self.target_idx = 0
                            self.target_area = AREA0
                            self.arduino.turn_on(0,'R')
                        else:
                            self.target_idx = 1
                            self.target_area = AREA1
                            self.arduino.turn_on(1,'R')
                # If waiting (Red LED on)
                else:
                    # If the time limit has not passed
                    if time.time() - self.waiting_start < WAIT_TIME:
                        # If the mouse is inside the target area
                        if self.inside(pos, self.target_area):
                            # If mouse is now entering the area
                            # To prevent sending arduino too much orders
                            if not self.was_inside:
                                self.was_inside = True
                                self.arduino.turn_on(self.target_idx,'G')
                                self.inside_start = time.time()
                            # If the mouse was already in the area
                            else:
                                # If the mouse stayed long enough
                                # Drop food and turn on the Blue LED
                                if time.time()-self.inside_start > STAY_TIME:
                                    self.arduino.drop_food()
                                    self.reward_given = True
                                    self.arduino.turn_on(self.target_idx,'B')
                                    self.rewarded_time = time.time()
                                    # Do not set self.waiting to False here
                        else:
                            if self.was_inside:
                                self.was_inside = False
                                self.arduino.turn_off(self.target_idx,'G')
                    # If the time limit has passed, 
                    # but still in target hour/min
                    else:
                        self.waiting = False
                        self.arduino.turn_off_all()

            # If it is not testing time
            else:
                # Just in case waiting time exceeds 1 minutes
                if self.waiting:
                    self.arduino.turn_off_all()
                self.waiting = False
                self.waited = False
                self.waiting_start = None
                self.target_idx = None
                self.target_area = None
                self.rewarded_time = None

        return self.waiting, self.was_inside, self.reward_given

    def inside(self, pos, area):
        return np.all(np.logical_and(np.less(area[0],pos),np.less(pos,area[1])))