; Mutable palette-update template copied into the shared NMI program buffer

.segment "PRG_ROOM_LOAD_PALETTE"

RoomLoadPaletteTemplate:
    .byte $3f, $00, $5f
    .byte $0f, $07, $10, $30, $0f, $07, $27, $30
    .byte $0f, $07, $2c, $30, $0f, $07, $27, $38
    .byte $0f, $26, $29, $30, $0f, $30, $16, $27
    .byte $0f, $16, $10, $30, $0f, $2c, $26, $30
    .byte $00

; Initial AI and gameplay-object values for the room-clear presentation

.segment "PRG_ROOM_CLEAR_DATA"

RoomClearAiStateTemplate:
    .byte $00, $00, $00, $00, $03, $00, $01, $80

RoomClearObjectHeaderPredecessors:
    .byte $00, $c0, $1c, $ff

RoomClearObjectXPositions:
    .byte $28, $c8

; Room-index palette selection and Dana state preload values

.segment "PRG_ROOM_LOAD_DATA"

RoomLoadDanaHeaderPredecessors:
    .byte $00, $e0, $00, $ff

RoomPaletteColorByRoomGroup:
    .byte $07, $1c, $04, $09, $1c, $07, $04
    .byte $07, $09, $1c, $07, $04, $80, $80

RoomPaletteColorOffsets:
    .byte $01, $05, $09, $0d

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

; AI-state and spark headers shared by room transition presentations

.segment "PRG_ROOM_ENTRY_ANIMATION_DATA"

RoomEntryAiStateTemplate:
    .byte $00, $00, $78, $78, $60, $00, $fe, $80, $00

RoomEntrySparkHeader:
    .byte $c0, $1c, $ff, $00

TransitionAiCoordinateSourceOffsets:
    .byte $00, $02, $01, $03

; Constellation, timer-rate, and special-room tables used by room item decoding

.segment "PRG_ROOM_ITEM_DECODE_DATA"

ConstellationTilePatterns:
    .byte $28, $c1, $2a, $c3, $c0, $c5, $c2, $c7, $c4, $29, $c6, $2b
    .byte $28, $c9, $2a, $cb, $c8, $cd, $ca, $cf, $cc, $29, $ce, $2b
    .byte $28, $d1, $2a, $d3, $d0, $d5, $d2, $d7, $d4, $29, $d6, $2b
    .byte $28, $d9, $2a, $db, $d8, $dd, $da, $df, $dc, $29, $de, $2b
    .byte $28, $e1, $2a, $e3, $e0, $e5, $e2, $e7, $e4, $29, $e6, $2b
    .byte $28, $e9, $2a, $eb, $e8, $ed, $ea, $ef, $ec, $29, $ee, $2b
    .byte $28, $f1, $2a, $f3, $f0, $f5, $f2, $f7, $f4, $29, $f6, $2b
    .byte $28, $f9, $2a, $fb, $f8, $fd, $fa, $ff, $fc, $29, $fe, $2b

ConstellationTileLowBits:
    .byte $03, $03, $03, $03, $02, $03, $00, $02, $00, $01, $00, $01

TimerDecrementSpeedTable:
.if SolomonRevision = SolomonRevisionEurope
    .byte $36, $29, $1e
.else
    .byte $2d, $22, $19
.endif

SpecialRoomItemPositions:
    .byte $22, $69, $b2, $2c, $86, $bc, $24, $88
    .byte $b4, $2a, $65, $ba, $6c, $87, $62, $3c
    .byte $69, $a2, $ac, $32, $29, $66, $b5, $25
    .byte $b9, $72, $a7, $7c, $67, $37, $84, $8a

SpecialRoomItemTypes:
    .byte $ab, $8c, $aa, $88, $91, $ab, $ac, $98
    .byte $94, $ac, $aa, $88, $aa, $ad, $aa, $ab

.assert SpecialRoomItemPositions + 1 - TimerDecrementSpeedTable = 4, error, "overlapping timer speed table changed"
.assert ConstellationTileLowBits - ConstellationTilePatterns = ConstellationPatternSize * 4, error, "constellation patterns changed"
.assert * - SpecialRoomItemTypes = SpecialRoomPlacementCount, error, "special-room item type count changed"
