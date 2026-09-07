; AI-state and spark headers shared by room transition presentations

.segment "PRG_ROOM_ENTRY_ANIMATION_DATA"

RoomEntryAiStateTemplate:
    .byte $00, $00, $78, $78, $60, $00, $fe, $80, $00

RoomEntrySparkHeader:
    .byte $c0, $1c, $ff, $00

TransitionAiCoordinateSourceOffsets:
    .byte $00, $02, $01, $03
