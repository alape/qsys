from time import time

import cv2
import numpy as np

from emulation.ip.common import IP, IPRegisterAccessMode, IPException


class VGI(IP):
    """VGI IP block. Outputs its address space as an image via Numpy array & OpenCV."""
    _alloc_addrspace = False
    _fb_offset = 2
    addr_space_size = 0x4bfff
    easymmap_id = 0x56474930
    reg_descr = {
        0: ("EASYMMAP_ID", IPRegisterAccessMode.R, "EasyMMap identifier"),
        1: ("MODE", IPRegisterAccessMode.W, "Changes VGI mode of operation. Reserved for now"),
        2: ("STATUS", IPRegisterAccessMode.R, "Outputs the current status of VGI. Always set to 1 for now"),
        3: ("MEM_START", IPRegisterAccessMode.RW, "Start address of VGI framebuffer")
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.height = 480
        self.width = 640
        self._wname = "QSim VGI output"
        self._last_update = 0.0

        # initialize the framebuffer (640x480, BGR, 8bpp) as Numpy array
        self.fb = np.zeros((self.height, self.width, 3), dtype=np.uint8)

        # default update rate is 30 FPS
        if "fps" in kwargs:
            self.fps = kwargs["fps"]
        else:
            self.fps = 30

        # initialize the named window with empty framebuffer
        # cv2.startWindowThread()
        cv2.imshow(self._wname, self.fb)

    def process_tick(self) -> None:
        # if it's time, update the OpenCV named window with contents of the framebuffer
        current_time = time()
        if self._last_update < (current_time - (1 / self.fps)):
            self._last_update = current_time
            cv2.imshow(self._wname, self.fb)
            cv2.pollKey()

    def read_reg(self, relative_address: int) -> int:
        if relative_address > self._fb_offset:
            try:
                y = (relative_address - self._fb_offset) // self.width
                x = (relative_address - self._fb_offset) % self.width
                bgr = self.fb[y][x]

                return (bgr[0] << 24) | (bgr[1] << 16) | (bgr[2] << 8)
            except IndexError:
                raise IPException(f"VGI: out of framebuffer memory (read): {relative_address:x}")
        else:
            return super().read_reg(relative_address)

    def write_reg(self, relative_address: int, value: int) -> None:
        if relative_address > self._fb_offset:
            try:
                y = (relative_address - self._fb_offset) // self.width
                x = (relative_address - self._fb_offset) % self.width

                # print(f"VGI FB write: X={x}, Y={y}, val={value:x}")

                self.fb[y][x] = [
                    (value & 0xFF000000) >> 24,
                    (value & 0xFF0000) >> 16,
                    (value & 0xFF00) >> 8
                ]
            except IndexError:
                raise IPException(f"VGI: out of framebuffer memory (write): {relative_address:x}")
        else:
            super().write_reg(relative_address, value)
