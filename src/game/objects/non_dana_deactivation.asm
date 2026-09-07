; Clear and move every non-Dana object record offscreen

.segment "PRG_DEACTIVATE_NON_DANA_OBJECTS"

DeactivateAllNonDanaObjects:
    LDX #ObjectRecordCount - 2

DeactivateNextNonDanaObject:
    JSR LoadObjectPointer
    LDY #$00
    TYA
    STA (TempPointer00),Y
    LDY #$07
    LDA #$F8
    STA (TempPointer00),Y
    DEX
    BPL DeactivateNextNonDanaObject
    RTS
