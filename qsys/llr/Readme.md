# QSys LLR
A collection of Low-Level Routines for QSys and other low-level QCpu uses.

## Calling convention
* R0..R6 are reserved for arguments and scratch: they are caller-saved and may be overwritten by routines;
* R7 is reserved for return value (also caller-saved);
* R8..R9 are callee-saved: a routine that uses them must preserve the caller's values (`psh` on entry, `pop`
  before `ret`).

## Modules
* `irq.s`: interrupt-related functionality (mostly interrupt handlers);
* `simio.s`: SIMIO-related routines: character IO, trap exit.
