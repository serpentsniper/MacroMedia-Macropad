"""
MelodyPad - 3x3 Music/Media Macropad Firmware
================================================
Hardware: Seeed XIAO RP2040 + 9 MX switches + 1 EC11 encoder + 0.91" OLED
Framework: KMK (CircuitPython)

Features:
  - 3-layer keymap (Media, DAW, System)
  - Rotary encoder for volume
  - Animated equalizer visualization on OLED
"""

import board
import busio
import digitalio
import random
import time

from kmk.kmk_keyboard import KMKKeyboard
from kmk.keys import KC
from kmk.scanners.keypad import MatrixScanner
from kmk.modules.layers import Layers
from kmk.modules.encoder import EncoderHandler
from kmk.modules.media_keys import MediaKeys
from kmk.extensions import Extension

# ============================================================
# OLED EQUALIZER EXTENSION
# ============================================================

import adafruit_ssd1306

class OledEqualizer(Extension):
    """Custom KMK extension that draws a randomized music
    equalizer animation on a 128x32 SSD1306 OLED."""

    def __init__(self, i2c, num_bars=16, bar_width=6, gap=2,
                 update_interval=0.05):
        self.i2c = i2c
        self.num_bars = num_bars
        self.bar_width = bar_width
        self.gap = gap
        self.update_interval = update_interval

        # Current and target heights for each bar (smooth animation)
        self.heights = [0] * num_bars
        self.targets = [0] * num_bars
        self.max_height = 30  # max bar height in pixels (screen is 32px)

        self.last_update = 0
        self.oled = None

    def on_runtime_enable(self, sandbox):
        self.oled = adafruit_ssd1306.SSD1306_I2C(128, 32, self.i2c)
        self.oled.fill(0)
        self.oled.show()
        self._new_targets()

    def on_runtime_disable(self, sandbox):
        if self.oled:
            self.oled.fill(0)
            self.oled.show()

    def during_bootup(self, sandbox):
        self.on_runtime_enable(sandbox)

    def before_matrix_scan(self, sandbox):
        """Called every scan cycle - update animation here."""
        now = time.monotonic()
        if now - self.last_update < self.update_interval:
            return
        self.last_update = now

        if not self.oled:
            return

        # Smoothly move current heights toward targets
        for i in range(self.num_bars):
            diff = self.targets[i] - self.heights[i]
            speed = max(1, abs(diff) // 3)
            if diff > 0:
                self.heights[i] = min(self.heights[i] + speed,
                                      self.targets[i])
            elif diff < 0:
                self.heights[i] = max(self.heights[i] - speed,
                                      self.targets[i])

        # Pick new targets when most bars have settled
        settled = sum(1 for i in range(self.num_bars)
                      if abs(self.heights[i] - self.targets[i]) <= 2)
        if settled > self.num_bars // 2:
            self._new_targets()

        self._draw()

    def after_matrix_scan(self, sandbox):
        pass

    def before_hid_send(self, sandbox):
        pass

    def after_hid_send(self, sandbox):
        pass

    def on_powersave_enable(self, sandbox):
        pass

    def on_powersave_disable(self, sandbox):
        pass

    def _new_targets(self):
        """Generate random target heights that look like a real
        equalizer - middle bars tend higher, adjacent bars
        are loosely correlated."""
        for i in range(self.num_bars):
            base = random.randint(3, self.max_height)

            # Middle bars tend taller (like a real audio spectrum)
            center = self.num_bars / 2
            dist_from_center = abs(i - center) / center
            boost = int((1.0 - dist_from_center * 0.4) * base)

            self.targets[i] = max(2, min(self.max_height,
                                         boost + random.randint(-4, 4)))

    def _draw(self):
        """Render equalizer bars to the OLED."""
        self.oled.fill(0)

        for i in range(self.num_bars):
            x = i * (self.bar_width + self.gap) + 1
            h = max(1, self.heights[i])

            # Bars grow upward from bottom of screen
            y_top = 31 - h
            y_bottom = 31

            # Draw filled bar
            for y in range(y_top, y_bottom + 1):
                for dx in range(self.bar_width):
                    px = x + dx
                    if 0 <= px < 128:
                        self.oled.pixel(px, y, 1)

            # Add horizontal gap lines for segmented look
            # (like the pink bars in the reference image)
            if h > 4:
                for seg_y in range(y_top + 2, y_bottom, 3):
                    for dx in range(self.bar_width):
                        px = x + dx
                        if 0 <= px < 128:
                            self.oled.pixel(px, seg_y, 0)

            # Floating peak dot above bar
            peak_y = max(0, y_top - 2)
            for dx in range(self.bar_width):
                px = x + dx
                if 0 <= px < 128:
                    self.oled.pixel(px, peak_y, 1)

        self.oled.show()


# ============================================================
# KEYBOARD SETUP
# ============================================================

keyboard = KMKKeyboard()

# Pins
COL_PINS = (board.D0, board.D1, board.D2)
ROW_PINS = (board.D3, board.D4, board.D5)

ENCODER_PIN_A = board.D9
ENCODER_PIN_B = board.D10

# Matrix
keyboard.matrix = MatrixScanner(
    cols=COL_PINS,
    rows=ROW_PINS,
    diode_orientation=digitalio.Direction.INPUT,
)

# Modules
layers = Layers()
encoder_handler = EncoderHandler()
media_keys = MediaKeys()
keyboard.modules = [layers, encoder_handler, media_keys]

# Encoder (no button)
encoder_handler.pins = (
    (ENCODER_PIN_A, ENCODER_PIN_B, None, False),
)

# OLED equalizer
i2c = busio.I2C(board.D7, board.D6)
equalizer = OledEqualizer(
    i2c=i2c,
    num_bars=16,           # number of bars across screen
    bar_width=6,           # pixel width per bar
    gap=2,                 # pixel gap between bars
    update_interval=0.06,  # seconds between frames (~16fps)
)
keyboard.extensions.append(equalizer)

# Layer keys
LYR1 = KC.MO(1)
LYR2 = KC.MO(2)

# Keymap
keyboard.keymap = [
    # Layer 0: Media Control
    # +----------+----------+----------+
    # |   Prev   | Play/Pse |   Next   |
    # +----------+----------+----------+
    # |   Stop   |   Mute   |  Vol Up  |
    # +----------+----------+----------+
    # |  Layer1  |  Layer2  |  Vol Dn  |
    # +----------+----------+----------+
    [
        KC.MPRV,   KC.MPLY,   KC.MNXT,
        KC.MSTP,   KC.MUTE,   KC.VOLU,
        LYR1,      LYR2,      KC.VOLD,
    ],

    # Layer 1: DAW Shortcuts
    [
        KC.LCTRL(KC.Z),  KC.LCTRL(KC.Y),  KC.LCTRL(KC.S),
        KC.LCTRL(KC.X),  KC.LCTRL(KC.C),  KC.LCTRL(KC.V),
        KC.TRNS,          KC.TRNS,          KC.TRNS,
    ],

    # Layer 2: System / F-Keys
    [
        KC.F13,    KC.F14,    KC.F15,
        KC.F16,    KC.F17,    KC.F18,
        KC.TRNS,   KC.TRNS,   KC.RESET,
    ],
]

# Encoder map (per layer)
encoder_handler.map = [
    ((KC.VOLD, KC.VOLU),),
    ((KC.LCTRL(KC.MINUS), KC.LCTRL(KC.EQUAL)),),
    ((KC.BRID, KC.BRIU),),
]

keyboard.go()
