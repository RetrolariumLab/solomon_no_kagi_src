; Repeated direct writes to PPU_DATA

.segment "PRG_PPU_DATA_WRITERS"

RepeatedPpuPatternSize = $04

WriteRepeatedFourBytePpuPattern:
    LDY #RepeatedPpuPatternSize - 1

WriteNextPpuPatternByte:
    LDA (TempPointer00),Y
    STA a:PPU_DATA
    DEY
    BPL WriteNextPpuPatternByte
    DEX
    BNE WriteRepeatedFourBytePpuPattern
    RTS

WriteRepeatedPpuByte:
    STY a:PPU_DATA
    DEX
    BNE WriteRepeatedPpuByte
    RTS
