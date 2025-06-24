from threading import Thread
from sys import exit

from emulation.ip.common import IP, IPRegisterAccessMode


class KeyboardThread(Thread):
    """Helper class that processes keyboard input in the background."""

    def __init__(self, input_cbk=None, name="keyboard-input-thread"):
        self.input_cbk = input_cbk
        super(KeyboardThread, self).__init__(name=name, daemon=True)
        self.start()

    def run(self):
        while True:
            # waits to get input + Return
            self.input_cbk(input())


class SimIO(IP):
    """SimIO IP block. Provides console I/O for the emulated CPU core."""
    reg_descr = {
        0: ("EASYMMAP_ID", IPRegisterAccessMode.R, "EasyMMap identifier"),
        1: ("SIMO", IPRegisterAccessMode.W, "Output port: first byte is written to SimIO"),
        2: ("SIMI", IPRegisterAccessMode.R, "Input port: first byte is taken from SimIO, 0 if there was no input"),
        3: ("TRAP", IPRegisterAccessMode.RW, "Simulation environment trapdoor: if set to 1, simulation environment"
                                             "terminates")
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # initialize the keyboard input thread: entered strings are stored in a buffer and output
        # one byte per each SIMI access
        self.input_buffer = ""
        self.kthread = KeyboardThread(lambda c: setattr(self, "input_buffer", getattr(self, "input_buffer") + c))

    def process_addr_space_update(self) -> None:
        """Outputs the byte stored in SIMO register."""
        if self.addrspace[3].value == 1:
            print("Simulation exit requested via TRAP, goodbye!")
            exit(0)

        if self.addrspace[1].value:
            print(chr((self.addrspace[1].value & 0xFF000000) >> 24), end="")
            self.addrspace[1].value = 0

    def read_reg(self, relative_address: int) -> int:
        """Overrides the superclass' read_reg() to intercept SIMI read requests."""
        if relative_address == 2:
            if self.input_buffer != "":
                self.addrspace[2].value = ord(self.input_buffer[0]) & 0xFF
                self.input_buffer = self.input_buffer[1:]

        return super().read_reg(relative_address)
