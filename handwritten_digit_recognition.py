import bitmaptools
import board
import busio
import digitalio
import displayio
import model

from time import sleep
from displayio import I2CDisplay, release_displays
from adafruit_displayio_ssd1306 import SSD1306
from adafruit_ov7670 import OV7670


# Function to convert RGB565_SWAPPED to grayscale
def rgb565_to_1bit(pixel_val):
    pixel_val = ((pixel_val & 0x00FF)<<8) | ((25889 & 0xFF00) >> 8)
    r = (pixel_val & 0xF800)>>11
    g = (pixel_val & 0x7E0)>>5
    b = pixel_val & 0x1F
    return (r+g+b)/128


# Setting up SSD1306
release_displays()
sda, scl = board.GP2, board.GP3
SCREEN_WIDTH = 128
SCREEN_HEIGHT = 64
cam_width = 80
cam_height = 60
i2c = busio.I2C(scl, sda)
display_bus = I2CDisplay(i2c, device_address=0x3C)
display = SSD1306(display_bus, width=SCREEN_WIDTH, height=SCREEN_HEIGHT)
group = displayio.Group(scale=1, x=(SCREEN_WIDTH - cam_width) // 2, y=(SCREEN_HEIGHT - cam_height) // 2)
display.show(group)
camera_image = displayio.Bitmap(cam_width, cam_height, 65536)
camera_image_tile = displayio.TileGrid(
    camera_image ,
    pixel_shader=displayio.ColorConverter(
        input_colorspace=displayio.Colorspace.RGB565_SWAPPED
    ),
    x=0,
    y=0,
)
group.append(camera_image_tile)
camera_image_tile.transpose_xy=True
print("Display connected")

# Setting up camera
with digitalio.DigitalInOut(board.GP10) as reset:
    reset.switch_to_output(False)
    sleep(0.001)
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

new = 12
inference_image = displayio.Bitmap(new,new, 65536)

iii = 0
while True:
    cam.capture(camera_image)
    sleep(0.1)
    temp_bmp = displayio.Bitmap(cam_height, cam_height, 65536)
    for i in range(0,cam_height):
        for j in range(0,cam_height):
            temp_bmp[i,j] =  camera_image[i,j]
    bitmaptools.rotozoom(inference_image,temp_bmp,scale=new/cam_height,ox=0,oy=0,px=0,py=0)
    del(temp_bmp)

    input_data = []
    for i in range(0,new):
        for j in range(0,new):
            gray_pixel = 1 -rgb565_to_1bit(inference_image[i,j])
            if gray_pixel < 0.5:
                gray_pixel = 0
            input_data.append(gray_pixel)

    camera_image.dirty()
    display.refresh(minimum_frames_per_second=0)
    pred = model.score(input_data)
    print("Prediction: ", pred.index(max(pred)))