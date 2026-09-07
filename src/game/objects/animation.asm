; Advance one object's packed animation phase and three-byte sprite record

.segment "PRG_OBJECT_ANIMATION"

ObjectAnimationDataPointer = $000A
ObjectAnimationFrameByte = $000C

AdvanceObjectAnimation:
    LDY #ObjectAnimationCounterOffset
    LDA (TempPointer08),Y
    CLC
    SBC #$00
    STA (TempPointer08),Y
    BPL FinishObjectAnimationUpdate
    INY
    LDA (TempPointer08),Y
    DEY
    STA (TempPointer08),Y
    LDY #ObjectAnimationPhaseOffset
    LDA (TempPointer08),Y
    CLC
    ADC #$F0
    STA (TempPointer08),Y
    BCS SelectObjectAnimationFrame

NormalizeObjectAnimationPhase:
    AND #$0F
    STA ObjectAnimationDataPointer
    ASL A
    ASL A
    ASL A
    ASL A
    ORA ObjectAnimationDataPointer
    STA (TempPointer08),Y

SelectObjectAnimationFrame:
    LSR A
    LSR A
    LSR A
    STA ObjectAnimationDataPointer
    LSR A
    CLC
    ADC ObjectAnimationDataPointer
    TAX
    INY
    LDA (TempPointer08),Y
    STA ObjectAnimationDataPointer
    INY
    LDA (TempPointer08),Y
    STA ObjectAnimationDataPointer + 1
    TXA
    TAY
    LDA (ObjectAnimationDataPointer),Y
    INY
    STA ObjectAnimationFrameByte
    LDA (ObjectAnimationDataPointer),Y
    INY
    TAX
    LDA (ObjectAnimationDataPointer),Y
    LDY #ObjectSpriteFlagsOffset
    STA (TempPointer08),Y
    DEY
    TXA
    STA (TempPointer08),Y
    DEY
    LDA ObjectAnimationFrameByte
    STA (TempPointer08),Y

FinishObjectAnimationUpdate:
    RTS
