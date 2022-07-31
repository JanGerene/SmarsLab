""" SMARS Python module
provides functions and classes for the SMARS quad robot
based on Kevin McAleers work 
"""

import time
import logging

import yaml

import Adafruit_PCA9685

SLEEP_COUNT = 0.05  # time between pwm operations

logging.basicConfig(filename='smars.log', encoding='utf-8', level=logging.DEBUG)

try:
    pwm = Adafruit_PCA9685.PCA9685()
    time.sleep(1)
except OSError as error:
    logging.error("failed to initialise PCA9685 servo driver")
    do_not_use_pca_driver = True
    pwm = ""
except (RuntimeError) as ex:
    logging.error("error loading the Adafruit driver; loading without PCA9685")
    do_not_use_pca_driver = True
else :
    do_not_use_pca_driver = False
    logging.info("pca9685 driver loaded")
try:
    if do_not_use_pca_driver is False:
        pwm.set_pwm_freq(60)
        time.sleep(1)
except ValueError as error:
    log_string = "failed to set pwm frequency: " + error
    logging.error(log_string)


class Limb:
    _angle = 0
    min_pulse = 150
    max_pulse = 600


    def __init__(self, name: str, channel: int, minangle: int, maxangle: int, invert: bool):
        self._name = name
        self._channel = channel
        self._minangle = minangle
        self._maxangle = maxangle
        self._invert = invert

        if not self.invert:
            self.bodyangle = self._minangle
            self.stretchangle = self._maxangle
            self.swing_angle = (self._minangle / 2) + self._minangle
        else:
            self.bodyangle = self._maxangle
            self.stretchangle = self._minangle
            self.swing_angle = (self._maxangle - self._minangle) / 2
        self.current_angle = self.bodyangle
        self.angle = self.bodyangle

    
    @property 
    def name(self):
        return self._name

    @name.setter
    def name(self, value: str):
        names = [
            'LEFT_FRONT', 'LEFT_BACK', 'RIGHT_FRONT', 'RIGHT_BACK'
        ]
        if not value in names:
            raise ValueError('not a valid leg name')
        self._name = value


    @property
    def angle(self):
        return self._angle 

    @angle.setter
    def angle(self, value: int):
        """ 
        works out the value of the angle by mapping min and max angle, 
        moves limb to that position
        """
        if self._minangle <= value <= self._maxangle:
            self._angle = value
            mapmax = self.max_pulse - self.min_pulse
            percentage = (float(value) / 100) * 100
            pulse = int(((float(mapmax) / 100) * percentage) + self.min_pulse)
            if do_not_use_pca_driver is False:
                try:
                    pwm.set_pwm(self._channel, self._channel, pulse)
                except RuntimeError as error:
                    logging.warning("Failed to set PWM frequency")
                    logging.warning(error)
            self.current_angle = value
        else:
            raise ValueError("angle outside bounds")


    @property
    def channel(self):
        return self._channel

    @channel.setter
    def channel(self, value):
        if not isinstance(value, int):
            raise TypeError("channel must be an interger")
        if 0 <= value <= 15:
            self._channel = value
        else:
            raise ValueError('channel must be between 0-15')


    @property
    def minangle(self):
        return self._minangle

    @minangle.setter
    def minangle(self, value: int):
        if not isinstance(value, int):
            raise TypeError("minangle must be integer")
        if 0 <= value <= 180:
            self._minangle = value
        else:
            raise ValueError("minangle must be between 0-180")


    @property
    def maxangle(self):
        return self._maxangle

    @maxangle.setter
    def maxangle(self, value:int):
        if not isinstance(value, int):
            raise TypeError("maxangle must be integer")
        if 0 <= value <= 180:
            self._maxangle = value
        else:
            raise ValueError("maxangle must be between 0-180")   

    
    @property
    def invert(self):
        return self._invert

    @invert.setter
    def invert(self, value):
        if not isinstance(value, bool):
            raise TypeError("invert must be bool")
        self._invert = value


    def default(self):
        """
        set the limb to the default angle
        """
        self.angle = self.maxangle - self.minangle
        self.current_angle = self.maxangle - self.minangle


    def body(self):
        """
        set limb to its body position
        """
        if not self.invert:
            self.angle =self.bodyangle = self.minangle
        else:
            self.angle = self.bodyangle = self.maxangle
        self.current_angle = self.bodyangle


    def swing(self):
        """
        sets limb to swing position (45° halfway between body and stretch position
        """
        if not self.invert:
            swing_angle = (self.minangle / 2) + self.minangle
        else:
            swing_angle = (self.maxangle - self.minangle) / 2
        self.angle = self.swing_angle = self.current_angle = swing_angle
    

    def stretch(self):
        """
        sets limb to stretch position
        """
        if not self.invert:
            self.angle = self.maxangle
        else:
            self.angle = self.minangle
        self.str
        

class Leg(Limb):
    def tick(self):
        """
        each tick received changes the current angle, unless limit is reached which returns true
        """
        if self.name in ['LEFT_FRONT', 'LEFT_BACK']:
            if self.current_angle <= self.maxangle:
                self.current_angle += 2
                self.angle = self.current_angle
                return False
        if self.name in ['RIGHT_FRONT', 'RIGHT_BACK']:
            if self.current_angle >= self.minangle:
                self.current_angle -= 2
                self.angle = self.current_angle
                return False
        return True


    def untick(self):
        if self.name in ['RIGHT_BACK', 'RIGHT_FRONT']:
            if self.current_angle <= self.maxangle:
                self.current_angle += 2
                self.angle = self.current_angle
                return False
        if self.name in ['LEFT_BACK', 'LEFT_FRONT']:
            if self.current_angle >= self.minangle:
                self.current_angle -= 2
                self.angle = self.current_angle
                return False
        return True
       

class Foot(Limb):
    def down(self):
        """
        lowers limb to max angle
        """
        if not self.invert:
            self.angle = self.maxangle
        else:
            self.angle = self.minangle


    def up(self):
        """
        raises limb to min angle
        """
        if not self.invert:
            self.angle = self.minangle
        else:
            self.angle = self.maxangle


class SmarsRobot():
    """
    models the robot
    """
    def __init__(self):
        with open('config.yaml','r') as file:
            config = yaml.safe_load(file)
        self.feet = [Foot]
        limbs = config['feet']
        for limb in limbs:
            self.feet.append(Foot(name=limb['name'], channel=limb['channel'], minangle=limb['minangle'], maxangle=limb['maxangle'],invert=limb['invert']))
        self.legs = [Leg]
        limbs = config['legs']
        for limb in limbs:
            self.legs.append(Leg(name=limb['name'], channel=limb['channel'], minangle=limb['minangle'], maxangle=limb['maxangle'],invert=limb['invert']))


    def get_leg(self, name:str)->Leg:
        for leg in self.legs:
            if leg.name == name:
                return leg


    def get_foot(self, name:str)->Foot:
        for foot in self.feet:
            if foot.name == name:
                return foot


    def default(self):
        """
        set the limbs to the default position (90°)
        """
        for limb in self.legs:
            limb.default()
        for limb in self.feet:
            limb.default()


    def sit(self):
        """
        set each foot to down posistion
        """
        for foot in self.feet:
            foot.down()


    def stand(self):
        """
        set each foot to up posistion
        """
        for foot in self.feet:
            foot.up()



    def swing(self):
        """
        move legs to swing position, robot forms a giant X shape
        """
        for index, foot in enumerate(self.feet):
            foot.down()
            time.sleep(SLEEP_COUNT)
            self.legs[index].swing()
            time.sleep(SLEEP_COUNT)
            foot.up()
            time.sleep(SLEEP_COUNT)



    def walkforward(self, steps: int=None):
        """
        walk forward number of steps.
        if steps not defined take single step
        """
        if steps is None:
            steps = 1

        self.sit()
        self.get_leg('LEFT_FRONT').body()
        self.get_leg('LEFT_BACK').body()
        self.get_leg('RIGHT_FRONT').swing()
        self.get_leg('RIGHT_BACK').swing()
        self.stand()

        for _ in range(steps):
            for index, leg in enumerate(self.legs):
                if not leg.tick():
                    leg.tick()
                else:
                    self.feet[index].down()
                    time.sleep(SLEEP_COUNT)
                    if not leg.invert:
                        if leg.name == "RIGHT_FRONT":
                            leg.stretch()
                        else:
                            leg.body()
                    else:
                        if leg.name == "RIGHT_BACK":
                            leg.body()
                        else:
                            leg.stretch()
                    time.sleep(SLEEP_COUNT)
                    self.feet[index].up()
                    time.sleep(SLEEP_COUNT)


    def walkbackward(self, steps: int=None):
        """
        walk backward number of steps.
        if steps not defined take single step
        """
        if steps is None:
            steps = 1

        self.sit()
        self.get_leg('LEFT_FRONT').body()
        self.get_leg('LEFT_BACK').body()
        self.get_leg('RIGHT_FRONT').swing()
        self.get_leg('RIGHT_BACK').swing()
        self.stand()

        for _ in range(steps):
            for index, leg in enumerate(self.legs):
                if not leg.untick():
                    leg.untick()
                else:
                    self.feet[index].down()
                    time.sleep(SLEEP_COUNT)
                    if not leg.invert:
                        if leg.name == "LEFT_BACK":
                            leg.stretch()
                        else:
                            leg.body()
                    else:
                        if leg.name == "LEFT_FRONT":
                            leg.body()
                        else:
                            leg.stretch()
                    time.sleep(SLEEP_COUNT)
                    self.feet[index].up()
                    time.sleep(SLEEP_COUNT)


    def turnleft(self):
        self.swing()
        self.get_leg('LEFT_FRONT').stretch()
        self.get_leg('LEFT_BACK').body()
        self.get_leg('RIGHT_FRONT').body()
        self.get_leg('RIGHT_BACK').stretch()       
        time.sleep(SLEEP_COUNT)
        self.swing()


    def turnright(self):
        self.swing()
        self.get_leg('RIGHT_FRONT').stretch()
        self.get_leg('RIGHT_BACK').body()
        self.get_leg('LEFT_FRONT').body()
        self.get_leg('LEFT_BACK').stretch()       
        time.sleep(SLEEP_COUNT)
        self.swing()       


    def wiggle(self, count: int=None):
        """
        wiggle but
        """
        if count is None:
            count = 1

        self.sit()
        self.get_foot("LEFT_BACK").up()
        self.get_foot('RIGHT_BACK').up()
        time.sleep(SLEEP_COUNT)

        LEFT_BACK = self.get_leg('LEFT_BACK')
        RIGHT_BACK = self.get_leg('RIGHT_BACK')
        for _ in range(count):
            LEFT_BACK.body()
            RIGHT_BACK.stretch()
            time.sleep(SLEEP_COUNT * 5)
            LEFT_BACK.stretch()
            RIGHT_BACK.body()
            time.sleep(SLEEP_COUNT * 5)

        self.stand()

    
    def get_telemetry(self):
        """
        returns a list of measurements
        """
        telemetry = []
        for limb in self.legs:
            telemetry.append([limb.name, limb.angle])
        for limb in self.feet:
            telemetry.append([limb.name, limb.angle])
        return telemetry