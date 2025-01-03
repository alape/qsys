from internals.program import Program


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
                s

            output += (f"{section_name}\t@{hex(section_offset)}..{hex(section_offset + section_length)} "
                       f"({hex(section_length)})\n")

            output += "NAME\tOFFSET\tLENGTH\n"

            for symbol in self._prg.sections[section_name]:
                offset = self._prg.get_absolute_symbol_offset(symbol.name)

                output += f"{symbol.name}\t{hex(offset)}\t{hex(symbol.length())}\n"

            output += "\n"

        return output
