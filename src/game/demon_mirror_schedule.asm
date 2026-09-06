; Sample both Demon Mirror bit schedules from the shared 16-bit frame counter

.segment "PRG_DEMON_MIRROR_SCHEDULE"

DemonMirrorPhaseMask = $3F
DemonMirrorLoopHalfMask = $20
DemonMirrorSchedulePendingMask = $C0
DemonMirrorScheduleBitMask = $07
DemonMirrorMaximumActiveEnemies = $0E
DemonMirrorScheduleCount = 16
DemonMirrorScheduleSize = 8
DemonMirrorEnemySetCount = 17

UpdateDemonMirrorSpawnSchedule:
    LDA DemonMirrorSpawnTimerHi
    ASL A
    ASL A
    AND #$3C
    STA TempPointer00
    LDA DemonMirrorSpawnTimerLo
    ROL A
    ROL A
    ROL A
    AND #$03
    ORA TempPointer00
    TAX
    LDA DemonMirrorSpawnState
    STA TempPointer00 + 1
    AND #$1F
    STA TempPointer00
    LDA #DemonMirrorSchedulePendingMask
    AND TempPointer00 + 1
    BNE FinishDemonMirrorScheduleUpdate
    TXA
    AND #$1F
    CMP TempPointer00
    BEQ FinishDemonMirrorScheduleUpdate
    STX TempPointer00
    LDA #DemonMirrorLoopHalfMask
    AND TempPointer00 + 1
    ORA TempPointer00
    STA DemonMirrorSpawnState
    TAY
    AND #DemonMirrorScheduleBitMask
    STA TempPointer00
    TAX
    TYA
    LSR A
    LSR A
    LSR A
    TAY
    LDA (DemonMirrorSchedulePointers),Y

SelectFirstDemonMirrorScheduleBit:
    ASL A
    DEX
    BPL SelectFirstDemonMirrorScheduleBit
    JSR CheckDemonMirrorSpawnCapacity
    ROL TempPointer00 + 1
    LDX TempPointer00
    LDA (DemonMirrorSchedulePointers + 2),Y

SelectSecondDemonMirrorScheduleBit:
    ASL A
    DEX
    BPL SelectSecondDemonMirrorScheduleBit
    JSR CheckDemonMirrorSpawnCapacity
    LDA TempPointer00 + 1
    ROR A
    ROR A
    AND #DemonMirrorSchedulePendingMask
    BEQ FinishDemonMirrorScheduleUpdate
    JMP SpawnScheduledDemonMirrorObjects

CheckDemonMirrorSpawnCapacity:
    BCC FinishDemonMirrorScheduleUpdate
    LDA #DemonMirrorMaximumActiveEnemies
    CMP ActiveEnemyCount

FinishDemonMirrorScheduleUpdate:
    RTS

.segment "PRG_DEMON_MIRROR_SCHEDULE_POINTERS"

DemonMirrorSchedulePointerLowTable:
    .byte <DemonMirrorSchedule00, <DemonMirrorSchedule01
    .byte <DemonMirrorSchedule02, <DemonMirrorSchedule03
    .byte <DemonMirrorSchedule04, <DemonMirrorSchedule05
    .byte <DemonMirrorSchedule06, <DemonMirrorSchedule07
    .byte <DemonMirrorSchedule08, <DemonMirrorSchedule09
    .byte <DemonMirrorSchedule10, <DemonMirrorSchedule11
    .byte <DemonMirrorSchedule12, <DemonMirrorSchedule13
    .byte <DemonMirrorSchedule14, <DemonMirrorSchedule15

DemonMirrorSchedulePointerHighTable:
    .byte >DemonMirrorSchedule00, >DemonMirrorSchedule01
    .byte >DemonMirrorSchedule02, >DemonMirrorSchedule03
    .byte >DemonMirrorSchedule04, >DemonMirrorSchedule05
    .byte >DemonMirrorSchedule06, >DemonMirrorSchedule07
    .byte >DemonMirrorSchedule08, >DemonMirrorSchedule09
    .byte >DemonMirrorSchedule10, >DemonMirrorSchedule11
    .byte >DemonMirrorSchedule12, >DemonMirrorSchedule13
    .byte >DemonMirrorSchedule14, >DemonMirrorSchedule15

.assert DemonMirrorSchedulePointerHighTable - DemonMirrorSchedulePointerLowTable = DemonMirrorScheduleCount, error, "unexpected Demon Mirror schedule pointer count"
.assert * - DemonMirrorSchedulePointerHighTable = DemonMirrorScheduleCount, error, "unexpected Demon Mirror schedule pointer count"

.segment "PRG_DEMON_MIRROR_ENEMY_SET_POINTERS"

DemonMirrorEnemySetPointerLowTable:
    .byte <DemonMirrorEnemySet00, <DemonMirrorEnemySet01
    .byte <DemonMirrorEnemySet02, <DemonMirrorEnemySet03
    .byte <DemonMirrorEnemySet04, <DemonMirrorEnemySet05
    .byte <DemonMirrorEnemySet06, <DemonMirrorEnemySet07
    .byte <DemonMirrorEnemySet08, <DemonMirrorEnemySet09
    .byte <DemonMirrorEnemySet10, <DemonMirrorEnemySet11
    .byte <DemonMirrorEnemySet12, <DemonMirrorEnemySet13
    .byte <DemonMirrorEnemySet14, <DemonMirrorEnemySet15
    .byte <DemonMirrorEnemySet16

DemonMirrorEnemySetPointerHighTable:
    .byte >DemonMirrorEnemySet00, >DemonMirrorEnemySet01
    .byte >DemonMirrorEnemySet02, >DemonMirrorEnemySet03
    .byte >DemonMirrorEnemySet04, >DemonMirrorEnemySet05
    .byte >DemonMirrorEnemySet06, >DemonMirrorEnemySet07
    .byte >DemonMirrorEnemySet08, >DemonMirrorEnemySet09
    .byte >DemonMirrorEnemySet10, >DemonMirrorEnemySet11
    .byte >DemonMirrorEnemySet12, >DemonMirrorEnemySet13
    .byte >DemonMirrorEnemySet14, >DemonMirrorEnemySet15
    .byte >DemonMirrorEnemySet16

.assert DemonMirrorEnemySetPointerHighTable - DemonMirrorEnemySetPointerLowTable = DemonMirrorEnemySetCount, error, "unexpected Demon Mirror enemy-set pointer count"
.assert * - DemonMirrorEnemySetPointerHighTable = DemonMirrorEnemySetCount, error, "unexpected Demon Mirror enemy-set pointer count"

.segment "PRG_DEMON_MIRROR_SCHEDULE_DATA"

.if SolomonRevision = SolomonRevisionEurope
DemonMirrorSchedule00:
    .byte $00, $00, $00, $00, $00, $00, $00, $00
DemonMirrorSchedule01:
    .byte $92, $49, $92, $49, $24, $92, $49, $24
DemonMirrorSchedule02:
    .byte $88, $88, $88, $88, $88, $88, $88, $88
DemonMirrorSchedule03:
    .byte $01, $24, $92, $49, $24, $92, $49, $24
DemonMirrorSchedule04:
    .byte $92, $49, $24, $92, $24, $92, $49, $24
DemonMirrorSchedule05:
    .byte $24, $92, $49, $24, $92, $49, $24, $92
DemonMirrorSchedule06:
    .byte $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF
DemonMirrorSchedule07:
    .byte $EA, $49, $EA, $49, $EA, $49, $EA, $49
DemonMirrorSchedule08:
    .byte $0A, $AA, $AA, $AA, $AA, $AA, $AA, $AA
DemonMirrorSchedule09:
    .byte $00, $00, $00, $00, $00, $00, $00, $01
DemonMirrorSchedule10:
    .byte $81, $02, $04, $08, $10, $20, $40, $82
DemonMirrorSchedule11:
    .byte $A1, $42, $85, $0A, $14, $28, $50, $A1
DemonMirrorSchedule12:
    .byte $49, $24, $92, $49, $24, $92, $49, $24
DemonMirrorSchedule13:
    .byte $00, $08, $00, $00, $00, $00, $00, $00
DemonMirrorSchedule14:
    .byte $00, $49, $24, $92, $49, $24, $92, $49
DemonMirrorSchedule15:
    .byte $00, $12, $49, $24, $92, $49, $24, $92
.else
DemonMirrorSchedule00:
    .byte $00, $00, $00, $00, $00, $00, $00, $00
DemonMirrorSchedule01:
    .byte $88, $88, $88, $88, $88, $88, $88, $88
DemonMirrorSchedule02:
    .byte $84, $21, $08, $42, $08, $42, $10, $84
DemonMirrorSchedule03:
    .byte $00, $44, $44, $44, $44, $44, $44, $44
DemonMirrorSchedule04:
    .byte $92, $49, $24, $92, $24, $92, $49, $24
DemonMirrorSchedule05:
    .byte $22, $22, $22, $22, $22, $22, $22, $22
DemonMirrorSchedule06:
    .byte $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF
DemonMirrorSchedule07:
    .byte $F5, $52, $49, $F5, $49, $F5, $52, $49
DemonMirrorSchedule08:
    .byte $05, $55, $55, $55, $55, $55, $55, $55
DemonMirrorSchedule09:
    .byte $00, $00, $00, $00, $00, $00, $00, $01
DemonMirrorSchedule10:
    .byte $80, $80, $80, $80, $80, $80, $80, $80
DemonMirrorSchedule11:
    .byte $A0, $A0, $A0, $A0, $A0, $A0, $A0, $A0
DemonMirrorSchedule12:
    .byte $44, $44, $44, $44, $44, $44, $44, $44
DemonMirrorSchedule13:
    .byte $00, $01, $00, $00, $00, $00, $00, $00
DemonMirrorSchedule14:
    .byte $00, $11, $11, $11, $11, $11, $11, $11
DemonMirrorSchedule15:
    .byte $00, $22, $22, $22, $22, $22, $22, $22
.endif

.assert * - DemonMirrorSchedule00 = DemonMirrorScheduleCount * DemonMirrorScheduleSize, error, "unexpected Demon Mirror schedule data size"

.segment "PRG_DEMON_MIRROR_ENEMY_SET_DATA"

DemonMirrorEnemySet00:
    .byte $78, DemonMirrorEnemySetLoopBase
DemonMirrorEnemySet01:
    .byte $50, DemonMirrorEnemySetLoopBase
DemonMirrorEnemySet02:
    .byte $51, DemonMirrorEnemySetLoopBase
DemonMirrorEnemySet03:
    .byte $50, $51, DemonMirrorEnemySetLoopBase
DemonMirrorEnemySet04:
    .byte $51, $50, DemonMirrorEnemySetLoopBase
DemonMirrorEnemySet05:
    .byte $5C, DemonMirrorEnemySetLoopBase
DemonMirrorEnemySet06:
    .byte $50, $51, $5C, DemonMirrorEnemySetLoopBase
DemonMirrorEnemySet07:
    .byte $51, $50, $5C, DemonMirrorEnemySetLoopBase
DemonMirrorEnemySet08:
    .byte $58, DemonMirrorEnemySetLoopBase
DemonMirrorEnemySet09:
    .byte $54, DemonMirrorEnemySetLoopBase
DemonMirrorEnemySet10:
    .byte $55, DemonMirrorEnemySetLoopBase
DemonMirrorEnemySet11:
    .byte $60, DemonMirrorEnemySetLoopBase
DemonMirrorEnemySet12:
    .byte $59, DemonMirrorEnemySetLoopBase
DemonMirrorEnemySet13:
    .byte $64, DemonMirrorEnemySetLoopBase
DemonMirrorEnemySet14:
    .byte $70, DemonMirrorEnemySetLoopBase
DemonMirrorEnemySet15:
    .byte $54, $55, $60, DemonMirrorEnemySetLoopBase
DemonMirrorEnemySet16:
    .byte $59, DemonMirrorEnemySetLoopBase

.assert * - DemonMirrorEnemySet00 = $2A, error, "unexpected Demon Mirror enemy-set data size"
