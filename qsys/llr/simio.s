; Collection of SIMIO-related routines (character IO, trap exit).

.text_llr
    simio_puts:
        ; Prints a string via SIMIO. R0 is string pointer, R1 is string length (in words).

        ld r2, $_putsloop        ; _putsloop() vector
        ld r3, r0               ; current word
        ld r4, 0                ; word counter

        _putsloop:  jal _putw               ; output current word
                    add r4, r4, 1           ; increment word counter and word pointer
                    add r0, r0, 1

                    ld r3, r0               ; load next word into R3
                    
                    blt r2, r4, r1          ; repeat if word counter is less than message length...
                    ret                     ; ...otherwise, exit simio_puts()


        _putw:      ld r5, 0                ; byte counter (4 bytes per word)
                    ld r6, $_putwloop       ; loop vector
        _putwloop:  st r3, @0x201           ; output current word via SIMIO (its first byte will be printed)

                    lsh r3, 8               ; shift current word left by one byte
                    add r5, r5, 1           ; increment byte counter

                    blt r6, r5, 4           ; repeat loop if byte counter < 4 to output all bytes in current word

                    ret                     ; exit _putw()

    simio_putc:
        ; Prints a single character (from R0) via SIMIO.
        lsh r0, 24                          ; shift char to MSB
        st r0, @0x201                       ; output via SIMIO

        ret                                 ; exit simio_putc()
    
    simio_getc:
        ; Fetches a character via SIMIO and returns it via R7 LSB; takes no arguments.
        ; Blocks until a symbol is available.
        ld r0, $_getcloop

        _getcloop:  ld r1, @0x202            ; wait until SIMI (0x202) is not zero
                    beq r0, r1, 0

        add r7, r1, 0                        ; move char to R7

        ret                                  ; exit simio_getc()

    simio_trap_exit:
        ; Terminates simulation via TRAP. Takes no arguments, never returns.
        ld r0, 1
        st r0, @0x203                         ; store 1 to TRAP

        ret                                   ; o.0 return in case we're not in simulation after all
