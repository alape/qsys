.text
    _start: 
        ld r0, $hello_text
        ld r1, hello_len
        jal simio_puts

        ld r0, $prompt_text
        ld r1, prompt_len
        jal simio_puts

        ld r3, $end
        loop:
            jal simio_getc

            add r0, r7, 0
            jal simio_putc

            beq r3, r7, 0x2E

            jmp loop

        end:
            ld r0, 0xa
            jal simio_putc

            jal simio_trap_exit

.data
    hello_text:     data "Hello, world!  " 0xA
    hello_len:      word 4
    prompt_text:    data "Echoing characters; enter '.' to quit  " 0xA
    prompt_len:     word 10
