; Initialize and animate fifteen objects around a changing center and radius

.segment "PRG_TRANSITION_OBJECT_ORBIT"

TransitionOrbitObjectCount = $0F
TransitionOrbitFrameLimit = $40
TransitionOrbitStateBytes = $19
TransitionObjectState = $04
TransitionObjectType = $05
TransitionPreviousFrame = $07
TransitionAngleStep = $80

RunTransitionObjectOrbit:
    JSR DeactivateAllNonDanaObjects
    LDX #TransitionOrbitObjectCount - 1

InitializeTransitionOrbitObject:
    LDA NonDanaObjectPointerLowTable,X
    STA TempPointer00
    LDA NonDanaObjectPointerHighTable,X
    STA TempPointer00 + 1
    LDA #$C0
    STA TransitionObjectState
    LDA #$1C
    STA TransitionObjectType
    LDA #$00
    JSR InitializeObjectStateHeader
    DEX
    BPL InitializeTransitionOrbitObject
    LDA #$00
    STA GameplayDelayCounter

WaitForTransitionOrbitFrame:
    JSR SwitchThreads
    LDA GameplayDelayCounter
    CMP #TransitionOrbitFrameLimit
    BCC UpdateTransitionOrbitFrame
    LDA #$00
    LDX #TransitionOrbitStateBytes - 1

ClearTransitionOrbitState:
    STA EnemyAiState,X
    DEX
    BPL ClearTransitionOrbitState
    STA TempPointer02
    JMP SetActiveNonDanaObjectState

UpdateTransitionOrbitFrame:
    CMP TransitionPreviousFrame
    BEQ WaitForTransitionOrbitFrame
    STA TransitionPreviousFrame
    JSR PositionTransitionOrbitObjects
    LDX #$01

AdvanceTransitionOrbitCenter:
    LDA EnemyAiState,X
    CLC
    ADC EnemyAiState + 4,X
    STA EnemyAiState + 4,X
    LDA EnemyAiState + 2,X
    ADC EnemyAiState + 6,X
    STA EnemyAiState + 6,X
    DEX
    BPL AdvanceTransitionOrbitCenter
    LDX #$01
    CLC

AdvanceTransitionOrbitRadius:
    LDA EnemyAiState + 8,X
    ADC EnemyAiState + 10,X
    STA EnemyAiState + 8,X
    DEX
    BPL AdvanceTransitionOrbitRadius
    CLC
    LDA EnemyAiState + 12
    ADC TransitionAngleStep
    AND #$3F
    STA EnemyAiState + 12
    BPL WaitForTransitionOrbitFrame

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
