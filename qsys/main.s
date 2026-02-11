.text @START_VECTOR
    _start:     ld sc, $stack

                ld r0, $message_text
                ld r1, message_len
                jal textmode_puts

    endloop:    nop
                jmp endloop

.data
    message_text: data "Hello, world! This is a rather long message, so it will take some time to be displayed... But we have all the time in the world, don't we? So relax and let it run its course... grab some coffee, read a nice book and come back some time later. It will wait for you."
    message_len:  word 66

; forward declaration of LLR runtime for linking purposes
.text_llr

.data_llr

.bss_llr

.bss @0x53100
    stack:      word 0
