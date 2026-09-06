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
