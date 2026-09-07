; Reset the PPU address latch and write the address supplied in A:X

.segment "PRG_SET_PPU_ADDRESS"

SetPpuAddressAX:
    PHA
    LDA a:PPU_STATUS
    PLA
    STA a:PPU_ADDR
    STX a:PPU_ADDR
    RTS
