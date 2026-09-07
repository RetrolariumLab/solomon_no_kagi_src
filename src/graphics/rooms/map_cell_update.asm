; Build and publish the buffered PPU update for one logical RoomMap cell

.segment "PRG_ROOM_MAP_CELL_UPDATE"

RoomCellTwoByteLiteralCommand = $41
RoomCellOneByteLiteralCommand = $40

RoomMapUpdateSavedIndex = $0000
RoomMapUpdateSavedTile = $0001
RoomMapUpdateAttributeByte = $0002
RoomMapUpdateAttributeAddressLow = $0003
RoomMapUpdatePpuAddressLow = $0004
RoomMapUpdatePpuAddressHigh = $0005
RoomMapUpdateTilePatternPointer = $0006

RoomCellUpdateTopAddressHigh = PpuUpdateBuffer + $00
RoomCellUpdateTopAddressLow = PpuUpdateBuffer + $01
RoomCellUpdateTopCommand = PpuUpdateBuffer + $02
RoomCellUpdateTopTiles = PpuUpdateBuffer + $03
RoomCellUpdateBottomAddressHigh = PpuUpdateBuffer + $05
RoomCellUpdateBottomAddressLow = PpuUpdateBuffer + $06
RoomCellUpdateBottomCommand = PpuUpdateBuffer + $07
RoomCellUpdateBottomTiles = PpuUpdateBuffer + $08
RoomCellUpdateAttributeAddressHigh = PpuUpdateBuffer + $0A
RoomCellUpdateAttributeAddressLow = PpuUpdateBuffer + $0B
RoomCellUpdateAttributeCommand = PpuUpdateBuffer + $0C
RoomCellUpdateAttributeValue = PpuUpdateBuffer + $0D
RoomCellUpdateTerminator = PpuUpdateBuffer + $0E

BuildAndPublishRoomMapCellUpdate:
    LDA RoomMapUpdateTile
    PHA
    LDA RoomMapUpdateIndex
    PHA

WaitForPreviousAttributeReadRequest:
    LDA #GameplayFlagAttributeReadRequest
    AND GameplayFlags
    BEQ WaitForAttributeReadStateIdle
    JSR SwitchThreads
    BCS WaitForPreviousAttributeReadRequest

WaitForAttributeReadStateIdle:
    LDA PpuAttributeReadState
    BPL RequestRoomCellAttributeRead
    JSR SwitchThreads
    BCS WaitForAttributeReadStateIdle

RequestRoomCellAttributeRead:
    PLA
    TAX
    PHA
    JSR CalculateRoomMapAttributeAddressLow
    STA PpuAttributeAddressOrValue
    LDA #GameplayFlagAttributeReadRequest
    ORA GameplayFlags
    STA GameplayFlags

WaitForRoomCellAttributeRead:
    JSR SwitchThreads
    LDA PpuAttributeReadState
    BMI CaptureRoomCellAttributeByte
    LDA GameplayFlags
    AND #GameplayFlagAttributeReadRequest
    BNE WaitForRoomCellAttributeRead

CaptureRoomCellAttributeByte:
    LDA PpuAttributeAddressOrValue
    PHA
    LDA #GameplayFlagAttributeReadRequestMask
    AND GameplayFlags
    STA GameplayFlags

WaitForRoomCellUpdateBuffer:
    LDA PpuUpdateStreamPointer + 1
    BEQ RestoreRoomCellUpdateInputs
    JSR SwitchThreads
    BCS WaitForRoomCellUpdateBuffer

RestoreRoomCellUpdateInputs:
    PLA
    STA RoomMapUpdateAttributeByte
    PLA
    STA RoomMapUpdateSavedIndex
    TAY
    PLA
    STA RoomMapUpdateSavedTile

BuildRoomCellUpdateBuffer:
    LDA #<RoomTilePatternTable
    STA RoomMapUpdateTilePatternPointer
    LDA #>RoomTilePatternTable
    STA RoomMapUpdateTilePatternPointer + 1
    LDX RoomMapUpdateSavedIndex
    JSR CalculateRoomMapAttributeAddressLow
    STA RoomMapUpdateAttributeAddressLow
    LDA RoomMapUpdateSavedTile
    CMP #RoomMapEmptyIdentity
    BNE SelectRoomCellTilePattern
    LDA ConstellationPosition
    BEQ SelectDefaultRoomCellTilePattern
    LDA RoomMapUpdateSavedIndex
    LDX #$00
    SEC
    SBC ConstellationPosition
    BCC SelectDefaultRoomCellTilePattern
    CMP #$03
    BCC SelectConstellationTilePattern
    CMP #$10
    BCC SelectDefaultRoomCellTilePattern
    CMP #$13
    BCC SelectLowerConstellationTilePattern

SelectDefaultRoomCellTilePattern:
    LDA #RoomMapEmptyIdentity
    BPL SelectRoomCellTilePattern

SelectLowerConstellationTilePattern:
    LDX #$03

SelectConstellationTilePattern:
    STX RoomMapUpdatePpuAddressLow
    AND #$03
    ADC RoomMapUpdatePpuAddressLow
    LDX #<ConstellationPattern
    STX RoomMapUpdateTilePatternPointer
    LDX #>ConstellationPattern
    STX RoomMapUpdateTilePatternPointer + 1

SelectRoomCellTilePattern:
    ASL A
    ASL A
    TAY
    LDA RoomMapUpdateAttributeByte
    LDX RoomMapUpdatePpuAddressHigh
    BEQ ClearRoomCellAttributeQuadrant

RotateRoomCellAttributeToLowBits:
    ROR A
    ROR A
    DEX
    BNE RotateRoomCellAttributeToLowBits

ClearRoomCellAttributeQuadrant:
    AND #$FC
    STA RoomMapUpdateAttributeByte
    LDA (RoomMapUpdateTilePatternPointer),Y
    AND #$03
    ORA RoomMapUpdateAttributeByte
    LDX RoomMapUpdatePpuAddressHigh
    BEQ StoreRoomCellAttributeByte

RestoreRoomCellAttributeQuadrant:
    ROL A
    ROL A
    DEX
    BNE RestoreRoomCellAttributeQuadrant

StoreRoomCellAttributeByte:
    STA RoomMapUpdateAttributeByte
    LDA RoomMapUpdateSavedIndex
    STA RoomMapUpdatePpuAddressLow
    JSR ConvertRoomMapIndexToNametableAddress
    LDA RoomMapUpdatePpuAddressHigh
    LDX #$00
    STA RoomCellUpdateTopAddressHigh,X
    STA RoomCellUpdateBottomAddressHigh,X
    LDA RoomMapUpdatePpuAddressLow
    STA RoomCellUpdateTopAddressLow,X
    CLC
    ADC #$20
    STA RoomCellUpdateBottomAddressLow,X
    LDA (RoomMapUpdateTilePatternPointer),Y
    INY
    AND #$FC
    STA RoomCellUpdateTopTiles,X
    LDA (RoomMapUpdateTilePatternPointer),Y
    INY
    STA RoomCellUpdateTopTiles + 1,X
    LDA (RoomMapUpdateTilePatternPointer),Y
    INY
    STA RoomCellUpdateBottomTiles,X
    LDA (RoomMapUpdateTilePatternPointer),Y
    STA RoomCellUpdateBottomTiles + 1,X
    LDA #$23
    STA RoomCellUpdateAttributeAddressHigh,X
    LDA RoomMapUpdateAttributeAddressLow
    STA RoomCellUpdateAttributeAddressLow,X
    LDA RoomMapUpdateAttributeByte
    STA RoomCellUpdateAttributeValue,X
    TXA
    STA RoomCellUpdateTerminator,X
    LDA #RoomCellTwoByteLiteralCommand
    STA RoomCellUpdateTopCommand,X
    STA RoomCellUpdateBottomCommand,X
    LDA #RoomCellOneByteLiteralCommand
    STA RoomCellUpdateAttributeCommand,X
    JMP PublishPpuUpdateBuffer

.segment "PRG_ROOM_TILE_PATTERNS"

; Four bytes per logical tile: attribute palette bits in byte 0's low pair,
; then top-left, top-right, bottom-left, and bottom-right tile information as
; consumed by BuildRoomCellUpdateBuffer's overlapping reads
RoomTilePatternTable:
    .byte $91, $91, $92, $93
    .byte $95, $95, $96, $97
    .byte $41, $41, $42, $43
    .byte $84, $85, $86, $87
    .byte $3C, $3D, $3E, $3F
    .byte $59, $59, $5A, $5B
    .byte $2F, $8D, $8E, $8F
    .byte $45, $45, $46, $47
    .byte $72, $71, $72, $73
    .byte $62, $65, $66, $67
    .byte $37, $80, $36, $82
    .byte $6D, $6D, $6E, $6F
    .byte $73, $71, $72, $73
    .byte $61, $65, $66, $67
    .byte $2D, $99, $9A, $9B
    .byte $9F, $9D, $9E, $9F
    .byte $2C, $2D, $2E, $2F
    .byte $64, $B5, $4E, $4F
    .byte $4C, $4D, $4E, $4F
    .byte $7A, $79, $7A, $7B
    .byte $7D, $7D, $7E, $7F
    .byte $62, $65, $66, $67
    .byte $61, $65, $66, $67
    .byte $2D, $99, $9A, $9B
    .byte $9F, $9D, $9E, $9F
    .byte $4D, $4D, $4E, $4F
    .byte $2E, $8D, $8E, $8F
    .byte $6E, $6D, $6E, $6F
    .byte $53, $51, $52, $53
    .byte $57, $55, $56, $57
    .byte $5F, $5D, $5E, $5F
    .byte $77, $75, $76, $77
    .byte $68, $69, $6A, $6B
    .byte $8B, $89, $8A, $8B
    .byte $AF, $AD, $AE, $AF
    .byte $45, $45, $46, $47
    .byte $45, $45, $46, $47
    .byte $34, $35, $36, $37
    .byte $34, $80, $36, $82
    .byte $32, $31, $32, $33
    .byte $37, $35, $36, $37
    .byte $37, $80, $36, $82
    .byte $31, $31, $32, $33
    .byte $3B, $39, $3A, $3B
    .byte $3B, $81, $3A, $83
    .byte $33, $31, $32, $33
    .byte $AB, $A9, $49, $4B
    .byte $21, $21, $1A, $23
    .byte $11, $13, $19, $8C
    .byte $8B, $89, $8A, $8B
    .byte $17, $1D, $1E, $1F
    .byte $61, $61, $62, $63
    .byte $49, $45, $4A, $47
    .byte $AE, $AD, $AE, $AF
    .byte $B9, $B9, $BA, $BB
    .byte $BD, $BD, $BE, $BF
    .byte $B8, $B9, $BA, $BB
    .byte $B9, $B9, $BA, $BB

.assert * - RoomTilePatternTable = 58 * 4, error, "unexpected room tile pattern table size"
