; Position fifteen transition objects around the current orbit center

.segment "PRG_TRANSITION_ORBIT_POSITION"

PositionTransitionOrbitObjects:
    LDX #TransitionOrbitObjectCount - 1
    STX SpawnSlotIndex
    LDA EnemyAiState + 8
    STA CoordinateY
    LDA EnemyAiState + 12
    STA CoordinateX

PositionNextTransitionOrbitObject:
    LDA CoordinateX
    JSR LoadQuarterSineMagnitude
    JSR ScaleTransitionOrbitOffset
    STA TempPointer02
    LDA CoordinateX
    AND #$3F
    STA TempPointer00
    LDA #$20
    SEC
    SBC TempPointer00
    JSR LoadQuarterSineMagnitude
    JSR ScaleTransitionOrbitOffset
    STA $03
    LDX SpawnSlotIndex
    LDA NonDanaObjectPointerLowTable,X
    STA TempPointer00
    LDA NonDanaObjectPointerHighTable,X
    STA TempPointer00 + 1
    LDA #$40
    AND CoordinateX
    BEQ PositionTransitionOrbitY
    LDA #$FF
    EOR TempPointer02
    STA TempPointer02

PositionTransitionOrbitY:
    LDA TempPointer02
    CLC
    ADC EnemyAiState + 6
    LDY #ObjectYPositionOffset
    STA (TempPointer00),Y
    LDA #$20
    CLC
    ADC CoordinateX
    AND #$40
    BEQ PositionTransitionOrbitX
    LDA #$FF
    EOR $03
    STA $03

PositionTransitionOrbitX:
    LDA $03
    CLC
    ADC EnemyAiState + 7
    LDY #ObjectXPositionOffset
    STA (TempPointer00),Y
    LDA #$08
    ADC CoordinateX
    STA CoordinateX
    DEC SpawnSlotIndex
    BPL PositionNextTransitionOrbitObject
    RTS
