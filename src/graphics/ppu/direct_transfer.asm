; Enter and leave the rendering-disabled state used by direct PPU transfers

.segment "PRG_DIRECT_PPU_TRANSFER"

PpuMaskRenderingEnableBits = $18
PpuMaskRenderingDisableMask = $E7
PpuCtrlNmiEnableBit = $80
PpuCtrlDirectTransferMask = $7B

EndDirectPpuTransfer:
    LDA #PpuMaskRenderingEnableBits
    ORA PpuMaskShadow
    STA PpuMaskShadow
    LDA PpuCtrlShadow
    ORA #PpuCtrlNmiEnableBit
    STA PpuCtrlShadow
    STA a:PPU_CTRL
    RTS

BeginDirectPpuTransfer:
    LDX #PpuUpdateStreamPointer + 1
    LDA #$FF
    JSR WaitForMaskedBitsClear
    LDA PpuCtrlShadow
    AND #PpuCtrlDirectTransferMask
    STA PpuCtrlShadow
    STA a:PPU_CTRL
    LDA #PpuMaskRenderingDisableMask
    AND PpuMaskShadow
    STA a:PPU_MASK
    RTS
