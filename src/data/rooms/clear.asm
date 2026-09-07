; Initial AI and gameplay-object values for the room-clear presentation

.segment "PRG_ROOM_CLEAR_DATA"

RoomClearAiStateTemplate:
    .byte $00, $00, $00, $00, $03, $00, $01, $80

RoomClearObjectHeaderPredecessors:
    .byte $00, $c0, $1c, $ff

RoomClearObjectXPositions:
    .byte $28, $c8
