; Decode the current room's enemy stream into runtime slots

.segment "PRG_ROOM_ENEMY_LOAD"

EnemyAiActiveFlag = $80
EnemySpawnLifetimeLowMask = $E0
EnemySpawnLifetimeHighMask = $1F

LoadRoomEnemies:
    LDX CurrentRoomIndex
    LDA RoomEnemyPointerLowTable,X
    STA RoomEnemyPointer
    LDA RoomEnemyPointerHighTable,X
    STA RoomEnemyPointer + 1
    LDY #$00
    LDA (RoomEnemyPointer),Y
    INY
    TAX
    AND #EnemySpawnLifetimeLowMask
    STA EnemySpawnLifetimeThresholdLo
    TXA
    AND #EnemySpawnLifetimeHighMask
    STA EnemySpawnLifetimeThresholdHi

DecodeNextRoomEnemy:
    LDA (RoomEnemyPointer),Y
    BEQ FinishRoomEnemyLoad
    STA SpawnType
    INY
    STY RoomEnemyStreamOffset
    JSR FindFreeEnemySlotIndex
    STX SpawnSlotIndex
    LDA #EnemyAiActiveFlag
    STA (TempPointer04),Y
    LDY RoomEnemyStreamOffset
    LDA (RoomEnemyPointer),Y
    INC RoomEnemyStreamOffset
    STA MapCellIndex
    JSR ConvertMapIndexToPixelCoordinates
    JSR InitializeEnemy
    JSR ConfigureEnemyType
    LDY RoomEnemyStreamOffset
    BNE DecodeNextRoomEnemy

FinishRoomEnemyLoad:
    RTS

; Load room item metadata, Demon Mirror pointers, and the compressed item stream

.segment "PRG_ROOM_ITEM_DECODE"

RoomItemHeaderSize = $0A
RoomItemRuntimeClearCount = $0A
RoomItemRleBase = $C0
RoomItemTerminatorBase = $E0
RoomItemConstellationBit = $10
RoomItemChrBankMask = $0C
SpecialRoomIndex = $32
SpecialRoomRandomPositionMask = $1F
SpecialRoomPlacementCount = $10
ConstellationPatternSize = $18

LoadRoomItemsAndMetadata:
    LDX CurrentRoomIndex
    LDA RoomItemPointerLowTable,X
    STA RoomItemPointer
    LDA RoomItemPointerHighTable,X
    STA RoomItemPointer + 1
    LDY #$00
    STY RoomItemStreamOffset
    LDX #$00

ResolveNextDemonMirrorSchedule:
    LDY RoomItemStreamOffset
    LDA (RoomItemPointer),Y
    INC RoomItemStreamOffset
    TAY
    LDA DemonMirrorSchedulePointerLowTable,Y
    STA DemonMirrorSchedulePointers,X
    LDA DemonMirrorSchedulePointerHighTable,Y
    STA DemonMirrorSchedulePointers + 1,X
    INX
    INX
    CPX #$04
    BNE ResolveNextDemonMirrorSchedule
    LDX #$00

ResolveNextDemonMirrorEnemySet:
    LDY RoomItemStreamOffset
    LDA (RoomItemPointer),Y
    INC RoomItemStreamOffset
    TAY
    LDA DemonMirrorEnemySetPointerLowTable,Y
    STA DemonMirrorEnemySetPointers,X
    LDA DemonMirrorEnemySetPointerHighTable,Y
    STA DemonMirrorEnemySetPointers + 1,X
    INX
    INX
    CPX #$04
    BNE ResolveNextDemonMirrorEnemySet
    LDY RoomItemStreamOffset
    LDX #RoomItemRuntimeClearCount - 1
    LDA #$00

ClearRoomItemRuntimeByte:
    STA RoomItemRuntimeData + 1,X
    DEX
    BPL ClearRoomItemRuntimeByte
    LDA (RoomItemPointer),Y
    STA RoomKeyStatusAndTimerRate
    AND #$0F
    TAX
    LDA TimerDecrementSpeedTable,X
    STA TimerDecrementSpeed
    LDX #$01
    STX TimerDecrementStep
    STX TimerDigit10000
    DEX
    STX TimerWarningState
    TXA
    LDX #$03

ClearRoomTimerDigits:
    STA TimerFraction,X
    DEX
    BNE ClearRoomTimerDigits
    INY
    LDA (RoomItemPointer),Y
    INY
    TAX
    BEQ DecodeRoomKeyPosition
    LDA #RoomMapClosedDoorIdentity
    STA RoomDoorTile
    LDA #$20
    BIT GameplayFlags
    BEQ StoreRoomDoorTile
    LDA #RoomMapOpenDoorIdentity
    STA RoomDoorTile

StoreRoomDoorTile:
    LDA RoomDoorTile
    STA RoomMap,X

DecodeRoomKeyPosition:
    LDA (RoomItemPointer),Y
    BNE SelectRoomKeyTile
    LDA #RoomMapDeferredDoorIdentity
    BNE StoreRoomKeyTile

SelectRoomKeyTile:
    TAX
    LDA #$20
    BIT GameplayFlags
    BNE DecodeDemonMirrorPositions
    LDA #RoomMapKeyIdentity
    BIT RoomKeyStatusAndTimerRate
    BPL SelectAlternateKeyTile
    LDA #RoomMapHiddenKey

SelectAlternateKeyTile:
    BVC StoreRoomKeyTile
    LDA #RoomMapEmbeddedKey

StoreRoomKeyTile:
    STA RoomMap,X

DecodeDemonMirrorPositions:
    INY
    INY
    LDX #$00

PlaceNextDemonMirror:
    STX RoomItemStreamOffset
    LDA (RoomItemPointer),Y
    INY
    STA MapCellIndex
    TAX
    LDA #RoomMapDemonMirrorIdentity
    STA RoomMap,X
    JSR ConvertMapIndexToPixelCoordinates
    LDX RoomItemStreamOffset
    LDA CoordinateY
    STA DemonMirrorYPositions,X
    LDA CoordinateX
    STA DemonMirrorXPositions,X
    INX
    CPX #$02
    BNE PlaceNextDemonMirror
    LDA CurrentRoomIndex
    CMP #SpecialRoomIndex
    BNE BeginRoomItemStream
    JSR AdvanceRandomState
    AND #SpecialRoomRandomPositionMask
    TAX
    LDY #SpecialRoomPlacementCount - 1
    STY RoomItemStreamOffset

PlaceNextSpecialRoomItem:
    LDY RoomItemStreamOffset
    LDA SpecialRoomItemTypes,Y
    LDY SpecialRoomItemPositions,X
    STA RoomMap,Y
    DEX
    BPL ContinueSpecialRoomItems
    LDX #SpecialRoomRandomPositionMask

ContinueSpecialRoomItems:
    DEC RoomItemStreamOffset
    BPL PlaceNextSpecialRoomItem
    LDY #RoomItemHeaderSize

BeginRoomItemStream:
    LDA #$00
    STA RoomItemRuntimeData

DecodeNextRoomItemCommand:
    LDA (RoomItemPointer),Y
    INY
    CMP #RoomItemTerminatorBase
    BCS DecodeRoomItemTerminator
    CMP #RoomItemRleBase
    BCC DecodeSingleRoomItem
    SBC #RoomItemRleBase
    STA RoomItemRepeatCount
    LDA (RoomItemPointer),Y
    STA RoomItemScratch
    INY

StoreNextRepeatedRoomItem:
    LDA (RoomItemPointer),Y
    INY
    TAX
    LDA RoomItemScratch
    STA RoomMap,X
    DEC RoomItemRepeatCount
    BPL StoreNextRepeatedRoomItem
    BMI DecodeNextRoomItemCommand

DecodeSingleRoomItem:
    STA RoomItemScratch
    AND #RoomMapTileIdentityMask
    CMP #$2E
    BCC StoreSingleRoomItem
    LDA RoomStateFlags
    ROR A
    BCC StoreSingleRoomItem
    INY
    BNE DecodeNextRoomItemCommand

StoreSingleRoomItem:
    LDA (RoomItemPointer),Y
    INY
    TAX
    LDA RoomItemScratch
    STA RoomMap,X
    BNE DecodeNextRoomItemCommand

DecodeRoomItemTerminator:
    AND #$1F
    TAX
    AND #RoomItemChrBankMask
    LSR A
    LSR A
    STA ChrBankRequest
    TXA
    AND #RoomItemConstellationBit
    BNE DecodeConstellationMetadata
    STA ConstellationPosition
    BEQ FinishRoomItemDecode

DecodeConstellationMetadata:
    TXA
    AND #$0F
    TAX
    LDA ConstellationTileLowBits,X
    STA RoomItemScratch
    TXA
    AND #$03
    TAX
    INX
    STX RoomItemRepeatCount
    TXA
    ASL A
    CLC
    ADC RoomItemRepeatCount
    ASL A
    ASL A
    ASL A
    TAX
    DEX
    LDA (RoomItemPointer),Y
    STA ConstellationPosition
    LDY #ConstellationPatternSize - 1

CopyNextConstellationByte:
    TYA
    AND #$03
    BNE CopyRawConstellationByte
    LDA ConstellationTilePatterns,X
    AND #$FC
    ORA RoomItemScratch
    BNE StoreConstellationByte

CopyRawConstellationByte:
    LDA ConstellationTilePatterns,X

StoreConstellationByte:
    STA ConstellationPattern,Y
    DEX
    DEY
    BPL CopyNextConstellationByte

FinishRoomItemDecode:
    LDA #$01
    ORA RoomStateFlags
    STA RoomStateFlags
    RTS

; Initialize the runtime room map and expand its two 16x12 block bitplanes

.segment "PRG_ROOM_BLOCK_DECODE"

RoomBlockBytesPerPlane = $18
RoomBlockBytesPerRoom = RoomBlockBytesPerPlane * 2
BitsPerBlockByte = $08

InitializeRoomBlockMap:
    LDX #RoomMapStorageSize
    LDA #RoomMapEmptyIdentity

FillRoomMapInterior:
    STA RoomMap - 1,X
    DEX
    BNE FillRoomMapInterior
    LDA #RoomMapWhiteBlock
    LDX #RoomMapWidth - 1

FillRoomMapTopBoundary:
    STA RoomMap,X
    DEX
    BPL FillRoomMapTopBoundary
    LDX #RoomMapWidth

FillRoomMapBottomBoundary:
    STA RoomMapBottomBoundary - 1,X
    DEX
    BNE FillRoomMapBottomBoundary
    STX RoomBlockDataPointer + 1
    LDA CurrentRoomIndex
    STA RoomBlockDataPointer
    ASL A
    CLC
    ADC RoomBlockDataPointer
    STA RoomBlockDataPointer
    TXA
    ROL A
    STA RoomBlockDataPointer + 1
    LDY #$04

ScaleRoomBlockDataOffset:
    ASL RoomBlockDataPointer
    ROL RoomBlockDataPointer + 1
    DEY
    BNE ScaleRoomBlockDataOffset
    LDA #<RoomBlockData
    ADC RoomBlockDataPointer
    STA RoomBlockDataPointer
    LDA #>RoomBlockData
    ADC RoomBlockDataPointer + 1
    STA RoomBlockDataPointer + 1
    LDA #RoomMapBrownBlock
    JSR ExpandRoomMapBitplane
    CLC
    LDA #RoomBlockBytesPerPlane
    ADC RoomBlockDataPointer
    STA RoomBlockDataPointer
    LDA #$00
    ADC RoomBlockDataPointer + 1
    STA RoomBlockDataPointer + 1
    LDA #RoomMapWhiteBlock
    JMP ExpandRoomMapBitplane

ExpandRoomMapBitplane:
    STA RoomBlockTile
    LDX #RoomMapPlayableLastIndex
    LDY #RoomBlockBytesPerPlane - 1
    STY RoomBlockByteIndex

LoadNextRoomBlockByte:
    LDY RoomBlockByteIndex
    LDA (RoomBlockDataPointer),Y
    STA RoomBlockBits
    LDY #BitsPerBlockByte
    LDA RoomBlockTile

DecodeNextRoomBlockBit:
    ROR RoomBlockBits
    BCC AdvanceRoomBlockBit
    STA RoomMap,X

AdvanceRoomBlockBit:
    DEX
    DEY
    BNE DecodeNextRoomBlockBit
    DEC RoomBlockByteIndex
    BPL LoadNextRoomBlockByte
    RTS

.assert RoomMapStorageSize = $E0, error, "unexpected RoomMap storage size"
.assert RoomMapPlayableFirstIndex = $10, error, "unexpected RoomMap playable start"
.assert RoomMapPlayableLastIndex = $CF, error, "unexpected RoomMap playable end"
