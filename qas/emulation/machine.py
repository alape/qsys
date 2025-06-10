from typing import Self

from internals.instructions import Register, Opcode, Instruction, Flavour
from emulation.ip.controller import IPController
from emulation.ip.memory import MemoryBlock


class QCPUException(Exception):
    """A generic emulator-related exception class."""
    pass


class QCPUMachine:
    """Class that contains current state of emulated machine and processes CPU instructions."""
    def __init__(self, addr_space: list[dict] | None = None, load_at: int = 0, start_at: int = 0):
        if addr_space is not None:
            self.addr_space = IPController.from_config(addr_space)
        else:
            self.addr_space = IPController()

        self.load_at = load_at
        self.start_at = start_at

        # initialize registers
        self.registers = [0] * 0x10
        self.registers[Register.ONES.value] = 0xFFFFFFFF
        self.registers[Register.PC.value] = start_at

    @classmethod
    def from_config(cls, cfg: dict) -> Self:
        """Constructs a `QCPUMachine` instance from data contained in the configuration object."""
        return cls(**cfg)

    def load_from_binary(self, contents: bytes) -> None:
        """Load memory contents from a chunk of bytes. Assumes that `load_at` is located in a MemoryBlock instance."""
        ip = self.addr_space.get_ip_by_absolute_address(self.load_at)
        assert isinstance(ip, MemoryBlock)

        ip.load_bytes(contents)

    def step(self) -> None:
        """Perform a single step of the emulation."""
        increment_pc = True

        # honour interrupts: if IRQ is triggered, SR.IE = 1 and SR.II = 0, set SR.II and JAL to the interrupt vector
        if self.addr_space.irq != 0:
            sr_ie = bool(self.registers[Register.SR.value] & 0b10)
            sr_ii = bool(self.registers[Register.SR.value] & 0b100)

            if not sr_ii:
                self.registers[Register.IR.value] = self.addr_space.irq

            if sr_ie and not sr_ii:
                # set SR.II
                self.registers[Register.SR.value] |= 0b100

                # JAL to IV
                self.addr_space.write_reg(self.registers[Register.SC.value], self.registers[Register.PC.value])
                self.registers[Register.SC.value] += 1
                self.registers[Register.PC.value] = self.registers[Register.IV.value]
                increment_pc = False

        # load instruction
        instruction = Instruction.from_bytes(self.addr_space.read_reg(self.registers[Register.PC.value]).to_bytes(4))

        # extract operands and source/destination register from loaded instruction
        # note that `st_dest` is used exclusively by the ST opcode
        operand_1 = operand_2 = st_dest = None
        src_dest = Register.R0

        match instruction.flavour:
            case Flavour.R:
                operand_1 = self.registers[instruction.arguments[1].value]
                operand_2 = self.registers[instruction.arguments[2].value]
            case Flavour.I:
                operand_1 = self.registers[instruction.arguments[1].value]
                operand_2 = instruction.arguments[2]
            case Flavour.S:
                operand_1 = instruction.arguments[1]
            case Flavour.F:
                if instruction.opcode == Opcode.ST:
                    st_dest = self.registers[instruction.arguments[1].value]
                elif instruction.opcode == Opcode.LD:
                    operand_1 = self.addr_space.read_reg(self.registers[instruction.arguments[1].value])
                else:
                    operand_1 = self.registers[instruction.arguments[1].value]
            case Flavour.A:
                if instruction.opcode == Opcode.ST:
                    st_dest = instruction.arguments[1].address
                else:
                    operand_1 = self.addr_space.read_reg(instruction.arguments[1].address)
            case Flavour.Q:
                operand_1 = instruction.arguments[0].address
            case Flavour.E:
                operand_1 = self.registers[instruction.arguments[0]]
            case Flavour.N:
                pass
            case _:
                raise QCPUException(f"Malformed or unsupported instruction flavour: {instruction.flavour}")

        if instruction.flavour in (Flavour.R, Flavour.I, Flavour.S, Flavour.F, Flavour.A):
            assert len(instruction.arguments) > 0
            src_dest: Register = instruction.arguments[0]

        # execute instruction
        match instruction.opcode:
            case Opcode.NOP:
                pass
            case Opcode.ADD:
                self.registers[src_dest.value] = operand_1 + operand_2
            case Opcode.SUB:
                self.registers[src_dest.value] = operand_1 - operand_2
            case Opcode.AND:
                self.registers[src_dest.value] = operand_1 & operand_2
            case Opcode.OR:
                self.registers[src_dest.value] = operand_1 | operand_2
            case Opcode.XOR:
                self.registers[src_dest.value] = operand_1 ^ operand_2
            case Opcode.LSH:
                self.registers[src_dest.value] = self.registers[src_dest.value] << operand_1
            case Opcode.RSH:
                self.registers[src_dest.value] = self.registers[src_dest.value] >> operand_1
            case Opcode.NOT:
                self.registers[src_dest.value] = operand_1 ^ 0xFFFFFFFF
            case Opcode.LD:
                self.registers[src_dest.value] = operand_1
            case Opcode.ST:
                self.addr_space.write_reg(st_dest, self.registers[src_dest.value])
            case Opcode.BEQ:
                if operand_1 == operand_2:
                    self.registers[Register.PC.value] = self.registers[src_dest.value]
                    increment_pc = False
            case Opcode.BNE:
                if operand_1 != operand_2:
                    self.registers[Register.PC.value] = self.registers[src_dest.value]
                    increment_pc = False
            case Opcode.BGT:
                if operand_1 > operand_2:
                    self.registers[Register.PC.value] = self.registers[src_dest.value]
                    increment_pc = False
            case Opcode.BLT:
                if operand_1 < operand_2:
                    self.registers[Register.PC.value] = self.registers[src_dest.value]
                    increment_pc = False
            case Opcode.JMP:
                self.registers[Register.PC.value] = operand_1
                increment_pc = False
            case Opcode.JAL:
                self.addr_space.write_reg(self.registers[Register.SC.value], self.registers[Register.PC.value] + 1)
                self.registers[Register.SC.value] += 1
                self.registers[Register.PC.value] = operand_1
                increment_pc = False
            case Opcode.RET:
                self.registers[Register.SC.value] -= 1
                self.registers[Register.PC.value] = self.addr_space.read_reg(self.registers[Register.SC.value])
                increment_pc = False
            case _:
                raise QCPUException(f"Malformed or unsupported instruction opcode: {instruction.opcode}")

        if self.registers[Register.PC.value] == 0xa9b90000:
            pass

        # increment PC if required
        if increment_pc:
            self.registers[Register.PC.value] += 1

        # process address space-related updates
        self.addr_space.tick()
