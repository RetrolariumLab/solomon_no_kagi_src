; Per-room metadata and compressed item placement commands

RoomItemStreamCount = 53

.macro RoomItemHeader mirror_2_schedule, mirror_1_schedule, mirror_2_enemy_set, mirror_1_enemy_set, status_rate, door_position, key_position, player_start_position, mirror_1_position, mirror_2_position
    .byte mirror_2_schedule, mirror_1_schedule
    .byte mirror_2_enemy_set, mirror_1_enemy_set, status_rate
    .byte door_position, key_position, player_start_position
    .byte mirror_1_position, mirror_2_position
.endmacro

.macro RoomItemRecord item_type, map_position
    .byte item_type, map_position
.endmacro

.macro BeginRoomItemRepeat item_type, repeat_count
    .byte $C0 + repeat_count - 1, item_type
.endmacro

.macro EndRoomItemStream opcode
    .byte opcode
.endmacro

.macro RoomConstellationItem opcode, map_position
    .byte opcode, map_position
.endmacro

.segment "PRG_ROOM_ITEM_POINTERS"

RoomItemPointerLowTable:
    .byte <RoomItemStream01, <RoomItemStream02
    .byte <RoomItemStream03, <RoomItemStream04
    .byte <RoomItemStream05, <RoomItemStream06
    .byte <RoomItemStream07, <RoomItemStream08
    .byte <RoomItemStream09, <RoomItemStream10
    .byte <RoomItemStream11, <RoomItemStream12
    .byte <RoomItemStream13, <RoomItemStream14
    .byte <RoomItemStream15, <RoomItemStream16
    .byte <RoomItemStream17, <RoomItemStream18
    .byte <RoomItemStream19, <RoomItemStream20
    .byte <RoomItemStream21, <RoomItemStream22
    .byte <RoomItemStream23, <RoomItemStream24
    .byte <RoomItemStream25, <RoomItemStream26
    .byte <RoomItemStream27, <RoomItemStream28
    .byte <RoomItemStream29, <RoomItemStream30
    .byte <RoomItemStream31, <RoomItemStream32
    .byte <RoomItemStream33, <RoomItemStream34
    .byte <RoomItemStream35, <RoomItemStream36
    .byte <RoomItemStream37, <RoomItemStream38
    .byte <RoomItemStream39, <RoomItemStream40
    .byte <RoomItemStream41, <RoomItemStream42
    .byte <RoomItemStream43, <RoomItemStream44
    .byte <RoomItemStream45, <RoomItemStream46
    .byte <RoomItemStream47, <RoomItemStream48
    .byte <RoomItemStream49, <RoomItemStream50
    .byte <RoomItemStream51, <RoomItemStream52
    .byte <RoomItemStream53

RoomItemPointerHighTable:
    .byte >RoomItemStream01, >RoomItemStream02
    .byte >RoomItemStream03, >RoomItemStream04
    .byte >RoomItemStream05, >RoomItemStream06
    .byte >RoomItemStream07, >RoomItemStream08
    .byte >RoomItemStream09, >RoomItemStream10
    .byte >RoomItemStream11, >RoomItemStream12
    .byte >RoomItemStream13, >RoomItemStream14
    .byte >RoomItemStream15, >RoomItemStream16
    .byte >RoomItemStream17, >RoomItemStream18
    .byte >RoomItemStream19, >RoomItemStream20
    .byte >RoomItemStream21, >RoomItemStream22
    .byte >RoomItemStream23, >RoomItemStream24
    .byte >RoomItemStream25, >RoomItemStream26
    .byte >RoomItemStream27, >RoomItemStream28
    .byte >RoomItemStream29, >RoomItemStream30
    .byte >RoomItemStream31, >RoomItemStream32
    .byte >RoomItemStream33, >RoomItemStream34
    .byte >RoomItemStream35, >RoomItemStream36
    .byte >RoomItemStream37, >RoomItemStream38
    .byte >RoomItemStream39, >RoomItemStream40
    .byte >RoomItemStream41, >RoomItemStream42
    .byte >RoomItemStream43, >RoomItemStream44
    .byte >RoomItemStream45, >RoomItemStream46
    .byte >RoomItemStream47, >RoomItemStream48
    .byte >RoomItemStream49, >RoomItemStream50
    .byte >RoomItemStream51, >RoomItemStream52
    .byte >RoomItemStream53

.assert RoomItemPointerHighTable - RoomItemPointerLowTable = RoomItemStreamCount, error, "unexpected room item pointer count"
.assert * - RoomItemPointerHighTable = RoomItemStreamCount, error, "unexpected room item pointer count"

.segment "PRG_ROOM_ITEM_DATA"

RoomItemStream01:
    RoomItemHeader $00, $00, $00, $00, $01, $A7, $7C, $82, $27, $27
    RoomItemRecord $18, $27
    RoomItemRecord $58, $A3
    BeginRoomItemRepeat $95, 2
    .byte $44, $4A
    RoomItemRecord $A7, $74
    RoomItemRecord $88, $7A
    RoomConstellationItem $F0, $36
RoomItemStream02:
    RoomItemHeader $0C, $0C, $01, $01, $01, $9D, $3D, $91, $21, $23
    RoomItemRecord $18, $37
    RoomItemRecord $95, $68
    RoomItemRecord $99, $85
    EndRoomItemStream $E0
RoomItemStream03:
    RoomItemHeader $00, $00, $00, $00, $01, $79, $9A, $43, $25, $25
    RoomItemRecord $73, $1D
    RoomItemRecord $AA, $7B
    RoomItemRecord $18, $B1
    RoomItemRecord $95, $A1
    EndRoomItemStream $E4
RoomItemStream04:
    RoomItemHeader $0D, $0D, $0E, $0E, $01, $71, $67, $7D, $33, $3B
    BeginRoomItemRepeat $98, 2
    .byte $A4, $AA
    BeginRoomItemRepeat $1B, 2
    .byte $66, $68
    RoomItemRecord $1B, $57
    RoomItemRecord $08, $77
    RoomItemRecord $1C, $27
    EndRoomItemStream $E0
RoomItemStream05:
    RoomItemHeader $00, $00, $00, $00, $01, $27, $87, $C7, $24, $2A
    BeginRoomItemRepeat $1B, 6
    .byte $53, $6B, $73, $8B, $93, $AB
    BeginRoomItemRepeat $08, 2
    .byte $B3, $CB
    RoomItemRecord $6B, $C0
    RoomConstellationItem $F8, $56
RoomItemStream06:
    RoomItemHeader $00, $00, $00, $00, $01, $CD, $33, $31, $2D, $2D
    RoomItemRecord $48, $1E
    BeginRoomItemRepeat $1B, 4
    .byte $4C, $62, $8C, $A2
    BeginRoomItemRepeat $28, 4
    .byte $4D, $61, $8D, $A1
    RoomItemRecord $58, $50
    BeginRoomItemRepeat $18, 2
    .byte $C0, $B7
    RoomItemRecord $16, $27
    EndRoomItemStream $E0
RoomItemStream07:
    RoomItemHeader $00, $00, $00, $00, $01, $6A, $64, $C7, $14, $1A
    BeginRoomItemRepeat $25, 8
    .byte $43, $72, $45, $56, $58, $49, $4B, $7C
    RoomItemRecord $18, $52
    RoomItemRecord $15, $76
    RoomItemRecord $1B, $78
    RoomItemRecord $17, $5C
    RoomItemRecord $54, $11
    RoomItemRecord $6B, $C7
    RoomItemRecord $62, $1D
    EndRoomItemStream $E4
RoomItemStream08:
    RoomItemHeader $00, $00, $00, $00, $01, $CD, $77, $C1, $26, $28
    BeginRoomItemRepeat $29, 4
    .byte $66, $86, $68, $88
    BeginRoomItemRepeat $15, 2
    .byte $57, $97
    RoomItemRecord $1D, $37
    BeginRoomItemRepeat $67, 4
    .byte $61, $63, $81, $83
    BeginRoomItemRepeat $69, 2
    .byte $67, $87
    BeginRoomItemRepeat $58, 2
    .byte $6D, $8B
    BeginRoomItemRepeat $5B, 2
    .byte $6B, $8D
    EndRoomItemStream $E0
RoomItemStream09:
    RoomItemHeader $0C, $00, $03, $00, $01, $9C, $87, $92, $67, $67
    BeginRoomItemRepeat $29, 2
    .byte $54, $5A
    RoomItemRecord $18, $85
    RoomConstellationItem $F1, $26
RoomItemStream10:
    RoomItemHeader $00, $04, $00, $02, $01, $21, $6E, $CD, $7A, $23
    BeginRoomItemRepeat $08, 2
    .byte $46, $48
    RoomItemRecord $17, $2D
    RoomItemRecord $18, $C1
    RoomItemRecord $6A, $80
    RoomItemRecord $58, $77
    EndRoomItemStream $E4
RoomItemStream11:
    RoomItemHeader $00, $00, $00, $00, $01, $BD, $86, $B5, $34, $92
    RoomItemRecord $11, $3A
    BeginRoomItemRepeat $98, 2
    .byte $AA, $B3
    RoomItemRecord $6B, $88
    EndRoomItemStream $E5
RoomItemStream12:
    RoomItemHeader $01, $00, $05, $00, $01, $51, $5C, $C4, $15, $15
    BeginRoomItemRepeat $1B, 2
    .byte $C9, $CD
    RoomItemRecord $15, $CB
    RoomItemRecord $18, $11
    RoomItemRecord $6B, $10
    RoomItemRecord $58, $7C
    RoomItemRecord $96, $5A
    RoomItemRecord $AA, $5E
    RoomItemRecord $1E, $2C
    EndRoomItemStream $E0
RoomItemStream13:
    RoomItemHeader $05, $05, $05, $05, $02, $C1, $CD, $C7, $26, $28
    BeginRoomItemRepeat $19, 2
    .byte $C4, $CA
    BeginRoomItemRepeat $08, 2
    .byte $91, $A1
    BeginRoomItemRepeat $28, 2
    .byte $41, $4D
    RoomItemRecord $14, $27
    BeginRoomItemRepeat $6B, 2
    .byte $21, $2D
    BeginRoomItemRepeat $9B, 2
    .byte $31, $3D
    RoomItemRecord $A9, $B1
    RoomItemRecord $AD, $BD
    BeginRoomItemRepeat $98, 2
    .byte $CC, $CE
    RoomConstellationItem $F4, $66
RoomItemStream14:
    RoomItemHeader $01, $0C, $0F, $0F, $41, $17, $42, $CC, $12, $1C
    BeginRoomItemRepeat $04, 20
    .byte $20, $21, $22, $23, $24, $2A, $2B, $2C
    .byte $2D, $2E, $B0, $B1, $B2, $B3, $B4, $BA
    .byte $BB, $BC, $BD, $BE
    BeginRoomItemRepeat $9B, 9
    .byte $64, $65, $66, $74, $75, $84, $86, $97
    .byte $A8
    BeginRoomItemRepeat $93, 2
    .byte $72, $7C
    RoomItemRecord $98, $AC
    RoomItemRecord $B3, $3C
    EndRoomItemStream $E0
RoomItemStream15:
    RoomItemHeader $0B, $00, $0B, $00, $01, $C0, $22, $C5, $10, $10
    BeginRoomItemRepeat $1B, 6
    .byte $67, $68, $77, $78, $87, $88
    RoomItemRecord $15, $34
    RoomItemRecord $53, $61
    RoomItemRecord $59, $5C
    BeginRoomItemRepeat $98, 2
    .byte $66, $9C
    RoomItemRecord $62, $CA
    EndRoomItemStream $E4
RoomItemStream16:
    RoomItemHeader $01, $01, $04, $03, $01, $67, $77, $C7, $26, $28
    RoomItemRecord $13, $27
    RoomItemRecord $18, $47
    BeginRoomItemRepeat $2A, 2
    .byte $66, $68
    BeginRoomItemRepeat $1B, 2
    .byte $86, $88
    BeginRoomItemRepeat $88, 2
    .byte $33, $3B
    BeginRoomItemRepeat $AA, 2
    .byte $46, $48
    RoomItemRecord $1F, $57
    EndRoomItemStream $E0
RoomItemStream17:
    RoomItemHeader $00, $00, $00, $00, $01, $91, $75, $BE, $21, $21
    BeginRoomItemRepeat $28, 2
    .byte $94, $95
    RoomItemRecord $94, $7A
    RoomItemRecord $98, $7C
    RoomItemRecord $52, $28
    RoomItemRecord $69, $11
    RoomItemRecord $58, $A2
    RoomConstellationItem $F9, $36
RoomItemStream18:
    RoomItemHeader $00, $08, $00, $0C, $01, $B0, $4E, $C6, $2C, $22
    BeginRoomItemRepeat $2A, 2
    .byte $7B, $7C
    BeginRoomItemRepeat $5B, 2
    .byte $CC, $CD
    RoomItemRecord $98, $3D
    RoomItemRecord $58, $A4
    EndRoomItemStream $E8
RoomItemStream19:
    RoomItemHeader $01, $05, $05, $05, $01, $77, $74, $C8, $2B, $28
    RoomItemRecord $19, $63
    RoomItemRecord $13, $72
    RoomItemRecord $33, $81
    RoomItemRecord $4C, $23
    RoomItemRecord $6F, $21
    EndRoomItemStream $E0
RoomItemStream20:
    RoomItemHeader $00, $00, $00, $00, $02, $17, $27, $37, $75, $79
    RoomItemRecord $18, $A4
    RoomItemRecord $53, $83
    RoomItemRecord $5C, $2A
    EndRoomItemStream $E4
RoomItemStream21:
    RoomItemHeader $01, $00, $01, $00, $01, $6C, $BD, $C7, $B3, $44
    BeginRoomItemRepeat $27, 5
    .byte $8C, $8D, $8E, $9C, $9E
    RoomItemRecord $15, $9D
    RoomItemRecord $94, $86
    RoomItemRecord $AC, $89
    RoomItemRecord $98, $BB
    RoomConstellationItem $F2, $36
RoomItemStream22:
    RoomItemHeader $08, $08, $05, $05, $01, $BE, $9B, $5E, $4E, $89
    RoomItemRecord $0C, $8E
    RoomItemRecord $6E, $8A
    BeginRoomItemRepeat $98, 2
    .byte $6A, $97
    RoomItemRecord $92, $79
    EndRoomItemStream $E4
RoomItemStream23:
    RoomItemHeader $00, $00, $00, $00, $01, $A3, $86, $2D, $96, $A6
    BeginRoomItemRepeat $04, 4
    .byte $2B, $2C, $3B, $3C
    RoomItemRecord $18, $5C
    BeginRoomItemRepeat $58, 2
    .byte $32, $43
    RoomItemRecord $6E, $CE
    RoomItemRecord $62, $C3
    RoomItemRecord $6B, $33
    RoomItemRecord $6A, $42
    EndRoomItemStream $E8
RoomItemStream24:
    RoomItemHeader $00, $00, $00, $00, $02, $4D, $91, $B1, $83, $68
    BeginRoomItemRepeat $68, 5
    .byte $C7, $C8, $C9, $CA, $CB
    RoomItemRecord $58, $9D
    RoomItemRecord $14, $51
    RoomItemRecord $12, $46
    RoomItemRecord $18, $3D
    RoomItemRecord $97, $75
    RoomItemRecord $9D, $CE
    EndRoomItemStream $E4
RoomItemStream25:
    RoomItemHeader $08, $08, $06, $07, $01, $27, $67, $C7, $14, $1A
    BeginRoomItemRepeat $27, 4
    .byte $21, $2D, $A1, $AD
    BeginRoomItemRepeat $58, 2
    .byte $61, $6D
    BeginRoomItemRepeat $A5, 2
    .byte $42, $4C
    BeginRoomItemRepeat $A6, 2
    .byte $41, $4D
    BeginRoomItemRepeat $A7, 2
    .byte $40, $4E
    RoomItemRecord $91, $47
    RoomConstellationItem $FA, $A6
RoomItemStream26:
    RoomItemHeader $06, $06, $03, $04, $01, $27, $77, $A7, $22, $2C
    BeginRoomItemRepeat $18, 2
    .byte $42, $4C
    RoomItemRecord $14, $67
    RoomItemRecord $16, $C7
    BeginRoomItemRepeat $A8, 4
    .byte $A3, $A4, $AA, $AB
    BeginRoomItemRepeat $98, 2
    .byte $B6, $B8
    BeginRoomItemRepeat $A6, 4
    .byte $73, $74, $7A, $7B
    BeginRoomItemRepeat $99, 2
    .byte $86, $88
    RoomItemRecord $AE, $15
    RoomItemRecord $91, $19
    EndRoomItemStream $E8
RoomItemStream27:
    RoomItemHeader $00, $00, $00, $00, $01, $2C, $C1, $CD, $21, $5D
    BeginRoomItemRepeat $69, 2
    .byte $2A, $B3
    RoomItemRecord $2B, $6A
    RoomItemRecord $2D, $34
    RoomItemRecord $18, $60
    RoomItemRecord $92, $CB
    RoomItemRecord $B3, $3D
    EndRoomItemStream $E4
RoomItemStream28:
    RoomItemHeader $00, $00, $00, $00, $02, $A7, $97, $C7, $93, $9B
    BeginRoomItemRepeat $2C, 2
    .byte $A0, $AE
    BeginRoomItemRepeat $1B, 2
    .byte $44, $4A
    RoomItemRecord $2A, $47
    RoomItemRecord $58, $13
    RoomItemRecord $51, $A5
    RoomItemRecord $5B, $A9
    RoomItemRecord $5E, $1E
    EndRoomItemStream $E4
RoomItemStream29:
    RoomItemHeader $0A, $0A, $01, $02, $01, $6D, $67, $61, $2C, $23
    BeginRoomItemRepeat $26, 2
    .byte $96, $98
    RoomItemRecord $18, $27
    BeginRoomItemRepeat $6B, 2
    .byte $5B, $6E
    RoomItemRecord $6A, $59
    RoomItemRecord $69, $57
    RoomItemRecord $68, $55
    RoomItemRecord $67, $53
    RoomItemRecord $4C, $62
    RoomConstellationItem $F5, $36
RoomItemStream30:
    RoomItemHeader $01, $01, $01, $02, $02, $16, $18, $37, $1E, $10
    RoomItemRecord $94, $47
    RoomItemRecord $98, $87
    RoomItemRecord $73, $A1
    RoomItemRecord $59, $AD
    RoomItemRecord $6F, $27
    EndRoomItemStream $E0
RoomItemStream31:
    RoomItemHeader $03, $03, $10, $08, $02, $13, $1B, $C7, $11, $1D
    RoomItemRecord $62, $CE
    RoomItemRecord $52, $18
    RoomItemRecord $58, $16
    RoomItemRecord $70, $87
    EndRoomItemStream $E4
RoomItemStream32:
    RoomItemHeader $08, $08, $01, $02, $02, $17, $67, $27, $19, $15
    BeginRoomItemRepeat $1B, 10
    .byte $25, $29, $35, $36, $38, $39, $95, $99
    .byte $A5, $A9
    BeginRoomItemRepeat $27, 4
    .byte $65, $69, $75, $79
    RoomItemRecord $6E, $57
    RoomItemRecord $58, $C7
    RoomItemRecord $54, $9E
    RoomItemRecord $5F, $7E
    EndRoomItemStream $E4
RoomItemStream33:
    RoomItemHeader $00, $00, $00, $00, $01, $C7, $C2, $CC, $23, $2B
    BeginRoomItemRepeat $58, 2
    .byte $C1, $C6
    RoomItemRecord $6C, $6C
    RoomItemRecord $6D, $6D
    RoomItemRecord $6E, $6E
    RoomItemRecord $52, $17
    RoomConstellationItem $FB, $69
RoomItemStream34:
    RoomItemHeader $08, $08, $09, $0A, $40, $C7, $77, $37, $2C, $22
    BeginRoomItemRepeat $18, 2
    .byte $35, $39
    RoomItemRecord $12, $38
    RoomItemRecord $54, $36
    EndRoomItemStream $E0
RoomItemStream35:
    RoomItemHeader $04, $04, $01, $02, $02, $17, $27, $C7, $15, $19
    BeginRoomItemRepeat $29, 4
    .byte $75, $79, $95, $99
    RoomItemRecord $13, $87
    RoomItemRecord $73, $67
    BeginRoomItemRepeat $AC, 2
    .byte $36, $38
    EndRoomItemStream $E8
RoomItemStream36:
    RoomItemHeader $07, $00, $08, $00, $01, $C1, $25, $C7, $11, $11
    BeginRoomItemRepeat $68, 2
    .byte $AC, $AD
    BeginRoomItemRepeat $6B, 2
    .byte $4C, $4D
    RoomItemRecord $19, $71
    RoomItemRecord $18, $47
    RoomItemRecord $14, $1E
    RoomItemRecord $1C, $23
    EndRoomItemStream $E8
RoomItemStream37:
    RoomItemHeader $00, $00, $00, $00, $01, $2D, $CC, $CD, $A0, $A0
    BeginRoomItemRepeat $1B, 11
    .byte $83, $87, $93, $94, $96, $97, $A3, $A5
    .byte $A7, $B3, $B7
    BeginRoomItemRepeat $58, 2
    .byte $5D, $7D
    RoomItemRecord $51, $B9
    RoomConstellationItem $F6, $46
RoomItemStream38:
    RoomItemHeader $09, $09, $00, $00, $02, $17, $27, $47, $10, $1E
    BeginRoomItemRepeat $55, 2
    .byte $55, $59
    BeginRoomItemRepeat $A6, 2
    .byte $B0, $BE
    RoomItemRecord $98, $41
    RoomItemRecord $53, $90
    RoomItemRecord $0E, $9C
    EndRoomItemStream $E4
RoomItemStream39:
    RoomItemHeader $00, $00, $00, $00, $02, $77, $2D, $B0, $67, $67
    RoomItemRecord $53, $66
    RoomItemRecord $58, $67
    RoomItemRecord $4C, $68
    RoomItemRecord $62, $70
    EndRoomItemStream $E8
RoomItemStream40:
    RoomItemHeader $00, $00, $00, $00, $01, $6D, $67, $61, $47, $47
    BeginRoomItemRepeat $58, 2
    .byte $26, $28
    RoomItemRecord $6D, $6B
    RoomItemRecord $73, $1C
    RoomItemRecord $5D, $63
    EndRoomItemStream $E8
RoomItemStream41:
    RoomItemHeader $04, $04, $09, $0A, $01, $57, $B7, $67, $1A, $14
    RoomItemRecord $2B, $84
    RoomItemRecord $AF, $A4
    RoomItemRecord $92, $AB
    RoomItemRecord $99, $C7
    RoomConstellationItem $F3, $26
RoomItemStream42:
    RoomItemHeader $00, $00, $00, $00, $82, $10, $1E, $47, $11, $1D
    BeginRoomItemRepeat $AD, 2
    .byte $36, $38
    RoomItemRecord $6F, $37
    RoomItemRecord $58, $47
    RoomItemRecord $93, $B4
    EndRoomItemStream $E4
RoomItemStream43:
    RoomItemHeader $04, $00, $05, $00, $42, $21, $C1, $CD, $28, $28
    RoomItemRecord $18, $52
    RoomItemRecord $2D, $64
    RoomItemRecord $12, $68
    RoomItemRecord $58, $5B
    RoomItemRecord $70, $56
    EndRoomItemStream $E4
RoomItemStream44:
    RoomItemHeader $00, $00, $00, $00, $02, $10, $CE, $C7, $1E, $C0
    RoomItemRecord $52, $87
    RoomItemRecord $6E, $6E
    RoomItemRecord $98, $23
    RoomItemRecord $9E, $50
    EndRoomItemStream $E8
RoomItemStream45:
    RoomItemHeader $0E, $03, $01, $02, $42, $60, $6E, $C7, $5B, $53
    BeginRoomItemRepeat $18, 2
    .byte $C0, $CE
    BeginRoomItemRepeat $6B, 3
    .byte $63, $6B, $C4
    RoomItemRecord $AD, $9B
    RoomItemRecord $AE, $82
    RoomConstellationItem $F7, $26
RoomItemStream46:
    RoomItemHeader $01, $05, $05, $05, $42, $2D, $1A, $CE, $21, $20
    RoomItemRecord $52, $58
    RoomItemRecord $53, $7A
    RoomItemRecord $58, $2A
    RoomItemRecord $6E, $4B
    RoomItemRecord $72, $6D
    RoomItemRecord $54, $38
    EndRoomItemStream $E4
RoomItemStream47:
    RoomItemHeader $0F, $00, $03, $00, $02, $B1, $35, $11, $BA, $30
    RoomItemRecord $25, $B7
    RoomItemRecord $73, $4A
    RoomItemRecord $71, $6D
    BeginRoomItemRepeat $98, 2
    .byte $65, $CD
    EndRoomItemStream $E0
RoomItemStream48:
    RoomItemHeader $00, $00, $00, $00, $02, $80, $A0, $C0, $57, $57
    RoomItemRecord $5F, $44
    RoomItemRecord $6D, $33
    RoomItemRecord $6F, $50
    RoomItemRecord $18, $A3
    RoomItemRecord $AB, $41
    RoomItemRecord $B3, $53
    RoomItemRecord $AE, $3A
    EndRoomItemStream $E8
RoomItemStream49:
    RoomItemHeader $00, $00, $00, $00, $81, $00, $00, $37, $19, $19
    RoomItemRecord $6D, $19
    BeginRoomItemRepeat $6E, 2
    .byte $C4, $CA
    EndRoomItemStream $E8
RoomItemStream50:
    RoomItemHeader $00, $00, $00, $00, $82, $67, $00, $2C, $62, $6C
    BeginRoomItemRepeat $04, 2
    .byte $A6, $A8
    EndRoomItemStream $E0
RoomItemStream51:
    RoomItemHeader $00, $00, $00, $00, $00, $47, $9B, $93, $77, $77
    RoomItemRecord $1B, $77
    EndRoomItemStream $E0
RoomItemStream52:
    RoomItemHeader $00, $00, $00, $00, $01, $3D, $57, $31, $10, $10
    RoomItemRecord $6A, $10
    EndRoomItemStream $E4
RoomItemStream53:
    RoomItemHeader $00, $00, $00, $00, $01, $A1, $87, $AD, $CE, $CE
    RoomItemRecord $6A, $CE
    EndRoomItemStream $E8

.assert * - RoomItemStream01 = $053E, error, "unexpected room item data size"

.segment "PRG_FILLER_BEFORE_AUDIO"

PreAudioPadding:
.if SolomonRevision = SolomonRevisionEurope
    .res $003C, $FF
.else
    .byte $00, $FF, $00, $FF, $00, $FF, $00, $FF
    .byte $00, $FF, $00, $FF, $FF, $00, $FF, $00
    .byte $FF, $00, $FF, $00, $FF, $00, $BF, $00
    .byte $FF, $00, $FF, $00, $00, $FF, $00, $FF
    .byte $00, $FF, $00, $FF, $00, $FF, $00, $FF
    .byte $00, $FF, $00, $BF, $FF, $00, $FF, $00
    .byte $FF, $00, $FF, $00, $FF, $00, $FF, $00
    .byte $FF, $00, $FF, $00
.endif

.assert * - PreAudioPadding = $003C, error, "unexpected pre-audio padding size"
