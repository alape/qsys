; Textmode routines that expand the VGI module functionality by allowing routines to print text to VGI framebuffer
;  using a common bitfont.

#define FONT_WIDTH 8
#define FONT_HEIGHT 16
#define FONT_CHAR_SIZE 0x80

#define DISPLAY_WIDTH 80
#define DISPLAY_HEIGHT 30

.text_llr
    textmode_newline:
        ; Moves current position to the new line (wraps around if needed). This function takes no arguments.

        ; Set _txt_pos_x to zero
        st zeroes, _txt_pos_x
        
        ; If _txt_pos_y = DISPLAY_HEIGHT, set _txt_pos_y to zero
        ld r6, _txt_pos_y
        ld r7, $_tnewline
        bne r7, r6, DISPLAY_HEIGHT
        st zeroes, _txt_pos_y
        ret

        ; If not, increment _txt_pos_y
        _tnewline:
            add r6, r6, 1
            st r6, _txt_pos_y
            ret

    textmode_putc:
        ; Output a single ASCII character to the current position.
        ;   R0: character
        ld r1, 0 

        ; skip adding newline if the end of current line is not yet reached:
        ld r2, $_tputc_premulx
        ld r3, _txt_pos_x
        blt r2, r3, DISPLAY_WIDTH
        jal textmode_newline

        ; skip _tputc_mulx() if current X is zero
        _tputc_premulx:
            ld r5, $_tputc_endmulx
            beq r5, r3, 0
        
        _tputc_mulx:
            ; framebuffer X (r1) = _txt_pos_x * FONT_WIDTH
            add r1, r1, FONT_WIDTH
            sub r3, r3, 1
            bgt r2, r3, 0
        
        _tputc_endmulx:
            ld r4, 0
            ld r2, $_tputc_muly
            ld r3, _txt_pos_y

            ; skip _tputc_muly() if current Y is zero
            ld r5, $_tputc_endmuly
            beq r5, r3, 0

        _tputc_muly:
            ; framebuffer Y (r4) = _txt_pos_y * FONT_HEIGHT
            add r4, r4, FONT_HEIGHT
            sub r3, r3, 1
            bgt r2, r3, 0

        _tputc_endmuly:
            sub r0, r0, 0x20
            ld r3, $bitfont

            ; skip _tputc_bfoffset if char = 0x20
            ld r2, $_tputc_endbfoffset
            beq r2, r0, 0

            ld r2, $_tputc_bfoffset

        _tputc_bfoffset:
            ; bitfont offset (r3) = $bitfont + ((char - 0x20) * FONT_CHAR_SIZE)
            add r3, r3, FONT_CHAR_SIZE
            sub r0, r0, 1
            ;jal simio_trap_exit
            bgt r2, r0, 0

        _tputc_endbfoffset:
            ; store arguments for vgi_blit() call
            add r0, r1, 0           ; r0: framebuffer X
            add r1, r4, 0           ; r1: framebuffer Y
            add r4, r3, 0           ; r4: bitmap offset
            ld r2, FONT_WIDTH       ; r2: bitmap width
            ld r3, FONT_HEIGHT      ; r3: bitmap height

            ; call vgi_blit()
            jal vgi_blit

            ; increment current X position
            ld r7, _txt_pos_x
            add r7, r7, 1
            st r7, _txt_pos_x

            ; that's all, folks!
            ret

    textmode_puts:
        ; Prints a string via SIMIO. 
        ;   R0: string pointer, 
        ;   R1: string length (in words)

        ld r2, $_tputsloop                   ; _putsloop() vector
        ld r3, r0                            ; current word
        ld r4, 0                             ; word counter

        _tputsloop:
            jal _tputw               ; output current word
            add r4, r4, 1            ; increment word counter and word pointer
            add r0, r0, 1

            ld r3, r0                ; load next word into R3
                    
            blt r2, r4, r1           ; repeat if word counter is less than message length...
            ret                      ; ...otherwise, exit textmode_puts()


        _tputw:      
            ld r5, 0                 ; byte counter (4 bytes per word)
            ld r6, $_tputwloop        ; loop vector

        _tputwloop:
            psh r0
            psh r1
            psh r2
            psh r3
            psh r4
            psh r5
            psh r6

            xor r0, r0, r0
            add r0, r3, 0
            rsh r0, 24
            ;lsh r0, 24
            jal textmode_putc

            pop r6
            pop r5
            pop r4
            pop r3
            pop r2
            pop r1
            pop r0

            lsh r3, 8                ; shift current word left by one byte
            add r5, r5, 1            ; increment byte counter

            blt r6, r5, 4            ; repeat loop if byte counter < 4 to output all bytes in current word

            ret                      ; exit _tputw()

        

.data_llr
    bitfont:        data file:build/bitfont.gray

.bss_llr
    _txt_pos_x:     word 0
    _txt_pos_y:     word 0
