# QSys LLR
A collection of Low-Level Routines for QSys and other low-level QCpu uses.

## Calling convention
* R0..R6 are reserved for arguments and may be overwritten by routines;
* R7 is reserved for return value.

## Modules
* `irq.s`: interrupt-related functionality (mostly interrupt handlers);
* `simio.s`: SIMIO-related routines: character IO, trap exit.
