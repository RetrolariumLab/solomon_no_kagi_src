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
