# TH3 HACKP4D - KMK, XIAO RP2040

import board
import busio
import displayio
import terminalio
import neopixel
import usb_cdc

import adafruit_displayio_ssd1306
from adafruit_display_text import label

try:
    from i2cdisplaybus import I2CDisplayBus
except ImportError:
    from displayio import I2CDisplay as I2CDisplayBus

from kmk.kmk_keyboard import KMKKeyboard
from kmk.scanners.keypad import KeysScanner
from kmk.keys import KC
from kmk.modules import Module
from kmk.extensions.media_keys import MediaKeys


PINS = [board.D10, board.D9, board.D8, board.D7]

KEYS = [
    (KC.MPLY, "PLAY/PAUSE"),
    (KC.VOLD, "VOL -"),
    (KC.VOLU, "VOL +"),
    (KC.MUTE, "MUTE"),
]

COLORS = [
    (255, 0, 0),
    (255, 140, 0),
    (0, 255, 60),
    (0, 80, 255),
]

BRIGHTNESS = 0.3
CHARS = 21
FLIP_SCREEN = False  # upside down? -> True


class HackPad(Module):
    def __init__(self):
        self.pixels = None
        self.title = None
        self.artist = None
        self.serial = usb_cdc.data
        self.buf = b""

    def during_bootup(self, keyboard):
        self.pixels = neopixel.NeoPixel(board.D0, 4, brightness=BRIGHTNESS, auto_write=False)
        self.pixels.fill(0)
        self.pixels.show()

        try:
            displayio.release_displays()
            i2c = busio.I2C(scl=board.D5, sda=board.D4)
            bus = I2CDisplayBus(i2c, device_address=0x3C)
            screen = adafruit_displayio_ssd1306.SSD1306(
                bus, width=128, height=32, rotation=180 if FLIP_SCREEN else 0
            )
            self.title = label.Label(
                terminalio.FONT, text="", anchor_point=(0.5, 0.0), anchored_position=(64, 1)
            )
            self.artist = label.Label(
                terminalio.FONT, text="", anchor_point=(0.5, 0.0), anchored_position=(64, 17)
            )
            group = displayio.Group()
            group.append(self.title)
            group.append(self.artist)
            screen.root_group = group
        except Exception as e:
            print("OLED not found:", e)
            self.title = None

    def now_playing(self, line):
        if self.title is None:
            return
        parts = line.strip("\r").split("\t")
        self.title.text = parts[0][:CHARS]
        self.artist.text = parts[1][:CHARS] if len(parts) > 1 else ""

    def read_serial(self):
        s = self.serial
        if s is None or not s.in_waiting:
            return
        self.buf += s.read(s.in_waiting)
        while b"\n" in self.buf:
            line, self.buf = self.buf.split(b"\n", 1)
            try:
                self.now_playing(line.decode("utf-8"))
            except Exception:
                pass
        if len(self.buf) > 256:
            self.buf = b""

    def process_key(self, keyboard, key, is_pressed, int_coord):
        if int_coord is not None and 0 <= int_coord < len(COLORS):
            if is_pressed:
                self.pixels[int_coord] = COLORS[int_coord]
            else:
                self.pixels[int_coord] = (0, 0, 0)
            self.pixels.show()
        return key

    def before_matrix_scan(self, keyboard):
        self.read_serial()


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
