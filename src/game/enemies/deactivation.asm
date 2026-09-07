; Deactivate one enemy slot and move its object record offscreen

.segment "PRG_ENEMY_DEACTIVATION"

DeactivateEnemySlot:
    TAX
    LDY #$00
    LDA EnemyAiRecordPointerLowTable,X
    STA TempPointer04
    LDA EnemyAiRecordPointerHighTable,X
    STA TempPointer04 + 1
    TYA
    STA (TempPointer04),Y
    LDA EnemyObjectPointerLowTable,X
    STA TempPointer04
    LDA EnemyObjectPointerHighTable,X
    STA TempPointer04 + 1
    TYA
    STA (TempPointer04),Y
    LDY #$07
    LDA #$F8
    STA (TempPointer04),Y
    RTS
