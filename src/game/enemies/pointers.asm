; Resolve an enemy slot index to its parallel runtime records

.segment "PRG_ENEMY_POINTERS"

LoadEnemyObjectPointer:
    TAX
    LDA EnemyObjectPointerLowTable,X
    STA TempPointer00
    LDA EnemyObjectPointerHighTable,X
    STA TempPointer00 + 1
    RTS

LoadEnemyAiPointer:
    TAX
    LDA EnemyAiRecordPointerLowTable,X
    STA TempPointer00
    LDA EnemyAiRecordPointerHighTable,X
    STA TempPointer00 + 1
    RTS
