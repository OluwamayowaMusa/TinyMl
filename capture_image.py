import board, busio, digitalio, time, displayio
from adafruit_ov7670 import OV7670, OV7670_SIZE_DIV8
from adafruit_displayio_ssd1306 import SSD1306

from displayio import (Bitmap,
                       Group,
                       TileGrid,
                       ColorConverter,
                       Colorspace,
                       release_displays,
                       I2CDisplay)

release_displays()
sda, scl = board.GP2, board.GP3
SCREEN_WIDTH = 128
SCREEN_HEIGHT = 64
i2c = busio.I2C(scl, sda)
display_bus = I2CDisplay(i2c, device_address=0x3C)
display = SSD1306(display_bus, width=SCREEN_WIDTH, height=SCREEN_HEIGHT)
print("Display connected")


with digitalio.DigitalInOut(board.GP10) as reset:
    reset.switch_to_output(False)
    time.sleep(0.001)
    bus = busio.I2C(board.GP9, board.GP8)


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
cam.size = OV7670_SIZE_DIV8
cam.OV7670_NIGHT_MODE_OFF= 0
cam.flip_y = True
print("Camera connected")

buf = bytearray(2 * cam.width * cam.height)

bitmap = Bitmap(cam.width, cam.height, 65536)

width, height = 128, 64
group = Group(scale=1, x=(width - cam.width) // 2, y=(height - cam.height) // 2)
tile_grid = TileGrid(bitmap,
                    pixel_shader=ColorConverter(input_colorspace=Colorspace.RGB555))

tile_grid.transpose_xy = True
group.append(tile_grid)
cam.capture(bitmap)
display.show(group)
print("Image Captured")