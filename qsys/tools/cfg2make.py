# Helper script that converts QSim config files into QSys Makefile includes

import argparse
import json
import sys


def cfg2make(cfg_string: str) -> str:
    """Reads QSim config as JSON from provided string and returns Makefile syntax-compliant list of QAS flags."""
    cfg = json.loads(cfg_string)
    macros = {}

    assert "addr_space" in cfg

    for ip in cfg["addr_space"]:
        assert "type" in ip
        assert "cfg" in ip
        assert "addr_offset" in ip["cfg"]

        macros[ip["type"] + "_OFFSET"] = hex(ip["cfg"]["addr_offset"])

    if "load_at" in cfg:
        macros["START_VECTOR"] = hex(cfg["load_at"])

    flags = [f"-D {macro_name}={macro_contents}" for macro_name, macro_contents in macros.items()]

    return ' '.join(flags)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("usage: cfg2make.py [PATH TO JSON CFG FILE]")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        print(cfg2make(f.read()))
