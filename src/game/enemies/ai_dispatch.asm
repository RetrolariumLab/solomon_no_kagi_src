; Select enemy records eligible for the per-enemy AI handler

.segment "PRG_ENEMY_AI_DISPATCH"

EnemyAiDispatchTypeMinimum = $14

RunEnemyAiDispatcher:
    LDX #EnemyObjectCount - 1

CheckNextEnemyAiSlot:
    TXA
    PHA
    LDA EnemyAiRecordPointerLowTable,X
    STA EnemyAiPointer
    LDA EnemyAiRecordPointerHighTable,X
    STA EnemyAiPointer + 1
    LDA EnemyObjectPointerLowTable,X
    STA EnemyObjectPointer
    LDA EnemyObjectPointerHighTable,X
    STA EnemyObjectPointer + 1
    LDY #ObjectStateOffset
    LDA (EnemyObjectPointer),Y
    CMP #ActiveObjectStateMinimum
    BCC NextEnemyAiSlot
    INY  ; ObjectTypeOffset immediately follows ObjectStateOffset
    LDA (EnemyObjectPointer),Y
    SBC #EnemyAiDispatchTypeMinimum
    BCC NextEnemyAiSlot
    JSR DispatchEnemyAiHandler

NextEnemyAiSlot:
    PLA
    TAX
    DEX
    BPL CheckNextEnemyAiSlot
    RTS
