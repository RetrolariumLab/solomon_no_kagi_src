; Align an object's Y coordinate to a tile surface

.segment "PRG_OBJECT_Y_CLAMP"

ObjectClampYCoordinateToSurface:
    LDY #ObjectYPositionOffset
    LDA (TempPointer08),Y
    TAX
    CLC
    ADC #$10
    AND #$0F
    STA CoordinateClampRemainder
    TXA
    SEC
    SBC CoordinateClampRemainder
    STA (TempPointer08),Y
    LDY #ObjectYMotionOffset
    LDA (TempPointer08),Y
    ROL A
    LDA #$00
    ROR A
    STA (TempPointer08),Y
    RTS
