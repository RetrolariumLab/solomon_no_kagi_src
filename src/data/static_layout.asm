; Non-code filler between the NMI PPU services and Reset

.segment "PRG_PRE_STARTUP_PADDING"

PreStartupPadding:
.if SolomonRevision = SolomonRevisionEurope
    .res $1E, $FF
.else
    .byte $00
    .byte $ff, $00, $ff, $00, $ff, $00, $ff, $00, $ff, $00, $ff, $00, $ff, $ff, $00, $ff
    .byte $00, $ff, $00, $ff, $00, $ff, $00, $ff, $00, $ff, $00, $ff, $00
.endif

.assert * - PreStartupPadding = $1E, error, "unexpected pre-startup padding size"

; Non-code filler between the RoomMap PPU helpers and MainGameplayThread

.segment "PRG_MAIN_THREAD_PADDING"

MainThreadPadding:
.if SolomonRevision = SolomonRevisionEurope
    .res $D5, $FF
.else
    .byte $ff, $00, $ff, $00, $ff, $00, $ff, $00, $ff, $00, $ff, $00, $ff, $ff, $00, $ff
    .byte $00, $ff, $00, $ff, $00, $ff, $00, $ff, $00, $ff, $00, $ff, $00, $00, $ff, $00
    .byte $ff, $00, $ff, $00, $ff, $00, $ff, $00, $ff, $00, $ff, $00, $ff, $ff, $00, $ff
    .byte $00, $ff, $00, $ff, $00, $ff, $00, $ff, $00, $ff, $00, $ff, $00, $00, $ff, $00
    .byte $ff, $00, $ff, $00, $ff, $00, $ff, $00, $ff, $00, $fb, $00, $ff, $ff, $00, $ff
    .byte $00, $ff, $00, $ff, $00, $ff, $00, $ff, $00, $ff, $00, $ff, $00, $00, $ff, $00
    .byte $ff, $00, $ff, $00, $ff, $00, $ff, $00, $ff, $00, $ff, $00, $ff, $ff, $00, $ff
    .byte $00, $ff, $00, $ff, $00, $ff, $00, $ff, $00, $ff, $00, $ff, $00, $00, $ff, $00
    .byte $ff, $00, $ff, $00, $ff, $00, $ff, $00, $ff, $00, $ff, $00, $ff, $ff, $00, $ff
    .byte $00, $ff, $00, $ff, $00, $ff, $00, $ff, $00, $ff, $00, $ff, $00, $00, $ff, $00
    .byte $ff, $00, $ff, $00, $ff, $00, $ff, $00, $ff, $00, $ff, $00, $ff, $ff, $00, $ff
    .byte $00, $ff, $00, $ff, $00, $ff, $00, $ff, $00, $ff, $00, $ff, $00, $00, $ff, $00
    .byte $ff, $00, $ff, $00, $ff, $00, $ff, $00, $ff, $00, $ff, $00, $ff, $ff, $00, $ff
    .byte $00, $ff, $00, $ff, $00, $ff, $00, $ff, $00, $ff, $00, $ff, $00
.endif

.assert * - MainThreadPadding = $DD - (SolomonRevision = SolomonRevisionEurope) * 8, error, "unexpected main-thread padding size"

; Split pointer tables and 18 ROM-resident PPU update streams

PpuUpdateRepeat = $00
PpuUpdateLiteral = $40

.macro PpuUpdateCommand address, flags, count
    .byte >address, <address, flags | (count - 1)
.endmacro

.segment "PRG_STATIC_PPU_UPDATE_POINTERS"

StaticPpuUpdatePointerLowTable:
    .byte <StaticPpuUpdateStream00
    .byte <StaticPpuUpdateStream01
    .byte <StaticPpuUpdateStream02
    .byte <StaticPpuUpdateStream03
    .byte <StaticPpuUpdateStream04
    .byte <StaticPpuUpdateStream05
    .byte <StaticPpuUpdateStream06
    .byte <StaticPpuUpdateStream07
    .byte <StaticPpuUpdateStream08
    .byte <StaticPpuUpdateStream09
    .byte <StaticPpuUpdateStream10
    .byte <StaticPpuUpdateStream11
    .byte <StaticPpuUpdateStream12
    .byte <StaticPpuUpdateStream13
    .byte <StaticPpuUpdateStream14
    .byte <StaticPpuUpdateStream15
    .byte <StaticPpuUpdateStream16
    .byte <StaticPpuUpdateStream17

StaticPpuUpdatePointerHighTable:
    .byte >StaticPpuUpdateStream00
    .byte >StaticPpuUpdateStream01
    .byte >StaticPpuUpdateStream02
    .byte >StaticPpuUpdateStream03
    .byte >StaticPpuUpdateStream04
    .byte >StaticPpuUpdateStream05
    .byte >StaticPpuUpdateStream06
    .byte >StaticPpuUpdateStream07
    .byte >StaticPpuUpdateStream08
    .byte >StaticPpuUpdateStream09
    .byte >StaticPpuUpdateStream10
    .byte >StaticPpuUpdateStream11
    .byte >StaticPpuUpdateStream12
    .byte >StaticPpuUpdateStream13
    .byte >StaticPpuUpdateStream14
    .byte >StaticPpuUpdateStream15
    .byte >StaticPpuUpdateStream16
    .byte >StaticPpuUpdateStream17

.segment "PRG_STATIC_PPU_UPDATE_STREAMS"

StaticPpuUpdateStream00:
    PpuUpdateCommand $2043, PpuUpdateLiteral, 17
    .byte $1c, $0c, $18, $1b, $0e, $24, $24, $15, $12
    .byte $0f, $0e, $24, $0f, $0a, $12, $1b, $22
    PpuUpdateCommand $2069, PpuUpdateLiteral, 5
    .byte $01, $00, $00, $00, $00
    PpuUpdateCommand $23C0, PpuUpdateRepeat, 5
    .byte $a0
    PpuUpdateCommand $23C5, PpuUpdateRepeat, 3
    .byte $50, $00

StaticPpuUpdateStream01:
    PpuUpdateCommand $3F00, PpuUpdateLiteral, 16
    .byte $0f, $0f, $10, $30, $0f, $0f, $27, $30
    .byte $0f, $0f, $16, $30, $0f, $0f, $27, $38, $00

StaticPpuUpdateStream02:
    PpuUpdateCommand $2168, PpuUpdateLiteral, 14
    .byte $1d, $11, $0a, $17, $14, $24, $22
    .byte $18, $1e, $24, $0d, $0a, $17, $0a, $00

StaticPpuUpdateStream03:
    PpuUpdateCommand $21C4, PpuUpdateLiteral, 22
    .byte $22, $18, $1e, $24, $1b, $0e, $15, $0e, $0a, $1c, $0e
    .byte $0d, $24, $1d, $11, $12, $1c, $24, $1b, $18, $18, $16, $00

StaticPpuUpdateStream04:
    PpuUpdateCommand $2208, PpuUpdateLiteral, 13
    .byte $1d, $1b, $22, $24, $17, $0e, $21
    .byte $1d, $24, $1b, $18, $18, $16, $00

StaticPpuUpdateStream06:
    PpuUpdateCommand $21AA, PpuUpdateLiteral, 9
    .byte $10, $0a, $16, $0e, $24, $18, $1f, $0e, $1b, $00

StaticPpuUpdateStream07:
    PpuUpdateCommand $23E8, PpuUpdateRepeat, 24
    .byte $ff, $00

StaticPpuUpdateStream08:
    PpuUpdateCommand $2322, PpuUpdateRepeat, 28
    .byte $24
    PpuUpdateCommand $2369, PpuUpdateRepeat, 12
    .byte $24
    PpuUpdateCommand $23A3, PpuUpdateRepeat, 24
    .byte $24
    PpuUpdateCommand $22A4, PpuUpdateRepeat, 21
    .byte $24
    PpuUpdateCommand $22E2, PpuUpdateRepeat, 25
    .byte $24, $00

StaticPpuUpdateStream09:
    PpuUpdateCommand $2863, PpuUpdateLiteral, 25
    .byte $1c, $0c, $18, $1b, $0e, $24, $24, $24, $11, $12, $24, $1c, $0c
    .byte $18, $1b, $0e, $24, $24, $24, $11, $12, $24, $10, $0d, $1f, $00

StaticPpuUpdateStream10:
    PpuUpdateCommand $29E6, PpuUpdateLiteral, 17
    .byte $19, $1e, $1c, $11, $24, $1c, $1d, $0a, $1b
    .byte $1d, $24, $0b, $1e, $1d, $1d, $18, $17, $00

StaticPpuUpdateStream11:
    PpuUpdateCommand $2A26, PpuUpdateLiteral, 16
    .byte $2a, $24, $1d, $0e, $0c, $16, $18, $25
    .byte $15, $1d, $0d, $29, $01, $09, $08
.if SolomonRevision = SolomonRevisionEurope
    .byte $09
.else
    .byte $07
.endif
    .byte $00

StaticPpuUpdateStream12:
    PpuUpdateCommand $23E8, PpuUpdateRepeat, 24
    .byte $00, $00

StaticPpuUpdateStream14:
    PpuUpdateCommand $2BD0, PpuUpdateRepeat, 24
    .byte $00, $00

StaticPpuUpdateStream15:
    PpuUpdateCommand $2907, PpuUpdateLiteral, 16
    .byte $1c, $18, $15, $18, $16, $18, $17, $3b
    .byte $1c, $24, $14, $0e, $22, $24, $1d, $16, $00

StaticPpuUpdateStream16:
    PpuUpdateCommand $2983, PpuUpdateLiteral, 24
    .byte $1d, $16, $24, $0a, $17, $0d, $24, $2a
    .byte $24, $01, $09, $08
.if SolomonRevision = SolomonRevisionEurope
    .byte $09
.else
    .byte $07
.endif
    .byte $24, $1d, $0e
    .byte $0c, $16, $18, $25, $15, $1d, $0d, $29, $00

StaticPpuUpdateStream17:
.if SolomonRevision = SolomonRevisionEurope
    PpuUpdateCommand $2A05, PpuUpdateLiteral, 20
    .byte $15, $12, $0c, $0e, $17, $1c, $0e, $0d, $24, $0b
    .byte $22, $24, $17, $12, $17, $1d, $0e, $17, $0d, $18, $00
.else
    PpuUpdateCommand $29C9, PpuUpdateLiteral, 11
    .byte $15, $12, $0c, $0e, $17, $1c, $0e, $0d, $24, $0b, $22
    PpuUpdateCommand $2A03, PpuUpdateLiteral, 24
    .byte $17, $12, $17, $1d, $0e, $17, $0d, $18
    .byte $24, $18, $0f, $24, $0a, $16, $0e, $1b
    .byte $12, $0c, $0a, $24, $12, $17, $0c, $29, $00
.endif

StaticPpuUpdateStream05:
    PpuUpdateCommand $3F00, PpuUpdateLiteral, 16
    .byte $0f, $2c, $10, $30, $0f, $27, $37, $16
    .byte $0f, $27, $3c, $30, $ff, $2c, $02, $30, $00

StaticPpuUpdateStream13:
    PpuUpdateCommand $3F00, PpuUpdateLiteral, 16
    .byte $0f, $0f, $0f, $30, $0f, $27, $37, $16
    .byte $0f, $0f, $0f, $30, $0f, $0f, $0f, $30, $00

; Four-byte patterns consumed in descending byte order by the direct PPU writer

.segment "PRG_REPEATED_PPU_PATTERNS"

RepeatedPpuPattern0:
    .byte $a3, $a6, $a6, $a4

RepeatedPpuPattern1:
    .byte $aa, $a2, $a2, $a0

RepeatedPpuPattern2:
    .byte $a4, $a1, $a1, $a0

RepeatedPpuPattern3:
    .byte $a3, $ab, $ab, $aa

.assert * - RepeatedPpuPattern0 = RepeatedPpuPatternSize * 4, error, "repeated PPU pattern data size changed"

; Width, start-index, and row-count descriptors for direct nametable clearing

.segment "PRG_NAMETABLE_CLEAR_DATA"

NametableClearDescriptors:
    .byte 32, $00, 26  ; 32 columns from PPU $2000 for 26 rows
    .byte 32, $20, 26  ; 32 columns from PPU $2080 for 26 rows
    .byte 30, $20, 24  ; 30 columns from PPU $2080 for 24 rows

.assert * - NametableClearDescriptors = NametableClearDescriptorSize * 3, error, "nametable clear descriptor count changed"

; Single-byte PPU update template for the collected-fairy HUD field

.segment "PRG_GAMEPLAY_HUD_DATA"

FairyCountDisplayPpuUpdateTemplate:
    .byte $20, $71, $40, $00, $00

; Tile mappings and reverse-copy headers for the fireball inventory HUD

.segment "PRG_FIREBALL_INVENTORY_DISPLAY_DATA"

FireballInventoryTopTileByValue:
    .byte FireballInventoryTopUnusedTile, $b0, $b1

FireballInventoryTopRowHeaderReversed:
    .byte $4a, $54, $20

FireballInventoryBottomRowHeaderReversed:
    .byte $4a, $74, $20

; Score digit and amount lookup tables used by collectible bonus items

.segment "PRG_ITEM_SCORE_TABLES"

ItemBonusScoreDigitIndices:
    .byte $05, $04, $03, $02, $01

ItemBonusScoreAmounts:
    .byte $01, $02, $05

.assert ItemBonusScoreAmounts - ItemBonusScoreDigitIndices = 5, error, "item score digit table must contain five entries"
.assert * - ItemBonusScoreAmounts = 3, error, "item score amount table must contain three entries"

; Item type $00-$1C handlers selected by the inline appendix dispatcher

.segment "PRG_ITEM_HANDLER_TABLE"

ItemInteractionHandlerTable:
    .addr CollectRoomKey
    .addr EnterRoomDoor
    .addr AwardBlueCrystalScore
    .addr ApplySmallFireballBottleItem
    .addr AwardType04Or06Score
    .addr ApplyRedTzoItem
    .addr AwardType04Or06Score
    .addr ApplyLargeFireballBottleItem
    .addr IncreaseInventorySlotLimit
    .addr QueueFairyItem
    .addr FinishMapTileInteraction
    .addr ApplyDoubleTimerItem
    .addr ApplyQuintupleTimerItem
    .addr SetTimerTo10000
    .addr SetTimerTo05000
    .addr ApplySmallFireballBottleItem
    .addr ApplyLargeFireballBottleItem
    .addr IncreaseInventorySlotLimit
    .addr QueueFairyItem
    .addr ApplyRedBottleKillAllEnemiesItem
    .addr FinishMapTileInteraction
    .addr ApplyBlueTzoItem
    .addr ApplyConstellationSymbolItem
    .addr ApplyConstellationSymbolItem
    .addr ApplyConstellationSymbolItem
    .addr ApplyConstellationSymbolItem
    .addr ApplySolomonSealItem
    .addr ApplySolomonPageItem
    .addr ApplyGoldenWingsItem

ItemInteractionHandlerCount = (* - ItemInteractionHandlerTable) / 2
.assert ItemInteractionHandlerCount = $1D, error, "item handler table must contain 29 entries"

; Countdown thresholds and the two timer-warning PPU update streams

.segment "PRG_TIMER_WARNING_DATA"

; This three-byte prefix matches the timer HUD writer header at $A271, but no
; direct reference to this copy has been proved yet
PreTimerWarningTableBytes:
    .byte $20, $69, $44

; The fourth BCD threshold is also the high address byte of the following PPU
; command. The original data deliberately shares that byte
TimerWarningThresholds:
    .byte $02, $04, $10

EnterTimerWarningPpuUpdate:
    .byte $23, $c2, $41, $f0, $30, $00

LeaveTimerWarningPpuUpdate:
    .byte $23, $c2, $41, $a0, $20, $00

; One quadrant of the transition object's seven-bit sine magnitude

.segment "PRG_QUARTER_SINE_DATA"

QuarterSineTable:
    .byte $00, $06, $0c, $13, $19, $1f, $25, $2b
    .byte $31, $37, $3d, $42, $48, $4d, $52, $57
    .byte $5b, $60, $63, $68, $6b, $6f, $72, $74
    .byte $77, $79, $7b, $7c, $7e, $7f, $7f, $7f
