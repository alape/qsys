.text @START_VECTOR
    _start:     ld sc, $stack

                ld r2, 0xFFFF       ; set r2 (pixel colour) to 0xFFFFFF (100% white)
                lsh r2, 16
                or r2, r2, 0xFF00

                ld r0, 50
                ld r1, 50
                jal vgi_putpixel

                ld r0, 150
                jal vgi_putpixel

                ld r1, 150
                jal vgi_putpixel

                ld r0, 50
                jal vgi_putpixel

                ld r0, 0
                ld r1, 0
                ld r2, 64
                ld r3, 64
                ld r4, $logo
                jal vgi_blit

                ;jal simio_trap_exit
                jmp endloop

    endloop:    nop
                jmp endloop

.data
    logo:       data file:logo.gray

.bss
    stack:      word 0

; forward declaration of LLR runtime for linking purposes
.text_llr @0x52000
