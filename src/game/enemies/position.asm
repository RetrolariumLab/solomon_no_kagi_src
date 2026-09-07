; Copy the current enemy object's integer position to shared spawn scratch

.segment "PRG_ENEMY_POSITION"

LoadCurrentEnemyPosition:
    LDY #$07
    LDA (EnemyObjectPointer),Y
    STA SpawnYPosition
    LDY #$0A
    LDA (EnemyObjectPointer),Y
    STA SpawnXPosition
    RTS
