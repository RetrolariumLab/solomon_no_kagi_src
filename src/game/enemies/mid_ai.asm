; Mid-table enemy AI families, action dispatch, and linked-slot allocation

.segment "PRG_MID_ENEMY_AI"

RunPanelMonsterEnemyAi:
    JSR LoadEnemyActionSelector
    JSR JumpWithParams

PanelMonsterActionHandlers:
    .addr AllocatePanelMonsterLinkedEnemy, UpdatePanelMonsterAction

UpdatePanelMonsterAction:
    LDY #EnemyAiPhaseOffset
    LDA (EnemyAiPointer),Y
    CMP #$10
    BCC FinishPanelMonsterUpdate
    LDY #ObjectActionOffset
    LDA (EnemyObjectPointer),Y
    AND #$03
    TAX
    JSR SpawnLinkedEnemyAtOffset
    LDY #ObjectActionOffset
    TYA
    AND (EnemyObjectPointer),Y
    STA (EnemyObjectPointer),Y
    DEY
    LDA #$00
    STA (EnemyAiPointer),Y

FinishPanelMonsterUpdate:
    RTS

AllocatePanelMonsterLinkedEnemy:
    LDY #$02
    LDA (EnemyAiPointer),Y
    CMP #$C0
    BCC FinishPanelMonsterAllocation
    JSR FindFreeEnemySlotIndex
    BCC FinishPanelMonsterAllocation
    TXA
    LDY #EnemyAiFirstLinkedSlotOffset
    STA (EnemyAiPointer),Y
    LDY #EnemyAiFlagsOffset
    LDA #EnemyAiActiveState
    STA (TempPointer04),Y
    LDY #ObjectActionOffset
    LDA #$03
    AND (EnemyObjectPointer),Y
    ORA #$04
    STA (EnemyObjectPointer),Y
    DEY
    LDA #$00
    STA (EnemyAiPointer),Y
    DEY
    STA (EnemyAiPointer),Y

FinishPanelMonsterAllocation:
    RTS

RunFlameEnemyAi:
    JSR LoadEnemyActionSelector
    JSR JumpWithParams

FlameActionHandlers:
    .addr UpdateFlamePhase
    .addr CheckFlameDanaRange22
    .addr RunEnemyActionA55C, RunEnemyActionA55C
    .addr CheckFlameDanaRange06
    .addr ResetFlameDirection
    .addr CheckFlameDanaRange16

CheckFlameDanaRange16:
    LDX #$16
    JMP CheckDanaEnemyProximityThreshold

UpdateFlamePhase:
    LDY #EnemyAiPhaseOffset
    LDA (EnemyAiPointer),Y
    CMP #$30
    BCS DeactivateFlameEnemy
    CMP #$20
    BCS FinishFlamePhase
    LDX #$0A
    JSR CheckDanaEnemyProximityThreshold

FinishFlamePhase:
    RTS

DeactivateFlameEnemy:
    JMP DeactivateCurrentEnemy

CheckFlameDanaRange22:
    LDY #ObjectTypeOffset
    LDA (EnemyObjectPointer),Y
    LSR A
    BCS SelectFlameAction14
    DEY
    LDA (EnemyAiPointer),Y
    TAX
    AND #$08
    BEQ SetFlameDirectionBit
    INY
    LDA #$00
    STA (EnemyAiPointer),Y
    BEQ StoreFlameAction

SetFlameDirectionBit:
    TXA
    ORA #$08
    STA (EnemyAiPointer),Y

SelectFlameAction14:
    LDA #$14

StoreFlameAction:
    LDY #ObjectActionOffset
    STA (EnemyObjectPointer),Y
    RTS

CheckFlameDanaRange06:
    LDX #$06
    JSR CheckDanaEnemyProximityThreshold
    LDY #EnemyAiPhaseOffset
    LDA (EnemyAiPointer),Y
    CMP #$D2
    BCS SelectDelayedFlameAction14
    RTS

SelectDelayedFlameAction14:
    LDA #$14
    BPL StoreFlameAction

ResetFlameDirection:
    LDX #$10
    JSR CheckDanaEnemyProximityThreshold
    LDY #EnemyAiFlagsOffset
    LDA (EnemyObjectPointer),Y
    TAX
    AND #$08
    BNE ClearFlameDirectionBit
    RTS

ClearFlameDirectionBit:
    TXA
    AND #$F7
    STA (EnemyObjectPointer),Y
    TYA
    INY
    STA (EnemyAiPointer),Y
    LDA #$10
    BPL StoreFlameAction

CheckDanaEnemyProximityThreshold:
    LDA DanaObject + ObjectActionOffset
    CMP #DanaCastActionBase
    BCS FinishDanaEnemyProximityCheck
    STX TempPointer00
    LDY #EnemyAiVerticalDeltaOffset
    LDA (EnemyAiPointer),Y
    ASL A
    BCC FinishDanaEnemyProximityCheck
    CMP TempPointer00
    BCS FinishDanaEnemyProximityCheck
    JSR CheckDanaHorizontalEnemyOverlap
    BCS FinishDanaEnemyProximityCheck
    LDA #$31
    JSR StartThread

FinishDanaEnemyProximityCheck:
    RTS

CheckDanaHorizontalEnemyOverlap:
    LDA DanaXPosition
    LDY #ObjectXPositionOffset
    SEC
    SBC (EnemyObjectPointer),Y
    ADC #$04
    CMP #$0A
    RTS

RunDragonEnemyAi:
    JSR LoadEnemyActionSelector
    JSR JumpWithParams

DragonActionHandlers:
    .addr RunEnemyActionA55C
    .addr UpdateLinkedEnemyDirectionState
    .addr SelectDragonActionByDirection
    .addr UpdatePairedEnemyState
    .addr RunEnemyActionA55C
    .addr UpdateDragonLinkedPair
    .addr ClearCurrentEnemyLinkedSlots

SelectDragonActionByDirection:
    LDY #ObjectActionOffset
    LDA (EnemyObjectPointer),Y
    LSR A
    LDA #$0A
    ROL A
    STA (EnemyObjectPointer),Y
    RTS

UpdateDragonLinkedPair:
    JSR CompareEnemyMotionThresholds
    BCS ProbeDragonForwardTile
    JSR SelectEnemyFacingAction
    BNE AllocateDragonLinkedPair

ProbeDragonForwardTile:
    JSR CheckEnemyForwardCollisionBit
    BNE UpdateDragonBlockedDirection
    LDA #$02
    LDY #ObjectActionOffset
    LDA (EnemyObjectPointer),Y
    ROR A
    ROR A
    BCS CheckDragonActionPhase
    SEC
    ROL A
    ROL A
    STA (EnemyObjectPointer),Y
    LDA #$00
    LDY #EnemyAiPhaseOffset
    STA (EnemyAiPointer),Y

FinishDragonUpdate:
    RTS

CheckDragonActionPhase:
    LDY #EnemyAiPhaseOffset
    LDA (EnemyAiPointer),Y
    CMP #$14
    BCC FinishDragonUpdate
    LDY #ObjectXMotionOffset
    TYA
    STA (EnemyObjectPointer),Y
    BPL ReverseDragonDirection

UpdateDragonBlockedDirection:
    LDY #ObjectXMotionOffset
    LDA (EnemyObjectPointer),Y
    BNE FinishDragonBlockedDirection
    JSR CalculateEnemyForwardMapCoordinates
    JSR ConvertPixelCoordinatesToMapIndex
    TAX
    LDA RoomMap,X
    BPL FinishDragonBlockedDirection
    CMP #$F8
    BCC AllocateDragonLinkedPair

ReverseDragonDirection:
    LDY #ObjectActionOffset
    LDA #EnemyDirectionBit
    EOR (EnemyObjectPointer),Y
    AND #EnemyActionLinkMask
    STA (EnemyObjectPointer),Y

FinishDragonBlockedDirection:
    RTS

AllocateDragonLinkedPair:
    JSR FindFreeEnemySlotIndex
    BCC FinishDragonPairAllocation
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
    BCS ActivateDragonLinkedPair
    TYA
    STA (TempPointer00),Y
    BCC FinishDragonPairAllocation

ActivateDragonLinkedPair:
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
    AND #EnemyDirectionBit
    ORA #EnemyPairActionBase
    STA (EnemyObjectPointer),Y
    LDY #EnemyAiSecondLinkedSlotOffset
    TXA
    STA (EnemyAiPointer),Y

FinishDragonPairAllocation:
    RTS

RunFairyEnemyAi:
    LDA $87
    LSR A
    BCS DispatchFairyAction
    JSR CheckEnemyAiDeltaRange
    BCS DispatchFairyAction
    JSR CheckDanaHorizontalEnemyOverlap
    BCS DispatchFairyAction
    LDY #ObjectActionOffset
    LDA (EnemyObjectPointer),Y
    CMP #$0C
    BEQ DispatchFairyAction
    LDA #$DF
    LDY #ObjectStateOffset
    AND (EnemyObjectPointer),Y
    STA (EnemyObjectPointer),Y
    TYA
    INY
    STA (EnemyAiPointer),Y
    LDY #ObjectActionOffset
    LDA #$0C
    STA (EnemyObjectPointer),Y

DispatchFairyAction:
    JSR LoadEnemyActionSelector
    JSR JumpWithParams

FairyActionHandlers:
    .addr UpdateFairyPhaseAction
    .addr UpdateFairyHorizontalOrientation
    .addr UpdateFairyVerticalOrientation
    .addr CollectFairyFairy
    .addr RunEnemyActionA55C, RunEnemyActionA55C
    .addr UpdateFairyMotion

CollectFairyFairy:
    LDY #EnemyAiPhaseOffset
    LDA (EnemyAiPointer),Y
    BNE CheckFairyFairyLifetime
    TYA
    STA (EnemyAiPointer),Y
    DEY
    LDA #$04
    ORA (EnemyObjectPointer),Y
    STA (EnemyObjectPointer),Y
    LDY #$0F
    JSR AddSoundEffect
    LDX FairiesCollected
    INX
    LDA #EnemyItemInteractionThread
    CPX #$0A
    BCC StoreFairyFairyCount
    INC GdvFactor2
    JSR LoadCurrentEnemyPosition
    JSR SpawnAuxiliaryEffectAtCoordinates
    JSR AwardExtraLifeFromMapTile
    LDX #$00
    LDA #ExtraLifeEnemyInteractionThread

StoreFairyFairyCount:
    STX FairiesCollected
    JSR StartThread
    LDY #EnemyAiPhaseOffset
    LDA (EnemyObjectPointer),Y
    CMP #$1C
    BNE StartFairyMapInteraction

FinishFairyFairyUpdate:
    RTS

CheckFairyFairyLifetime:
    CMP #$12
    BCC FinishFairyFairyUpdate
    JMP DeactivateCurrentEnemy

StartFairyMapInteraction:
    DEY
    STY RoomItemPointer + 1
    LDA #$04
    ORA RoomStateFlags
    STA RoomStateFlags
    LDY #ObjectYPositionOffset
    LDA (EnemyObjectPointer),Y
    STA CoordinateY
    LDY #ObjectXPositionOffset
    LDA (EnemyObjectPointer),Y
    STA CoordinateX
    JSR ConvertPixelCoordinatesToMapIndex
    STX EnemyObjectPointer + 1
    LDA #$2A
    STA RoomItemPointer
    LDA #$32
    JSR StartThread

UpdateFairyMotion:
    LDY #ObjectXMotionOffset
    LDA (EnemyObjectPointer),Y
    ASL A
    ASL A
    LDA #$18
    BCC StoreFairyAction
    ADC #$00

StoreFairyAction:
    LDY #ObjectActionOffset
    STA (EnemyObjectPointer),Y
    LDY #EnemyAiPhaseOffset
    LDA (EnemyAiPointer),Y
    BNE ApplyFairyMotionCorrection
    RTS

ApplyFairyMotionCorrection:
    LDA #$00
    STA (EnemyAiPointer),Y
    LDA (EnemyObjectPointer),Y
    SEC
    SBC #$1C
    ASL A
    STA TempPointer00
    LDY #EnemyAiFirstLinkedSlotOffset
    LDA (EnemyAiPointer),Y
    STA TempPointer00 + 1
    DEY
    LDA (EnemyObjectPointer),Y
    ASL A
    STA TempPointer02
    LDX TempPointer00
    LDA TempPointer00 + 1
    BPL SelectFairyVerticalAdjustment
    INX

SelectFairyVerticalAdjustment:
    LDA TempPointer02
    CLC
    ADC FairyVerticalAdjustments,X
    LDX TempPointer00
    STA TempPointer02
    LDY #EnemyAiVerticalDeltaOffset
    EOR (EnemyAiPointer),Y
    BPL NormalizeFairyVerticalDelta
    INX

NormalizeFairyVerticalDelta:
    LDA TempPointer02
    BPL CompareFairyVerticalLimit
    EOR #$FF

CompareFairyVerticalLimit:
    CMP FairyVerticalLimits,X
    BCC StoreFairyVerticalMotion
    ASL TempPointer00 + 1
    LDA TempPointer02
    ASL A
    ROR TempPointer00 + 1

StoreFairyVerticalMotion:
    LDY #ObjectYMotionOffset
    LDA TempPointer02
    LSR A
    STA (EnemyObjectPointer),Y
    LDY #ObjectXMotionOffset
    LDA (EnemyObjectPointer),Y
    ASL A
    STA TempPointer02
    LDA TempPointer00 + 1
    LDX TempPointer00
    ASL A
    BPL SelectFairyHorizontalAdjustment
    INX

SelectFairyHorizontalAdjustment:
    CLC
    LDA TempPointer02
    ADC FairyHorizontalAdjustments,X
    STA TempPointer02
    LDX TempPointer00
    LDY #EnemyAiHorizontalDeltaOffset
    EOR (EnemyAiPointer),Y
    BPL NormalizeFairyHorizontalDelta
    INX

NormalizeFairyHorizontalDelta:
    LDA TempPointer02
    BPL CompareFairyHorizontalLimit
    EOR #$FF

CompareFairyHorizontalLimit:
    CMP FairyHorizontalLimits,X
    BCC StoreFairyHorizontalMotion
    LDA #$80
    EOR TempPointer02
    ASL TempPointer00 + 1
    AND #$80
    ROR A
    STA TempPointer00 + 1

StoreFairyHorizontalMotion:
    LDY #ObjectXMotionOffset
    LDA TempPointer02
    LSR A
    STA (EnemyObjectPointer),Y
    LDY #EnemyAiFirstLinkedSlotOffset
    LDA TempPointer00 + 1
    STA (EnemyAiPointer),Y
    RTS

FairyVerticalAdjustments:
    .byte $FC, $04, $FA, $06

FairyVerticalLimits:
    .byte $40, $20, $60, $30

FairyHorizontalAdjustments:
    .byte $04, $FC, $06, $FA

FairyHorizontalLimits:
    .byte $40, $20, $60, $30
