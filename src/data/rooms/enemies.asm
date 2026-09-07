; Per-room enemy pointers, encoded lifetimes, and spawn records

RoomEnemyStreamCount = 53

.macro RoomEnemySpawnLifetime ntsc_value
    .if SolomonRevision = SolomonRevisionEurope
        .if ntsc_value = $20
            .byte $20
        .elseif ntsc_value = $02
            .byte $A1
        .elseif ntsc_value = $82
            .byte $02
        .elseif ntsc_value = $41
            .byte $01
        .elseif ntsc_value = $C0
            .byte $80
        .elseif ntsc_value = $01
            .byte $A0
        .elseif ntsc_value = $81
            .byte $21
        .elseif ntsc_value = $C1
            .byte $61
        .elseif ntsc_value = $42
            .byte $A1
        .elseif ntsc_value = $E1
            .byte $81
        .else
            .error "unmapped PAL room enemy spawn lifetime"
        .endif
    .else
        .byte ntsc_value
    .endif
.endmacro

.macro RoomEnemyRecord enemy_type, map_position
    .byte enemy_type, map_position
.endmacro

.macro EndRoomEnemyStream
    .byte $00
.endmacro

.segment "PRG_ROOM_ENEMY_POINTERS"

RoomEnemyPointerLowTable:
    .byte <RoomEnemyStream01, <RoomEnemyStream02
    .byte <RoomEnemyStream03, <RoomEnemyStream04
    .byte <RoomEnemyStream05, <RoomEnemyStream06
    .byte <RoomEnemyStream07, <RoomEnemyStream08
    .byte <RoomEnemyStream09, <RoomEnemyStream10
    .byte <RoomEnemyStream11, <RoomEnemyStream12
    .byte <RoomEnemyStream13, <RoomEnemyStream14
    .byte <RoomEnemyStream15, <RoomEnemyStream16
    .byte <RoomEnemyStream17, <RoomEnemyStream18
    .byte <RoomEnemyStream19, <RoomEnemyStream20
    .byte <RoomEnemyStream21, <RoomEnemyStream22
    .byte <RoomEnemyStream23, <RoomEnemyStream24
    .byte <RoomEnemyStream25, <RoomEnemyStream26
    .byte <RoomEnemyStream27, <RoomEnemyStream28
    .byte <RoomEnemyStream29, <RoomEnemyStream30
    .byte <RoomEnemyStream31, <RoomEnemyStream32
    .byte <RoomEnemyStream33, <RoomEnemyStream34
    .byte <RoomEnemyStream35, <RoomEnemyStream36
    .byte <RoomEnemyStream37, <RoomEnemyStream38
    .byte <RoomEnemyStream39, <RoomEnemyStream40
    .byte <RoomEnemyStream41, <RoomEnemyStream42
    .byte <RoomEnemyStream43, <RoomEnemyStream44
    .byte <RoomEnemyStream45, <RoomEnemyStream46
    .byte <RoomEnemyStream47, <RoomEnemyStream48
    .byte <RoomEnemyStream49, <RoomEnemyStream50
    .byte <RoomEnemyStream51, <RoomEnemyStream52
    .byte <RoomEnemyStream53

RoomEnemyPointerHighTable:
    .byte >RoomEnemyStream01, >RoomEnemyStream02
    .byte >RoomEnemyStream03, >RoomEnemyStream04
    .byte >RoomEnemyStream05, >RoomEnemyStream06
    .byte >RoomEnemyStream07, >RoomEnemyStream08
    .byte >RoomEnemyStream09, >RoomEnemyStream10
    .byte >RoomEnemyStream11, >RoomEnemyStream12
    .byte >RoomEnemyStream13, >RoomEnemyStream14
    .byte >RoomEnemyStream15, >RoomEnemyStream16
    .byte >RoomEnemyStream17, >RoomEnemyStream18
    .byte >RoomEnemyStream19, >RoomEnemyStream20
    .byte >RoomEnemyStream21, >RoomEnemyStream22
    .byte >RoomEnemyStream23, >RoomEnemyStream24
    .byte >RoomEnemyStream25, >RoomEnemyStream26
    .byte >RoomEnemyStream27, >RoomEnemyStream28
    .byte >RoomEnemyStream29, >RoomEnemyStream30
    .byte >RoomEnemyStream31, >RoomEnemyStream32
    .byte >RoomEnemyStream33, >RoomEnemyStream34
    .byte >RoomEnemyStream35, >RoomEnemyStream36
    .byte >RoomEnemyStream37, >RoomEnemyStream38
    .byte >RoomEnemyStream39, >RoomEnemyStream40
    .byte >RoomEnemyStream41, >RoomEnemyStream42
    .byte >RoomEnemyStream43, >RoomEnemyStream44
    .byte >RoomEnemyStream45, >RoomEnemyStream46
    .byte >RoomEnemyStream47, >RoomEnemyStream48
    .byte >RoomEnemyStream49, >RoomEnemyStream50
    .byte >RoomEnemyStream51, >RoomEnemyStream52
    .byte >RoomEnemyStream53

.assert RoomEnemyPointerHighTable - RoomEnemyPointerLowTable = RoomEnemyStreamCount, error, "unexpected room enemy pointer count"
.assert * - RoomEnemyPointerHighTable = RoomEnemyStreamCount, error, "unexpected room enemy pointer count"

.segment "PRG_ROOM_ENEMY_DATA"

RoomEnemyStream01:
    RoomEnemySpawnLifetime $20
    RoomEnemyRecord $71, $67
    EndRoomEnemyStream
RoomEnemyStream02:
    RoomEnemySpawnLifetime $02
    EndRoomEnemyStream
RoomEnemyStream03:
    RoomEnemySpawnLifetime $82
    RoomEnemyRecord $24, $31
    RoomEnemyRecord $29, $3C
    RoomEnemyRecord $2A, $4B
    RoomEnemyRecord $2A, $B7
    RoomEnemyRecord $36, $9B
    RoomEnemyRecord $70, $B2
    RoomEnemyRecord $78, $91
    RoomEnemyRecord $68, $85
    RoomEnemyRecord $69, $88
    EndRoomEnemyStream
RoomEnemyStream04:
    RoomEnemySpawnLifetime $82
    RoomEnemyRecord $69, $3D
    RoomEnemyRecord $68, $31
    RoomEnemyRecord $2B, $37
    RoomEnemyRecord $2B, $55
    RoomEnemyRecord $2B, $59
    RoomEnemyRecord $2B, $94
    RoomEnemyRecord $2B, $94
    RoomEnemyRecord $2B, $77
    RoomEnemyRecord $2B, $9A
    EndRoomEnemyStream
RoomEnemyStream05:
    RoomEnemySpawnLifetime $82
    RoomEnemyRecord $79, $4E
    RoomEnemyRecord $79, $6E
    RoomEnemyRecord $79, $8E
    RoomEnemyRecord $79, $AE
    RoomEnemyRecord $78, $30
    RoomEnemyRecord $78, $50
    RoomEnemyRecord $78, $70
    RoomEnemyRecord $78, $90
    EndRoomEnemyStream
RoomEnemyStream06:
    RoomEnemySpawnLifetime $82
    RoomEnemyRecord $36, $5B
    RoomEnemyRecord $36, $5E
    RoomEnemyRecord $34, $70
    RoomEnemyRecord $34, $73
    RoomEnemyRecord $36, $9B
    RoomEnemyRecord $36, $9E
    RoomEnemyRecord $74, $C2
    EndRoomEnemyStream
RoomEnemyStream07:
    RoomEnemySpawnLifetime $82
    RoomEnemyRecord $78, $27
    RoomEnemyRecord $2B, $24
    RoomEnemyRecord $2B, $2A
    RoomEnemyRecord $2B, $44
    RoomEnemyRecord $2B, $4A
    RoomEnemyRecord $2B, $84
    RoomEnemyRecord $2B, $8A
    RoomEnemyRecord $2A, $44
    RoomEnemyRecord $2A, $4A
    RoomEnemyRecord $2A, $84
    RoomEnemyRecord $2A, $8A
    RoomEnemyRecord $2A, $A4
    RoomEnemyRecord $2A, $AA
    EndRoomEnemyStream
RoomEnemyStream08:
    RoomEnemySpawnLifetime $82
    RoomEnemyRecord $42, $17
    RoomEnemyRecord $40, $B7
    RoomEnemyRecord $44, $60
    RoomEnemyRecord $44, $80
    RoomEnemyRecord $46, $6E
    RoomEnemyRecord $46, $8E
    EndRoomEnemyStream
RoomEnemyStream09:
    RoomEnemySpawnLifetime $41
    RoomEnemyRecord $78, $52
    RoomEnemyRecord $79, $5C
    RoomEnemyRecord $81, $A7
    EndRoomEnemyStream
RoomEnemyStream10:
    RoomEnemySpawnLifetime $C0
    RoomEnemyRecord $7D, $3D
    RoomEnemyRecord $24, $50
    RoomEnemyRecord $81, $6D
    RoomEnemyRecord $74, $C2
    RoomEnemyRecord $74, $C6
    EndRoomEnemyStream
RoomEnemyStream11:
    RoomEnemySpawnLifetime $82
    RoomEnemyRecord $26, $C2
    RoomEnemyRecord $27, $11
    RoomEnemyRecord $2E, $87
    RoomEnemyRecord $2E, $99
    RoomEnemyRecord $2E, $14
    RoomEnemyRecord $2F, $75
    RoomEnemyRecord $2F, $87
    RoomEnemyRecord $2B, $A3
    EndRoomEnemyStream
RoomEnemyStream12:
    RoomEnemySpawnLifetime $82
    EndRoomEnemyStream
RoomEnemyStream13:
    RoomEnemySpawnLifetime $01
    RoomEnemyRecord $3C, $37
    RoomEnemyRecord $70, $71
    RoomEnemyRecord $71, $7D
    RoomEnemyRecord $28, $9D
    RoomEnemyRecord $29, $9D
    RoomEnemyRecord $2A, $9D
    RoomEnemyRecord $2C, $AD
    RoomEnemyRecord $2D, $AD
    RoomEnemyRecord $2F, $AD
    EndRoomEnemyStream
RoomEnemyStream14:
    RoomEnemySpawnLifetime $81
    RoomEnemyRecord $48, $C7
    EndRoomEnemyStream
RoomEnemyStream15:
    RoomEnemySpawnLifetime $82
    RoomEnemyRecord $46, $2E
    EndRoomEnemyStream
RoomEnemyStream16:
    RoomEnemySpawnLifetime $01
    RoomEnemyRecord $80, $23
    RoomEnemyRecord $80, $2B
    RoomEnemyRecord $80, $81
    RoomEnemyRecord $80, $8D
    RoomEnemyRecord $3E, $75
    RoomEnemyRecord $3C, $79
    RoomEnemyRecord $71, $C5
    RoomEnemyRecord $70, $C9
    RoomEnemyRecord $2B, $97
    EndRoomEnemyStream
RoomEnemyStream17:
    RoomEnemySpawnLifetime $82
    RoomEnemyRecord $81, $6A
    RoomEnemyRecord $81, $6C
    RoomEnemyRecord $2B, $87
    RoomEnemyRecord $2B, $89
    RoomEnemyRecord $2B, $8B
    RoomEnemyRecord $2B, $8D
    RoomEnemyRecord $2B, $A6
    RoomEnemyRecord $2B, $A8
    RoomEnemyRecord $2B, $AA
    RoomEnemyRecord $2B, $AC
    RoomEnemyRecord $74, $C0
    RoomEnemyRecord $74, $C5
    RoomEnemyRecord $74, $CD
    EndRoomEnemyStream
RoomEnemyStream18:
    RoomEnemySpawnLifetime $41
    RoomEnemyRecord $78, $43
    RoomEnemyRecord $81, $1A
    RoomEnemyRecord $81, $38
    RoomEnemyRecord $81, $56
    RoomEnemyRecord $81, $74
    RoomEnemyRecord $81, $92
    EndRoomEnemyStream
RoomEnemyStream19:
    RoomEnemySpawnLifetime $82
    RoomEnemyRecord $68, $4B
    RoomEnemyRecord $2B, $6C
    RoomEnemyRecord $2A, $AA
    EndRoomEnemyStream
RoomEnemyStream20:
    RoomEnemySpawnLifetime $82
    EndRoomEnemyStream
RoomEnemyStream21:
    RoomEnemySpawnLifetime $82
    RoomEnemyRecord $81, $4B
    RoomEnemyRecord $81, $4C
    RoomEnemyRecord $81, $6A
    RoomEnemyRecord $81, $76
    RoomEnemyRecord $81, $77
    RoomEnemyRecord $81, $78
    RoomEnemyRecord $81, $79
    RoomEnemyRecord $79, $80
    RoomEnemyRecord $42, $19
    EndRoomEnemyStream
RoomEnemyStream22:
    RoomEnemySpawnLifetime $82
    RoomEnemyRecord $81, $99
    RoomEnemyRecord $81, $9A
    RoomEnemyRecord $81, $9C
    RoomEnemyRecord $81, $9D
    EndRoomEnemyStream
RoomEnemyStream23:
    RoomEnemySpawnLifetime $82
    RoomEnemyRecord $36, $4B
    RoomEnemyRecord $36, $4D
    RoomEnemyRecord $34, $6B
    RoomEnemyRecord $34, $6D
    RoomEnemyRecord $36, $8B
    RoomEnemyRecord $36, $8D
    RoomEnemyRecord $81, $C9
    RoomEnemyRecord $75, $CE
    EndRoomEnemyStream
RoomEnemyStream24:
    RoomEnemySpawnLifetime $82
    RoomEnemyRecord $69, $7B
    RoomEnemyRecord $81, $16
    RoomEnemyRecord $81, $47
    RoomEnemyRecord $81, $78
    RoomEnemyRecord $81, $AA
    RoomEnemyRecord $79, $29
    RoomEnemyRecord $2A, $81
    RoomEnemyRecord $2A, $97
    RoomEnemyRecord $2B, $85
    RoomEnemyRecord $2B, $A5
    RoomEnemyRecord $2B, $CD
    EndRoomEnemyStream
RoomEnemyStream25:
    RoomEnemySpawnLifetime $C1
    EndRoomEnemyStream
RoomEnemyStream26:
    RoomEnemySpawnLifetime $81
    EndRoomEnemyStream
RoomEnemyStream27:
    RoomEnemySpawnLifetime $82
    RoomEnemyRecord $2E, $66
    RoomEnemyRecord $2E, $88
    RoomEnemyRecord $2E, $A6
    RoomEnemyRecord $2E, $C8
    EndRoomEnemyStream
RoomEnemyStream28:
    RoomEnemySpawnLifetime $82
    RoomEnemyRecord $81, $65
    RoomEnemyRecord $81, $69
    RoomEnemyRecord $81, $81
    RoomEnemyRecord $81, $8D
    RoomEnemyRecord $2B, $67
    RoomEnemyRecord $46, $23
    RoomEnemyRecord $46, $2B
    EndRoomEnemyStream
RoomEnemyStream29:
    RoomEnemySpawnLifetime $C1
    RoomEnemyRecord $7D, $97
    RoomEnemyRecord $4D, $5E
    RoomEnemyRecord $4D, $7E
    RoomEnemyRecord $74, $C1
    RoomEnemyRecord $75, $CD
    EndRoomEnemyStream
RoomEnemyStream30:
    RoomEnemySpawnLifetime $02
    EndRoomEnemyStream
RoomEnemyStream31:
    RoomEnemySpawnLifetime $C1
    RoomEnemyRecord $81, $27
    RoomEnemyRecord $81, $47
    RoomEnemyRecord $81, $67
    RoomEnemyRecord $81, $72
    RoomEnemyRecord $81, $7C
    RoomEnemyRecord $81, $96
    RoomEnemyRecord $81, $98
    EndRoomEnemyStream
RoomEnemyStream32:
    RoomEnemySpawnLifetime $01
    RoomEnemyRecord $36, $36
    RoomEnemyRecord $78, $51
    RoomEnemyRecord $79, $5D
    RoomEnemyRecord $81, $A3
    RoomEnemyRecord $81, $A7
    RoomEnemyRecord $81, $AB
    EndRoomEnemyStream
RoomEnemyStream33:
    RoomEnemySpawnLifetime $82
    RoomEnemyRecord $34, $33
    RoomEnemyRecord $36, $27
    RoomEnemyRecord $36, $3B
    RoomEnemyRecord $2E, $71
    RoomEnemyRecord $2E, $73
    RoomEnemyRecord $2E, $A1
    RoomEnemyRecord $2E, $A3
    RoomEnemyRecord $2F, $61
    RoomEnemyRecord $2F, $63
    RoomEnemyRecord $2F, $91
    RoomEnemyRecord $2F, $93
    EndRoomEnemyStream
RoomEnemyStream34:
    RoomEnemySpawnLifetime $41
    RoomEnemyRecord $44, $70
    RoomEnemyRecord $46, $7E
    EndRoomEnemyStream
RoomEnemyStream35:
    RoomEnemySpawnLifetime $02
    RoomEnemyRecord $81, $53
    RoomEnemyRecord $81, $55
    RoomEnemyRecord $81, $59
    RoomEnemyRecord $81, $5B
    RoomEnemyRecord $81, $91
    RoomEnemyRecord $81, $9D
    RoomEnemyRecord $78, $11
    RoomEnemyRecord $79, $1D
    RoomEnemyRecord $46, $57
    RoomEnemyRecord $46, $77
    RoomEnemyRecord $46, $97
    EndRoomEnemyStream
RoomEnemyStream36:
    RoomEnemySpawnLifetime $82
    RoomEnemyRecord $75, $27
    RoomEnemyRecord $74, $57
    RoomEnemyRecord $75, $87
    RoomEnemyRecord $25, $BE
    EndRoomEnemyStream
RoomEnemyStream37:
    RoomEnemySpawnLifetime $82
    RoomEnemyRecord $24, $40
    RoomEnemyRecord $24, $50
    RoomEnemyRecord $24, $60
    RoomEnemyRecord $24, $70
    RoomEnemyRecord $24, $80
    EndRoomEnemyStream
RoomEnemyStream38:
    RoomEnemySpawnLifetime $82
    RoomEnemyRecord $81, $33
    RoomEnemyRecord $81, $3B
    RoomEnemyRecord $81, $74
    RoomEnemyRecord $81, $7A
    RoomEnemyRecord $81, $86
    RoomEnemyRecord $81, $88
    RoomEnemyRecord $46, $67
    RoomEnemyRecord $36, $A7
    EndRoomEnemyStream
RoomEnemyStream39:
    RoomEnemySpawnLifetime $42
    RoomEnemyRecord $28, $27
    RoomEnemyRecord $28, $6D
    RoomEnemyRecord $29, $60
    RoomEnemyRecord $29, $B7
    RoomEnemyRecord $30, $6C
    RoomEnemyRecord $32, $51
    RoomEnemyRecord $34, $37
    RoomEnemyRecord $36, $A7
    EndRoomEnemyStream
RoomEnemyStream40:
    RoomEnemySpawnLifetime $82
    RoomEnemyRecord $26, $A2
    RoomEnemyRecord $26, $AC
    RoomEnemyRecord $26, $B5
    RoomEnemyRecord $26, $B9
    RoomEnemyRecord $27, $24
    RoomEnemyRecord $27, $2A
    RoomEnemyRecord $2D, $6E
    RoomEnemyRecord $79, $77
    EndRoomEnemyStream
RoomEnemyStream41:
    RoomEnemySpawnLifetime $82
    RoomEnemyRecord $44, $51
    RoomEnemyRecord $46, $5D
    EndRoomEnemyStream
RoomEnemyStream42:
    RoomEnemySpawnLifetime $82
    RoomEnemyRecord $68, $C7
    RoomEnemyRecord $36, $77
    RoomEnemyRecord $81, $16
    RoomEnemyRecord $81, $18
    RoomEnemyRecord $80, $45
    RoomEnemyRecord $80, $49
    RoomEnemyRecord $81, $94
    RoomEnemyRecord $81, $9A
    EndRoomEnemyStream
RoomEnemyStream43:
    RoomEnemySpawnLifetime $82
    RoomEnemyRecord $44, $41
    RoomEnemyRecord $44, $71
    RoomEnemyRecord $44, $A1
    RoomEnemyRecord $46, $4D
    RoomEnemyRecord $46, $7D
    RoomEnemyRecord $46, $AD
    EndRoomEnemyStream
RoomEnemyStream44:
    RoomEnemySpawnLifetime $82
    RoomEnemyRecord $80, $1B
    RoomEnemyRecord $80, $5A
    RoomEnemyRecord $81, $11
    RoomEnemyRecord $81, $34
    RoomEnemyRecord $81, $42
    RoomEnemyRecord $81, $4D
    RoomEnemyRecord $81, $70
    RoomEnemyRecord $81, $76
    RoomEnemyRecord $81, $95
    RoomEnemyRecord $81, $98
    EndRoomEnemyStream
RoomEnemyStream45:
    RoomEnemySpawnLifetime $E1
    RoomEnemyRecord $81, $62
    RoomEnemyRecord $81, $6C
    RoomEnemyRecord $81, $A2
    RoomEnemyRecord $81, $AC
    RoomEnemyRecord $79, $A6
    RoomEnemyRecord $78, $A8
    EndRoomEnemyStream
RoomEnemyStream46:
    RoomEnemySpawnLifetime $41
    RoomEnemyRecord $70, $5A
    RoomEnemyRecord $70, $16
    RoomEnemyRecord $70, $38
    RoomEnemyRecord $70, $7C
    RoomEnemyRecord $70, $42
    RoomEnemyRecord $70, $64
    RoomEnemyRecord $70, $86
    RoomEnemyRecord $70, $A8
    EndRoomEnemyStream
RoomEnemyStream47:
    RoomEnemySpawnLifetime $42
    RoomEnemyRecord $81, $1A
    RoomEnemyRecord $81, $1E
    RoomEnemyRecord $81, $55
    RoomEnemyRecord $81, $7B
    RoomEnemyRecord $81, $7E
    RoomEnemyRecord $81, $9E
    RoomEnemyRecord $81, $B0
    RoomEnemyRecord $81, $CA
    EndRoomEnemyStream
RoomEnemyStream48:
    RoomEnemySpawnLifetime $82
    RoomEnemyRecord $81, $12
    RoomEnemyRecord $81, $14
    RoomEnemyRecord $81, $1B
    RoomEnemyRecord $81, $1D
    RoomEnemyRecord $81, $1E
    RoomEnemyRecord $81, $5A
    RoomEnemyRecord $81, $65
    RoomEnemyRecord $81, $67
    RoomEnemyRecord $81, $83
    RoomEnemyRecord $81, $88
    RoomEnemyRecord $81, $8B
    RoomEnemyRecord $81, $8E
    EndRoomEnemyStream
RoomEnemyStream49:
    RoomEnemySpawnLifetime $82
    RoomEnemyRecord $80, $AD
    RoomEnemyRecord $1D, $67
    RoomEnemyRecord $80, $A1
    EndRoomEnemyStream
RoomEnemyStream50:
    RoomEnemySpawnLifetime $82
    RoomEnemyRecord $80, $21
    RoomEnemyRecord $81, $2D
    RoomEnemyRecord $68, $38
    RoomEnemyRecord $79, $97
    RoomEnemyRecord $75, $73
    RoomEnemyRecord $26, $B1
    RoomEnemyRecord $27, $4D
    RoomEnemyRecord $29, $A6
    RoomEnemyRecord $29, $AA
    RoomEnemyRecord $2A, $B7
    RoomEnemyRecord $36, $36
    RoomEnemyRecord $30, $A3
    RoomEnemyRecord $32, $AB
    EndRoomEnemyStream
RoomEnemyStream51:
    RoomEnemySpawnLifetime $82
    RoomEnemyRecord $74, $57
    RoomEnemyRecord $6D, $77
    RoomEnemyRecord $1C, $43
    RoomEnemyRecord $1C, $4B
    RoomEnemyRecord $1C, $B7
    EndRoomEnemyStream
RoomEnemyStream52:
    RoomEnemySpawnLifetime $82
    EndRoomEnemyStream
RoomEnemyStream53:
    RoomEnemySpawnLifetime $82
    EndRoomEnemyStream

.assert * - RoomEnemyStream01 = $02D6, error, "unexpected room enemy data size"
