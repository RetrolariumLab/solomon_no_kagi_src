; Test a point-like interaction coordinate against one active object record

.segment "PRG_COORDINATE_OBJECT_OVERLAP"

CheckCoordinateOverlapWithObject:
    SEC
    LDY #$00
    LDA (OverlapObjectPointer),Y
    BPL FinishCoordinateObjectOverlapCheck
    LDY #ObjectXPositionOffset
    LDA MapInteractionX
    SEC
    SBC (OverlapObjectPointer),Y
    ADC #$09
    CMP #$15
    BCS FinishCoordinateObjectOverlapCheck
    LDY #ObjectYPositionOffset
    LDA MapInteractionY
    SBC (OverlapObjectPointer),Y
    ADC #$0D
    CMP #$1D

FinishCoordinateObjectOverlapCheck:
    RTS
