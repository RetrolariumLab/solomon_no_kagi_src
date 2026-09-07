; Initialize the position-bearing fields for one allocated enemy slot

.segment "PRG_ENEMY_INITIALIZATION"

InitializeEnemy:
    LDA SpawnSlotIndex
    JSR LoadEnemyAiPointer
    LDY #EnemyAiFlagsOffset
    TYA

ClearEnemyAiStateFields:
    INY
    STA (TempPointer00),Y
    CPY #EnemyAiLifetimeHighOffset
    BNE ClearEnemyAiStateFields
    LDA SpawnSlotIndex
    JSR LoadEnemyObjectPointer
    LDY #$07
    LDA SpawnYPosition
    STA (TempPointer00),Y
    LDY #$0A
    LDA SpawnXPosition
    STA (TempPointer00),Y
    RTS
