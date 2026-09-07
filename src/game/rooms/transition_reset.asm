; Gameplay-exit presentation data and shared room-transition reset

.segment "PRG_GAMEPLAY_EXIT_DATA"

LifeLossPpuMaskCycle:
    .byte $00, $21, $00, $81

; Static PPU program displaying "TIME OVER."
TimeOverPpuUpdateStream:
    .byte $21, $EA, $48
    .byte $1D, $12, $16, $0E, $24, $18, $1F, $0E, $1B, $23
    .byte $DA, $42, $C0, $F0, $F0, $00

; Copied to PpuUpdateBuffer and patched with the calculated result value
PostGameResultPpuTemplate:
    .byte $21, $E9, $4A
    .byte $22, $18, $1E, $1B, $24, $10, $0D, $1F, $24, $24, $24
    .byte $00

.assert * - LifeLossPpuMaskCycle = $26, error, "unexpected gameplay-exit data size"

.segment "PRG_ROOM_TRANSITION_RESET"

RoomTransitionWorkerContext = $03
RoomTransitionGameplayFlagsMask = $BB
RoomTransitionSoundEffect = $03

ResetRoomTransitionState:
    LDX #RoomTransitionWorkerContext
    JSR ResetOtherSecondaryThreads
    LDA GameplayFlags
    AND #RoomTransitionGameplayFlagsMask
    STA GameplayFlags
    LDA #$00
    STA FireballActive
    LDY #RoomTransitionSoundEffect
    JSR AddSoundEffect
    RTS
