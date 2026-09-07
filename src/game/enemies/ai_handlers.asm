; Enemy AI dispatch tables and linked-slot behavior support

.segment "PRG_ENEMY_AI_HANDLERS"

DispatchEnemyAiHandler:
    LSR A
    LSR A
    JSR JumpWithParams

EnemyAiHandlerTable:
    .addr RunType00To03EnemyAi, RunType04To07EnemyAi, RunType08To0BEnemyAi, RunType0CTo0FEnemyAi
    .addr RunType10To13EnemyAi, RunType14To17EnemyAi, RunType18To1BEnemyAi, RunType1CTo37EnemyAi
    .addr RunType1CTo37EnemyAi, RunType1CTo37EnemyAi, RunType1CTo37EnemyAi, RunType1CTo37EnemyAi
    .addr RunType1CTo37EnemyAi, RunType1CTo37EnemyAi, RunType1CTo37EnemyAi, RunType50To5BEnemyAi
    .addr RunType50To5BEnemyAi, RunType50To5BEnemyAi, RunType48To53EnemyAi, RunType48To53EnemyAi
    .addr RunType48To53EnemyAi, RunType54To5BEnemyAi, RunType54To5BEnemyAi, RunType5CTo63EnemyAi
    .addr RunType5CTo63EnemyAi, RunType64To6BEnemyAi, RunType64To6BEnemyAi, RunType6CTo6FEnemyAi

EnemyAiHandlerCount = (* - EnemyAiHandlerTable) / 2
.assert EnemyAiHandlerCount = 28, error, "unexpected enemy AI handler count"

; Shared action dispatch and linked-slot helpers for the $50-$67 type families

.segment "PRG_LINKED_ENEMY_AI"

EnemyAiLinkedSlotMask = $03
EnemyAiActiveState = $80
EnemyDirectionBit = $01
EnemyLinkedStateBit = $20
EnemyActionDirectionMask = $01
EnemyActionLinkMask = $FD
EnemyMapOpenTileMinimum = $F8
EnemyFacingActionBase = $14
EnemyPairActionBase = $0C
EnemySingleLinkActionBase = $16

SetEnemyHorizontalStepAndFacing:
    LDY #ObjectXMotionOffset
    TYA
    STA (EnemyObjectPointer),Y

SelectEnemyFacingAction:
    LDX #EnemyFacingActionBase
    LDY #EnemyAiHorizontalDeltaOffset
    LDA (EnemyAiPointer),Y
    BPL StoreEnemyFacingAction
    INX

StoreEnemyFacingAction:
    LDY #ObjectActionOffset
    TXA
    STA (EnemyObjectPointer),Y
    RTS

UpdateLinkedEnemyPairSpawn:
    JSR CompareEnemyMotionThresholds
    BCS CheckLinkedEnemyPairMotion
    LDY #EnemyAiPhaseOffset
    LDA (EnemyAiPointer),Y
    CMP #$20
    BCC CheckLinkedEnemyPairMotion
    JSR SelectEnemyFacingAction
    BNE AllocateLinkedEnemyPair

CheckLinkedEnemyPairMotion:
    LDY #ObjectXMotionOffset
    LDA (EnemyObjectPointer),Y
    BNE FinishLinkedEnemyUpdate
    JSR CalculateEnemyForwardMapCoordinates
    JSR ConvertPixelCoordinatesToMapIndex
    TAX
    LDA RoomMap,X
    BPL FinishLinkedEnemyPairProbe
    CMP #EnemyMapOpenTileMinimum
    BCC AllocateLinkedEnemyPair
    LDY #ObjectActionOffset
    LDA #EnemyDirectionBit
    EOR (EnemyObjectPointer),Y
    STA (EnemyObjectPointer),Y

FinishLinkedEnemyPairProbe:
    RTS

AllocateLinkedEnemyPair:
    JSR FindFreeEnemySlotIndex
    BCC FinishLinkedEnemyUpdate
    LDY #EnemyAiFirstLinkedSlotOffset
    TXA
    STA (EnemyAiPointer),Y
    LDY #EnemyAiFlagsOffset
    LDA #EnemyAiActiveState
    STA (TempPointer04),Y
    LDA TempPointer04
    STA TempPointer00
    LDA TempPointer04 + 1
    STA TempPointer00 + 1
    JSR FindFreeEnemySlotIndex
    LDY #EnemyAiFlagsOffset
    BCS ActivateSecondLinkedEnemy
    TYA
    STA (TempPointer00),Y
    BCC FinishLinkedEnemyUpdate

ActivateSecondLinkedEnemy:
    LDA #EnemyAiActiveState
    STA (TempPointer04),Y
    LDA (EnemyAiPointer),Y
    ORA #EnemyAiLinkedSlotMask
    STA (EnemyAiPointer),Y
    TYA
    INY
    STA (EnemyAiPointer),Y
    LDY #ObjectActionOffset
    LDA (EnemyObjectPointer),Y
    AND #EnemyActionDirectionMask
    ORA #EnemyPairActionBase
    STA (EnemyObjectPointer),Y
    LDY #EnemyAiSecondLinkedSlotOffset
    TXA
    STA (EnemyAiPointer),Y

FinishLinkedEnemyUpdate:
    RTS

CompareEnemyMotionThresholds:
    LDY #EnemyAiHorizontalDeltaOffset
    LDA (EnemyAiPointer),Y
    ASL A
    BCS CompareHorizontalEnemyMotion
    EOR #$FF

CompareHorizontalEnemyMotion:
    CMP #$14
    BCS FinishEnemyMotionComparison
    DEY
    LDA (EnemyAiPointer),Y
    ASL A
    BCS CompareVerticalEnemyMotion
    EOR #$FF

CompareVerticalEnemyMotion:
    CMP #$10

FinishEnemyMotionComparison:
    RTS

LoadEnemyActionSelector:
    LDY #ObjectActionOffset
    LDA (EnemyObjectPointer),Y
    LSR A
    LSR A
    RTS

RunType50To5BEnemyAi:
    JSR ApplyEnemyLifetimeThreshold
    JSR LoadEnemyActionSelector
    JSR JumpWithParams

Type50To5BActionHandlers:
    .addr DeactivateType50To5BAtPhase11
    .addr BeginType50To5BHorizontalStep
    .addr SetEnemyMovingAction18
    .addr RunEnemyActionA55C
    .addr RunEnemyActionA55C
    .addr UpdateSingleLinkedEnemy
    .addr RunEnemyActionA55C

DeactivateType50To5BAtPhase11:
    LDY #EnemyAiPhaseOffset
    LDA (EnemyAiPointer),Y
    CMP #$11
    BCS DeactivateCurrentType50To5BEnemy
    RTS

DeactivateCurrentType50To5BEnemy:
    JMP DeactivateCurrentEnemy

BeginType50To5BHorizontalStep:
    LDY #ObjectXMotionOffset
    LDA #$01
    STA (EnemyObjectPointer),Y
    LDY #ObjectActionOffset
    LDA #EnemyActionDirectionMask
    AND (EnemyObjectPointer),Y
    ORA #EnemyFacingActionBase
    STA (EnemyObjectPointer),Y

FinishSingleLinkedEnemyUpdate:
    RTS

UpdateSingleLinkedEnemy:
    LDY #ObjectXMotionOffset
    LDA (EnemyObjectPointer),Y
    BNE FinishSingleLinkedEnemyUpdate
    LDY #EnemyAiFlagsOffset
    LDA (EnemyAiPointer),Y
    ROR A
    BCS CheckSingleLinkedEnemyPhase
    JSR CalculateEnemyForwardMapCoordinates
    JSR ConvertPixelCoordinatesToMapIndex
    TAX
    LDA RoomMap,X
    BMI AllocateSingleLinkedEnemy
    LDY #ObjectCachedActionOffset
    LDA #$FF
    STA (EnemyObjectPointer),Y

FinishSingleLinkedMapProbe:
    RTS

AllocateSingleLinkedEnemy:
    STX TempPointer00
    JSR FindFreeEnemySlotIndex
    BCC FinishSingleLinkedEnemyUpdate
    LDY #EnemyAiFirstLinkedSlotOffset
    TXA
    STA (EnemyAiPointer),Y
    LDY #EnemyAiFlagsOffset
    LDA #EnemyAiActiveState
    STA (TempPointer04),Y
    LDA #EnemyDirectionBit
    ORA (EnemyAiPointer),Y
    STA (EnemyAiPointer),Y
    TYA
    INY
    STA (EnemyAiPointer),Y
    LDA TempPointer00
    STA TempPointer04
    LDA EnemyObjectPointerLowTable,X
    STA TempPointer00
    LDA EnemyObjectPointerHighTable,X
    STA TempPointer00 + 1
    LDY #ObjectStateOffset
    LDA #$DF
    AND (EnemyObjectPointer),Y
    STA (EnemyObjectPointer),Y
    LDY #ObjectActionOffset
    LDA (EnemyObjectPointer),Y
    AND #EnemyActionDirectionMask
    STA TempPointer02
    ORA #EnemySingleLinkActionBase
    STA (EnemyObjectPointer),Y
    LDY TempPointer04
    LDA RoomMap,Y
    JSR ApplyMapTileInteractionToObject

CheckSingleLinkedEnemyPhase:
    LDY #EnemyAiPhaseOffset
    LDA (EnemyAiPointer),Y
    CMP #$0F
    BCC FinishSingleLinkedMapProbe
    LDY #ObjectXMotionOffset
    LDA #$03
    STA (EnemyObjectPointer),Y
    LDY #ObjectActionOffset
    LDA #EnemyDirectionBit
    EOR (EnemyObjectPointer),Y
    AND #EnemyActionLinkMask
    STA (EnemyObjectPointer),Y
    LDY #ObjectStateOffset
    LDA #EnemyLinkedStateBit
    ORA (EnemyObjectPointer),Y
    STA (EnemyObjectPointer),Y

ClearSingleLinkedEnemyState:
    LDY #EnemyAiFlagsOffset
    LDA #$FE
    AND (EnemyAiPointer),Y
    STA (EnemyAiPointer),Y
    LDX #$01
    JSR ClearLinkedEnemySlots
    RTS

CalculateEnemyForwardMapCoordinates:
    LDY #ObjectActionOffset
    LDA (EnemyObjectPointer),Y
    ROR A
    LDA #$18
    BCC AddEnemyForwardXOffset
    LDA #$F7

AddEnemyForwardXOffset:
    LDY #ObjectXPositionOffset
    ADC (EnemyObjectPointer),Y
    STA CoordinateX
    LDY #ObjectYPositionOffset
    LDA #$08
    ADC (EnemyObjectPointer),Y
    STA CoordinateY
    RTS

.assert * - SetEnemyHorizontalStepAndFacing = $188, error, "unexpected linked enemy AI size"
