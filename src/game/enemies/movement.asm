; Advance active enemy movement records and cache their direction to Dana

.segment "PRG_ENEMY_MOVEMENT"

UpdateEnemiesMovement:
    LDA DanaYPosition
    STA $06
    LDA DanaXPosition
    STA $07
    LDA GameplayUpdateCount
    STA $00
    LDA #$00
    STA GameplayUpdateCount
    STA ActiveEnemyCount
    LDX #EnemyObjectCount - 1

UpdateNextEnemyMovement:
    LDA EnemyObjectPointerLowTable,X
    STA TempPointer02
    LDA EnemyObjectPointerHighTable,X
    STA TempPointer02 + 1
    LDA EnemyAiRecordPointerLowTable,X
    STA TempPointer04
    LDA EnemyAiRecordPointerHighTable,X
    STA TempPointer04 + 1
    LDY #EnemyAiFlagsOffset
    LDA (TempPointer04),Y
    BPL NextEnemyMovement
    INC ActiveEnemyCount
    INY
    LDA $00
    CLC
    ADC (TempPointer04),Y
    STA (TempPointer04),Y
    INY
    LDA $00
    CLC
    ADC (TempPointer04),Y
    STA (TempPointer04),Y
    INY
    LDA #$00
    ADC (TempPointer04),Y
    STA (TempPointer04),Y
    LDY #ObjectYPositionOffset
    LDA (TempPointer02),Y
    SEC
    SBC $06
    ROR A
    PHA
    LDY #ObjectXPositionOffset
    LDA (TempPointer02),Y
    SEC
    SBC $07
    ROR A
    LDY #EnemyAiHorizontalDeltaOffset
    STA (TempPointer04),Y
    DEY
    PLA
    STA (TempPointer04),Y

NextEnemyMovement:
    DEX
    BPL UpdateNextEnemyMovement
    RTS
