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
        add r3, r0, VGI_OFFSET + 3      ; addr = X + (VGI framebuffer offset)

        ld r4, 0
        ld r5, $_ycalc
        ld r6, $_wrpixel

        beq r6, r1, 0                   ; if Y = 0, skip _ycalc()

        _ycalc:
            add r3, r3, 0x280           ; addr = addr + 640 * X
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

        ; calculate linear coordinates of bitmap's anchor (i.e. framebuffer offset):
        add r5, r0, VGI_OFFSET + 3      ; addr = X + (VGI framebuffer offset)

        ld r6, 0                        ; X counter
        ld r7, $_xlineblit              ; util function vector

        _xlineblit:                     ; output a single line of bitmap to VGI framebuffer
            st r5, r4
            add r6, r6, 1
            add r5, r5, 1
            add r4, r4, 1

            blt r7, r6, r2

        sub r3, r3, 1                   ; decrement line counter in place
        add r5, r5, VGI_WIDTH           ; advance to the next line's starting position
        bgt r7, r3, 0                   ; repeat if there are still lines left to output

        ret
