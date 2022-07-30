import unittest

import yaml

import smarslab.smars as sl
import smarslab.smars_lab as smars_lab

class test_smars_robot(unittest.TestCase):
    def setUp(self):
        with open('config.yaml','r') as file:
            self.config = yaml.safe_load(file)
            
            
    def test_create_robot(self):
        r = sl.SmarsRobot()
        self.assertEqual(len(r.legs), 4)
        self.assertEqual(len(r.feet), 4)

        feet = self.config['feet']
        for index, foot in enumerate(feet):
            self.assertTrue(r.legs[index].name, foot['name'])
            self.assertLessEqual(r.legs[index].channel, 15)
            self.assertGreaterEqual(r.legs[index].channel, 0)


    def test_default(self):
        r = sl.SmarsRobot()
        r.default()
        feet = self.config['feet']
        for index, limb in enumerate(r.legs):
            self.assertEqual(limb.angle, feet[index]['maxangle'] - feet[index]['minangle'])
            self.assertEqual(limb.angle, limb.current_angle)


    def test_get_leg(self):
        r = sl.SmarsRobot()
        leg = r.get_leg('LEFT_LEG_BACK')
        self.assertEqual(leg.channel, 2)

    def test_get_telemetry(self):
        r = sl.SmarsRobot()
        r.get_telemetry()


class test_leg(unittest.TestCase):

    def test_create_leg(self):
        leg = sl.Leg("test_leg", 0, 0, 90, False)
        self.assertTrue(leg.name == "test_leg")
        self.assertEqual(leg.channel, 0)
        self.assertEqual(leg.minangle, 0)
        self.assertEqual(leg.maxangle, 90)
        self.assertFalse(leg.invert)
        self.assertEqual(leg.bodyangle, 0)
        self.assertEqual(leg.stretchangle, 90)
        self.assertEqual(leg.swing_angle, 0)
        leg = sl.Leg("test_leg", 0, 50, 150, True)
        self.assertTrue(leg.name == "test_leg")
        self.assertEqual(leg.channel, 0)
        self.assertEqual(leg.minangle, 50)
        self.assertEqual(leg.maxangle, 150)
        self.assertTrue(leg.invert)
        self.assertEqual(leg.bodyangle, 150)
        self.assertEqual(leg.stretchangle, 50)
        self.assertEqual(leg.swing_angle, 50)


    def test_default(self):
        leg = sl.Leg("test_leg", 0, 0, 90, False)
        leg.default()
        self.assertEqual(leg.angle, 90)
        self.assertEqual(leg.current_angle, 90)
        

class test_command_history(unittest.TestCase):

    def test_create_command_history(self):
        h = smars_lab.CommandHistory()
        self.assertEqual(h.history[0], "*** new history ***")
        h.append("first line")
        self.assertEqual(len(h.history), 2)
        self.assertTrue("first line" in h.history)
        self.assertEqual(h.history[1], "first line")
        h.clear()
        self.assertEqual(len(h.history), 0)
        h.append('1')
        h.append('2')
        h.append('3')
        h.append('4')
        h.append('5')
        h.append('6')
        h.append('7')
        h.append('8')
        h.append('9')
        h.append('10')
        h.append('11')
        self.assertEqual(len(h.history), 11)
        hist = h.get_last_ten()
        self.assertEqual(len(hist), 10)
        self.assertEqual(hist[9], "11")


if __name__ == '__main__':
    unittest.main()