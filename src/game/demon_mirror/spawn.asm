; Allocate placeholder enemy slots for one or both scheduled Demon Mirrors

.segment "PRG_DEMON_MIRROR_SPAWN"

DemonMirrorCount = $02
DemonMirrorPlaceholderState = $80

SpawnScheduledDemonMirrorObjects:
    STA TempPointer02
    LDX #DemonMirrorCount - 1
    STX $03

SpawnNextScheduledDemonMirror:
    ROL TempPointer02
    BCC AdvanceDemonMirrorSpawn
    JSR FindFreeEnemySlotIndex
    BCC AdvanceDemonMirrorSpawn
    TXA
    LDX $03
    STA DemonMirrorEnemySlots,X
    STA SpawnSlotIndex
    LDA #DemonMirrorPlaceholderState
    LDY #$00
    STA (TempPointer04),Y
    JSR InitializeDemonMirrorObject
    SEC

AdvanceDemonMirrorSpawn:
    DEC $03
    BPL SpawnNextScheduledDemonMirror
    ROR TempPointer02
    ROR TempPointer02
    LDA DemonMirrorSpawnState
    AND #DemonMirrorPhaseMask
    ORA TempPointer02
    STA DemonMirrorSpawnState
    RTS
