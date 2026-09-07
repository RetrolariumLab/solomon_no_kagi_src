; Room-map interactions shared by Dana magic and object behaviors

.segment "PRG_MAP_INTERACTIONS"

MapInteractionObjectState = $C6
MapInteractionObjectVariant = $04

ApplyMapTileInteractionToObject:
    STY MapInteractionMapIndex
    CMP #RoomMapImmutableTileMinimum
    BCS ClassifyMapInteractionTile
    AND #RoomMapTileIdentityMask
    STA RoomMap,Y

ClassifyMapInteractionTile:
    TAX
    JSR ConvertMapIndexToPixelCoordinates
    TXA
    BPL StoreMapInteractionCoordinates
    LDA #$02
    AND MapInteractionDirection
    BEQ OffsetMapInteractionX
    CLC
    LDA #$F8
    ADC MapInteractionY
    STA MapInteractionY
    BCS StoreMapInteractionCoordinates

OffsetMapInteractionX:
    LDA MapInteractionDirection
    ROR A
    LDY #$08
    BCS SelectMapInteractionXOffset
    LDY #$F7

SelectMapInteractionXOffset:
    TYA
    ADC MapInteractionX
    STA MapInteractionX

StoreMapInteractionCoordinates:
    LDY #ObjectYPositionOffset
    LDA MapInteractionY
    STA (MapInteractionObjectPointer),Y
    LDY #ObjectXPositionOffset
    LDA MapInteractionX
    STA (MapInteractionObjectPointer),Y
    LDA #MapInteractionObjectState
    STA MapInteractionY
    LDA #MapInteractionObjectVariant
    STA MapInteractionX
    CPX #RoomMapSolidBit
    LDA #$01
    BCC InitializeMapInteractionObject
    LDA #$04
    ORA MapInteractionDirection

InitializeMapInteractionObject:
    JSR InitializeObjectStateHeader
    LDY MapInteractionMapIndex
    STX MapInteractionMapIndex
    TXA
    BMI FinishMapInteraction
    STY RoomMapUpdateIndex
    STY DanaObject + ObjectCachedTypeOffset
    JMP BuildAndPublishRoomMapCellUpdate

FinishMapInteraction:
    RTS

TryCreateBlockAtMapCell:
    JSR ConvertMapIndexToPixelCoordinates
    STY MapInteractionMapIndex
    LDA MapInteractionY
    LDY #ObjectYPositionOffset
    STA (MapInteractionObjectPointer),Y
    LDA MapInteractionX
    LDY #ObjectXPositionOffset
    STA (MapInteractionObjectPointer),Y
    LDY MapInteractionMapIndex
    LDA RoomMap,Y
    CMP #RoomMapEmptyIdentity
    BEQ CheckBlockCreationOccupancy
    CMP #RoomMapItemInteractionLimit
    BCS CheckBlockCreationOccupancy
    JMP AdvanceRoomMapTileVariant

CheckBlockCreationOccupancy:
    LDA #<FireballObject
    STA OverlapObjectPointer
    LDA #>FireballObject
    STA OverlapObjectPointer + 1
    JSR CheckCoordinateOverlapWithObject
    BCC PositionBlockSparkFromFireball
    LDX #EnemyObjectCount
    LDA #<EnemyObjects
    STA OverlapObjectPointer
    LDA #>EnemyObjects
    STA OverlapObjectPointer + 1

CheckNextEnemyForBlockOverlap:
    JSR CheckCoordinateOverlapWithObject
    BCC HandleEnemyBlockOverlap
    LDA #ObjectRecordSize - 1
    ADC OverlapObjectPointer
    STA OverlapObjectPointer
    LDA #$00
    ADC OverlapObjectPointer + 1
    STA OverlapObjectPointer + 1
    DEX
    BNE CheckNextEnemyForBlockOverlap
    BEQ CreateBlockInRoomMap

HandleEnemyBlockOverlap:
    LDY #ObjectTypeOffset
    LDA (OverlapObjectPointer),Y
    BPL PositionBlockSparkFromEnemy
    DEY
    LDA #$08
    ORA (OverlapObjectPointer),Y
    STA (OverlapObjectPointer),Y
    BMI FinishBlockedBlockCreation

PositionBlockSparkFromEnemy:
    LDY #ObjectYPositionOffset
    LDA (OverlapObjectPointer),Y
    STA (MapInteractionObjectPointer),Y
    LDY #ObjectXPositionOffset
    ROR MapInteractionDirection
    LDA #$FC
    BCC SelectBlockSparkDirection
    LDA #$03

SelectBlockSparkDirection:
    TAX
    ADC (OverlapObjectPointer),Y
    STA (MapInteractionObjectPointer),Y
    LDA #MapInteractionObjectVariant
    STA MapInteractionX
    LDA #MapInteractionObjectState
    STA MapInteractionY
    TXA
    ASL A
    LDA #$01
    ROL A

InitializeBlockSpark:
    JSR InitializeObjectStateHeader

FinishBlockedBlockCreation:
    RTS

PositionBlockSparkFromFireball:
    LDX #$02
    LDY #ObjectYPositionOffset
    BNE CopyBlockSparkCoordinate

SelectBlockSparkXCoordinate:
    LDY #ObjectXPositionOffset

CopyBlockSparkCoordinate:
    LDA (OverlapObjectPointer),Y
    STA (MapInteractionObjectPointer),Y
    DEX
    BNE SelectBlockSparkXCoordinate

InitializeBlockedBlockSpark:
    LDA #MapInteractionObjectState
    STA MapInteractionY
    LDA #MapInteractionObjectVariant
    STA MapInteractionX
    LDA #$08
    BNE InitializeBlockSpark

CreateBlockInRoomMap:
    LDY MapInteractionMapIndex
    LDA RoomMap,Y
    CMP #RoomMapDecorationBit
    BCC NormalizeBlockSourceTile
    SEC
    SBC #RoomMapDecorationBit

NormalizeBlockSourceTile:
    ORA #RoomMapSolidBit
    STA RoomMap,Y
    LDA #MapInteractionObjectVariant
    STA MapInteractionX
    LDA #MapInteractionObjectState
    STA MapInteractionY
    LDA #$00
    JMP InitializeObjectStateHeader

AdvanceRoomMapTileVariant:
    CMP #$08
    BCC InitializeBlockedBlockSpark
    CMP #$10
    BCS FinishObjectStateHeaderInitialization
    TAX
    AND #$0C
    STA MapInteractionMapIndex
    INX
    TXA
    AND #$03
    ORA MapInteractionMapIndex
    STA RoomMap,Y
    STA RoomMapUpdateTile
    STY RoomMapUpdateIndex
    JMP BuildAndPublishRoomMapCellUpdate

InitializeObjectStateHeader:
    LDY #ObjectActionOffset
    CMP #$00
    BMI SkipObjectActionByte
    STA (MapInteractionObjectPointer),Y

SkipObjectActionByte:
    DEY
    LDA #$FF
    STA (MapInteractionObjectPointer),Y
    DEY
    LDA MapInteractionX
    STA (MapInteractionObjectPointer),Y
    DEY
    LDA MapInteractionY
    STA (MapInteractionObjectPointer),Y

FinishObjectStateHeaderInitialization:
    RTS
