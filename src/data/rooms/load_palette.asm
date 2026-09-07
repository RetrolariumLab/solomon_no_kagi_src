; Mutable palette-update template copied into the shared NMI program buffer

.segment "PRG_ROOM_LOAD_PALETTE"

RoomLoadPaletteTemplate:
    .byte $3f, $00, $5f
    .byte $0f, $07, $10, $30, $0f, $07, $27, $30
    .byte $0f, $07, $2c, $30, $0f, $07, $27, $38
    .byte $0f, $26, $29, $30, $0f, $30, $16, $27
    .byte $0f, $16, $10, $30, $0f, $2c, $26, $30
    .byte $00
