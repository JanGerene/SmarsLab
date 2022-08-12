""" SMARS Python module
provides functions and classes for the SMARS quad robot
based on Kevin McAleers work 
"""

from re import S
from time import sleep
import logging

import yaml

logger = logging.getLogger(__name__)
from adafruit_pca9685 import PCA9685
from adafruit_motor import servo
try:
    from board import SCL, SDA
    import busio
except (NotImplementedError):
    logger.warning("circuitpython not supported on this platform")
    raise


SLEEP_COUNT = 0.1  # time between pwm operations


try:
    i2c = busio.I2C(SCL, SDA)
    pca = PCA9685(i2c)
    pca.frequency = 50
except:
    logger.error("failed to initialise PCA9685 servo driver") 
    raise


class Limb:
    def __init__(self, name: str, channel: int, min_angle: int, max_angle: int, invert: bool):
        self._name = name
        self._channel = channel
        self._min_angle = min_angle
        self._max_angle = max_angle
        self._invert = invert
        self._angle = min_angle
        self._servo = servo.Servo(pca.channels[channel])


    @property 
    def name(self)->str:
        return self._name


    @property
    def angle(self)->int:
        """
        current angle of limb
        """
        return self._angle 

    @angle.setter
    def angle(self, value: int):
        """ 
        moves limb to position
        """
        if self._min_angle <= value <= self._max_angle:
            self._angle = value
            self._servo.angle = value
            self._current_angle = value
        else:
            raise ValueError(f"angle.setter: angle = {value}: outside bounds")


    @property
    def channel(self):
        return self._channel

    
    @property
    def invert(self):
        return self._invert
    

class Leg(Limb):
    def __init__(self, name: str, channel: int, min_angle: int, max_angle: int, invert: bool):
        super().__init__(name, channel, min_angle, max_angle, invert)
        if self._invert:
            self._body_angle = self._min_angle
            self._stretch_angle = self._max_angle
            self._swing_angle = (self._min_angle / 2) + self._min_angle
        else:
            self._body_angle = self._max_angle
            self._stretch_angle = self._min_angle
            self._swing_angle = (self._max_angle - self._min_angle) / 2
        self.body()


    def __str__(self):
        return(f"""Limb: {self._name}, channel: {self._channel}, invertr: {self._invert},
        _min_angle: {self._min_angle}, _max_angle: {self._max_angle},
        _stretch_angle: {self._stretch_angle}, _body_angle: {self._body_angle}
        angle: {self.angle} """)


    def body(self):
        """
        set leg to its body position
        """
        self.angle = self._body_angle
        sleep(SLEEP_COUNT)


    def swing(self):
        """
        sets leg to swing position (45° halfway between body and stretch position
        """
        self.angle = self._swing_angle
        sleep(SLEEP_COUNT)
    

    def stretch(self):
        """
        sets leg to stretch position
        """
        self.angle = self._stretch_angle
        sleep(SLEEP_COUNT)


    def tick(self):
        """
        each tick received changes the current angle, unless limit is reached which returns true
        """
        if self.name in ['LEFT_FRONT', 'LEFT_BACK']:
            self._current_angle += 2
            if self._current_angle <= self._max_angle:
                self.angle = self._current_angle
                return False
            else:
                return True
        elif self.name in ['RIGHT_FRONT', 'RIGHT_BACK']:
            self._current_angle -= 2
            if self._current_angle >=  self._min_angle:
                self.angle = self._current_angle
                return False
            else:
                return True


    def untick(self):
        if self.name in ['RIGHT_BACK', 'RIGHT_FRONT']:
            self._current_angle += 2
            if self._current_angle > self._max_angle:
                return True
        elif self.name in ['LEFT_BACK', 'LEFT_FRONT']:
            self._current_angle -= 2
            if self._current_angle < self._min_angle:
                return True
        self.angle = self._current_angle
        return False
       

class Foot(Limb):
    def __init__(self, name: str, channel: int, min_angle: int, max_angle: int, invert: bool):
        super().__init__(name, channel, min_angle, max_angle, invert)
        if self._invert:
            self._down_angle = self._min_angle
            self._up_angle = self._max_angle
        else:
            self._down_angle = self._max_angle
            self._up_angle = self._min_angle

    def down(self):
        """
        lowers foot
        """
        self.angle = self._down_angle


    def up(self):
        """
        raises foot
        """
        self.angle = self._up_angle


class SmarsRobot():
    """
    models the robot
    """
    def __init__(self):
        with open('config.yaml','r') as file:
            config = yaml.safe_load(file)
        self.feet = []
        limbs = config['feet']
        for limb in limbs:
            self.feet.append(Foot(name=limb['name'], channel=limb['channel'], min_angle=limb['minangle'], max_angle=limb['maxangle'],invert=limb['invert']))
        limbs = config['legs']
        self.legs = []
        for limb in limbs:
            self.legs.append(Leg(name=limb['name'], channel=limb['channel'], min_angle=limb['minangle'], max_angle=limb['maxangle'],invert=limb['invert']))
        logger.debug(f"we have {len(self.legs)} legs and {len(self.feet)} feet")

    @property
    def telemetry(self):
        """
        returns a list of measurements
        """
        _telemetry = []
        _telemetry.append(['legs', ''])
        for limb in self.legs:
            _telemetry.append([limb.name, limb.angle])
        _telemetry.append(['feet', ''])
        for limb in self.feet:
            _telemetry.append([limb.name, limb.angle])
        return _telemetry
        
        
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
        logger.debug("default position")
        for leg in self.legs:
            leg.default()
        for foot in self.feet:
            foot.default()


    def sit(self):
        """
        set each foot to up posistion
        """
        logger.debug("sitting down")
        for foot in self.feet:
            foot.up()


    def stand(self):
        """
        set each foot to down posistion
        """
        logger.debug("standing up")
        for foot in self.feet:
            foot.down()


    def swing(self):
        """
        move legs to swing position, robot forms a giant X shape
        """
        logger.debug("swinging")
        for index, foot in enumerate(self.feet):
            foot.up()
            sleep(SLEEP_COUNT)
            self.legs[index].swing()
            sleep(SLEEP_COUNT)
            foot.down()
            sleep(SLEEP_COUNT)


    def stretch(self):
        """
        move all limbs to strectch position
        legs are stretched out towards head and tail
        """
        logger.debug('stretching')
        for index, foot in enumerate(self.feet):
            foot.up()
            sleep(SLEEP_COUNT)
            self.legs[index].stretch()
            foot.down()
            sleep(SLEEP_COUNT)

    
    def walk_forward(self, steps=1):
        """
        walk forward number of steps.  Default is 1
        """
        logger.debug("walking forward")

        self.swing()
        for _ in range(steps):
            self.step_forward()


    def step_forward(self):
        """
        take a single step forward
        """
        front_left_leg = self.get_leg('LEFT_FRONT')
        front_right_leg = self.get_leg('RIGHT_FRONT')
        back_left_leg = self.get_leg('LEFT_BACK')
        back_right_leg = self.get_leg('RIGHT_BACK')

        foot = self.get_foot('RIGHT_FRONT')
        foot.up()
        front_left_leg.body()
        front_right_leg.stretch()
        foot.down()

        foot = self.get_foot('LEFT_FRONT')
        foot.up()
        front_left_leg.stretch()
        front_right_leg.body()
        foot.down()
        sleep(1)

        foot = self.get_foot('LEFT_BACK')
        foot.up()
        back_left_leg.stretch()
        back_right_leg.body()
        foot.down()

        foot = self.get_foot('RIGHT_BACK')
        foot.up()
        back_left_leg.body()
        back_right_leg.stretch()
        foot.down()
        sleep(1)

    def walk_backward(self, steps=1):
        """
        walk backward number of steps.
        if steps not defined take single step
        """
        logger.debug("walking backward")

        self.get_leg('LEFT_FRONT').body()
        self.get_leg('LEFT_BACK').body()
        self.get_leg('RIGHT_FRONT').swing()
        self.get_leg('RIGHT_BACK').swing()
        self.stand()

        for _ in range(steps):
            for leg, foot in zip(self.legs, self.feet):
                if not leg.untick():
                    leg.untick()
                else:
                    foot.up()
                    sleep(SLEEP_COUNT)
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
                    sleep(SLEEP_COUNT)
                    foot.down()
                    sleep(SLEEP_COUNT)


    def turn_left(self):
        logger.debug('turning left')
        self.swing()
        self.get_leg('LEFT_FRONT').stretch()
        self.get_leg('LEFT_BACK').body()
        self.get_leg('RIGHT_FRONT').body()
        self.get_leg('RIGHT_BACK').stretch()       
        sleep(SLEEP_COUNT)
        self.swing()


    def turn_right(self):
        logger.debug('turning right')
        self.swing()
        self.get_leg('RIGHT_FRONT').stretch()
        self.get_leg('RIGHT_BACK').body()
        self.get_leg('LEFT_FRONT').body()
        self.get_leg('LEFT_BACK').stretch()       
        sleep(SLEEP_COUNT)
        self.swing()       


    def wiggle(self, count=1):
        """
        wiggle but
        """
        logger.debug("wiggling")

        self.sit()
        self.get_foot("LEFT_BACK").down()
        self.get_foot('RIGHT_BACK').down()
        sleep(SLEEP_COUNT * 10)
        LEFT_BACK = self.get_leg('LEFT_BACK')
        RIGHT_BACK = self.get_leg('RIGHT_BACK')
        for _ in range(count):
            LEFT_BACK.body()
            RIGHT_BACK.stretch()
            sleep(SLEEP_COUNT * 5)
            LEFT_BACK.stretch()
            RIGHT_BACK.body()
            sleep(SLEEP_COUNT * 5)
        sleep(SLEEP_COUNT * 10)
        self.stand()

    
    def clap(self, count: int= None):
        """
        claps front 2 feet count times
        default is once
        """
        logger.debug('clapping')
        if count is None:
            count = 1
        self.sit()

        left_leg = self.get_leg("LEFT_FRONT")
        right_leg = self.get_leg("RIGHT_FRONT")
        for _ in range(count):
            left_leg.body()
            right_leg.body()
            sleep(SLEEP_COUNT * 2)
            left_leg.stretch()
            right_leg.stretch()
            sleep(SLEEP_COUNT * 2)

        self.stand()


def main():
    print("done")


if __name__ == '__main__':
    main()