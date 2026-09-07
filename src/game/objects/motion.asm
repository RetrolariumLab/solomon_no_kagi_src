; Signed fixed-point Y/X motion integration for one object record

.segment "PRG_OBJECT_MOTION"

ObjectMotionScratch = $000A

UpdateObjectMotionAndCollision:
    LDY #ObjectYMotionOffset
    LDA (TempPointer08),Y
    STA ObjectMotionScratch
    ASL A
    BCC IntegrateObjectYMotion
    TAX
    CLC
    ADC #$06
    BVC IntegrateObjectYMotion
    TXA

IntegrateObjectYMotion:
    TAX
    ROL ObjectMotionScratch
    ROR A
    STA (TempPointer08),Y
    TXA
    LDX #$00
    ASL A
    BCC SignExtendObjectYDelta
    DEX

SignExtendObjectYDelta:
    STX ObjectMotionScratch
    ASL A
    ROL ObjectMotionScratch
    INY
    CLC
    ADC (TempPointer08),Y
    STA (TempPointer08),Y
    INY
    LDA ObjectMotionScratch
    ADC (TempPointer08),Y
    STA (TempPointer08),Y

IntegrateObjectXMotion:
    INY
    LDA (TempPointer08),Y
    ASL A
    ASL A
    LDX #$00
    BCC SignExtendObjectXDelta
    DEX

SignExtendObjectXDelta:
    STX ObjectMotionScratch
    ROL A
    ROL ObjectMotionScratch
    CLC
    INY
    ADC (TempPointer08),Y
    STA (TempPointer08),Y
    INY
    LDA ObjectMotionScratch
    ADC (TempPointer08),Y
    STA (TempPointer08),Y
