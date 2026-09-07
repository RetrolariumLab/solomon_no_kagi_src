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

; Early enemy AI families and collision rewards

.segment "PRG_EARLY_ENEMY_AI"

RunType00To03EnemyAi:
    LDY #$03
    LDA ($2E),Y
    BNE RunType00To03Movement
    LDY #$01
    LDA ($2C),Y
    CMP #$2A
    BCC UpdateType00To03Collision
    LDY #$06
    LDA ($2C),Y
    BEQ DeactivateType00To03Enemy
    LDY #$03
    STA ($2E),Y
    LDA #$00
    STA ($2C),Y
    DEY
    STA ($2C),Y
    BPL UpdateType00To03Collision

RunType00To03Movement:
    LDA $87
    LSR A
    BCS CheckType00To03ActionPhase
    JSR CheckEnemyAiDeltaRange
    BCS CheckType00To03ActionPhase
    JSR CheckDanaHorizontalEnemyOverlap
    BCC HandleEnemyCollisionReward

CheckType00To03ActionPhase:
    LDY #$03
    LDA ($2C),Y
    CMP #$04
    BCC UpdateType00To03Collision

DeactivateType00To03Enemy:
    JMP DeactivateCurrentEnemy

UpdateType00To03Collision:
    JSR SampleCurrentEnemyRoomMapCollision
    LDA $07
    TAX
    AND #$0C
    BNE ClassifyType00To03Collision
    LDY #$00
    LDA #$01
    ORA ($2C),Y
    STA ($2C),Y

ClassifyType00To03Collision:
    TXA
    AND #$0F
    BEQ StopType00To03VerticalMotion
    CMP #$0F
    BNE ResolveType00To03Collision

StopType00To03VerticalMotion:
    LDY #$05
    LDA #$80
    ORA ($2E),Y
    STA ($2E),Y
    RTS

ResolveType00To03Collision:
    TXA
    AND #$03
    CMP #$03
    BEQ StopType00To03VerticalMotion
    TXA
    AND #$0C
    BEQ SelectType00To03HorizontalMotion
    TXA
    AND #$03
    BNE SelectType00To03HorizontalMotion
    LDY #$00
    LDA ($2C),Y
    LSR A
    BCC SelectType00To03HorizontalMotion
    TXA
    AND #$03
    BEQ ClearType00To03Motion
    TXA
    AND #$0C
    CMP #$0C
    BNE SelectType00To03HorizontalMotion

ClearType00To03Motion:
    LDY #$07
    LDA ($2E),Y
    AND #$0F
    CMP #$08
    BCS StopType00To03VerticalMotion
    INY
    LDA #$00
    STA ($2E),Y
    LDY #$05
    STA ($2E),Y
    RTS

SelectType00To03HorizontalMotion:
    TXA
    LDY #$08
    AND #$06
    CMP #$06
    BNE UseSlowType00To03HorizontalMotion
    LDA #$74
    BPL StoreType00To03HorizontalMotion

UseSlowType00To03HorizontalMotion:
    LDA #$0C

StoreType00To03HorizontalMotion:
    STA ($2E),Y
    RTS

RunEnemyActionA55C:
    RTS

HandleEnemyCollisionReward:
    JSR LoadCurrentEnemyPosition
    JSR SpawnAuxiliaryEffectAtCoordinates
    LDY #$0D
    JSR AddSoundEffect
    LDY #$03
    LDA ($2E),Y
    CMP #$08
    BCS AwardEnemyCollisionScore
    SBC #$01
    CMP #$04
    BCC DispatchEnemyCollisionInventoryReward
    JSR AwardExtraLifeFromMapTile
    LDA #ExtraLifeEnemyInteractionThread
    JSR StartThread
    JMP DeactivateCurrentEnemy

DispatchEnemyCollisionInventoryReward:
    JSR DispatchEnemyCollisionInventoryItem

QueueEnemyItemPresentation:
    LDA #EnemyItemInteractionThread
    JSR StartThread
    JMP DeactivateCurrentEnemy

AwardEnemyCollisionScore:
    SBC #$08
    LDX #$06

SelectEnemyCollisionScoreDigit:
    DEX
    SBC #$03
    BCS SelectEnemyCollisionScoreDigit
    ADC #$03
    TAY
    LDA $A5A0,Y
    JSR AddScoreByAAtDigitX
    BMI QueueEnemyItemPresentation

EnemyCollisionScoreAmounts:
    .byte $01, $02, $05

DispatchEnemyCollisionInventoryItem:
    JSR JumpWithParams

EnemyCollisionInventoryHandlers:
    .addr UpgradeSmallFireballInventory
    .addr IncreaseInventorySlotLimit, ApplyRedTzoItem, QueueFairyItem

UpgradeSmallFireballInventory:
    LDA InventorySlotCount
    STA $03
    LDX #$01
    LDA #$40
    STA $01

ScanPreviousFireballInventoryByte:
    LDY #$04

ScanPreviousFireballInventorySlot:
    LDA $01
    AND InventorySlotsHigh,X
    CMP $01
    BEQ UpgradeSmallFireballSlot
    DEC $03
    BEQ FinishSmallFireballUpgrade
    LSR $01
    LSR $01
    DEY
    BNE ScanPreviousFireballInventorySlot
    DEX
    BPL ScanPreviousFireballInventoryByte

FinishSmallFireballUpgrade:
    RTS

UpgradeSmallFireballSlot:
    ASL A
    ORA $01
    EOR InventorySlotsHigh,X
    STA InventorySlotsHigh,X
    RTS

RunType04To07EnemyAi:
    LDY #$03
    LDA ($2C),Y
    CMP #$07
    BCC RunType04To07Movement
    JMP DeactivateCurrentEnemy

RunType04To07Movement:
    JSR CheckEnemyAiDeltaRange
    BCS UpdateType04To07Collision
    JSR CheckDanaHorizontalEnemyOverlap
    BCC ReplaceActiveEnemiesAfterType04To07Collision

UpdateType04To07Collision:
    JSR SampleCurrentEnemyRoomMapCollision
    LDA $07
    TAX
    BEQ HandleType04To07OpenPath
    CMP #$0F
    BNE HandleType04To07BlockedPath

HandleType04To07OpenPath:
    LDY #$08
    LDA ($2E),Y
    BNE UpdateType04To07VerticalMotion
    JSR AdvanceRandomState
    LSR A
    LDA #$0C
    BCS StoreRandomType04To07HorizontalMotion
    LDA #$74

StoreRandomType04To07HorizontalMotion:
    LDY #$08
    STA ($2E),Y

UpdateType04To07VerticalMotion:
    LDY #$05
    LDA ($2E),Y
    BNE SelectType04To07Action
    TAX
    LDA #$80
    ORA ($2E),Y
    STA ($2E),Y
    TXA

SelectType04To07Action:
    LDX #$00
    ASL A
    BMI StoreType04To07Action
    LDX #$02

StoreType04To07Action:
    LDY #$03
    TXA
    STA ($2E),Y
    RTS

HandleType04To07BlockedPath:
    LDY #$05
    AND #$0C
    BNE UseNegativeType04To07VerticalMotion
    LDA ($2E),Y
    AND #$40
    BEQ SelectType04To07HorizontalMotion
    LDA #$80
    STA ($2E),Y
    BMI StoreType04To07VerticalMotion

UseNegativeType04To07VerticalMotion:
    LDA #$C0

StoreType04To07VerticalMotion:
    STA ($2E),Y

SelectType04To07HorizontalMotion:
    LDY #$08
    TXA
    AND #$09
    CMP #$09
    BNE CheckAlternateType04To07HorizontalMotion
    LDA #$0C
    BPL StoreType04To07HorizontalMotion

CheckAlternateType04To07HorizontalMotion:
    TXA
    AND #$06
    CMP #$06
    BNE FinishType04To07Movement
    LDA #$7A

StoreType04To07HorizontalMotion:
    STA ($2E),Y
    LDA #$00
    LDY #$05
    STA ($2E),Y

FinishType04To07Movement:
    RTS

ReplaceActiveEnemiesAfterType04To07Collision:
    LDX #$10

CheckNextEnemyForType04To07Replacement:
    TXA
    JSR LoadEnemyObjectPointer
    LDY #$00
    LDA ($00),Y
    BPL AdvanceType04To07ReplacementScan
    LDY #$03

CopyType04To07ReplacementHeader:
    LDA $A688,Y
    STA ($00),Y
    DEY
    BPL CopyType04To07ReplacementHeader
    TXA
    JSR LoadEnemyAiPointer
    LDY #$00
    TYA
    INY
    STA ($00),Y

AdvanceType04To07ReplacementScan:
    DEX
    BPL CheckNextEnemyForType04To07Replacement
    JMP DeactivateCurrentEnemy

Type04To07ReplacementHeader:
    .byte $E2, $1C, $FF, $00
