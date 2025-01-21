.text
    _start:     ld r0, 0xAAAAAAAA
                ld r1, 0xBBBBBBBB
                sub r2, r1, r0
                jmp cont
                nop
                nop
                nop
                nop

    cont:       ld r3, 0x11111111
                add r4, r2, r3
                st r4, variable

.bss
    variable:   data 0
