; PPU program, spark header, and fixed-width names used by the room intro

.segment "PRG_ROOM_INTRO_DATA"

RoomIntroPpuTemplate:
    .byte $21, $6b, $45
    .byte $1c, $11, $1b, $12, $17, $0e
    .byte $21, $cb, $47
    .byte $24, $1b, $18, $18, $16, $24, $00, $00
    .byte $22, $6f, $42
    .byte $98, $00, $00
    .byte $00

RoomIntroSparkHeader:
    .byte $c0, $04, $ff, $0e

SpecialRoomNameTiles:
    .byte $19, $1b, $12, $17, $1c, $0e, $1c, $1c
    .byte $24, $1c, $18, $15, $18, $16, $18, $17
    .byte $24, $11, $12, $0d, $0d, $0e, $17, $24
