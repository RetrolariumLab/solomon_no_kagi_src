; Scale the current sine magnitude by the transition orbit radius

.segment "PRG_TRANSITION_ORBIT_SCALE"

ScaleTransitionOrbitOffset:
    LDA CoordinateY
    STA TempPointer00 + 1
    LDX #$08
    LDA #$00

MultiplyTransitionOrbitBytes:
    ROR TempPointer00 + 1
    BCC ShiftTransitionOrbitProduct
    CLC
    ADC TempPointer00

ShiftTransitionOrbitProduct:
    ROR A
    DEX
    BNE MultiplyTransitionOrbitBytes
    ROL A
    STA TempPointer00
    RTS
