import pickle

from dataclasses import dataclass, field
from collections import defaultdict

from assembler.instructions import MemoryEntity, Instruction, SymbolReference, PointerReference, AddressArgument


@dataclass
class Symbol(MemoryEntity):
    """Intermediate representation of a named symbol in program code."""
    name: str
    contents: list[MemoryEntity] = field(default_factory=list)
    offset: int = 0

    def length(self) -> int:
        """Returns length of symbol in bytes."""
        return sum([m.length() for m in self.contents])

    def get_bytes(self) -> bytes:
        """Renders symbol into a sequence of bytes."""
        return b"".join([m.get_bytes() for m in self.contents])


class Program:
    """Intermediate representation of an assembled QCPU program."""
    def __init__(self):
        self.sections: dict[str, list[Symbol]] = defaultdict(list)
        self.section_lengths: dict[str, int] = defaultdict(int)
        self.section_offsets: dict[str, int] = defaultdict(int)
        self.section_order = []

    def put_symbol(self, section_name: str, symbol: Symbol):
        """Adds symbol to the specified section. N.B.: modifies symbol's offset in-place."""
        if section_name not in self.section_order:
            self.section_order.append(section_name)

        symbol.offset = self.section_lengths[section_name] + 1
        self.sections[section_name].append(symbol)
        self.section_lengths[section_name] += symbol.length()

    def get_symbol(self, section_name: str, symbol_name: str) -> Symbol:
        """Retrieves symbol from specified section."""
        if section_name not in self.section_order:
            raise KeyError(f"No such section: '{section_name}'")

        for s in self.sections[section_name]:
            if s.name == symbol_name:
                return s

        raise KeyError(f"Symbol with name '{symbol_name}' is not present in section '{section_name}'")

    def is_symbol_in_section(self, section_name: str, symbol_name: str) -> bool:
        """Checks if whether symbol with given name is present in given section."""
        if section_name not in self.section_order:
            raise KeyError(f"No such section: '{section_name}'")

        for s in self.sections[section_name]:
            if s.name == symbol_name:
                return True

        return False

    def get_absolute_symbol_offset(self, symbol_name: str) -> int:
        """Resolves symbol name into offset: that is, calculates absolute offset of given symbol across all sections
        (i.e. relative to the program start)."""
        for section in self.section_order:
            offset = self.get_absolute_section_offset(section)
            for symbol in self.sections[section]:
                if symbol.name == symbol_name:
                    return offset
                else:
                    offset += symbol.length()

        raise KeyError(f"Symbol with name '{symbol_name}' is not present in any sections.")

    def get_absolute_section_offset(self, section_name: str) -> int:
        """Calculates absolute offset of given section relative to the program start."""
        offset = 0
        prev_length = 0

        for section in self.section_order:
            if self.section_offsets[section] != 0:
                offset = self.section_offsets[section]
            else:
                offset += prev_length

            prev_length = sum([symbol.length() for symbol in self.sections[section]])

            if section == section_name:
                return offset

        raise ValueError(f"Section '{section_name}' not found in code")

    def resolve_references(self) -> None:
        """Recursively resolves references between symbols in program sections: replaces instructions'
        `SymbolReference` arguments with symbol offsets."""
        for section in self.section_order:
            for symbol in self.sections[section]:
                for entity in symbol.contents:
                    if isinstance(entity, Instruction):
                        # resolve SymbolReferences into AddressArguments
                        references = [(idx, ref) for idx, ref in enumerate(entity.arguments) if
                                      isinstance(ref, SymbolReference)]

                        for idx, ref in references:
                            entity.arguments[idx] = AddressArgument(self.get_absolute_symbol_offset(ref.symbol_name))

                        # resolve PointerReferences into immediate int values
                        pointers = [(idx, ref) for idx, ref in enumerate(entity.arguments) if
                                    isinstance(ref, PointerReference)]

                        for idx, ref in pointers:
                            entity.arguments[idx] = self.get_absolute_symbol_offset(ref.symbol_name)

    def render_code(self) -> bytes:
        """Renders intermediate representation of the program into bytes of machine code."""
        code = b""
        current_position = 0

        for section in self.section_order:
            # pad code with NOPs to make sure section offset is honoured, but check for section overlap first
            offset = self.section_offsets[section]
            if 0 < offset < current_position:
                raise ValueError(f"Section '{section}' overlaps previous section "
                                 f"(section offset is {hex(offset)}, but previous sections "
                                 f"take up {current_position} words)")

            code += b"\x00\x00\x00\x00" * (offset - current_position)
            current_position = offset

            # render symbols into bytecode
            for symbol in self.sections[section]:
                s_code = symbol.get_bytes()
                s_length = symbol.length()
                code += symbol.get_bytes()
                current_position += symbol.length()

        return code

    def render_object_file(self) -> bytes:
        """Renders `Program` instance into an object file (essentially, a pickle of itself) to be used in other
        compilation units w/ `load_object_file()`."""
        return pickle.dumps(self)

    def render_verilog_header(self, entity_name: str = "memory") -> str:
        """Renders `Program` instance into a Verilog header that consists of an `initial` block that assigns values
        to the array accessed by `entity_name`, 1 word (32 bits) per array element."""
        v_text = "`ifndef MEMORY_VH_\n`define MEMORY_VH_\n\ninitial begin\n"

        # render bytecode and split it into chunks of 4 bytes (1 word)
        bytecode = self.render_code()
        words = [bytecode[i:i + 4] for i in range(0, len(bytecode), 4)]

        # render code words into assignment statements, staring with index 0
        for i, word in enumerate(words):
            v_text += f"    {entity_name}[{i}] = 32'h{word.hex().upper()};\n"

        # finalize header file
        v_text += "end\n\n`endif\n"
        return v_text

    def load_object_file(self, data: bytes) -> None:
        """Merges contents of provided object file with itself, making its symbols available to local code fragments."""
        foreign_program: Program = pickle.loads(data)

        for foreign_section in foreign_program.section_order:
            if foreign_section in self.section_order:
                for symbol in foreign_program.sections[foreign_section]:
                    if not self.is_symbol_in_section(foreign_section, symbol.name):
                        self.put_symbol(foreign_section, symbol)
                    else:
                        raise ValueError(f"Error while importing object file: "
                                         f"symbol {symbol.name} is already present in section {foreign_section}")
            else:
                self.section_order.append(foreign_section)
                self.sections[foreign_section] = foreign_program.sections[foreign_section]

    def get_sections(self) -> list[tuple[str, int, int]]:
        """Returns information about program sections as a list of tuples:
        section name, section offset, section length."""
        output = []

        for section in self.section_order:
            output.append((section, self.section_offsets[section], self.section_lengths[section]))

        return output
