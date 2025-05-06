from internals.program import Program
from internals.instructions import Word, DB, Instruction


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

            output += (f"{section_name} {section_offset:#x}..{section_offset + section_length:#x} "
                       f"({section_length:#x})\n")

            for symbol in self._prg.sections[section_name]:
                offset = self._prg.get_absolute_symbol_offset(symbol.name)

                output += (f"{offset:0{10}X}: <{symbol.name}> {offset:#x}..{offset + symbol.length():#x} "
                           f"({symbol.length():#x})\n")

                intra_symbol_offset = 0

                for entity in symbol.contents:
                    if isinstance(entity, DB):
                        entity_name = f"DB, {entity.data}"
                    elif isinstance(entity, Word):
                        entity_name = f"Word, {entity.value:#x}"
                    else:
                        entity_name = str(entity)

                    entity_contents = entity.get_bytes().hex()
                    entity_contents_sliced = \
                        " ".join([entity_contents[i:i + 2] for i in range(0, len(entity_contents), 2)])
                    output += f"{offset + intra_symbol_offset:0{10}X}: {entity_contents_sliced}: {entity_name}\n"
                    intra_symbol_offset += entity.length()

                output += "\n"

            output += "\n"

        return output
