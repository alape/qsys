; VGI framebuffer-related routines.

#define VGI_WIDTH  640
#define VGI_HEIGHT 480

.text_llr
    vgi_putpixel:   
        ; Update a pixel by specified coordinates in the VGI framebuffer:
        ;   R0: X coordinate,
        ;   R1: Y coordinate,
        ;   R2: colour (24bpp big-endian BGR)
        
        ; calculate pixel's linear coordinates (i.e. framebuffer offset):
        add r3, r0, VGI_OFFSET + 3      ; calculate X offset: addr = X + (VGI framebuffer offset)

        ld r4, 0
        ld r5, $_ycalc
        ld r6, $_wrpixel

        beq r6, r1, 0                   ; if Y = 0, skip _ycalc()

        _ycalc:
            add r3, r3, VGI_WIDTH       ; calculate Y offset: addr = addr + VGI_WIDTH * Y
            add r4, r4, 1
            blt r5, r4, r1

        _wrpixel:
            st r2, r3                   ; write pixel to the framebuffer

        ret 

    vgi_blit:
        ; Place (blit) a bitmap by specified coordinates in the VGI framebuffer:
        ;   R0: X coordinate,
        ;   R1: Y coordinate,
        ;   R2: Bitmap width,
        ;   R3: Bitmap height,
        ;   R4: Bitmap offset
        ;
        ; Note that this routine consumes the register values (by modifying them in-place).

        ; calculate linear coordinates of bitmap's anchor (i.e. framebuffer offset):
        add r5, r0, VGI_OFFSET + 3      ; calculate X offset: addr = X + (VGI framebuffer offset)
        
        ld r6, 0                        ; Y counter
        ld r7, $_xlineblit              ; util function vectors
        ld r0, $_ycalcblit                  

        beq r7, r1, 0                   ; if Y = 0, skip _ycalc()

        _ycalcblit:
            add r5, r5, VGI_WIDTH       ; calculate Y offset: addr = addr + VGI_WIDTH * Y
            add r6, r6, 1
            blt r0, r6, r1

        ld r6, 0                        ; it's X counter now

        _xlineblit:                     ; output a single line of bitmap to VGI framebuffer
            ld r0, r4                   ;   (copy words from bitmap to framebuffer until X counter reaches
            st r0, r5                   ;    the width of bitmap)
            add r6, r6, 1
            add r5, r5, 1
            add r4, r4, 1

            blt r7, r6, r2

        sub r3, r3, 1                   ; decrement line counter in place
        add r5, r5, VGI_WIDTH           ; advance to the next line's starting position
        sub r5, r5, r2                  ;   (screen width minus bitmap width)
        ld r6, 0                        ; reset the X counter
        bgt r7, r3, 0                   ; repeat if there are still lines left to output

        ret

    vgi_blit_1bpp:
        ; Place (blit) a 1bpp black & white bitmap by specified coordinates in the VGI framebuffer:
        ;   R0: X coordinate,
        ;   R1: Y coordinate,
        ;   R2: Bitmap width (non-zero),
        ;   R3: Bitmap height (non-zero),
        ;   R4: Bitmap offset,
        ;   R5: Palette offset: two words, colour of zero bits (background) followed by colour of set bits (foreground)
        ;
        ; Note that this routine consumes the register values (by modifying them in-place) and also overwrites R6..R9.

        ; calculate linear coordinates of bitmap's anchor: addr = X + (VGI framebuffer offset) + Y * VGI_WIDTH
        add r0, r0, VGI_OFFSET + 3
        add r7, r1, 0                   ; Y * VGI_WIDTH is calculated with shifts, since 640 = 5 << 7:
        lsh r7, 2                       ;   r7 = Y * 4
        add r7, r7, r1                  ;   r7 = Y * 5
        lsh r7, 7                       ;   r7 = Y * 640
        add r0, r0, r7

        add r1, r2, 0                   ; r1: pixels left in the current line
        ld r6, 0                        ; r6: bits left in the current bitmap word (zero forces loading the first one)
        ld r8, $_blit1bpp_pixel         ; r8: loop vector (both loops go back to the same place)

        _blit1bpp_pixel:
            ld r9, $_blit1bpp_draw      ; skip loading the next bitmap word while current one still has bits left
            bne r9, r6, 0

            ld r7, r4                   ; r7: current bitmap word (shifted left as bits are consumed)
            add r4, r4, 1
            ld r6, 32

        _blit1bpp_draw:
            add r9, r7, 0               ; get the current bit (MSB of the current word)...
            rsh r9, 31
            add r9, r9, r5              ; ...use it as an index into palette...
            ld r9, r9
            st r9, r0                   ; ...and write the resulting colour to the framebuffer

            lsh r7, 1                   ; advance to the next bit
            sub r6, r6, 1
            add r0, r0, 1               ; advance to the next pixel
            sub r1, r1, 1
            bne r8, r1, 0               ; repeat until the line is finished

        add r0, r0, VGI_WIDTH           ; advance to the next line's starting position
        sub r0, r0, r2                  ;   (screen width minus bitmap width)
        add r1, r2, 0                   ; reset the X counter
        sub r3, r3, 1                   ; decrement line counter in place
        bne r8, r3, 0                   ; repeat if there are still lines left to output

        ret
