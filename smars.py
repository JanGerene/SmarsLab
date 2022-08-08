""" SMARS Python module
provides functions and classes for the SMARS quad robot
based on Kevin McAleers work 
"""

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


SLEEP_COUNT = 0.05  # time between pwm operations


try:
    i2c = busio.I2C(SCL, SDA)
    pca = PCA9685(i2c)
    pca.frequency = 50
except:
    logger.error("failed to initialise PCA9685 servo driver") 
    do_not_use_pca_driver = True
else :
    do_not_use_pca_driver = False
    logger.info("pca9685 driver loaded")


class Limb:
    def __init__(self, name: str, channel: int, min_angle: int, max_angle: int, invert: bool):
        self._name = name
        self._channel = channel
        self._min_angle = min_angle
        self._max_angle = max_angle
        self._invert = invert
        self._servo = servo.Servo(pca.channels[channel])

        if self.invert:
            self._body_angle = self._min_angle
            self._stretch_angle = self._max_angle
            self._swing_angle = (self._min_angle / 2) + self._min_angle
        else:
            self._body_angle = self._max_angle
            self._stretch_angle = self._min_angle
            self._swing_angle = (self._max_angle - self._min_angle) / 2
        self.angle = self._angle = self._body_angle

    def __str__(self):
        return(f"Limb: {self._name}, channel: {self._channel}, angle: {self.angle} ")



    @property 
    def name(self)->str:
        return self._name

    @name.setter
    def name(self, value: str):
        names = [
            'LEFT_FRONT', 'LEFT_BACK', 'RIGHT_FRONT', 'RIGHT_BACK'
        ]
        if not value in names:
            raise ValueError('not a valid name')
        self._name = value


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
            self.current_angle = value
        else:
            raise ValueError(f"angle.setter: angle = {value}: outside bounds")


    @property
    def channel(self):
        return self._channel

    @channel.setter
    def channel(self, value):
        if not isinstance(value, int):
            raise TypeError("channel must be an integer")
        if 0 <= value <= 15:
            self._channel = value
        else:
            raise ValueError('channel must be between 0-15')


    @property
    def min_angle(self):
        return self._min_angle

    @min_angle.setter
    def min_angle(self, value: int):
        if not isinstance(value, int):
            raise TypeError("min_angle must be integer")
        if 0 <= value <= 180:
            self._min_angle = value
        else:
            raise ValueError("min_angle must be between 0-180")


    @property
    def max_angle(self):
        return self._max_angle

    @max_angle.setter
    def max_angle(self, value:int):
        if not isinstance(value, int):
            raise TypeError("max_angle must be integer")
        if 0 <= value <= 180:
            self._max_angle = value
        else:
            raise ValueError("max_angle must be between 0-180")   

    
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
        self.angle = self.max_angle - self.min_angle


    def body(self):
        """
        set limb to its body position
        """
        if not self.invert:
            self.angle =self._body_angle = self.min_angle
        else:
            self.angle = self._body_angle = self.max_angle


    def swing(self):
        """
        sets limb to swing position (45° halfway between body and stretch position
        """
        self.angle = self._swing_angle
    

    def stretch(self):
        """
        sets limb to stretch position
        """
        self.angle = self._stretch_angle
        
        
class Leg(Limb):
    def tick(self):
        """
        each tick received changes the current angle, unless limit is reached which returns true
        """
        if self.name in ['LEFT_FRONT', 'LEFT_BACK']:
            self.current_angle += 2
            if self.current_angle > self.max_angle:
                return True
        elif self.name in ['RIGHT_FRONT', 'RIGHT_BACK']:
            self.current_angle -= 2
            if self.current_angle < self.min_angle:
                return True
        self.angle = self.current_angle
        return False


    def untick(self):
        if self.name in ['RIGHT_BACK', 'RIGHT_FRONT']:
            self.current_angle += 2
            if self.current_angle > self.max_angle:
                return True
        elif self.name in ['LEFT_BACK', 'LEFT_FRONT']:
            self.current_angle -= 2
            if self.current_angle < self.min_angle:
                return True
        self.angle = self.current_angle
        return False
       

class Foot(Limb):
    def down(self):
        """
        lowers limb to max angle
        """
        if not self.invert:
            self.angle = self.max_angle
        else:
            self.angle = self.min_angle


    def up(self):
        """
        raises limb to min angle
        """
        if not self.invert:
            self.angle = self.min_angle
        else:
            self.angle = self.max_angle


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
        set each foot to down posistion
        """
        logger.debug("sitting down")
        for foot in self.feet:
            foot.down()


    def stand(self):
        """
        set each foot to up posistion
        """
        logger.debug("standing up")
        for foot in self.feet:
            foot.up()


    def swing(self):
        """
        move legs to swing position, robot forms a giant X shape
        """
        logger.debug("swinging")
        for index, foot in enumerate(self.feet):
            foot.down()
            sleep(SLEEP_COUNT)
            self.legs[index].swing()
            sleep(SLEEP_COUNT)
            foot.up()
            sleep(SLEEP_COUNT)


    def walkforward(self, steps: int=None):
        """
        walk forward number of steps.
        if steps not defined take single step
        """
        logger.debug("walking forward")
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
                    sleep(SLEEP_COUNT)
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
                    sleep(SLEEP_COUNT)
                    self.feet[index].up()
                    sleep(SLEEP_COUNT)


    def walkbackward(self, steps: int=None):
        """
        walk backward number of steps.
        if steps not defined take single step
        """
        logger.debug("walking backward")
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
                    self.feet[index].up()
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


    def wiggle(self, count: int=None):
        """
        wiggle but
        """
        logger.debug("wingling")
        if count is None:
            count = 1

        self.sit()
        self.get_foot("LEFT_BACK").up()
        self.get_foot('RIGHT_BACK').up()
        sleep(SLEEP_COUNT)

        LEFT_BACK = self.get_leg('LEFT_BACK')
        RIGHT_BACK = self.get_leg('RIGHT_BACK')
        for _ in range(count):
            LEFT_BACK.body()
            RIGHT_BACK.stretch()
            sleep(SLEEP_COUNT * 5)
            LEFT_BACK.stretch()
            RIGHT_BACK.body()
            sleep(SLEEP_COUNT * 5)

        self.stand()

    
    def stretch(self):
        """
        move all limbs to strectch position
        legs are stretched out towards head and tail
        """
        logger.debug('stretching')
        for index, foot in enumerate(self.feet):
            foot.down()
            sleep(SLEEP_COUNT)
            self.legs[index].stretch()
            foot.up()
            sleep(SLEEP_COUNT)

    
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
    pass


if __name__ == '__main__':
    main()