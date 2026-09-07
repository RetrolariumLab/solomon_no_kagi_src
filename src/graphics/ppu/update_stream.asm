; NMI-side interpreter for compact PPU update streams

.segment "PRG_PPU_UPDATE_STREAM"

PpuCtrlIncrement32 = $04
PpuCtrlIncrement1Mask = $FB
PpuUpdateLiteralCarryMarker = $02
PaletteAddressHigh = $3F

ExecutePpuUpdateStream:
    DEY
    LDA (PpuUpdateStreamPointer),Y

DecodeNextPpuUpdateCommand:
    LDX a:PPU_STATUS
    STA a:PPU_ADDR
    INY
    LDA (PpuUpdateStreamPointer),Y
    STA a:PPU_ADDR
    INY
    LDA (PpuUpdateStreamPointer),Y
    INY
    ASL A
    TAX
    LDA PpuCtrlShadow
    ORA #PpuCtrlIncrement32
    BCS SelectPpuUpdateAddressIncrement
    AND #PpuCtrlIncrement1Mask

SelectPpuUpdateAddressIncrement:
    STA a:PPU_CTRL
    TXA
    ASL A
    BCC DecodePpuUpdateLength
    ORA #PpuUpdateLiteralCarryMarker

DecodePpuUpdateLength:
    LSR A
    LSR A
    TAX
    INX

WriteNextPpuUpdateByte:
    LDA (PpuUpdateStreamPointer),Y
    STA a:PPU_DATA
    BCC AdvancePpuUpdateWrite
    INY

AdvancePpuUpdateWrite:
    DEX
    BNE WriteNextPpuUpdateByte
    BCS CheckNextPpuUpdateCommand
    INY

CheckNextPpuUpdateCommand:
    LDA (PpuUpdateStreamPointer),Y
    BNE DecodeNextPpuUpdateCommand

FinishPpuUpdateStream:
    LDA #PaletteAddressHigh
    STA a:PPU_ADDR
    LDA #$00
    STA a:PPU_ADDR
    STA a:PPU_ADDR
    STA a:PPU_ADDR
    STA PpuUpdateStreamPointer + 1

RestorePpuStateAfterUpdate:
    LDX a:PPU_STATUS
    LDA PpuScrollX
    STA a:PPU_SCROLL
    LDA PpuScrollY
    STA a:PPU_SCROLL
    LDA PpuCtrlShadow
    STA a:PPU_CTRL
    RTS
