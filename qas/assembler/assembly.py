import re
import shlex
import operator

from struct import pack

from assembler.instructions import (SymbolReference, PointerReference, Register, Instruction,
                                    Opcode, AddressArgument, DB, Word)
from assembler.program import Program, Symbol


class ParsingError(Exception):
    """A generic assembly parsing exception."""
    pass


class ParsingTools:
    """A collection of helper functions for assembly parsing."""
    _re_is_immediate_int = re.compile(r"^(0b|'b|0x|'h|)(\d+|(?<=0x|'h)[\da-fA-F]+)$")
    _re_is_symbol_name = re.compile(r"^[a-zA-Z0-9\-_]+$")
    _re_is_eval_math = re.compile(r"[+\-*&|/]")

    _op_map = {
        "+": operator.add,
        "-": operator.sub,
        "*": operator.mul,
        "/": operator.floordiv,
        "&": operator.and_,
        "|": operator.or_
    }

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

    @classmethod
    def parse_instruction_argument(cls, argument: str) -> (SymbolReference | PointerReference |
                                                           AddressArgument | Register | int):
        """Parses a single instruction argument into corresponding wrapper type."""
        argument_is_math = re.search(cls._re_is_eval_math, argument) is not None

        if argument_is_math:
            if len(argument) > 0 and argument[0] == "$":
                raise ParsingError("Symbol references cannot contain math expressions")

            op = re.findall(cls._re_is_eval_math, argument.lstrip("@"))[0]
            arguments = [cls.parse_numeral(arg) for arg in re.split(cls._re_is_eval_math,
                                                                    argument.lstrip("@"), 2)]

            # dumb, but safe way of evaluating math operators
            eval_result = cls._op_map[op](arguments[0], arguments[1])

            # if math argument starts with "@", wrap evaluation result into AddressArgument, else emit it as is
            return AddressArgument(eval_result) if (len(argument) > 0 and argument[0] == "@") else eval_result
        else:
            if argument.upper() in Register.indices():
                # argument is a register index, parse into `Register` enum value
                return Register.from_string(argument)

            if argument.startswith("@"):
                # argument is an absolute address, wrap value into an `AddressArgument`
                return AddressArgument(cls.parse_numeral(argument.lstrip("@")))

            if argument.startswith("$"):
                # argument is an address of a symbol, wrap value into a `SymbolReference`
                return PointerReference(argument.lstrip("$"))

            if ParsingTools.is_valid_numeral(argument):
                # immediate numeral argument, parse to int according to specified radix
                return cls.parse_numeral(argument)

        # IDK, this might be a symbol reference or some shit
        # (validate it first tho, only A-Za-z0-9_- characters are allowed in symbol names)
        if cls.is_valid_symbol_name(argument):
            return SymbolReference(argument)
        else:
            raise ParsingError(f"Invalid instruction argument format: '{argument}'")

    @staticmethod
    def parse_word_argument(token: str) -> int:
        """Parses a single `word` argument into a numeric value."""

        # check if whether token is a valid numeral. If not, raise an exception
        if ParsingTools.is_valid_numeral(token):
            return ParsingTools.parse_numeral(token)
        else:
            raise ParsingError(f"Invalid word argument: '{token}'")

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

    @classmethod
    def tokenize(cls, line: str) -> list[str]:
        """Splits assembly line into tokens: removes commas between arguments, removes comments,
        joins quoted string values."""
        output = []

        in_comment = False
        last_token_is_math = False

        for token in shlex.split(line, posix=False):
            if in_comment:
                # skip all tokens once the comment starts
                continue

            elif token == ",":
                # trailing comma after a string
                continue

            elif token.startswith(";"):
                # comment begins at the start of token, all further tokens will be ignored
                in_comment = True

            elif re.search(cls._re_is_eval_math, token):
                # token is math operator, append it to the last processed token
                last_token_is_math = True
                if len(output) > 0:
                    output[-1] += token
                else:
                    raise ParsingError(f"Operator \"{token}\" requires a prefix")

            else:
                token_stripped = token.rstrip(",")
                if last_token_is_math:
                    # if last token was a math operator, append current token to the last one
                    last_token_is_math = False
                    output[-1] += token_stripped
                else:
                    output.append(token_stripped)

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
            word: Word | None = None

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

                    elif token.lower() == "word":
                        # data word declaration
                        word = Word()

                    else:
                        # this might be either an instruction name, one of its arguments or a piece of data...
                        if data is not None:
                            # ...token is a `data` statement argument
                            data.data += ParsingTools.parse_data_argument(token)
                        elif word is not None:
                            # ...token is a `word` statement argument
                            word.value = ParsingTools.parse_word_argument(token)
                        elif instruction is None:
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

                # wrap up a word object if it's been declared on this line
                if word is not None:
                    if curr_symbol is None:
                        raise ParsingError(f"Word object declared out of symbol")

                    curr_symbol.contents.append(word)

            except (ValueError, KeyError, AttributeError, ParsingError) as e:
                raise ParsingError(f"At line {lineno + 1}: {str(e)}") from e

        # wrap up the current symbol if it exists
        if curr_symbol is not None:
            self._prg.put_symbol(curr_section, curr_symbol)

    def get_program(self) -> Program:
        """Returns the current intermediate representation of program being assembled."""
        return self._prg
