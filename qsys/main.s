.text @START_VECTOR
    _start:     ld sc, $stack

                ld r0, $message_text
                ld r1, message_len
                jal textmode_puts

    endloop:    nop
                jmp endloop

.data
    message_text: data "Hello, world!"
    message_len:  word 4

; forward declaration of LLR runtime for linking purposes
.text_llr

.data_llr

.bss_llr

.bss @0x53100
    stack:      word 0
