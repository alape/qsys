; Textmode routines that expand the VGI module functionality by allowing routines to print text to VGI framebuffer
;  using a common bitfont.

#define FONT_WIDTH 8
#define FONT_HEIGHT 16
; size of a single character bitmap in words (8x16 pixels at 1bpp = 128 bits = 4 words)
#define FONT_CHAR_SIZE 4

; sase-2 logarithms of the three font metrics above: all of them are powers of two, so multiplying by them is a
;  single shift rather than a loop of additions
#define FONT_WSHIFT 3
#define FONT_HSHIFT 4
#define FONT_CSHIFT 2

#define DISPLAY_WIDTH 80
#define DISPLAY_HEIGHT 30

.text_llr
    textmode_newline:
        ; Moves current position to the new line (wraps around if needed). This function takes no arguments.

        ; Set _txt_pos_x to zero
        ld r5, 0
        st r5, _txt_pos_x
        
        ; If _txt_pos_y is the last line (DISPLAY_HEIGHT - 1), set _txt_pos_y to zero
        ld r6, _txt_pos_y
        ld r7, $_tnewline
        bne r7, r6, DISPLAY_HEIGHT - 1
        st r5, _txt_pos_y
        ret

        ; If not, increment _txt_pos_y
        _tnewline:
            add r6, r6, 1
            st r6, _txt_pos_y
            ret

    textmode_putc:
        ; Output a single ASCII character to the current position.
        ;   R0: character

        ; wrap to the next line if the end of the current one has been reached
        ld r2, $_tputc_blit
        ld r3, _txt_pos_x
        blt r2, r3, DISPLAY_WIDTH
        jal textmode_newline
        ld r3, 0                        ; textmode_newline() has reset X, so the current cell is the leftmost one

        _tputc_blit:
            ; bitmap offset (r4) = $bitfont + (char - 0x20) * FONT_CHAR_SIZE
            sub r0, r0, 0x20
            lsh r0, FONT_CSHIFT
            ld r4, $bitfont
            add r4, r4, r0

            ; framebuffer X (r0) = _txt_pos_x * FONT_WIDTH
            lsh r3, FONT_WSHIFT
            add r0, r3, 0

            ; framebuffer Y (r1) = _txt_pos_y * FONT_HEIGHT
            ld r1, _txt_pos_y
            lsh r1, FONT_HSHIFT

            ld r2, FONT_WIDTH           ; r2: bitmap width
            ld r3, FONT_HEIGHT          ; r3: bitmap height
            ld r5, $_txt_palette        ; r5: palette offset

            ; call vgi_blit_1bpp()
            jal vgi_blit_1bpp

            ; increment current X position
            ld r7, _txt_pos_x
            add r7, r7, 1
            st r7, _txt_pos_x

            ; that's all, folks!
            ret

    textmode_puts:
        ; Prints a string to the VGI framebuffer.
        ;   R0: string pointer,
        ;   R1: string length (in words)

        psh r8                          ; R8 and R9 are callee-saved, so the caller's copies are to be preserved
        psh r9

        add r1, r1, r0                  ; the loop is bounded by a pointer, so no separate word counter is needed
        st r1, _txt_str_end
        add r9, r0, 0                   ; r9: pointer to the current word (survives textmode_putc)

        _tputsloop:
            ld r8, r9                   ; r8: current word, consumed byte by byte (survives textmode_putc as well)

            add r0, r8, 0
            rsh r0, 24
            jal textmode_putc

            lsh r8, 8
            add r0, r8, 0
            rsh r0, 24
            jal textmode_putc

            lsh r8, 8
            add r0, r8, 0
            rsh r0, 24
            jal textmode_putc

            lsh r8, 8
            add r0, r8, 0
            rsh r0, 24
            jal textmode_putc

            ; advance to the next word and repeat until the end of the string is reached
            add r9, r9, 1
            ld r8, _txt_str_end
            ld r7, $_tputsloop
            blt r7, r9, r8

        pop r9                          ; restore the caller's callee-saved registers and exit textmode_puts()
        pop r8
        ret


.data_llr
    bitfont:        data file:build/bitfont.gray
    _txt_palette:   word 0x00000000         ; background colour
                    word 0x00BFFF00         ; foreground colour

.bss_llr
    _txt_pos_x:     word 0
    _txt_pos_y:     word 0
    _txt_str_end:   word 0
