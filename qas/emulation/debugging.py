from sys import exit

from assembler.instructions import Register, Instruction
from emulation.machine import QCPUMachine


class QCPUDebugger:
    def __init__(self, machine: QCPUMachine):
        self.vm = machine
        self.stepping = True
        self.breakpoints = []

    def _process_debugger_command(self, command: str) -> bool:
        """Process a single debugger command. Return value indicates if whether debugger should quit prompt and proceed
        with the next step (`True`) or ask user for the next command (`False`)"""
        tokens = command.split(" ")
        match tokens[0].lower()[0]:
            case "s":
                # single step
                self.stepping = True
                self.vm.step()
                return True

            case "c":
                # continue: perform single step & disable stepping
                self.stepping = False
                self.vm.step()
                return True

            case "b":
                # set a breakpoint
                if len(tokens) > 1:
                    # if there is an argument, parse it as a hex and add as a breakpoint
                    self.breakpoints.append(int(tokens[1], 16))
                else:
                    # if there isn't an argument, add current PC to breakpoints
                    self.breakpoints.append(self.vm.registers[Register.PC.value])

                return False

            case "x":
                # remove a breakpoint
                if len(tokens) > 1:
                    # if there is an argument, parse it as a hex and remove it from breakpoints
                    addr = int(tokens[1], 16)
                else:
                    # if there isn't an argument, remove current PC from breakpoints
                    addr = self.vm.registers[Register.PC.value]

                if addr in self.breakpoints:
                    self.breakpoints.remove(addr)
                else:
                    print(f"[X] No breakpoint currently set at address {addr:X}.")

                return False

            case "r":
                # print or set registers
                if len(tokens) > 1:
                    reg = Register.from_string(tokens[1].upper())

                    if len(tokens) == 2:
                        # print a specific register
                        print(f"{reg.name}: {self.vm.registers[reg.value]:X}")
                    elif len(tokens) == 3:
                        # set a specific register:
                        self.vm.registers[reg.value] = int(tokens[2], 16)
                    else:
                        print(f"[X] Invalid syntax for \"register\" command.")
                else:
                    # print all registers
                    for reg in Register:
                        print(f"{reg.name}: {self.vm.registers[reg.value]:X}")

                return False

            case "q":
                # quit the debugger (and qsim)
                print("Bye!")
                exit(0)

            case "?":
                # read memory
                addr_list = []

                if len(tokens) < 2:
                    print(f"[X] Not enough arguments for \"read memory\" command.")

                for arg in tokens[1:]:
                    if "." in arg:
                        # argument is an address range
                        start, end = [int(a, 16) for a in arg.split(".", 1)]
                        addr_list += list(range(start, end + 1))
                    else:
                        # argument is a singular address
                        addr_list.append(int(arg, 16))

                for addr in addr_list:
                    print(f"{addr:X}: {self.vm.addr_space.read_reg(addr):X}")

            case "!":
                # write memory
                base_address: int | None = None
                values: list[tuple[int, int]] = []

                if len(tokens) < 2:
                    print(f"[X] Not enough arguments for \"write memory\" command.")

                for arg in tokens[1:]:
                    if ":" in arg:
                        # argument specifies base address
                        base_address, value = [int(a, 16) for a in arg.split(":", 1)]
                    else:
                        # argument contains value only
                        value = int(arg, 16)

                    if base_address is None:
                        print(f"[X] Base address not specified for value {value:X}")
                        return False

                    values.append((base_address, value))
                    base_address += 1

                for addr, value in values:
                    self.vm.addr_space.write_reg(addr, value)

                return False

            case _:
                # unrecognized command
                print(f"[X] Unrecognized command: \"{command}\", check syntax.")
                return False

    def debug_step(self, trace: bool = False) -> None:
        pc = self.vm.registers[Register.PC.value]

        if (not self.stepping) and (pc not in self.breakpoints):
            self.vm.step()
            return

        current_instruction = Instruction.from_bytes(self.vm.addr_space.read_reg(pc).to_bytes(4))

        arguments = []
        for a in current_instruction.arguments:
            if isinstance(a, Register):
                arguments.append(f"{str(a)} = {hex(self.vm.registers[a.value])}")
            elif isinstance(a, int):
                arguments.append(hex(a))
            else:
                arguments.append(str(a))

        print(f"{'[!] Break at ' if pc in self.breakpoints else '@'}{pc:X}: "
              f"{current_instruction} | {', '.join(arguments)}")

        if not trace:
            while True:
                cmd = ""
                while not cmd:
                    cmd = input("> ")

                if self._process_debugger_command(cmd):
                    break
        else:
            self.vm.step()
