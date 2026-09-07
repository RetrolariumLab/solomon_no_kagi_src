; Locate the first inactive entry in the seventeen-slot enemy AI pool

.segment "PRG_FIND_FREE_ENEMY_SLOT"

FindFreeEnemySlotIndex:
    LDX #$00
    LDY #$00

CheckEnemySlotAvailable:
    LDA EnemyAiRecordPointerLowTable,X
    STA TempPointer04
    LDA EnemyAiRecordPointerHighTable,X
    STA TempPointer04 + 1
    LDA (TempPointer04),Y
    BPL EnemySlotAvailable
    INX
    CPX #EnemyAiStateCount
    BCC CheckEnemySlotAvailable
    CLC
    BCC FinishEnemySlotSearch

EnemySlotAvailable:
    SEC

FinishEnemySlotSearch:
    RTS
