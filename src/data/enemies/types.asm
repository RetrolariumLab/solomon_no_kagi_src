; Packed configuration flags indexed by (SpawnType - $18) / 4

.segment "PRG_ENEMY_TYPE_DATA"

EnemyTypeConfigurationTable:
    .byte $0B, $0A, $09, $08, $19
    .byte $19, $09, $09, $09, $09, $09, $09, $09, $09
    .byte $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00
    .byte $06

EnemyTypeConfigurationCount = * - EnemyTypeConfigurationTable
.assert EnemyTypeConfigurationCount = 27, error, "unexpected enemy type table size"
