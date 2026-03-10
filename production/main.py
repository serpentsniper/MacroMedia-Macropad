"""
MelodyPad - 3x3 Music/Media Macropad Firmware
================================================
Hardware: Seeed XIAO RP2040 + 9 MX switches + 1 EC11 encoder + 0.91" OLED
Framework: KMK (CircuitPython keyboard firmware)

Wiring Summary:
  - Switch matrix: 3 cols x 3 rows (1N4148 diodes, cathode to row)
  - Encoder: EC11 on D9 (A), D10 (B), common to GND
  - Encoder button: D8 (optional) or unused
  - OLED: I2C on D6 (SDA), D7 (SCL)

Pin Assignment (XIAO RP2040):
  D0  -> COL0        D6  -> SDA (OLED)
  D1  -> COL1        D7  -> SCL (OLED)
  D2  -> COL2        D8  -> (free / encoder button)
  D3  -> ROW0        D9  -> ENCODER_A
  D4  -> ROW1        D10 -> ENCODER_B
  D5  -> ROW2
"""

import board
import digitalio

from kmk.kmk_keyboard import KMKKeyboard
from kmk.keys import KC
from kmk.scanners.keypad import MatrixScanner
from kmk.modules.layers import Layers
from kmk.modules.encoder import EncoderHandler
from kmk.modules.media_keys import MediaKeys

# ---- Keyboard Setup --------------------------------------------------------

keyboard = KMKKeyboard()

# ---- Pin Definitions -------------------------------------------------------

COL_PINS = (board.D0, board.D1, board.D2)
ROW_PINS = (board.D3, board.D4, board.D5)

ENCODER_PIN_A = board.D9
ENCODER_PIN_B = board.D10
# ENCODER_BTN = board.D8  # uncomment if using encoder press

# ---- Matrix Scanner --------------------------------------------------------

keyboard.matrix = MatrixScanner(
    cols=COL_PINS,
    rows=ROW_PINS,
    diode_orientation=digitalio.Direction.INPUT,  # COL2ROW
)

# ---- Modules ---------------------------------------------------------------

layers = Layers()
encoder_handler = EncoderHandler()
media_keys = MediaKeys()

keyboard.modules = [layers, encoder_handler, media_keys]

# ---- Encoder ---------------------------------------------------------------
# No button pin — set to None if not using encoder press
# To enable button: change None to ENCODER_BTN and uncomment above

encoder_handler.pins = (
    (ENCODER_PIN_A, ENCODER_PIN_B, None, False),
)

# ---- Layer Definitions ------------------------------------------------------
#
# Physical layout (top view):
#
#   [Encoder]  twist=volume, no press
#   [OLED display]
#
#   +--------+--------+--------+
#   |  K00   |  K01   |  K02   |  Row 0
#   +--------+--------+--------+
#   |  K10   |  K11   |  K12   |  Row 1
#   +--------+--------+--------+
#   |  K20   |  K21   |  K22   |  Row 2
#   +--------+--------+--------+
#     Col0     Col1     Col2

LYR1 = KC.MO(1)
LYR2 = KC.MO(2)

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
    # +----------+----------+----------+
    # |   Undo   |   Redo   |   Save   |
    # +----------+----------+----------+
    # |   Cut    |   Copy   |  Paste   |
    # +----------+----------+----------+
    # |  (trns)  |  (trns)  |  (trns)  |
    # +----------+----------+----------+
    [
        KC.LCTRL(KC.Z),  KC.LCTRL(KC.Y),  KC.LCTRL(KC.S),
        KC.LCTRL(KC.X),  KC.LCTRL(KC.C),  KC.LCTRL(KC.V),
        KC.TRNS,          KC.TRNS,          KC.TRNS,
    ],

    # Layer 2: System / F-Keys
    # +----------+----------+----------+
    # |   F13    |   F14    |   F15    |
    # +----------+----------+----------+
    # |   F16    |   F17    |   F18    |
    # +----------+----------+----------+
    # |  (trns)  |  (trns)  |  Reset   |
    # +----------+----------+----------+
    [
        KC.F13,    KC.F14,    KC.F15,
        KC.F16,    KC.F17,    KC.F18,
        KC.TRNS,   KC.TRNS,   KC.RESET,
    ],
]

# ---- Encoder Keymap (per layer) --------------------------------------------
# Format: (counter-clockwise, clockwise)
# No press since encoder button is not wired

encoder_handler.map = [
    ((KC.VOLD, KC.VOLU),),                                  # Layer 0: Volume
    ((KC.LCTRL(KC.MINUS), KC.LCTRL(KC.EQUAL)),),            # Layer 1: Zoom
    ((KC.BRID, KC.BRIU),),                                   # Layer 2: Brightness
]

# ---- GO! -------------------------------------------------------------------

if __name__ == "__main__":
    keyboard.go()
