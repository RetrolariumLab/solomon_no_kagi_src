; Align an object's X coordinate against a wall on its right

.segment "PRG_OBJECT_X_RIGHT_CLAMP"

ObjectClampXCoordinateToRightSurface:
    LDY #ObjectXPositionOffset
    LDA (TempPointer08),Y
    TAX
    CLC
    ADC #$04
    AND #$0F
    STA CoordinateClampDelta
    TXA
    SEC
    SBC CoordinateClampDelta
    STA (TempPointer08),Y
    DEY
    LDA #$00
    STA (TempPointer08),Y
    DEY
    STA (TempPointer08),Y
    .byte $D0, $DD  ; BNE ClearObjectXMotion across linker segments
