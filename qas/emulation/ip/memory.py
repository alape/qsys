from emulation.ip.common import IP, IPRegisterAccessMode
from code.util import slice_by_chunks


class MemoryBlock(IP):
    """A generic memory instance (either ROM or RAM), contents can be loaded from file."""
    def __init__(self,
                 mem_size: int = 0xFF,
                 access_mode: IPRegisterAccessMode = IPRegisterAccessMode.RW, *args, **kwargs):
        self.addr_space_size = mem_size

        for i in range(mem_size):
            self.reg_descr[i] = ("MEM", access_mode, f"Memory block (word {i:#x})")

        super().__init__(*args, **kwargs)

    def load_bytes(self, image: bytes) -> None:
        """Fill the contents of memory with provided bytes."""
        for i, chunk in enumerate(slice_by_chunks(image, 4)):
            self.addrspace[i].value = int.from_bytes(chunk)
