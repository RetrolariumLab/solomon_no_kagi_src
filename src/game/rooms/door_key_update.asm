; Publish the current room's initial door and optional key map cells

.segment "PRG_ROOM_DOOR_KEY_UPDATE"

RoomHeaderFlagsOffset = $04
RoomHeaderDoorPositionOffset = $05
RoomHeaderKeyPositionOffset = $06

PublishRoomDoorAndKeyUpdates:
    LDY #RoomHeaderDoorPositionOffset
    LDA (RoomItemPointer),Y
    BEQ FinishRoomDoorAndKeyUpdates
    STA RoomMapUpdateIndex
    LDX #RoomMapClosedDoorIdentity
    INY
    LDA (RoomItemPointer),Y
    BNE PublishInitialDoorCell
    LDX #RoomMapDeferredDoorIdentity

PublishInitialDoorCell:
    STX RoomMapUpdateTile
    JSR BuildAndPublishRoomMapCellUpdate
    LDA #$20
    AND GameplayFlags
    BNE FinishRoomDoorAndKeyUpdates
    LDY #RoomHeaderFlagsOffset
    LDA #$C0
    AND (RoomItemPointer),Y
    BNE FinishRoomDoorAndKeyUpdates
    LDY #RoomHeaderKeyPositionOffset
    LDA (RoomItemPointer),Y
    STA RoomMapUpdateIndex
    LDA #RoomMapKeyIdentity
    STA RoomMapUpdateTile
    JMP BuildAndPublishRoomMapCellUpdate

FinishRoomDoorAndKeyUpdates:
    RTS
