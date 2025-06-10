import logging
import json

from argparse import ArgumentParser

from emulation.machine import QCPUMachine
from emulation.debugging import QCPUDebugger
from internals.versioning import get_version

if __name__ == "__main__":
    # parse command line arguments
    parser = ArgumentParser("qsim",
                            description="A reference implementation of a QCPU simulator / debugger.",
                            epilog="QSIM has Super Pesets Powers.")

    parser.add_argument("-c", "--config", type=str, required=True, help="JSON file that specifies machine "
                                                                        "configuration (address space map etc.)")

    parser.add_argument("-d", "--debug", action="store_true", help="Enable debugging")

    parser.add_argument("bin", metavar="BINFILE", type=str, help="Binary file containing the QCPU startup "
                                                                 "code")

    args = parser.parse_args()

    # initialize logging
    logging.basicConfig(level=logging.INFO)
    log = logging.getLogger("qsim")
    log.info(f"This is QSIM v. {get_version()}")

    # initialize VM:
    # first, read machine config
    log.info(f"Reading machine configuration from {args.config}...")
    with open(args.config, "r") as f:
        cfg = json.load(f)

    # then, initialize VM instance
    vm = QCPUMachine.from_config(cfg)

    # print current system configuration
    log.info("Address space configuration is as follows:")
    for start, end, ip in vm.addr_space.spans:
        log.info(f"{start:X}..{end:X}: {ip.__class__.__name__}")

    # load the program
    log.info(f"Reading startup code from {args.bin}...")
    with open(args.bin, "rb") as f:
        startup_code = f.read()

    vm.load_from_binary(startup_code)

    # begin
    log.info(f"Running...")

    if args.debug:
        dbg = QCPUDebugger(vm)

        while True:
            dbg.debug_step()
    else:
        while True:
            vm.step()
