from enum import Enum, auto

from internals.instructions import Word


class IPException(Exception):
    """A generic IP block-related exception class."""
    pass


class IPRegisterAccessMode(Enum):
    """Enum that represents one of possible register access modes."""
    RW = auto()
    R = auto()
    W = auto()


class IP:
    """Prototype class of an EasyMMap-compliant IP block."""
    # static parameters: address space size, EasyMMap ID, and human-readable register descriptions
    addr_space_size = 0xff
    easymmap_id = 0xDEADBEEF
    reg_descr = {}

    def __init__(self, addr_offset: int = 0):
        # create an empty address space
        assert self.addr_space_size > 0
        self.addrspace = [Word() for _ in range(self.addr_space_size)]

        # set first word of addrspace to be an EasyMMap ID
        self.addrspace[0].value = self.easymmap_id

        self.addr_offset = addr_offset

        # note that IP controller will OR all blocks' IRQ outputs to produce value fed into CPU core
        self.irq = 0

        self._config_address_space()

    def _config_address_space(self) -> None:
        """Hook that configures address space. Called after class's constructor is done configuring the main aspects
        of the IP block instance."""
        pass

    def process_addr_space_update(self) -> None:
        """Process updates caused to the IP block's address space by other components of the emulator."""
        pass

    def process_tick(self) -> None:
        """Process various other tasks tied to the system clock."""
        pass

    def write_reg(self, relative_address: int, value: int) -> None:
        """Writes IP block's address space using absolute addresses."""
        if (relative_address in self.reg_descr and
                (self.reg_descr[relative_address][1] not in (IPRegisterAccessMode.RW, IPRegisterAccessMode.W))):
            raise IPException(f"Register {self.reg_descr[relative_address][0]} cannot be written "
                              f"(access mode {self.reg_descr[relative_address][1].value})")

        try:
            self.addrspace[relative_address].value = value
        except IndexError:
            raise IPException(f"Register w/ address {relative_address:#x} doesn't exist in this IP block")

    def read_reg(self, relative_address: int) -> int:
        """Reads IP block's address space using absolute addresses."""
        if (relative_address in self.reg_descr and
                (self.reg_descr[relative_address][1] not in (IPRegisterAccessMode.RW, IPRegisterAccessMode.R))):
            raise IPException(f"Register {self.reg_descr[relative_address][0]} cannot be read "
                              f"(access mode {self.reg_descr[relative_address][1].value})")

        try:
            return self.addrspace[relative_address].value
        except IndexError:
            raise IPException(f"Register w/ address {relative_address:#x} doesn't exist in this IP block")
