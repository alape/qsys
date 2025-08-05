import builtins

from struct import pack
from dataclasses import dataclass, field
from math import ceil
from typing import Self

from assembler.util import IndexableEnum


class Opcode(IndexableEnum):
    """Enum that represents a QCPU opcode."""
    NOP = 0x0
    ADD = 0x1
    SUB = 0x2
    AND = 0x3
    OR = 0x4
    XOR = 0x5
    LSH = 0x6
    RSH = 0x7
    NOT = 0x8
    LD = 0x9
    ST = 0xA
    BEQ = 0xB
    BNE = 0xC
    BGT = 0xD
    BLT = 0xE
    JMP = 0xF
    JAL = 0x10
    RET = 0x11
    PSH = 0x12
    POP = 0x13


class Flavour(IndexableEnum):
    """Enum that represents a QCPU instruction flavour (i.e. addressing mode)."""
    N = 0
    R = 1
    I = 2
    S = 3
    Q = 4
    F = 5
    E = 6
    A = 7


class Register(IndexableEnum):
    """Enum that represents a QCPU register index."""
    ZEROES = 0x0
    ONES = 0x1
    PC = 0x2
    SC = 0x3
    SR = 0x4
    IR = 0x5
    IV = 0x6
    R0 = 0x8
    R1 = 0x9
    R2 = 0xA
    R3 = 0xB
    R4 = 0xC
    R5 = 0xD
    R6 = 0xE
    R7 = 0xF

    def lo(self) -> int:
        """Returns value of register in the lower nibble (byte[3:0])."""
        return self.value

    def hi(self) -> int:
        """Returns value of index bit-shifted to higher nibble (byte[7:4])."""
        return self.value << 4


@dataclass
class SymbolReference:
    """Reference promise: class that wraps a symbol, referenced by its name: this is to be replaced by symbol's
    absolute offset wrapped in an `AddressArgument` during compilation."""
    symbol_name: str


@dataclass
class PointerReference:
    """Same as `SymbolReference`, but resolves into immediate address (i.e., int) instead of an `AddressArgument`. """
    symbol_name: str


@dataclass
class AddressArgument:
    """Absolute address as argument: class that wraps a numeric address."""
    address: int


class MemoryEntity:
    """Abstract class that represents an entity stored in QCPU memory that has definite length and can be rendered
    into bytes."""

    def length(self) -> int:
        pass

    def get_bytes(self) -> bytes:
        pass


@dataclass
class Word(MemoryEntity):
    """Dataclass that represents a non-instruction word stored in QCPU memory (32 bits)."""
    value: int = 0

    def get_bytes(self) -> bytes:
        """Render contents of `MemoryWord` instance into bytes. Note that, since QCPU is a big-endian architecture,
        words are rendered as big-endian unsigned integers."""
        return pack(">I", self.value)

    def length(self) -> int:
        """Returns length of a QCPU word (which is always 1 word)."""
        return 1


@dataclass
class DB(MemoryEntity):
    """Dataclass that represents an arbitrary sequence of bytes stored in QCPU memory."""
    data: bytes = field(default_factory=bytes)

    def get_bytes(self) -> bytes:
        # pad data to whole words
        padding = (4 * self.length()) - len(self.data)
        return self.data + (b"\x00" * padding)

    def length(self) -> int:
        # note that data is aligned to 4 bytes (1 QCPU word)
        return ceil(len(self.data) / 4)


@dataclass
class Instruction(MemoryEntity):
    """Dataclass that represents a single QCPU instruction."""
    opcode: Opcode
    flavour: Flavour = Flavour.N
    arguments: list[Register | SymbolReference | PointerReference | AddressArgument | int] = field(default_factory=list)

    def __str__(self) -> str:
        base_name = self.opcode.name + self.flavour.name

        arguments_rendered = []
        for argument in self.arguments:
            if isinstance(argument, int):
                arguments_rendered.append(hex(argument))
            elif isinstance(argument, Register):
                arguments_rendered.append(argument.name)
            elif isinstance(argument, AddressArgument):
                arguments_rendered.append(f"@{argument.address:#x}")
            else:
                arguments_rendered.append(str(argument))

        return base_name.ljust(4) + " " + ", ".join(arguments_rendered)

    def length(self) -> int:
        return 1

    def get_instruction(self) -> bytes:
        """Combines opcode and flavour into an instruction byte."""
        return bytes([(self.flavour.value << 5) | self.opcode.value])

    def deduce_flavour(self) -> None:
        """Deduce instruction flavour based on its arguments and save it to `flavour` attribute."""
        signature = [type(arg) for arg in self.arguments]
        if not signature:
            # N flavour: no arguments
            self.flavour = Flavour.N
        elif signature == [Register, Register, Register]:
            # R flavour: dest [Register], src1 [Register], src2 [Register]
            self.flavour = Flavour.R
        elif signature == [Register, Register, builtins.int] or signature == [Register, Register, PointerReference]:
            # I flavour: dest [Register], src1 [Register], src2 [int: 16-bit immediate]
            self.flavour = Flavour.I
        elif signature == [Register, builtins.int] or signature == [Register, PointerReference]:
            # S flavour: dest [Register], src [int: 20-bit immediate]
            self.flavour = Flavour.S
        elif signature == [Register, Register]:
            # F flavour: dest [Register], src [Register]
            self.flavour = Flavour.F
        elif signature == [Register]:
            # E flavour: dest [Register]
            self.flavour = Flavour.E
        elif signature == [Register, AddressArgument] or signature == [Register, SymbolReference]:
            # A flavour: dest [Register], addr [AddressArgument / ?SymbolReference]
            self.flavour = Flavour.A
        elif signature == [AddressArgument] or signature == [SymbolReference] or signature == [builtins.int]:
            # Q flavour: dest [AddressArgument / int]
            self.flavour = Flavour.Q
        else:
            raise AttributeError(f"Invalid argument signature for instruction {self.opcode.name}: "
                                 f"{[a.__class__.__name__ for a in self.arguments]}")

    def get_bytes(self) -> bytes:
        """Render instruction into bytes."""
        def _check_arglen(expected_length):
            if not len(self.arguments) == expected_length:
                raise AttributeError(f"Argument quantity mismatch: "
                                     f"{self.opcode.name}{self.flavour.name} expects {expected_length} arguments, "
                                     f"but {len(self.arguments)} were provided.")

        def _check_argtype(signature):
            argument_types = [type(a) for a in self.arguments]
            for present, required in zip(argument_types, signature):
                if present != required:
                    raise AttributeError(f"Argument type mismatch: "
                                         f"{self.opcode.name}{self.flavour.name} expects arguments of "
                                         f"signature {signature}, but {argument_types} were provided.")

        if self.flavour == Flavour.N and self.opcode not in (Opcode.NOP, Opcode.RET):
            raise AttributeError(f"Flavour not set for instruction: {self.opcode.name}")

        match self.flavour:
            case Flavour.N:
                # N flavour: no arguments
                return self.get_instruction() + b"\x00\x00\x00"

            case Flavour.R:
                # R flavour: dest [Register], src1 [Register], src2 [Register]: all arguments must be Register indices
                _check_arglen(3)
                _check_argtype([Register, Register, Register])

                return (self.get_instruction() +
                        bytes([self.arguments[0].hi() | self.arguments[1].lo(), self.arguments[2].hi(), 0]))

            case Flavour.I:
                # I flavour: dest [Register], src1 [Register], src2 [int: 16-bit immediate]
                _check_arglen(3)
                _check_argtype([Register, Register, int])

                src2 = self.arguments[2]

                return (self.get_instruction() +
                        bytes([self.arguments[0].hi() | self.arguments[1].lo(), (src2 & 0xFF00) >> 8, src2 & 0xFF]))

            case Flavour.S:
                # S flavour: dest [Register], src [int: 20-bit immediate]
                _check_arglen(2)
                _check_argtype([Register, int])

                src = self.arguments[1]

                return (self.get_instruction() +
                        bytes([self.arguments[0].hi() | (src & 0xF0000) >> 16, (src & 0xFF00) >> 8, src & 0xFF]))

            case Flavour.F:
                # F flavour: dest [Register], src [Register]
                _check_arglen(2)
                _check_argtype([Register, Register])

                return self.get_instruction() + bytes([self.arguments[0].hi() | self.arguments[1].lo(), 0, 0])

            case Flavour.E:
                # E flavour: dest [Register]
                _check_arglen(1)
                _check_argtype([Register])

                return (self.get_instruction() +
                        bytes([self.arguments[0].hi(), 0, 0]))

            case Flavour.A:
                # A flavour: dest [Register], ref [AddressArgument / ?SymbolReference]
                _check_arglen(2)

                if isinstance(self.arguments[1], SymbolReference):
                    raise AttributeError(f"Instruction contains unresolved reference: {self.arguments[1].symbol_name}")

                _check_argtype([Register, AddressArgument])

                src = self.arguments[1].address

                return (self.get_instruction() +
                        bytes([self.arguments[0].hi() | (src & 0xF0000) >> 16, (src & 0xFF00) >> 8, src & 0xFF]))

            case Flavour.Q:
                # Q flavour: ref [AddressArgument / ?SymbolReference]
                _check_arglen(1)

                if isinstance(self.arguments[0], SymbolReference):
                    raise AttributeError(f"Instruction contains unresolved reference: {self.arguments[1].symbol_name}")

                _check_argtype([AddressArgument])

                src = self.arguments[0].address

                return (self.get_instruction() +
                        bytes([(src & 0xFF0000) >> 16, (src & 0xFF00) >> 8, src & 0xFF]))

    @classmethod
    def from_bytes(cls, val: bytes) -> Self:
        """Parses bytecode into an `Instruction` instance. Assumes `val` is a `bytes` object of length 4 (1 word)."""
        assert len(val) == 4

        # parse Opcode and Flavour from first and second nibbles of the first byte respectively
        opcode = Opcode.from_value(val[0] & 0x1F)
        flavour = Flavour.from_value(val[0] >> 5)

        # parse arguments according to the retrieved Flavour
        arguments = []
        match flavour:
            case Flavour.R:
                # R flavour: dest [Register], src1 [Register], src2 [Register]: all arguments must be Register indices
                arguments = [Register.from_value(val[1] >> 4), Register.from_value(val[1] & 0xF),
                             Register.from_value(val[2] >> 4)]

            case Flavour.I:
                # I flavour: dest [Register], src1 [Register], src2 [int: 16-bit immediate]
                arguments = [Register.from_value(val[1] >> 4), Register.from_value(val[1] & 0xF),
                             (val[2] << 8) | val[3]]

            case Flavour.S:
                # S flavour: dest [Register], src [int: 20-bit immediate]
                arguments = [Register.from_value(val[1] >> 4),
                             ((val[1] & 0xF) << 16) | (val[2] << 8) | val[3]]

            case Flavour.F:
                # F flavour: dest [Register], src [Register]
                arguments = [Register.from_value(val[1] >> 4), Register.from_value(val[1] & 0xF)]

            case Flavour.E:
                # E flavour: dest [Register]
                arguments = [Register.from_value(val[1] >> 4)]

            case Flavour.A:
                # A flavour: dest [Register], ref [AddressArgument]
                arguments = [Register.from_value(val[1] >> 4),
                             AddressArgument(((val[1] & 0xF) << 16) | (val[2] << 8) | val[3])]

            case Flavour.Q:
                # Q flavour: ref [AddressArgument]
                arguments = [AddressArgument((val[1] << 16) | val[2] << 8 | val[3])]

        # pack parsed data into an Instruction instance and send it away
        return Instruction(opcode, flavour, arguments)
