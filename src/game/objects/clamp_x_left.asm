; Align an object's X coordinate against a wall on its left

.segment "PRG_OBJECT_X_LEFT_CLAMP"

ObjectClampXCoordinateToLeftSurface:
    LDY #ObjectXPositionOffset
    LDA (TempPointer08),Y
    TAX
    SEC
    SBC #$04
    ORA #$F0
    EOR #$FF
    STA CoordinateClampDelta
    INC CoordinateClampDelta
    TXA
    CLC
    ADC CoordinateClampDelta
    STA (TempPointer08),Y
    DEY
    LDA #$00
    STA (TempPointer08),Y
    DEY
    STA (TempPointer08),Y

ClearObjectXMotion:
    LDY #ObjectXMotionOffset
    LDA #$00
    STA (TempPointer08),Y
    RTS
