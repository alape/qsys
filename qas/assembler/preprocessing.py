import re
import shlex

from typing import Iterable

from os.path import isfile, join


class PreprocessorException(Exception):
    """A generic class for preprocessor-related exceptions."""
    pass


class Preprocessor:
    """A collection of preprocessing routines that handle tasks such as resolution of include directives,
    macros etc."""
    _macro_re = r"#define\s+([^\s\(]+)(\(.+?\)|)\s+(.+)$"

    @staticmethod
    def resolve_includes(code: str, paths: Iterable[str]) -> str:
        """Resolves includes for given paths, returns code with #include directives replaced with
        their respective contents."""
        processed_code = code
        includes = []

        for line in code.splitlines():
            if line.strip().startswith("#include "):
                _, include = [t.strip("\"\"<>") for t in line.split(" ", 1)]
                includes.append(include)

        for include in includes:
            for path in paths:
                include_candidate = join(path, include)
                if isfile(include_candidate):
                    with open(include_candidate, "r") as f:
                        include_contents = f.read()

                    for template in [
                        f"#include {include}",
                        f"#include \"{include}\"",
                        f"#include <{include}>"
                    ]:
                        processed_code = processed_code.replace(template, include_contents)

                    break
            else:
                raise PreprocessorException(f"Include file {include} not found in {paths}")

        return processed_code

    @classmethod
    def parse_macro(cls, macro: str) -> tuple[str, tuple[str], str]:
        """Parses a macrodefintion (e.g. "#define FOO(X, Y) add X, Y, 42") into the tuple:
        (name, argument list, contents)."""
        match = re.findall(cls._macro_re, macro)

        if len(match) == 0:
            raise PreprocessorException(f"Malformed macrodefinition: \"{macro}\"")

        tokens = match[0]

        name = tokens[0]
        contents = tokens[2]

        if len(tokens[1]) > 0:
            parameters = tuple(shlex.split(tokens[1].strip("()")))
        else:
            parameters = tuple()

        return name, parameters, contents

    @staticmethod
    def _apply_arguments_to_function_macro(parameters: Iterable[str], arguments: Iterable[str], contents: str) -> str:
        """Applies _arguments_ to a _parameterized_ macro, returning the contents of said macro with parameters replaced
        with their respective values."""
        processed_macro = contents
        for parameter, argument in zip(parameters, arguments):
            processed_macro = processed_macro.replace(parameter, argument)

        return processed_macro

    @classmethod
    def resolve_macros(cls, code: str, external_macros: dict[str, tuple[tuple[str], str]]) -> str:
        """Resolves macrodefinitions: extracts them on-the-fly from the block of code being processed, adds them to
        those supplied via `external_macros` and applies them to the code block provided."""
        processed_code = code
        macros = external_macros

        # extract macros' definitions
        for line in code.splitlines():
            stripped_line = line.strip()
            if stripped_line.startswith("#define"):
                name, parameters, contents = cls.parse_macro(stripped_line)
                macros[name] = (parameters, contents)
                processed_code = processed_code.replace(line + "\n", "")

        # use them to replace the macros' invocations
        for macro_name, macro_data in macros.items():
            parameters = macro_data[0]
            contents = macro_data[1]
            if macro_name + "(" in code:
                # macro invocation is function-ish
                if len(parameters) == 0:
                    raise PreprocessorException(f"Macrodefinition \"{macro_name}\" is not a function")

                re_arguments = re.findall(rf"{macro_name}\((.+?)\)", code)
                if len(re_arguments) == 0:
                    raise PreprocessorException(f"Malformed call for \"{macro_name}\" function macro")

                for invocation in re_arguments:
                    arguments = shlex.split(invocation)
                    resolved_macro = cls._apply_arguments_to_function_macro(parameters, arguments, contents)

                    processed_code = processed_code.replace(f"{macro_name}({invocation})", resolved_macro)
            elif macro_name in code:
                # macro is a plain replacement
                processed_code = processed_code.replace(macro_name, contents)

        return processed_code

    @classmethod
    def preprocess(cls, code: str, include_paths: Iterable[str],
                   external_macros: dict[str, tuple[tuple[str], str]]) -> str:
        """Helper function that performs all preprocessing steps in one go."""
        includes_resolved = cls.resolve_includes(code, include_paths)
        return cls.resolve_macros(includes_resolved, external_macros)
