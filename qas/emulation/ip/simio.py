from emulation.ip.common import IP, IPRegisterAccessMode


class SimIO(IP):
    """SimIO IP block. Provides console I/O for the emulated CPU core."""
    reg_descr = {
        0: ("EASYMMAP_ID", IPRegisterAccessMode.R, "EasyMMap identifier"),
        1: ("SIMO", IPRegisterAccessMode.W, "Output port: first byte is written to SimIO")
    }

    def process_addr_space_update(self) -> None:
        """Outputs the byte stored in SIMO register."""
        if self.addrspace[1].value:
            print(chr((self.addrspace[1].value & 0xFF000000) >> 24), end="")
            self.addrspace[1].value = 0
