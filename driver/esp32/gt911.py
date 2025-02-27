"""
Pure python GT911 touch driver for micropython, lvgl on esp32s3.

usage:

.. code-block::python
    from machine import Pin,I2C
    from gt911 import GT911

    # [... init lvgl and lv_display here ...]

    i2c = I2C(0, sda=Pin(17), scl=Pin(18), freq=444444)
    touch = GT911(i2c)


For I2C timeout on esp32s3, see this patch https://github.com/micropython/micropython/pull/9434/commits/8f479ab42e26e5b91db2ca079945d6e552798ab5
from https://github.com/micropython/micropython/issues/7772
in mpconfigboard.h, you'll need to define

.. code-block::c
    // (this constant is specific for every esp32 subvariant, there for s3)
    #define I2C_LL_MAX_TIMEOUT  0x0000001FU


"""

from micropython import const
import touch_base as _touch_base


GT911_I2C_SLAVE_ADDR = const(0x5D)

# Write only registers
GT911_REG_COMMAND = const(0x8040)
GT911_REG_ESD_CHECK = const(0x8041)
GT911_REG_PROXIMITY_EN = const(0x8042)

# Read/write registers
# The version number of the configuration file
GT911_REG_CONFIG_DATA = const(0x8047)
# X output maximum value (LSB 2 bytes)
GT911_REG_MAX_X = const(0x8048)
# Y output maximum value (LSB 2 bytes)
GT911_REG_MAX_Y = const(0x804A)
# Maximum number of output contacts: 1~5 (4 bit value 3:0, 7:4 is reserved)
GT911_REG_MAX_TOUCH = const(0x804C)

# Module switch 1
# 7:6 Reserved, 5:4 Stretch rank, 3 X2Y, 2 SITO
# (Single sided ITO touch screen), 1:0 INT Trigger mode
GT911_REG_MOD_SW1 = const(0x804D)
# Module switch 2
# 7:1 Reserved, 0 Touch key */
GT911_REG_MOD_SW2 = const(0x804E)

# Number of debuffs fingers press/release
GT911_REG_SHAKE_CNT = const(0x804F)

# X threshold
GT911_REG_X_THRESHOLD = const(0x8057)

# Configuration update fresh
GT911_REG_CONFIG_FRESH = const(0x8100)

# ReadOnly registers (device and coordinates info)
# Product ID (LSB 4 bytes, GT9110: 0x06 0x00 0x00 0x09)
GT911_REG_ID = const(0x8140)
# Firmware version (LSB 2 bytes)
GT911_REG_FW_VER = const(0x8144)

# Current output X resolution (LSB 2 bytes)
GT911_READ_X_RES = const(0x8146)
# Current output Y resolution (LSB 2 bytes)
GT911_READ_Y_RES = const(0x8148)
# Module vendor ID
GT911_READ_VENDOR_ID = const(0x814A)

GT911_READ_COORD_ADDR = const(0x814E)

GT911_POINT1_X_ADDR = const(0x8150)
GT911_POINT1_Y_ADDR = const(0x8152)


# Commands for REG_COMMAND
# 0: read coordinate state
GT911_CMD_READ = const(0x00)
# 1: difference value original value
GT911_CMD_DIFFVAL = const(0x01)
# 2: software reset
GT911_CMD_SOFTRESET = const(0x02)
# 3: Baseline update
GT911_CMD_BASEUPDATE = const(0x03)
# 4: Benchmark calibration
GT911_CMD_CALIBRATE = const(0x04)
# 5: Off screen (send other invalid)
GT911_CMD_SCREEN_OFF = const(0x05)


class GT911(_touch_base.TouchBase):

    def __init__(self, i2c):
        self.i2c = i2c
        self.data_buf = bytearray(6)
        self.mv = memoryview(self.data_buf)

        super().__init__()

    def init(self):
        config = bytearray([
            (GT911_REG_CONFIG_DATA & 0xFF00) >> 8,
            GT911_REG_CONFIG_DATA & 0xFF, 0x81,
            self.width & 0x00FF, (self.width >> 8) & 0x00FF,
            self.height & 0x00FF, (self.height >> 8) & 0x00FF, 1, (1 << 2),
            0x20, 0x01, 0x08, 0x28, 0x05, 0x50,  # 0x8047 - 0x8053
            0x3C, 0x0F, 0x05, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # 0x8054 - 0x8060
            0x00, 0x89, 0x2A, 0x0B, 0x2D, 0x2B, 0x0F, 0x0A, 0x00, 0x00, 0x01, 0xA9, 0x03,  # 0x8061 - 0x806D
            0x2D, 0x00, 0x01, 0x00, 0x00, 0x00, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x21,  # 0x806E - 0x807A
            0x59, 0x94, 0xC5, 0x02, 0x07, 0x00, 0x00, 0x04, 0x93, 0x24, 0x00, 0x7D, 0x2C,  # 0x807B - 0x8087
            0x00, 0x6B, 0x36, 0x00, 0x5D, 0x42, 0x00, 0x53, 0x50, 0x00, 0x53, 0x00, 0x00,  # 0x8088 - 0x8094
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # 0x8095 - 0x80A1
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # 0x80A2 - 0x80AD
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x02, 0x04, 0x06, 0x08, 0x0A,  # 0x80AE - 0x80BA
            0x0C, 0x0E, 0x10, 0x12, 0x14, 0x16, 0xFF, 0xFF, 0xFF, 0x00, 0x00, 0x00, 0x00,  # 0x80BB - 0x80C7
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # 0x80C8 - 0x80D4
            0x02, 0x04, 0x06, 0x08, 0x0A, 0x0F, 0x10, 0x12, 0x16, 0x18, 0x1C, 0x1D, 0x1E,  # 0x80D5 - 0x80E1
            0x1F, 0x20, 0x21, 0x22, 0x24, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x00,  # 0x80E2 - 0x80EE
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # 0x80EF - 0x80FB
            0x00, 0x00, 0xD6, 0x01  # 0x80FC - 0x8100
        ])

        config[184] = 0
        
        for i in range(184):
            config[184] += config[i]
        
        config[184] = (~config[184]) + 1
                
        # Get product ID
        print('Touch product id:', self.product_id)
        print('Touch firmware:', self.firmware)

        self.i2c.writeto(GT911_I2C_SLAVE_ADDR, config)
        self.set_command_register(0x00)

    def _get_coords(self):
        status = self.status

        if (status & 0x80) != 0:
            coord_num = status & 0x0F
            if coord_num != 0:
                coord_x = []
                coord_y = []
                for i in range(coord_num):
                    self.data_buf[0] = (
                        ((GT911_POINT1_X_ADDR + (i * 8)) & 0xFF00) >> 8
                    )
                    self.data_buf[1] = (GT911_POINT1_X_ADDR + (i * 8)) & 0xFF
                    self.i2c.writeto(GT911_I2C_SLAVE_ADDR, self.mv[:2])

                    self.i2c.readfrom_into(GT911_I2C_SLAVE_ADDR, self.mv[:6])

                    x = self.data_buf[0]
                    y = self.data_buf[2]
                    x |= (self.data_buf[1] << 8)
                    y |= (self.data_buf[3] << 8)

                    coord_x.append(x)
                    coord_y.append(y)

                x = int(sum(coord_x) / len(coord_x))
                y = int(sum(coord_y) / len(coord_y))

                self.status = 0
                return x, y

            self.status = 0

    def set_command_register(self, command):
        self.data_buf[0] = (GT911_REG_COMMAND & 0xFF00) >> 8
        self.data_buf[1] = GT911_REG_COMMAND & 0xFF
        self.data_buf[2] = command

        self.i2c.writeto(GT911_I2C_SLAVE_ADDR, self.mv[:3])

    @property
    def product_id(self):
        self.data_buf[0] = (GT911_REG_ID & 0xFF00) >> 8
        self.data_buf[1] = GT911_REG_ID & 0xFF
        self.i2c.writeto(GT911_I2C_SLAVE_ADDR, self.mv[:2])
        self.i2c.readfrom_into(GT911_I2C_SLAVE_ADDR, self.mv[:4])

        buf = bytearray([self.data_buf[3], self.data_buf[2], self.data_buf[1], self.data_buf[0]])
        return buf.decode('utf-8')

    @property
    def firmware(self):
        self.data_buf[0] = (GT911_REG_FW_VER & 0xFF00) >> 8
        self.data_buf[1] = GT911_REG_FW_VER & 0xFF

        self.i2c.writeto(GT911_I2C_SLAVE_ADDR, self.mv[:2])
        self.i2c.readfrom_into(GT911_I2C_SLAVE_ADDR, self.mv[:2])

        return self.data_buf[1] << 8 | self.data_buf[0]

    @property
    def status(self):
        self.data_buf[0] = (GT911_READ_COORD_ADDR & 0xFF00) >> 8
        self.data_buf[1] = GT911_READ_COORD_ADDR & 0xFF

        self.i2c.writeto(GT911_I2C_SLAVE_ADDR, self.mv[:2])

        self.i2c.readfrom_into(GT911_I2C_SLAVE_ADDR, self.mv[:1])
        return self.data_buf[0]
        
    @status.setter
    def status(self, value):
        self.data_buf[0] = (GT911_READ_COORD_ADDR & 0xFF00) >> 8
        self.data_buf[1] = GT911_READ_COORD_ADDR & 0xFF
        self.data_buf[2] = value
        self.i2c.writeto(GT911_I2C_SLAVE_ADDR, self.mv[:3])
