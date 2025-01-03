import logging

from argparse import ArgumentParser

from internals.assembly import AssemblyParser
from internals.disassembly import Disassembler


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

    parser.add_argument("-o", "--output", type=str, metavar="OUTPUT_FILE", default="program.bin",
                        help="Specifies the output binary file.")

    parser.add_argument("files", nargs="+", type=str, metavar="SOURCE_FILE",
                        help="Source files to be assembled.")

    args = parser.parse_args()

    asm = AssemblyParser()

    # process input files
    for file in args.files:
        with open(file, "r") as f:
            asm.process_assembly(f.read())

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
            f.write(program.render_verilog_header())
