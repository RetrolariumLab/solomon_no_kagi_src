; Align object Y to the $D inset of a 16-pixel cell

.segment "PRG_OBJECT_Y_THIRTEEN_CLAMP"

ObjectClampYCoordinateToThirteenInset:
    LDY #ObjectYPositionOffset
    LDA (TempPointer08),Y
    CLC
    ADC #$03
    ORA #$F0
    EOR #$FF
    TAX
    INX
    TXA
    ADC (TempPointer08),Y
    STA (TempPointer08),Y
    DEY
    LDA #$00
    STA (TempPointer08),Y
    DEY
    LDA (TempPointer08),Y
    ASL A
    LDA #$00
    ROR A
    STA (TempPointer08),Y
    RTS
