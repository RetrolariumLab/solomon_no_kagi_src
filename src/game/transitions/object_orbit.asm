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
