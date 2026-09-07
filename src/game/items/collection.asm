; Dana-centered RoomMap interaction classification and item dispatch

.segment "PRG_ITEM_COLLISION"

DanaItemInteractionStateLimit = DanaCastActionBase
DanaItemInteractionCenterOffset = $08
FirstInventoryItemTile = RoomMapKeyIdentity
FirstVisualInventoryItemTile = RoomMapFirstModifiableItemIdentity
IgnoredMapTile = RoomMapEmptyIdentity
FirstBonusMapTile = RoomMapFirstBonusItemIdentity
FirstExtraLifeMapTile = RoomMapFirstExtraLifeIdentity
MapTileInteractionLimit = RoomMapItemInteractionLimit
BonusItemGroupSize = $03
NoItemInteractionThread = $00
InventoryItemInteractionThread = $40
ExtraLifeInteractionThread = $41
EnemyItemInteractionThread = $42
ExtraLifeEnemyInteractionThread = $43
ItemInteractionSound = $0D
ExtraLifeSound = $06

ItemInteractionThreadCode = $02

ReturnFromHudOrItemUpdate:
    RTS

; The three bytes are PPU data. Their accidental decoding as JSR $4760 in a
; linear disassembly is not an executable entry point
ScoreDisplayPpuCommandHeader:
    PpuUpdateCommand $2060, PpuUpdateLiteral, 8

CheckDanaMapTileInteraction:
    LDA DanaObject + ObjectActionOffset
    CMP #DanaItemInteractionStateLimit
    BCS ReturnFromHudOrItemUpdate
    LDA DanaYPosition
    ADC #DanaItemInteractionCenterOffset
    STA CoordinateY
    LDA DanaXPosition
    ADC #DanaItemInteractionCenterOffset
    STA CoordinateX
    JSR ConvertPixelCoordinatesToMapIndex
    LDA #NoItemInteractionThread
    STA ItemInteractionThreadCode
    LDA RoomMap,X
    JSR ClassifyDanaMapTileInteraction
    LDA ItemInteractionThreadCode
    BEQ ReturnFromHudOrItemUpdate
    JMP StartThread

ClassifyDanaMapTileInteraction:
    CMP #MapTileInteractionLimit
    BCS FinishMapTileInteraction
    CMP #IgnoredMapTile
    BEQ FinishMapTileInteraction
    CMP #FirstInventoryItemTile
    BCC FinishMapTileInteraction
    CMP #FirstBonusMapTile
    BCC DispatchInventoryItemInteraction
    TAX
    LDA $87
    LSR A
    BCS FinishMapTileInteraction
    LDA #InventoryItemInteractionThread
    STA ItemInteractionThreadCode
    TXA
    JSR SpawnAuxiliaryEffectAtMapCell
    CMP #FirstExtraLifeMapTile
    BCS CheckBonusItemExtraLifeScore
    LDY #ItemInteractionSound
    JSR AddSoundEffect
    SBC #FirstBonusMapTile - 1
    LDX #$FF

SelectBonusItemScore:
    SBC #BonusItemGroupSize
    INX
    BCS SelectBonusItemScore
    ADC #BonusItemGroupSize
    TAY
    LDA ItemBonusScoreDigitIndices,X
    TAX
    LDA ItemBonusScoreAmounts,Y
    JMP AddScoreByAAtDigitX

CheckBonusItemExtraLifeScore:
    BNE AwardExtraLifeFromMapTile
    LDX #$02
    LDA #$05
    JSR AddScoreByAAtDigitX

AwardExtraLifeFromMapTile:
    LDY #ExtraLifeSound
    JSR AddSoundEffect
    INC RemainingLives
    LDA #$00
    STA AuxiliaryObject + ObjectYMotionOffset
    INC ExtraLivesAcquiredTotal
    LDA #ExtraLifeInteractionThread
    STA ItemInteractionThreadCode

FinishMapTileInteraction:
    RTS

DispatchInventoryItemInteraction:
    CMP #FirstVisualInventoryItemTile
    BCC QueueInventoryItemInteraction
    TAY
    LDA $87
    LSR A
    TYA
    BCC SpawnInventoryItemEffect
    RTS

SpawnInventoryItemEffect:
    JSR SpawnAuxiliaryEffectAtMapCell

QueueInventoryItemInteraction:
    LDY #InventoryItemInteractionThread
    STY ItemInteractionThreadCode
    LDY #ItemInteractionSound
    JSR AddSoundEffect
; Carry is clear here, so subtracting 5 converts map tiles $06-$24 to
; selectors $00-$1E. Only $00-$1C have table entries; stock room streams do
; not contain the overflow values $23-$24
    SBC #FirstInventoryItemTile - 1
    JSR JumpWithParams

; Context-four lifecycles for map and enemy-originated item effects

.segment "PRG_ITEM_PRESENTATION"

ShortItemPresentationDuration = $12
ExtraLifePresentationDuration = $40
ExtraLifeItemYMotion = $C0
EmptyRoomMapTile = RoomMapEmptyIdentity
ItemPresentationThreadIndex = $04
ItemMapUpdateInProgressFlag = $01

RunExtraLifeMapItemPresentation:
    JSR ClearAuxiliaryItemMapCell

RunExtraLifeEnemyItemPresentation:
    LDA #ExtraLifeItemYMotion
    STA AuxiliaryObject + ObjectYMotionOffset
    JSR RefreshGameplayHud
    LDA #ExtraLifePresentationDuration
    BNE WaitForItemPresentation

RunMapItemPresentation:
    JSR ClearAuxiliaryItemMapCell

RunEnemyItemPresentation:
    JSR RefreshGameplayHud
    LDA #ShortItemPresentationDuration

WaitForItemPresentation:
    LDX #$00
    STX ItemEffectFrameCounter
    LDX #ItemEffectFrameCounter
    JSR WaitForZeroPageCounterAboveThreshold
    LDA #$00
    STA AuxiliaryObject + ObjectStateOffset
    LDA #ItemPresentationThreadIndex
; Stopping the current context replaces its stack, so this call does not
; return into the adjacent helper during normal execution
    JSR StopThread

ClearAuxiliaryItemMapCell:
    LDA #ItemMapUpdateInProgressFlag
    ORA $87
    STA $87
    LDA AuxiliaryYPosition
    STA CoordinateY
    LDA AuxiliaryXPosition
    STA CoordinateX
    JSR ConvertPixelCoordinatesToMapIndex
    LDA #EmptyRoomMapTile
    STA RoomMap,X
    STX RoomMapUpdateIndex
    STA RoomMapUpdateTile
    JSR BuildAndPublishRoomMapCellUpdate
    LSR $87
    ASL $87
    RTS

.assert * - RunExtraLifeMapItemPresentation = $4E, error, "item presentation size changed"

; Red-bottle effect that marks every eligible enemy for retirement

.segment "PRG_RED_BOTTLE_ITEM"

RedBottleEnemyStateMinimum = $C0
RedBottleEnemyTypeBase = $50
RedBottleEnemyTypeCount = $18
RedBottleThreadCode = $50

ApplyRedBottleKillAllEnemiesItem:
    LDX #EnemyObjectCount - 1

CheckNextRedBottleEnemy:
    TXA
    JSR LoadEnemyObjectPointer
    LDY #ObjectStateOffset
    LDA (TempPointer00),Y
    CMP #RedBottleEnemyStateMinimum
    BCC AdvanceRedBottleEnemy
    INY
    LDA (TempPointer00),Y
    SBC #RedBottleEnemyTypeBase
    CMP #RedBottleEnemyTypeCount
    BCS AdvanceRedBottleEnemy
    TYA
    DEY
    ORA (TempPointer00),Y
    STA (TempPointer00),Y
    STY ItemInteractionThreadCode

AdvanceRedBottleEnemy:
    DEX
    BPL CheckNextRedBottleEnemy
    LDA ItemInteractionThreadCode
    BNE FinishRedBottleItem
    LDA #RedBottleThreadCode
    JSR StartThread
    LDA #InventoryItemInteractionThread
    STA ItemInteractionThreadCode

FinishRedBottleItem:
    RTS

; Context 5 converts every enemy marked for retirement into a drop object

.segment "PRG_ENEMY_DROP_PROCESSING"

DefeatedEnemyIndex = $02
EnemyDropTableOffset = $03
EnemyAiSecondaryStateOffset = $01
EnemyDropInactiveMarker = $80
EnemyDropObjectState = $C6
EnemyDropObjectType = $14
EnemyDropSoundEffect = $09
EnemyDropThreadIndex = $05

ProcessDefeatedEnemyDrops:
    LDA #EnemyObjectCount - 1
    STA DefeatedEnemyIndex

CheckNextDefeatedEnemy:
    LDA DefeatedEnemyIndex
    JSR LoadEnemyObjectPointer
    LDY #ObjectStateOffset
    LDA (TempPointer00),Y
    BPL AdvanceDefeatedEnemyScan
    LSR A
    BCC AdvanceDefeatedEnemyScan
    INY
    LDA (TempPointer00),Y
    LSR A
    LSR A
    SEC
    SBC #$06
    BCC AdvanceDefeatedEnemyScan
    TAX
    LDA EnemyDropTableOffsetsByTypeGroup,X
    STA EnemyDropTableOffset
    LDA DefeatedEnemyIndex
    JSR LoadEnemyAiPointer
    LDA #$00
    STA (TempPointer00),Y
    TAY
    LDA (TempPointer00),Y
    LSR A
    BCC CheckSecondLinkedEnemy
    PHA
    LDY #EnemyAiFirstLinkedSlotOffset
    LDA (TempPointer00),Y
    JSR DeactivateEnemySlot
    PLA

CheckSecondLinkedEnemy:
    LSR A
    BCC SelectEnemyDrop
    LDY #EnemyAiSecondLinkedSlotOffset
    LDA (TempPointer00),Y
    JSR DeactivateEnemySlot

SelectEnemyDrop:
    LDA #EnemyDropInactiveMarker
    STA (TempPointer00),Y
    JSR AdvanceRandomState
    AND #$07
    CLC
    ADC EnemyDropTableOffset
    TAX
    LDA EnemyDropTypeTable,X
    LDY #EnemyAiFirstLinkedSlotOffset
    STA (TempPointer00),Y
    LDA DefeatedEnemyIndex
    JSR LoadEnemyObjectPointer
    LDA #EnemyDropObjectState
    STA SpawnYPosition
    LDA #EnemyDropObjectType
    STA SpawnXPosition
    LDA #$00
    JSR InitializeObjectStateHeader

AdvanceDefeatedEnemyScan:
    DEC DefeatedEnemyIndex
    BPL CheckNextDefeatedEnemy
    LDY #EnemyDropSoundEffect
    JSR AddSoundEffect
    LDA #EnemyDropThreadIndex
    JSR StopThread

EnemyDropTableOffsetsByTypeGroup:
    .byte $00, $00, $00, $48, $08, $08, $18, $10, $18, $10, $18
    .byte $10, $18, $10, $20, $20, $20, $28, $28, $28, $30, $30, $38, $38, $40, $40, $00

EnemyDropTypeTable:
    .byte $00, $00, $00, $00, $00, $00, $00, $00, $04, $08, $08, $08, $09, $09, $09, $09
    .byte $04, $08, $08, $08, $09, $09, $09, $0A, $08, $08, $09, $09, $09, $09, $0A, $0A
    .byte $04, $0B, $0B, $0B, $0B, $0C, $0C, $0C, $0B, $0B, $0C, $0C, $0C, $0D, $0D, $02
    .byte $0B, $0B, $0B, $0C, $0C, $03, $03, $06, $04, $0B, $0C, $0C, $0D, $0D, $02, $02
    .byte $0E, $0E, $0E, $0E, $0F, $05, $05, $05, $0E, $0E, $0E, $0F, $0F, $0F, $05, $05

.assert EnemyDropTypeTable - EnemyDropTableOffsetsByTypeGroup = $1B, error, "unexpected enemy drop offset table size"
.assert * - EnemyDropTypeTable = $50, error, "unexpected enemy drop type table size"
.assert * - ProcessDefeatedEnemyDrops = $E3, error, "unexpected enemy drop processing size"

; Shared deterministic state mixer used for room placement and enemy rewards

.segment "PRG_RANDOM_STATE"

RandomMirrorStateSnapshot = $3E
RandomSeedWordLo = $04
RandomSeedWordHi = $05
RandomAccumulatorLo = $06
RandomAccumulatorHi = $07
RandomAccumulatorHighMask = $7F
RandomSeedMixRoundCount = 8

AdvanceRandomState:
    LDA DemonMirrorSpawnState
    CMP RandomMirrorStateSnapshot
    BEQ MixRandomState
    STA RandomMirrorStateSnapshot
    LDA DemonMirrorSpawnTimerLo
    STA RandomStateLo
    LDA GameplayFrameCounters
    STA RandomStateHi

MixRandomState:
    LDA RandomStateLo
    ORA #$01
    STA RandomSeedWordLo
    LDA RandomStateHi
    STA RandomSeedWordHi
    LDA #$00
    STA RandomAccumulatorLo
    STA RandomAccumulatorHi
    LDY #$7C
    JSR AccumulateRandomSeedMask
    LDY #$FC
    JSR AccumulateRandomSeedMask
    LDA RandomAccumulatorHi
    AND #RandomAccumulatorHighMask
    STA RandomStateHi
    LDA RandomAccumulatorLo
    STA RandomStateLo
    LSR A
    RTS

AccumulateRandomSeedMask:
    LDX #RandomSeedMixRoundCount

MixNextRandomSeedBit:
    TYA
    LSR A
    TAY
    BCS ShiftRandomSeedWord
    LDA RandomAccumulatorLo
    ADC RandomSeedWordLo
    STA RandomAccumulatorLo
    LDA RandomAccumulatorHi
    ADC RandomSeedWordHi
    STA RandomAccumulatorHi

ShiftRandomSeedWord:
    LSR RandomSeedWordHi
    ROR RandomSeedWordLo
    DEX
    BNE MixNextRandomSeedBit
    RTS

.assert AccumulateRandomSeedMask - AdvanceRandomState = $3E, error, "unexpected random mixer helper offset"
.assert * - AdvanceRandomState = $59, error, "unexpected random state routine size"

; Flag-only handlers for item types $16-$1C

.segment "PRG_SPECIAL_ITEM_FLAGS"

GoldenWingsRoomSkipFlag = $40
PageOfTimeEndingFlag = $40
PageOfSpaceEndingFlag = $80
PageOfSpaceRoomThreshold = $1E
ConstellationCollectedFlag = $08

ApplyGoldenWingsItem:
    LDA #GoldenWingsRoomSkipFlag
    ORA GameplayFlags
    STA GameplayFlags
    RTS

ApplySolomonPageItem:
    LDA CurrentRoomIndex
    CMP #PageOfSpaceRoomThreshold
    LDA #PageOfTimeEndingFlag
    BCC StoreSolomonPageEndingFlag
    ASL A

StoreSolomonPageEndingFlag:
    ORA GameStateFlags
    STA GameStateFlags
    RTS

ApplySolomonSealItem:
    INC SolomonSealCount
    LDA CollectedSolomonSealFlags
    ORA CurrentRoomSolomonSealFlag
    STA CollectedSolomonSealFlags
    RTS

ApplyConstellationSymbolItem:
    LDA GameStateFlags
    ORA #ConstellationCollectedFlag
    STA GameStateFlags
    RTS
