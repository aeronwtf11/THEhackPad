# TH3 HACKP4D firmware
# KMK on CircuitPython, Seeed XIAO RP2040
#
# needs on CIRCUITPY:  kmk/  and in lib/:  neopixel.mpy,
# adafruit_displayio_ssd1306.mpy, adafruit_display_text/

import board
import busio
import displayio
import terminalio
import neopixel

import adafruit_displayio_ssd1306
from adafruit_display_text import label

try:
    from i2cdisplaybus import I2CDisplayBus  # CircuitPython 9+
except ImportError:
    from displayio import I2CDisplay as I2CDisplayBus  # CircuitPython 8

from kmk.kmk_keyboard import KMKKeyboard
from kmk.scanners.keypad import KeysScanner
from kmk.keys import KC
from kmk.modules import Module
from kmk.extensions.media_keys import MediaKeys


# SW1, SW2, SW3, SW4 (each one goes straight to GND)
PINS = [board.D10, board.D9, board.D8, board.D7]

# what each key does, and what the screen shows when you press it
KEYS = [
    (KC.MPLY, "PLAY/PAUSE"),
    (KC.VOLD, "VOL -"),
    (KC.VOLU, "VOL +"),
    (KC.MUTE, "MUTE"),
]

# LED 1-4, lights up while the matching key is held down
COLORS = [
    (255, 0, 0),
    (255, 140, 0),
    (0, 255, 60),
    (0, 80, 255),
]

BRIGHTNESS = 0.3
FLIP_SCREEN = False  # set to True if the text on the OLED is upside down


class HackPad(Module):
    def __init__(self):
        self.pixels = None
        self.text = None

    def during_bootup(self, keyboard):
        # LEDs, data on D0, 4 in a chain
        self.pixels = neopixel.NeoPixel(board.D0, 4, brightness=BRIGHTNESS, auto_write=False)
        self.pixels.fill(0)
        self.pixels.show()

        # 0.91" OLED, SDA = D4, SCL = D5
        # if it's missing or wired wrong the keys still work
        try:
            displayio.release_displays()
            i2c = busio.I2C(scl=board.D5, sda=board.D4)
            bus = I2CDisplayBus(i2c, device_address=0x3C)
            screen = adafruit_displayio_ssd1306.SSD1306(
                bus, width=128, height=32, rotation=180 if FLIP_SCREEN else 0
            )
            self.text = label.Label(
                terminalio.FONT, text="", anchor_point=(0.5, 0.5), anchored_position=(64, 16)
            )
            group = displayio.Group()
            group.append(self.text)
            screen.root_group = group
            self.show("TH3 HACKP4D")
        except Exception as e:
            print("OLED not found:", e)
            self.text = None

    def show(self, msg):
        if self.text is None:
            return
        # font is 6 px wide, so scale 2 only fits 10 characters
        self.text.scale = 2 if len(msg) <= 10 else 1
        self.text.text = msg

    def process_key(self, keyboard, key, is_pressed, int_coord):
        if int_coord is not None and 0 <= int_coord < len(COLORS):
            if is_pressed:
                self.pixels[int_coord] = COLORS[int_coord]
                self.show(KEYS[int_coord][1])
            else:
                self.pixels[int_coord] = (0, 0, 0)
            self.pixels.show()
        return key

    # KMK wants all of these, nothing to do here
    def before_matrix_scan(self, keyboard):
        pass

    def after_matrix_scan(self, keyboard):
        pass

    def before_hid_send(self, keyboard):
        pass

    def after_hid_send(self, keyboard):
        pass

    def on_powersave_enable(self, keyboard):
        if self.pixels:
            self.pixels.fill(0)
            self.pixels.show()

    def on_powersave_disable(self, keyboard):
        pass


keyboard = KMKKeyboard()
keyboard.matrix = KeysScanner(pins=PINS, value_when_pressed=False, pull=True)
keyboard.extensions.append(MediaKeys())
keyboard.modules.append(HackPad())
keyboard.keymap = [[k for k, _ in KEYS]]

if __name__ == "__main__":
    keyboard.go()
