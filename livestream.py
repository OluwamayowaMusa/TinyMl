# SPDX-FileCopyrightText: 2017 Scott Shawcroft, written for Adafruit Industries
# SPDX-FileCopyrightText: Copyright (c) 2021 Jeff Epler for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense

"""
Capture an image from the camera and display it on a supported LCD.
"""

import time
from displayio import (
    Bitmap,
    Group,
    TileGrid,
    release_displays,
    ColorConverter,
    Colorspace,
    I2CDisplay
)
from adafruit_displayio_ssd1306 import SSD1306
import board
import busio
import digitalio
from adafruit_ov7670 import (
    OV7670,
    OV7670_SIZE_DIV1,
    OV7670_SIZE_DIV16,
)

# Display for SSD1306
release_displays()
sda, scl = board.GP2, board.GP3
SCREEN_WIDTH = 128
SCREEN_HEIGHT = 64
i2c = busio.I2C(scl, sda)
display_bus = I2CDisplay(i2c, device_address=0x3C)
display = SSD1306(display_bus, width=SCREEN_WIDTH, height=SCREEN_HEIGHT)
print("Display Connected")

# Ensure the camera is shut down, so that it releases the SDA/SCL lines,
# then create the configuration I2C bus


with digitalio.DigitalInOut(board.GP10) as reset:
    reset.switch_to_output(False)
    time.sleep(0.001)
    bus = busio.I2C(board.GP9, board.GP8)

# Set up the camera (you must customize this for your board!)

cam = OV7670(
    bus,
    data_pins=[
        board.GP12,
        board.GP13,
        board.GP14,
        board.GP15,
        board.GP16,
        board.GP17,
        board.GP18,
        board.GP19,
    ],  # [16]     [org] etc
    clock=board.GP11,  # [15]     [blk]
    vsync=board.GP7,  # [10]     [brn]
    href=board.GP21,  # [27/o14] [red]
    mclk=board.GP20,  # [16/o15]
    shutdown=None,
    reset=board.GP10,
)  # [14]
print("Camera Connected")

cam.flip_y = True
width = display.width
height = display.height

# cam.test_pattern = OV7670_TEST_PATTERN_COLOR_BAR

bitmap = None
# Select the biggest size for which we can allocate a bitmap successfully, and
# which is not bigger than the display
for size in range(OV7670_SIZE_DIV1, OV7670_SIZE_DIV16 + 1):
    cam.size = size
    if cam.width > width:
        continue
    if cam.height > height:
        continue
    try:
        bitmap = Bitmap(cam.width, cam.height, 65536)
        break
    except MemoryError:
        continue

if bitmap is None:
    raise SystemExit("Could not allocate a bitmap")

g = Group(scale=1, x=(width - cam.width) // 2, y=(height - cam.height) // 2)
tg = TileGrid(
    bitmap, pixel_shader=ColorConverter(input_colorspace=Colorspace.RGB565_SWAPPED)
)
tg.transpose_xy = True
g.append(tg)
display.show(g)

t0 = time.monotonic_ns()
display.auto_refresh = False
print("LiveStream Started")
while True:
    cam.capture(bitmap)
    bitmap.dirty()
    display.refresh(minimum_frames_per_second=0)
    t1 = time.monotonic_ns()
    #print("fps", 1e9 / (t1 - t0))
    t0 = t1

