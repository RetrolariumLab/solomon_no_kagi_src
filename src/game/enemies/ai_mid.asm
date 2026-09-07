; Mid-table enemy AI families, action dispatch, and linked-slot allocation

.segment "PRG_MID_ENEMY_AI"

RunType10To13EnemyAi:
    JSR LoadEnemyActionSelector
    JSR JumpWithParams

Type10To13ActionHandlers:
    .addr AllocateType10To13LinkedEnemy, UpdateType10To13Action

UpdateType10To13Action:
    LDY #EnemyAiPhaseOffset
    LDA (EnemyAiPointer),Y
    CMP #$10
    BCC FinishType10To13Update
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

FinishType10To13Update:
    RTS

AllocateType10To13LinkedEnemy:
    LDY #$02
    LDA (EnemyAiPointer),Y
    CMP #$C0
    BCC FinishType10To13Allocation
    JSR FindFreeEnemySlotIndex
    BCC FinishType10To13Allocation
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

FinishType10To13Allocation:
    RTS

RunType6CTo6FEnemyAi:
    JSR LoadEnemyActionSelector
    JSR JumpWithParams

Type6CTo6FActionHandlers:
    .addr UpdateType6CTo6FPhase
    .addr CheckType6CTo6FDanaRange22
    .addr RunEnemyActionA55C, RunEnemyActionA55C
    .addr CheckType6CTo6FDanaRange06
    .addr ResetType6CTo6FDirection
    .addr CheckType6CTo6FDanaRange16

CheckType6CTo6FDanaRange16:
    LDX #$16
    JMP CheckDanaEnemyProximityThreshold

UpdateType6CTo6FPhase:
    LDY #EnemyAiPhaseOffset
    LDA (EnemyAiPointer),Y
    CMP #$30
    BCS DeactivateType6CTo6FEnemy
    CMP #$20
    BCS FinishType6CTo6FPhase
    LDX #$0A
    JSR CheckDanaEnemyProximityThreshold

FinishType6CTo6FPhase:
    RTS

DeactivateType6CTo6FEnemy:
    JMP DeactivateCurrentEnemy

CheckType6CTo6FDanaRange22:
    LDY #ObjectTypeOffset
    LDA (EnemyObjectPointer),Y
    LSR A
    BCS SelectType6CTo6FAction14
    DEY
    LDA (EnemyAiPointer),Y
    TAX
    AND #$08
    BEQ SetType6CTo6FDirectionBit
    INY
    LDA #$00
    STA (EnemyAiPointer),Y
    BEQ StoreType6CTo6FAction

SetType6CTo6FDirectionBit:
    TXA
    ORA #$08
    STA (EnemyAiPointer),Y

SelectType6CTo6FAction14:
    LDA #$14

StoreType6CTo6FAction:
    LDY #ObjectActionOffset
    STA (EnemyObjectPointer),Y
    RTS

CheckType6CTo6FDanaRange06:
    LDX #$06
    JSR CheckDanaEnemyProximityThreshold
    LDY #EnemyAiPhaseOffset
    LDA (EnemyAiPointer),Y
    CMP #$D2
    BCS SelectDelayedType6CTo6FAction14
    RTS

SelectDelayedType6CTo6FAction14:
    LDA #$14
    BPL StoreType6CTo6FAction

ResetType6CTo6FDirection:
    LDX #$10
    JSR CheckDanaEnemyProximityThreshold
    LDY #EnemyAiFlagsOffset
    LDA (EnemyObjectPointer),Y
    TAX
    AND #$08
    BNE ClearType6CTo6FDirectionBit
    RTS

ClearType6CTo6FDirectionBit:
    TXA
    AND #$F7
    STA (EnemyObjectPointer),Y
    TYA
    INY
    STA (EnemyAiPointer),Y
    LDA #$10
    BPL StoreType6CTo6FAction

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

RunType54To5BEnemyAi:
    JSR LoadEnemyActionSelector
    JSR JumpWithParams

Type54To5BActionHandlers:
    .addr RunEnemyActionA55C
    .addr UpdateLinkedEnemyDirectionState
    .addr SelectType54To5BActionByDirection
    .addr UpdatePairedEnemyState
    .addr RunEnemyActionA55C
    .addr UpdateType54To5BLinkedPair
    .addr ClearCurrentEnemyLinkedSlots

SelectType54To5BActionByDirection:
    LDY #ObjectActionOffset
    LDA (EnemyObjectPointer),Y
    LSR A
    LDA #$0A
    ROL A
    STA (EnemyObjectPointer),Y
    RTS

UpdateType54To5BLinkedPair:
    JSR CompareEnemyMotionThresholds
    BCS ProbeType54To5BForwardTile
    JSR SelectEnemyFacingAction
    BNE AllocateType54To5BLinkedPair

ProbeType54To5BForwardTile:
    JSR CheckEnemyForwardCollisionBit
    BNE UpdateType54To5BBlockedDirection
    LDA #$02
    LDY #ObjectActionOffset
    LDA (EnemyObjectPointer),Y
    ROR A
    ROR A
    BCS CheckType54To5BActionPhase
    SEC
    ROL A
    ROL A
    STA (EnemyObjectPointer),Y
    LDA #$00
    LDY #EnemyAiPhaseOffset
    STA (EnemyAiPointer),Y

FinishType54To5BUpdate:
    RTS

CheckType54To5BActionPhase:
    LDY #EnemyAiPhaseOffset
    LDA (EnemyAiPointer),Y
    CMP #$14
    BCC FinishType54To5BUpdate
    LDY #ObjectXMotionOffset
    TYA
    STA (EnemyObjectPointer),Y
    BPL ReverseType54To5BDirection

UpdateType54To5BBlockedDirection:
    LDY #ObjectXMotionOffset
    LDA (EnemyObjectPointer),Y
    BNE FinishType54To5BBlockedDirection
    JSR CalculateEnemyForwardMapCoordinates
    JSR ConvertPixelCoordinatesToMapIndex
    TAX
    LDA RoomMap,X
    BPL FinishType54To5BBlockedDirection
    CMP #$F8
    BCC AllocateType54To5BLinkedPair

ReverseType54To5BDirection:
    LDY #ObjectActionOffset
    LDA #EnemyDirectionBit
    EOR (EnemyObjectPointer),Y
    AND #EnemyActionLinkMask
    STA (EnemyObjectPointer),Y

FinishType54To5BBlockedDirection:
    RTS

AllocateType54To5BLinkedPair:
    JSR FindFreeEnemySlotIndex
    BCC FinishType54To5BPairAllocation
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
    BCS ActivateType54To5BLinkedPair
    TYA
    STA (TempPointer00),Y
    BCC FinishType54To5BPairAllocation

ActivateType54To5BLinkedPair:
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

FinishType54To5BPairAllocation:
    RTS

RunType08To0BEnemyAi:
    LDA $87
    LSR A
    BCS DispatchType08To0BAction
    JSR CheckEnemyAiDeltaRange
    BCS DispatchType08To0BAction
    JSR CheckDanaHorizontalEnemyOverlap
    BCS DispatchType08To0BAction
    LDY #ObjectActionOffset
    LDA (EnemyObjectPointer),Y
    CMP #$0C
    BEQ DispatchType08To0BAction
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

DispatchType08To0BAction:
    JSR LoadEnemyActionSelector
    JSR JumpWithParams

Type08To0BActionHandlers:
    .addr UpdateType08To0BPhaseAction
    .addr UpdateType08To0BHorizontalOrientation
    .addr UpdateType08To0BVerticalOrientation
    .addr CollectType08To0BFairy
    .addr RunEnemyActionA55C, RunEnemyActionA55C
    .addr UpdateType08To0BMotion

CollectType08To0BFairy:
    LDY #EnemyAiPhaseOffset
    LDA (EnemyAiPointer),Y
    BNE CheckType08To0BFairyLifetime
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
    BCC StoreType08To0BFairyCount
    INC GdvFactor2
    JSR LoadCurrentEnemyPosition
    JSR SpawnAuxiliaryEffectAtCoordinates
    JSR AwardExtraLifeFromMapTile
    LDX #$00
    LDA #ExtraLifeEnemyInteractionThread

StoreType08To0BFairyCount:
    STX FairiesCollected
    JSR StartThread
    LDY #EnemyAiPhaseOffset
    LDA (EnemyObjectPointer),Y
    CMP #$1C
    BNE StartType08To0BMapInteraction

FinishType08To0BFairyUpdate:
    RTS

CheckType08To0BFairyLifetime:
    CMP #$12
    BCC FinishType08To0BFairyUpdate
    JMP DeactivateCurrentEnemy

StartType08To0BMapInteraction:
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

UpdateType08To0BMotion:
    LDY #ObjectXMotionOffset
    LDA (EnemyObjectPointer),Y
    ASL A
    ASL A
    LDA #$18
    BCC StoreType08To0BAction
    ADC #$00

StoreType08To0BAction:
    LDY #ObjectActionOffset
    STA (EnemyObjectPointer),Y
    LDY #EnemyAiPhaseOffset
    LDA (EnemyAiPointer),Y
    BNE ApplyType08To0BMotionCorrection
    RTS

ApplyType08To0BMotionCorrection:
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
    BPL SelectType08To0BVerticalAdjustment
    INX

SelectType08To0BVerticalAdjustment:
    LDA TempPointer02
    CLC
    ADC Type08To0BVerticalAdjustments,X
    LDX TempPointer00
    STA TempPointer02
    LDY #EnemyAiVerticalDeltaOffset
    EOR (EnemyAiPointer),Y
    BPL NormalizeType08To0BVerticalDelta
    INX

NormalizeType08To0BVerticalDelta:
    LDA TempPointer02
    BPL CompareType08To0BVerticalLimit
    EOR #$FF

CompareType08To0BVerticalLimit:
    CMP Type08To0BVerticalLimits,X
    BCC StoreType08To0BVerticalMotion
    ASL TempPointer00 + 1
    LDA TempPointer02
    ASL A
    ROR TempPointer00 + 1

StoreType08To0BVerticalMotion:
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
    BPL SelectType08To0BHorizontalAdjustment
    INX

SelectType08To0BHorizontalAdjustment:
    CLC
    LDA TempPointer02
    ADC Type08To0BHorizontalAdjustments,X
    STA TempPointer02
    LDX TempPointer00
    LDY #EnemyAiHorizontalDeltaOffset
    EOR (EnemyAiPointer),Y
    BPL NormalizeType08To0BHorizontalDelta
    INX

NormalizeType08To0BHorizontalDelta:
    LDA TempPointer02
    BPL CompareType08To0BHorizontalLimit
    EOR #$FF

CompareType08To0BHorizontalLimit:
    CMP Type08To0BHorizontalLimits,X
    BCC StoreType08To0BHorizontalMotion
    LDA #$80
    EOR TempPointer02
    ASL TempPointer00 + 1
    AND #$80
    ROR A
    STA TempPointer00 + 1

StoreType08To0BHorizontalMotion:
    LDY #ObjectXMotionOffset
    LDA TempPointer02
    LSR A
    STA (EnemyObjectPointer),Y
    LDY #EnemyAiFirstLinkedSlotOffset
    LDA TempPointer00 + 1
    STA (EnemyAiPointer),Y
    RTS

Type08To0BVerticalAdjustments:
    .byte $FC, $04, $FA, $06

Type08To0BVerticalLimits:
    .byte $40, $20, $60, $30

Type08To0BHorizontalAdjustments:
    .byte $04, $FC, $06, $FA

Type08To0BHorizontalLimits:
    .byte $40, $20, $60, $30
