; Draw the two-column and two-row frame around the 30x24 room tile area

.segment "PRG_ROOM_NAMETABLE_FRAME"

PpuCtrlAddressIncrement32Bit = $04
RoomFramePpuAddressHigh = $20
RoomFrameOuterColumnAddressLow = $9F
RoomFrameInnerColumnAddressLow = $9E
RoomFrameBottomRowsAddressHigh = $23
RoomFrameBottomRowsAddressLow = $80
RoomFrameAttributesAddressHigh = $23
RoomFrameAttributesAddressLow = $C0
RoomFrameColumnPatternCount = $06
RoomFrameRowPatternCount = $08
RoomFrameAttributeByteCount = $40
RoomFrameOuterTailTile0 = $A4

DrawRoomNametableFrame:
    LDA PpuUpdateStreamPointer + 1
    BNE DrawRoomNametableFrame
    JSR BeginDirectPpuTransfer
    LDA #RoomFramePpuAddressHigh
    LDX #RoomFrameOuterColumnAddressLow
    JSR SetPpuAddressAX
    LDA PpuCtrlShadow
    ORA #PpuCtrlAddressIncrement32Bit
    STA PpuCtrlShadow
    STA a:PPU_CTRL
    LDA #<RepeatedPpuPattern0
    STA TempPointer00
    LDA #>RepeatedPpuPattern0
    STA TempPointer00 + 1
    LDX #RoomFrameColumnPatternCount
    JSR WriteRepeatedFourBytePpuPattern
    LDX #RoomFrameOuterTailTile0
    STX a:PPU_DATA
    DEX
    STX a:PPU_DATA
    LDX a:PPU_STATUS
    LDA #RoomFramePpuAddressHigh
    LDX #RoomFrameInnerColumnAddressLow
    JSR SetPpuAddressAX
    LDA PpuCtrlShadow
    STA a:PPU_CTRL
    LDA #<RepeatedPpuPattern1
    STA TempPointer00
    LDA #>RepeatedPpuPattern1
    STA TempPointer00 + 1
    LDX #RoomFrameColumnPatternCount
    JSR WriteRepeatedFourBytePpuPattern
    LDX a:PPU_STATUS
    LDA #RoomFrameBottomRowsAddressHigh
    LDX #RoomFrameBottomRowsAddressLow
    JSR SetPpuAddressAX
    LDA PpuCtrlShadow
    AND #<~PpuCtrlAddressIncrement32Bit
    STA PpuCtrlShadow
    STA a:PPU_CTRL
    LDA #<RepeatedPpuPattern2
    STA TempPointer00
    LDA #>RepeatedPpuPattern2
    STA TempPointer00 + 1
    LDX #RoomFrameRowPatternCount
    JSR WriteRepeatedFourBytePpuPattern
    LDA #<RepeatedPpuPattern3
    STA TempPointer00
    LDA #>RepeatedPpuPattern3
    STA TempPointer00 + 1
    LDX #RoomFrameRowPatternCount
    JSR WriteRepeatedFourBytePpuPattern
    LDX a:PPU_STATUS
    LDA #RoomFrameAttributesAddressHigh
    LDX #RoomFrameAttributesAddressLow
    JSR SetPpuAddressAX
    LDA PpuCtrlShadow
    STA a:PPU_CTRL
    LDX #RoomFrameAttributeByteCount
    LDY #$00
    JSR WriteRepeatedPpuByte
    LDX a:PPU_STATUS
    JMP EndDirectPpuTransfer
