; Render the 16x12 interior RoomMap cells through direct PPU transfers

.segment "PRG_ROOM_MAP_RENDER"

RoomMapRenderStartIndex = RoomMapPlayableLastIndex + 1
RoomMapRenderStopIndex = RoomMapPlayableFirstIndex + 1
NametableAttributeHigh = $23
ImmutableRoomMapPatternIndex = $03
SolidRoomMapPatternIndex = $00
DecoratedRoomMapPatternIndex = $10

DrawRoomMapToNametable:
    LDA a:PpuUpdateStreamPointer + 1
    BNE DrawRoomMapToNametable
    JSR BeginDirectPpuTransfer
    LDA a:PPU_STATUS
    LDA #RoomMapRenderStartIndex

DrawNextRoomMapCell:
    PHA
    TAX
    AND #RoomMapColumnMask
    BEQ AdvanceRoomMapCell
    DEX
    STX RoomRenderMapIndex
    JSR CalculateRoomMapAttributeAddressLow
    STA RoomRenderPpuAddressLow
    LDY #NametableAttributeHigh
    STY a:PPU_ADDR
    STA a:PPU_ADDR
    LDA a:PPU_DATA
    LDA a:PPU_DATA
    STA RoomRenderAttributeByte
    LDX RoomRenderMapIndex
    LDA RoomMap,X
    LDX #ImmutableRoomMapPatternIndex
    CMP #RoomMapImmutableTileMinimum
    BCS SelectRoomMapTileClass
    CMP #RoomMapSolidBit
    LDX #SolidRoomMapPatternIndex
    BCS SelectRoomMapTileClass
    LDX #DecoratedRoomMapPatternIndex
    CMP #RoomMapDecorationBit
    BCS SelectRoomMapTileClass
    TAX

SelectRoomMapTileClass:
    STX RoomRenderTileClass
    JSR BuildRoomCellUpdateBuffer
    LDX #$00

WriteNextRoomCellPpuChunk:
    LDY #$02

WriteRoomCellPpuAddress:
    LDA PpuUpdateBuffer,X
    INX
    STA a:PPU_ADDR
    DEY
    BNE WriteRoomCellPpuAddress
    LDA PpuCtrlShadow
    STA a:PPU_CTRL
    INX
    LDY #$02

WriteRoomCellPpuData:
    LDA PpuUpdateBuffer,X
    BEQ AdvanceRoomMapCell
    INX
    STA a:PPU_DATA
    DEY
    BNE WriteRoomCellPpuData
    BEQ WriteNextRoomCellPpuChunk

AdvanceRoomMapCell:
    PLA
    TAX
    DEX
    CPX #RoomMapRenderStopIndex
    TXA
    BCS DrawNextRoomMapCell
    LDA a:PPU_STATUS
    JMP EndDirectPpuTransfer
