import re
import shlex

from struct import pack

from internals.instructions import SymbolReference, OffsetArgument, Register, Instruction, Opcode, AddressArgument, DB
from internals.program import Program, Symbol


class ParsingError(Exception):
    """A generic assembly parsing exception."""
    pass


class ParsingTools:
    """A collection of helper functions for assembly parsing."""
    _re_is_immediate_int = re.compile(r"(0b|'b|0x|'h|)(\d+)")
    _re_is_symbol_name = re.compile(r"^[a-zA-Z0-9\-_]+$")

    @staticmethod
    def is_valid_symbol_name(name: str) -> bool:
        """Returns True if `name` is a valid qas symbol name, False otherwise."""
        return re.match(ParsingTools._re_is_symbol_name, name) is not None

    @staticmethod
    def is_valid_numeral(token: str) -> bool:
        """Returns True if `token` is a valid numeral with radix of 2, 10 or 6; otherwise returns False."""
        return re.match(ParsingTools._re_is_immediate_int, token) is not None

    @staticmethod
    def parse_numeral(token: str) -> int:
        """Parses a numeral token radix of 2, 10 or 6 into int. Both C- and Verilog- style syntax flavours
        are supported."""
        numeral_match = re.findall(ParsingTools._re_is_immediate_int, token)

        radix, digits = numeral_match[0]

        match radix:
            case "0x" | "'h":
                return int(digits, 16)
            case "0b" | "'b":
                return int(digits, 2)
            case _:
                return int(digits)

    @staticmethod
    def parse_instruction_argument(argument: str) -> (SymbolReference |
                                                      OffsetArgument | AddressArgument | Register | int):
        """Parses a single instruction argument into corresponding wrapper type."""
        if argument.upper() in Register.indices():
            # argument is a register index, parse into `Register` enum value
            return Register.from_string(argument)

        if len(argument) > 0 and argument[0] in ("+", "-"):
            # argument is a PC offset (E-flavoured instruction), wrap value into an `OffsetArgument`
            return OffsetArgument(int(argument))

        if len(argument) > 0 and argument[0] == "@":
            # argument is an absolute address, wrap value into an `AddressArgument`
            return AddressArgument(ParsingTools.parse_numeral(argument.lstrip("@")))

        if ParsingTools.is_valid_numeral(argument):
            # immediate numeral argument, parse to int according to specified radix
            return ParsingTools.parse_numeral(argument)

        # IDK, this might be a symbol reference or some shit
        # (validate it first tho, only A-Za-z0-9_- characters are allowed in symbol names)
        if ParsingTools.is_valid_symbol_name(argument):
            return SymbolReference(argument)
        else:
            raise ParsingError(f"Invalid instruction argument format: '{argument}'")

    @staticmethod
    def parse_data_argument(token: str) -> bytes:
        """Parses a single `data` statement argument into bytes."""
        if ParsingTools.is_valid_numeral(token):
            # numeral bytes
            num = ParsingTools.parse_numeral(token)

            # determine byte format based on numeral's size
            if num <= 0xFF:
                # unsigned char
                fmt = "B"
            elif num <= 0xFFFF:
                # unsigned short
                fmt = "H"
            elif num <= 0xFFFFFFFF:
                # unsigned int:
                fmt = "I"
            else:
                # unsigned long long
                fmt = "Q"

            return pack(">" + fmt, num)

        if (token.startswith("\"") and token.endswith("\"")) or (token.startswith("'") and token.endswith("'")):
            # ASCII string
            return token.strip("\"'").encode("ascii")

        raise ParsingError(f"Invalid data argument: '{token}'")

    @staticmethod
    def tokenize(line: str) -> list[str]:
        """Splits assembly line into tokens: removes commas between arguments, removes comments,
        joins quoted string values."""
        output = []

        in_comment = False

        for token in shlex.split(line, posix=False):
            if in_comment:
                # skip all tokens once the comment starts
                continue

            elif token == ",":
                # trailing comma after a string
                continue

            elif token.startswith(";"):
                # comment begins, all further tokens will be ignored
                in_comment = True

            else:
                output.append(token.rstrip(","))

        return output


class AssemblyParser:
    """Core of qas operations. Lines of assembly come in, `Program` instances come out."""
    def __init__(self):
        self._prg = Program()

    def process_assembly(self, code: str):
        """Process assembly code, store results in internal structures to be retrieved later w/ `get_program()`."""
        curr_section = ".text"
        curr_symbol: Symbol | None = None

        for lineno, line in enumerate(code.splitlines()):
            tokens = ParsingTools.tokenize(line)
            instruction: Instruction | None = None
            data: DB | None = None

            try:
                for token in tokens:
                    if token.startswith("."):
                        # new section: finalize current symbol and start new one
                        if curr_symbol is not None:
                            self._prg.put_symbol(curr_section, curr_symbol)
                            curr_symbol = None

                        # section declaration
                        curr_section = token

                    elif token.startswith("@"):
                        # this might either be a section offset or an absolute address argument...
                        address: AddressArgument = ParsingTools.parse_instruction_argument(token.strip(","))

                        if instruction is not None:
                            # instruction declaration is open, this is an argument
                            instruction.arguments.append(address)
                        else:
                            # this is a section offset, check if it's already set
                            if self._prg.section_offsets[curr_section] != 0:
                                raise ParsingError(f"Offset for section '{curr_section}' is already set")

                            self._prg.section_offsets[curr_section] = address.address

                    elif token.endswith(":"):
                        # symbol declaration: finalize current symbol and start new one
                        if curr_symbol is not None:
                            self._prg.put_symbol(curr_section, curr_symbol)

                        new_symbol_name = token.rstrip(":")

                        if not ParsingTools.is_valid_symbol_name(new_symbol_name):
                            raise ParsingError(f"Invalid symbol name: {new_symbol_name}")

                        curr_symbol = Symbol(name=new_symbol_name)

                    elif token.lower() == "data":
                        # data element declaration
                        data = DB()

                    else:
                        # this might be either an instruction name, one of its arguments or a piece of data...
                        if data is not None:
                            # ...token is a `data` statement argument
                            data.data += ParsingTools.parse_data_argument(token)
                        else:
                            if instruction is None:
                                # ...token is an instruction name
                                instruction = Instruction(Opcode.from_string(token))
                            else:
                                # ...token is an instruction argument
                                instruction.arguments.append(
                                    ParsingTools.parse_instruction_argument(token))

                # wrap up an instruction if it's been declared on this line
                if instruction is not None:
                    if curr_symbol is None:
                        raise ParsingError(f"Instruction declared out of symbol")

                    instruction.deduce_flavour()
                    curr_symbol.contents.append(instruction)

                # wrap up a data object if it's been declared on this line
                if data is not None:
                    if curr_symbol is None:
                        raise ParsingError(f"Data object declared out of symbol")

                    curr_symbol.contents.append(data)

            except (ValueError, KeyError, AttributeError, ParsingError) as e:
                raise ParsingError(f"At line {lineno + 1}: {str(e)}") from e

        # wrap up the current symbol if it exists
        if curr_symbol is not None:
            self._prg.put_symbol(curr_section, curr_symbol)

    def get_program(self) -> Program:
        """Returns the current intermediate representation of program being assembled."""
        return self._prg
