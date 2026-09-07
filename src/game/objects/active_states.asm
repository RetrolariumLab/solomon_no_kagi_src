; Replace byte 0 for every active non-Dana object record

.segment "PRG_SET_ACTIVE_OBJECT_STATES"

SetActiveNonDanaObjectState:
    LDX #ObjectRecordCount - 2

SetNextActiveNonDanaObjectState:
    JSR LoadObjectPointer
    LDY #$00
    LDA (TempPointer00),Y
    BPL SkipInactiveNonDanaObject
    LDA $02
    STA (TempPointer00),Y

SkipInactiveNonDanaObject:
    DEX
    BPL SetNextActiveNonDanaObjectState
    RTS
