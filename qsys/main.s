.text @START_VECTOR
    _start:     ld sc, $stack

                ld r0, 0x48
                jal textmode_putc

                ld r0, 0x65
                jal textmode_putc

                ld r0, 0x6c
                jal textmode_putc
                
                ld r0, 0x6c
                jal textmode_putc

                ld r0, 0x6f
                jal textmode_putc

                ld r0, 0x2c
                jal textmode_putc

                ld r0, 0x20
                jal textmode_putc

                ld r0, 0x77
                jal textmode_putc

                ld r0, 0x6f
                jal textmode_putc

                ld r0, 0x72
                jal textmode_putc

                ld r0, 0x6c
                jal textmode_putc

                ld r0, 0x64
                jal textmode_putc

                ld r0, 0x21
                jal textmode_putc

                ;jal simio_trap_exit

    endloop:    nop
                jmp endloop

; forward declaration of LLR runtime for linking purposes
.text_llr

.data_llr

.bss_llr

.bss
    stack:      word 0
