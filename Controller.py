import RPi.GPIO as GPIO
import time
from MCP4728 import MCP4728
import math
GPIO.setmode(GPIO.BCM)
#GPIO.setwarnings(False)
def degToCoord(deg, intensity = 1, xcenter=1.9, ycenter=1.9, radius=2):
    deg += 90
    r = (radius) * intensity;
    x = round(r*math.cos(math.radians(deg)) + xcenter, 3)
    y = round(r*math.sin(math.radians(deg)) + ycenter, 3)
    print("At an intensity of {}, {} degrees has coordinates {}, {}".format(intensity, (deg-90)%360, x, y))
    return [x, y]

class SwitchController:
    Radius = 1.2
    Buttons = {
    "UP": 26,
    "RIGHT": 19,
    "DOWN": 13,
    "LEFT": 6,
    "X": 5,
    "A": 22,
    "B": 27,
    "Y": 17,
    "START": 21,
    "BACK": 20,
    "HOME": 16,
    "ZR": 14,
    "R": 15,
    "ZL": 18,
    "L": 23,
    "R3": 24,
    "L3": 25,
    }
    CHARGE = 12

    def __init__(self, StickDefaults = { "LX": 1.85, "LY": 1.85, "RX": 1.85, "RY": 1.85 }, StickChannels = {"LX": 4, "LY": 3, "RX": 2, "RY": 1}):
        self.StickDefaults = StickDefaults
        self.StickChannels = StickChannels
        for idx in self.Buttons:
            print("Setting up {} as pin {}".format(idx, self.Buttons[idx]))
            GPIO.setup(self.Buttons[idx], GPIO.OUT)
            GPIO.setup(self.CHARGE, GPIO.OUT)
            self.LEFT_STICK = ["LX", "LY"]
            self.RIGHT_STICK = ["RX","RY"]
        self.dac = MCP4728(0x60)
        self.ReleaseAll()
        self.DisableCharge()

    def Press(self,idx, duration = 0.4):
        print("Pressing {} for {}s".format(idx, duration))
        self.Hold(idx)
        time.sleep(duration)
        self.Release(idx)

    def MultiPress(self,buttons, duration = 0.3):
        for idx in buttons:
            self.Hold(idx)

        time.sleep(duration)
        for idx in buttons:
            self.Release(idx)


    def Hold(self,idx):
        GPIO.output(self.Buttons[idx], GPIO.HIGH)


    def Release(self,idx):
        GPIO.output(self.Buttons[idx], GPIO.LOW)


    def ReleaseAll(self):
        for idx in self.Buttons:
            self.Release(idx)

    def EnableCharge(self):
        GPIO.output(self.CHARGE, GPIO.HIGH)

    def DisableCharge(self):
        GPIO.output(self.CHARGE, GPIO.LOW)

    def UpdateStick(self, Stick, Angle, Intensity):
        x,y = degToCoord(Angle, Intensity, self.StickDefaults[Stick[0]], self.StickDefaults[Stick[1]], self.Radius)
        self.dac.single_internal(self.StickChannels[Stick[0]],x,False)
        self.dac.single_internal(self.StickChannels[Stick[1]],y,False)


    def CenterStick(self, Stick):
        self.UpdateStick(Stick, 0, 0)

    def ResetSticks(self):
        self.UpdateStick(self.LEFT_STICK, 0, 0)
        self.UpdateStick(self.RIGHT_STICK, 0, 0)

    def WakeUp(self):
        self.DisableCharge()
        time.sleep(2)
        self.Press("HOME", 0.5)
        time.sleep(2)
        self.EnableCharge()
        self.CenterStick(self.LEFT_STICK)
        self.CenterStick(self.RIGHT_STICK)
