import logging

from sys import exit
from argparse import ArgumentParser

from assembler.preprocessing import Preprocessor
from assembler.assembly import AssemblyParser
from assembler.disassembly import Disassembler


if __name__ == "__main__":
    parser = ArgumentParser("qas",
                            description="A reference implementation of a relocating assembler for QCPU ISA.",
                            epilog="QAS has Super Pesets Powers.")

    parser.add_argument("-m", "--memory_map", type=str, metavar="MEM_MAP_FILE",
                        help="Render memory map and output it to the specified text file.")

    parser.add_argument("--object", type=str, metavar="OBJECT_FILE",
                        help="Output object file instead of linked binary. If this argument is supplied, "
                             "\"--output\" argument is ignored.")

    parser.add_argument("-v", "--verilog", type=str, metavar="VH_FILE",
                        help="Output Verilog header file. If this argument is supplied, qas will additionally "
                             "produce bytecode rendered as Verilog header file.")

    parser.add_argument("--verilog_entity", type=str, metavar="ENTITY_NAME", default="memory",
                        help="Specifies name of array that is used in '--verilog' parameter output (default 'memory')")

    parser.add_argument("-o", "--output", type=str, metavar="OUTPUT_FILE", default="program.bin",
                        help="Specifies the output binary file.")

    parser.add_argument("-p", "--preprocess", type=str, metavar="OUTPUT_FILE", default="",
                        help="Preprocess input files and output result to a specified file. If this option is used, no "
                             "further actions will be performed.")

    parser.add_argument("-I", "--include", type=str, action="extend", nargs="+", metavar="PATH",
                        help="Adds a path to the list of paths assembler is looking into while processing includes.")

    parser.add_argument("-D", "--define", type=str, action="extend", nargs="+", metavar="MACRO",
                        help="Defines a global macro. Can be overridden by `#define` statements in code. "
                             "Format is MACRO_NAME=MACRO_CONTENTS, e.g. FOO=42.")

    parser.add_argument("files", nargs="+", type=str, metavar="SOURCE_FILE",
                        help="Source files to be assembled.")

    args = parser.parse_args()

    asm = AssemblyParser()

    # preprocess and assemble input files
    for file in args.files:
        with open(file, "r") as f:
            preprocessed_code = Preprocessor.preprocess(f.read(), ["."] + args.include, {})

        if args.preprocess:
            with open(args.preprocess, "a") as f:
                f.write(preprocessed_code + "\n")
        else:
            asm.process_assembly(preprocessed_code)

    # don't perform any further actions if preprocessor option is used
    if args.preprocess:
        exit(0)

    # link the program
    program = asm.get_program()
    program.resolve_references()

    # render primary output representations
    if args.object:
        # output object file
        with open(args.object, "wb") as f:
            f.write(program.render_object_file())
    else:
        # output bytecode file
        with open(args.output, "wb") as f:
            f.write(program.render_code())

    # optionally render secondary output representations

    # output memory map
    if args.memory_map:
        disasm = Disassembler(program)

        with open(args.memory_map, "w") as f:
            f.write(disasm.render_memory_map())

    # output Verilog header file
    if args.verilog:
        with open(args.verilog, "w") as f:
            f.write(program.render_verilog_header(args.verilog_entity))
