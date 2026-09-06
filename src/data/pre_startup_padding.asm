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
