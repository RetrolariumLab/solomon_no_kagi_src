; Clear all 21 object records and all 17 parallel enemy AI records

.segment "PRG_GAMEPLAY_POOL_CLEAR"

ObjectPoolFirstPageSize = $100
ObjectPoolTailSize = ObjectRecordCount * ObjectRecordSize - ObjectPoolFirstPageSize
EnemyAiStateSize = EnemyAiStateCount * EnemyAiStateStride

ClearGameplayObjectAndEnemyState:
    LDA #$00
    LDY #ObjectPoolTailSize

ClearObjectPoolTail:
    DEY
    STA DanaObject + ObjectPoolFirstPageSize,Y
    BNE ClearObjectPoolTail
    TAY

ClearObjectPoolFirstPage:
    STA DanaObject,Y
    DEY
    BNE ClearObjectPoolFirstPage
    LDY #EnemyAiStateSize

ClearEnemyAiStatePool:
    DEY
    STA EnemyAiState,Y
    BNE ClearEnemyAiStatePool
    RTS
