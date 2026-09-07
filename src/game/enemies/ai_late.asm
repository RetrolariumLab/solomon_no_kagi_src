; Final enemy AI families and shared collision-direction helpers

.segment "PRG_LATE_ENEMY_AI"

RunType64To6BEnemyAi:
    JSR LoadEnemyActionSelector
    JSR JumpWithParams

Type64To6BActionHandlers:
    .addr UpdateType64To6BLinkedSpawn
    .addr UpdateLinkedEnemyDirectionState
    .addr SetEnemyMovingAction18
    .addr RunEnemyActionA55C, RunEnemyActionA55C
    .addr UpdateType64To6BSpawn
    .addr RunEnemyActionA55C

SetEnemyMovingAction18:
    LDY #ObjectActionOffset
    LDA #EnemyDirectionBit
    AND (EnemyObjectPointer),Y
    ORA #$18
    STA (EnemyObjectPointer),Y
    RTS

UpdateType64To6BLinkedSpawn:
    LDY #EnemyAiPhaseOffset
    LDA (EnemyAiPointer),Y
    TAX
    LDY #ObjectActionOffset
    LDA (EnemyObjectPointer),Y
    AND #$02
    BEQ CheckType64To6BSpawnPhase
    CPX #$50
    BCC FinishType64To6BLinkedSpawn
    LDA #$00
    LDY #EnemyAiPhaseOffset
    STA (EnemyAiPointer),Y
    TYA
    LDY #ObjectXMotionOffset
    STA (EnemyObjectPointer),Y
    LDX #$00
    JSR CheckEnemyForwardCollisionBit
    BNE SelectType64To6BLinkedAction
    INX

SelectType64To6BLinkedAction:
    LDY #ObjectActionOffset
    LDA (EnemyObjectPointer),Y
    LSR A
    TXA
    ROL A
    ORA #$14
    STA (EnemyObjectPointer),Y
    RTS

CheckType64To6BSpawnPhase:
    CPX #$10
    BCC FinishType64To6BLinkedSpawn
    LDA (EnemyObjectPointer),Y
    TAX
    ORA #$02
    STA (EnemyObjectPointer),Y

SpawnLinkedEnemyAtOffset:
    STX TempPointer02 + 1
    LDA LinkedEnemySpawnXOffsets,X
    STA CoordinateY
    LDA LinkedEnemySpawnYOffsets,X
    STA CoordinateX
    LDY #EnemyAiFirstLinkedSlotOffset
    LDA (EnemyAiPointer),Y
    STA TempPointer02
    JSR LoadEnemyAiPointer
    LDY #EnemyAiFlagsOffset
    LDA #$FE
    AND (EnemyAiPointer),Y
    STA (EnemyAiPointer),Y
    INY
    LDA #$00
    STA (TempPointer00),Y
    LDA TempPointer02
    JSR LoadEnemyObjectPointer
    LDY #ObjectYPositionOffset
    LDA (EnemyObjectPointer),Y
    CLC
    ADC CoordinateY
    STA (TempPointer00),Y
    LDY #ObjectXPositionOffset
    LDA (EnemyObjectPointer),Y
    CLC
    ADC CoordinateX
    STA (TempPointer00),Y
    LDA #$C0
    STA CoordinateY
    LDA #$20
    STA CoordinateX
    LDA TempPointer02 + 1
    JSR InitializeObjectStateHeader
    LDY #$17
    JSR AddSoundEffect

FinishType64To6BLinkedSpawn:
    RTS

LinkedEnemySpawnYOffsets:
    .byte $06, $FA, $00, $00, $FA, $06

LinkedEnemySpawnXOffsets = LinkedEnemySpawnYOffsets + 2

UpdateLinkedEnemyDirectionState:
    LDY #EnemyAiFlagsOffset
    LDA (EnemyAiPointer),Y
    TAX
    AND #$08
    BNE CheckLinkedEnemyDirectionPhase
    TXA
    ORA #$08
    STA (EnemyAiPointer),Y
    LDA #EnemyDirectionBit
    LDY #ObjectActionOffset
    AND (EnemyObjectPointer),Y
    ORA #$14
    STA (EnemyObjectPointer),Y
    RTS

CheckLinkedEnemyDirectionPhase:
    LDY #ObjectActionOffset
    LDA (EnemyObjectPointer),Y
    AND #$02
    BEQ CheckLinkedEnemyReplacementPhase
    LDA #$04
    STA (EnemyObjectPointer),Y
    LDY #EnemyAiPhaseOffset
    LDA #$00
    STA (EnemyAiPointer),Y

FinishLinkedEnemyDirectionUpdate:
    RTS

CheckLinkedEnemyReplacementPhase:
    LDY #EnemyAiPhaseOffset
    LDA (EnemyAiPointer),Y
    CMP #$11
    BCC FinishLinkedEnemyDirectionUpdate
    DEY
    LDA #$40
    AND (EnemyAiPointer),Y
    BNE ReplaceLinkedEnemyObjectHeader
    JMP DeactivateCurrentEnemy

ReplaceLinkedEnemyObjectHeader:
    LDY #ObjectActionOffset

CopyLinkedEnemyReplacementHeader:
    LDA LinkedEnemyReplacementHeader,Y
    STA (EnemyObjectPointer),Y
    DEY
    BPL CopyLinkedEnemyReplacementHeader
    RTS

LinkedEnemyReplacementHeader:
    .byte $E2, $1C, $FF, $00

UpdateType64To6BSpawn:
    LDA #$18
    STA TempPointer00
    JSR CheckEnemyForwardCollisionBit
    BNE CheckType64To6BSpawnDirection
    JSR CheckEnemyDeltaDirectionThreshold
    BCS HandleType64To6BBlockedSpawn
    LDY #ObjectActionOffset
    LDA #$02
    ORA (EnemyObjectPointer),Y
    STA (EnemyObjectPointer),Y

CheckType64To6BSpawnPhaseAgain:
    LDY #EnemyAiPhaseOffset
    LDA (EnemyAiPointer),Y
    CMP #$68
    BCC FinishType64To6BSpawn
    JSR FindFreeEnemySlotIndex
    BCC FinishType64To6BSpawn
    LDY #EnemyAiFlagsOffset
    LDA #EnemyAiActiveState
    STA (TempPointer04),Y
    LDA #$01
    ORA (EnemyAiPointer),Y
    STA (EnemyAiPointer),Y
    TXA
    LDY #EnemyAiFirstLinkedSlotOffset
    STA (EnemyAiPointer),Y
    LDA #$00
    LDY #EnemyAiPhaseOffset
    STA (EnemyAiPointer),Y
    LDY #ObjectActionOffset
    LDA #EnemyDirectionBit
    AND (EnemyObjectPointer),Y
    STA (EnemyObjectPointer),Y

FinishType64To6BSpawn:
    RTS

CheckType64To6BSpawnDirection:
    JSR CheckEnemyDeltaDirectionThreshold
    BCC CheckType64To6BSpawnPhaseAgain
    LDY #ObjectXMotionOffset
    LDA (EnemyObjectPointer),Y
    BNE FinishType64To6BSpawn

HandleType64To6BBlockedSpawn:
    LDY #ObjectActionOffset
    LDA (EnemyObjectPointer),Y
    TAX
    AND #$02
    BNE CheckType64To6BBlockedPhase
    TXA
    ORA #$02
    STA (EnemyObjectPointer),Y
    LDY #$02
    LDA #$00
    STA (EnemyAiPointer),Y

CheckType64To6BBlockedPhase:
    LDY #$02
    LDA (EnemyAiPointer),Y
    CMP #$18
    BCC FinishType64To6BBlockedSpawn
    LDY #ObjectXMotionOffset
    LDA #$01
    STA (EnemyObjectPointer),Y
    LDY #ObjectActionOffset
    EOR (EnemyObjectPointer),Y
    AND #$FD
    STA (EnemyObjectPointer),Y

FinishType64To6BBlockedSpawn:
    RTS

CheckEnemyForwardCollisionBit:
    LDY #ObjectActionOffset
    LDA (EnemyObjectPointer),Y
    LSR A
    LDA #ObjectCollisionBelowRightBit
    BCC ApplyEnemyForwardCollisionMask
    LDA #ObjectCollisionBelowLeftBit

ApplyEnemyForwardCollisionMask:
    LDY #ObjectCollisionMaskOffset
    AND (EnemyObjectPointer),Y
    RTS

CheckEnemyDeltaDirectionThreshold:
    LDY #EnemyAiVerticalDeltaOffset
    LDA (EnemyAiPointer),Y
    ASL A
    BCS CompareEnemyDeltaThreshold
    EOR #$FF

CompareEnemyDeltaThreshold:
    CMP TempPointer00
    BCS FinishEnemyDeltaDirectionCheck
    INY
    LDA (EnemyAiPointer),Y
    ROL A
    ROL A
    CLC
    LDY #ObjectActionOffset
    EOR (EnemyObjectPointer),Y
    AND #EnemyDirectionBit
    BEQ FinishEnemyDeltaDirectionCheck
    SEC

FinishEnemyDeltaDirectionCheck:
    RTS

RunType0CTo0FEnemyAi:
    JSR LoadEnemyActionSelector
    JSR JumpWithParams

Type0CTo0FActionHandlers:
    .addr UpdateType0CTo0FPhaseAction
    .addr DeactivateType0CTo0FAtPhase0F
    .addr UpdateType0CTo0FMapInteraction

UpdateType0CTo0FPhaseAction:
    LDY #EnemyAiPhaseOffset
    LDA (EnemyAiPointer),Y
    CMP #$0A
    BCC FinishType0CTo0FPhaseAction
    LDY #ObjectActionOffset
    LDA #$08
    ORA (EnemyObjectPointer),Y
    STA (EnemyObjectPointer),Y

FinishType0CTo0FPhaseAction:
    RTS

UpdateType0CTo0FMapInteraction:
    JSR SampleCurrentEnemyRoomMapCollision
    LDA TempPointer04 + 3
    BEQ FinishType0CTo0FMapInteraction
    JSR SelectEnemyCollisionMapCoordinates
    JSR ConvertPixelCoordinatesToMapIndex
    TAY
    LDA RoomMap,Y
    CMP #$F8
    BCC ApplyType0CTo0FMapInteraction
    JMP DeactivateCurrentEnemy

ApplyType0CTo0FMapInteraction:
    STY MapCellIndex
    LDX EnemyObjectPointer
    STX TempPointer00
    LDX EnemyObjectPointer + 1
    STX TempPointer00 + 1
    JSR ApplyMapTileInteractionToObject
    LDY #ObjectTypeOffset
    LDA #$20
    STA (EnemyObjectPointer),Y
    LDY #ObjectActionOffset
    LDA #$04
    STA (EnemyObjectPointer),Y

FinishType0CTo0FMapInteraction:
    RTS

DeactivateType0CTo0FAtPhase0F:
    LDY #EnemyAiPhaseOffset
    LDA (EnemyAiPointer),Y
    CMP #$0F
    BCS DeactivateType0CTo0FEnemy
    RTS

DeactivateType0CTo0FEnemy:
    JMP DeactivateCurrentEnemy

SelectEnemyCollisionMapCoordinates:
    AND #$0F
    LDX #$FF

FindEnemyCollisionDirectionBit:
    INX
    LSR A
    BCC FindEnemyCollisionDirectionBit
    LDY #ObjectYPositionOffset
    LDA EnemyCollisionCoordinateOffsets,X
    CLC
    ADC (EnemyObjectPointer),Y
    STA CoordinateY
    LDY #ObjectXPositionOffset
    LDA EnemyCollisionCoordinateOffsets + 1,X
    CLC
    ADC (EnemyObjectPointer),Y
    STA CoordinateX
    RTS

EnemyCollisionCoordinateOffsets:
    .byte $00, $00, $0F, $0F, $00

RunType48To53EnemyAi:
    JSR ApplyEnemyLifetimeThreshold
    JSR LoadEnemyActionSelector
    JSR JumpWithParams

Type48To53ActionHandlers:
    .addr DeactivateType50To5BAtPhase11
    .addr SetEnemyHorizontalStepAndFacing
    .addr SetEnemyMovingAction18
    .addr UpdatePairedEnemyState
    .addr RunEnemyActionA55C
    .addr UpdateLinkedEnemyPairSpawn
    .addr ClearCurrentEnemyLinkedSlots

ClearCurrentEnemyLinkedSlots:
    LDY #EnemyAiFlagsOffset
    LDA (EnemyAiPointer),Y
    AND #EnemyAiLinkedSlotMask
    BEQ FinishClearCurrentEnemyLinkedSlots
    TAX
    LDA (EnemyAiPointer),Y
    AND #$F8
    STA (EnemyAiPointer),Y

ClearLinkedEnemySlots:
    STX TempPointer00
    LDY #EnemyAiFirstLinkedSlotOffset
    JSR ClearNextLinkedEnemySlot
    LDY #EnemyAiSecondLinkedSlotOffset
    JSR ClearNextLinkedEnemySlot

FinishClearCurrentEnemyLinkedSlots:
    RTS

ClearNextLinkedEnemySlot:
    LSR TempPointer00
    BCC FinishClearCurrentEnemyLinkedSlots
    LDA (EnemyAiPointer),Y
    JSR DeactivateEnemySlot
    RTS

UpdatePairedEnemyState:
    LDY #ObjectActionOffset
    LDA (EnemyObjectPointer),Y
    LDY #EnemyAiPhaseOffset
    AND #$02
    BEQ ActivatePairedEnemyAttack
    LDA (EnemyAiPointer),Y
    CMP #$20
    BCC FinishPairedEnemyStateUpdate
    TAX
    DEY
    LDA (EnemyAiPointer),Y
    AND #$04
    BNE CheckPairedEnemyReturnPhase
    CPX #$2C
    BCS CheckPairedEnemyReleasePhase
    LDA #$04
    ORA (EnemyAiPointer),Y
    STA (EnemyAiPointer),Y
    JSR LoadPairedEnemyObjectState
    AND #$FD
    STA (TempPointer00),Y
    RTS

CheckPairedEnemyReturnPhase:
    CPX #$2C
    BCC FinishPairedEnemyStateUpdate
    LDA (EnemyAiPointer),Y
    AND #$FB
    STA (EnemyAiPointer),Y
    JSR LoadPairedEnemyObjectState
    ORA #$02
    STA (TempPointer00),Y
    JSR ClearSingleLinkedEnemyState

CheckPairedEnemyReleasePhase:
    CPX #$34
    BCC FinishPairedEnemyStateUpdate
    LDA (EnemyAiPointer),Y
    AND #EnemyAiLinkedSlotMask
    TAX
    LDA (EnemyAiPointer),Y
    AND #$F8
    STA (EnemyAiPointer),Y
    TYA
    INY
    STA (EnemyAiPointer),Y
    JSR ClearLinkedEnemySlots
    LDY #ObjectActionOffset
    LDA (EnemyObjectPointer),Y
    LSR A
    LDA #$0A
    ROL A
    STA (EnemyObjectPointer),Y
    TYA
    LDY #ObjectXMotionOffset
    STA (EnemyObjectPointer),Y

FinishPairedEnemyStateUpdate:
    RTS

LoadPairedEnemyObjectState:
    LDY #EnemyAiSecondLinkedSlotOffset
    LDA (EnemyAiPointer),Y
    JSR LoadEnemyObjectPointer
    LDY #ObjectStateOffset
    LDA (TempPointer00),Y
    RTS

ActivatePairedEnemyAttack:
    LDA (EnemyAiPointer),Y
    CMP #$18
    BCC FinishPairedEnemyStateUpdate
    LDY #ObjectActionOffset
    LDA (EnemyObjectPointer),Y
    ORA #$02
    STA (EnemyObjectPointer),Y
    STA TempPointer02
    LDY #$0B
    JSR AddSoundEffect
    LDY #EnemyAiSecondLinkedSlotOffset
    LDA (EnemyAiPointer),Y
    JSR LoadEnemyObjectPointer
    LDA (EnemyObjectPointer),Y
    STA (TempPointer00),Y
    LDA #$04
    STA CoordinateX
    LDA #$C6
    STA CoordinateY
    ROR TempPointer02
    LDA #$05
    ROL A
    TAX
    ROR A
    LDA #$EF
    BCS SelectPairedEnemyXOffset
    LDA #$10

SelectPairedEnemyXOffset:
    LDY #ObjectXPositionOffset
    ADC (EnemyObjectPointer),Y
    STA (TempPointer00),Y
    TXA
    JSR InitializeObjectStateHeader

ApplyForwardEnemyMapInteraction:
    JSR CalculateEnemyForwardMapCoordinates
    JSR ConvertPixelCoordinatesToMapIndex
    TAX
    LDA RoomMap,X
    BPL FinishForwardEnemyMapInteraction
    STX MapCellIndex
    LDY #EnemyAiFirstLinkedSlotOffset
    LDA (EnemyAiPointer),Y
    JSR LoadEnemyObjectPointer
    LDY #ObjectActionOffset
    LDA (EnemyObjectPointer),Y
    AND #EnemyDirectionBit
    STA TempPointer02
    LDY MapCellIndex
    LDA RoomMap,Y
    JSR ApplyMapTileInteractionToObject

FinishForwardEnemyMapInteraction:
    RTS
