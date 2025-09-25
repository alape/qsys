; VGI framebuffer-related routines.

#define VGI_HEIGHT 640
#define VGI_WIDTH  480

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
            add r3, r3, VGI_HEIGHT      ; calculate Y offset: addr = addr + VGI_HEIGHT * X
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
            add r5, r5, VGI_WIDTH       ; calculate Y offset: addr = addr + VGI_HEIGHT * X
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
        add r5, r5, VGI_HEIGHT          ; advance to the next line's starting position
        sub r5, r5, r2                  ;   (screen width minus bitmap width)
        ld r6, 0                        ; reset the X counter
        bgt r7, r3, 0                   ; repeat if there are still lines left to output

        ret
