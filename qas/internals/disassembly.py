from internals.program import Program
from internals.instructions import Instruction, DB


class Disassembler:
    """Collection of tools for disassembly and memory map rendering that are performed on an intermediate
    representation of the program."""

    def __init__(self, program: Program):
        self._prg = program

    def render_memory_map(self) -> str:
        """Renders a text representation of program memory map."""
        output = ""

        for section_name, section_offset, section_length in self._prg.get_sections():
            # section offset not specified, calculate the actual offset
            if section_offset == 0:
                section_offset = self._prg.get_absolute_section_offset(section_name)

            output += (f"{section_name.ljust(20)}{hex(section_offset)}..{hex(section_offset + section_length)} "
                       f"({hex(section_length)})\n")

            output += "NAME".ljust(20) + "OFFSET".ljust(12) + "LENGTH".ljust(12) + "\n"

            for symbol in self._prg.sections[section_name]:
                offset = self._prg.get_absolute_symbol_offset(symbol.name)

                output += symbol.name.ljust(20) + hex(offset).ljust(12) + hex(symbol.length()).ljust(12) + "\n"

                for entity in symbol.contents:
                    entity_name = entity.get_bytes().hex().upper() + ": " + str(entity)
                    output += entity_name.ljust(20) + "\n"

                output += "\n"

            output += "\n"

        return output
