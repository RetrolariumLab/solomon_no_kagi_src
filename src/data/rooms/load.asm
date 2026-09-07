; Room-index palette selection and Dana state preload values

.segment "PRG_ROOM_LOAD_DATA"

RoomLoadDanaHeaderPredecessors:
    .byte $00, $e0, $00, $ff

RoomPaletteColorByRoomGroup:
    .byte $07, $1c, $04, $09, $1c, $07, $04
    .byte $07, $09, $1c, $07, $04, $80, $80

RoomPaletteColorOffsets:
    .byte $01, $05, $09, $0d
