; Reflect a six-bit phase into the 32-entry transition sine table

.segment "PRG_QUARTER_SINE"

LoadQuarterSineMagnitude:
    AND #$3F
    TAX
    AND #$20
    BEQ LoadQuarterSineValue
    TXA
    EOR #$3F
    TAX

LoadQuarterSineValue:
    LDA QuarterSineTable,X
    STA TempPointer00
    RTS
