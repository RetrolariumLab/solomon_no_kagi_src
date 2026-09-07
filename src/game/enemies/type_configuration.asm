; Decode a spawn type into object and AI record configuration

.segment "PRG_ENEMY_TYPE_CONFIGURATION"

ConfigureEnemyType:
    LDA SpawnSlotIndex
    JSR LoadEnemyObjectPointer
    LDA SpawnType
    STA $05
    AND #$03
    TAX
    LDA $05
    SEC
    SBC #$18
    LSR A
    LSR A
    TAY
    LDA EnemyTypeConfigurationTable,Y
    LDY #$E0
    LSR A
    BCC DecodeEnemyTypeFlags
    LDY #$C0

DecodeEnemyTypeFlags:
    STY $04
    TAY
    ASL A
    AND #$06
    ORA $04
    STA $04
    TYA
    LSR A
    LSR A
    LSR A
    PHA
    BCS ApplyEnemyTypeConfiguration
    LDA #$80
    LDY #$05
    STA (TempPointer00),Y
    TXA
    ORA #$18
    TAX

ApplyEnemyTypeConfiguration:
    TXA
    JSR InitializeObjectStateHeader
    PLA
    LSR A
    BCC FinishEnemyTypeConfiguration
    LDA SpawnSlotIndex
    JSR LoadEnemyAiPointer
    LDA SpawnType
    AND #$03
    LDY #EnemyAiPathDirectionOffset
    STA (TempPointer00),Y
    INY
    EOR #$02
    AND #$02
    STA (TempPointer00),Y

FinishEnemyTypeConfiguration:
    RTS
