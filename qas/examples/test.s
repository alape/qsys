.text
    _start:     ld r0, answer
                nop
                nop
                nop
                jmp r0, whatevs
                nop
                data "Nothing to see here!"
                nop

    whatevs:    ld r1, answer
                ld r2, nice
                add r3, r1, r1
                st r3, output

.data @0x100
    answer:     data 42
    nice:       data 0x45
    string:     data "Hello, world!"

.bss @0x200
    output:     data 9999
