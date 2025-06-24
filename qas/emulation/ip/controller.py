from typing import Iterable, Self

from emulation.ip.common import IP
from emulation.ip.memory import *
from emulation.ip.simio import *

# a rather lazy way to map IP block classes to their mentions in config objects
KnownIPs = {
    "Memory": MemoryBlock,
    "SIMIO": SimIO
}


class IPController:
    """Class that compiles an address space from various IP blocks (either runtime objects or configuration)
    and provides a single entry point for interactions with them."""
    def __init__(self, ip_blocks: Iterable[IP] | None = None):
        self.blocks = []
        self.spans = []
        self.irq = 0

        if ip_blocks is not None:
            for ip in ip_blocks:
                self.add_ip(ip)

    def add_ip(self, ip: IP) -> None:
        """Add a single IP block to the address space."""
        self.blocks.append(ip)
        self.spans.append((ip.addr_offset, ip.addr_offset + ip.addr_space_size, ip))

    def tick(self) -> None:
        """Update IRQ output, process blocks' address space updates, as well as other actions that are dependent
        on the system clock."""
        self.irq = 0

        for _, _, ip in self.spans:
            ip.process_addr_space_update()
            ip.process_tick()
            self.irq |= ip.irq

    def get_ip_by_absolute_address(self, address: int) -> IP:
        """Returns an `IP` instance that corresponds to the specified absolute memory address in controller's
        address space."""
        for start, end, ip in self.spans:
            if start <= address <= end:
                return ip

        raise IndexError(f"Address space does not contain such address: {address:#x}")

    def write_reg(self, absolute_address: int, value: int) -> None:
        """Selects IP block by its absolute address and writes its memory (via its own write_reg() call)."""
        ip = self.get_ip_by_absolute_address(absolute_address)
        ip.write_reg(absolute_address - ip.addr_offset, value)

    def read_reg(self, absolute_address: int) -> int:
        """Selects IP block by its absolute address and reads its memory (via its own read_reg() call)."""
        ip = self.get_ip_by_absolute_address(absolute_address)
        return ip.read_reg(absolute_address - ip.addr_offset)

    @classmethod
    def from_config(cls, cfg: list[dict]) -> Self:
        """Creates an `IPController` instance from a config object (a block_name: block_config pair)."""
        ips = []

        for ip_config in cfg:
            # each entry should have at least two fields: "type" contains the name of IP block being configured,
            # "cfg" contains options that are passed to the class constructor
            assert "type" in ip_config
            assert "cfg" in ip_config

            try:
                ips.append(KnownIPs[ip_config["type"]](**ip_config["cfg"]))
            except KeyError:
                raise KeyError(f"Unknown IP block name: {ip_config['type']}")

        return cls(ips)
