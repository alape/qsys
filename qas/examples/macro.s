#define MESSAGE_TEXT "Hello, world!" 0xA
#define MESSAGE_LENGTH 4

.text
    _start:     ld sc, $stack           ; initialize stack

                ld r0, 0                ; word counter
                ld r1, $message_text    ; word pointer
                ld r2, $loop            ; loop() vector
                ld r3, r1               ; current word
                ld r4, message_len      ; message length (in words)


    loop:       jal putw                ; output current word
                add r0, r0, 1           ; increment word counter and word pointer
                add r1, r1, 1

                ld r3, r1               ; load next word into R3

                blt r2, r0, r4          ; repeat if word counter is less than message length...
                jmp end                 ; ...otherwise, go into infinite loop


    putw:       ld r5, 0                ; byte counter (4 bytes per word)
                ld r6, $putwloop        ; loop vector
    putwloop:   st r3, @0x201            ; output current word via SIMIO (its first byte will be printed)

                lsh r3, 8               ; shift current word left by one byte
                add r5, r5, 1           ; increment byte counter

                blt r6, r5, 4           ; repeat loop if byte counter < 4 to output all bytes in current word

                ret                     ; exit procedure


    end:        nop                     ; infinite loop
                jmp end

#include <macro_include.s>

.bss
    stack:           word 0
