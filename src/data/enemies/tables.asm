; Packed configuration flags indexed by (SpawnType - $18) / 4

.segment "PRG_ENEMY_TYPE_DATA"

EnemyTypeConfigurationTable:
    .byte $0B, $0A, $09, $08, $19
    .byte $19, $09, $09, $09, $09, $09, $09, $09, $09
    .byte $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00
    .byte $06

EnemyTypeConfigurationCount = * - EnemyTypeConfigurationTable
.assert EnemyTypeConfigurationCount = 27, error, "unexpected enemy type table size"

; Split pointer tables for parallel object and enemy AI record pools

.segment "PRG_ENEMY_POINTER_TABLES"

EnemyAiRecordPointerLowTable:
.repeat EnemyAiStateCount, Index
    .byte <(EnemyAiState + Index * EnemyAiStateStride)
.endrepeat

EnemyAiRecordPointerHighTable:
.repeat EnemyAiStateCount, Index
    .byte >(EnemyAiState + Index * EnemyAiStateStride)
.endrepeat

ObjectRecordPointerLowTable:
    .byte <DanaObject

NonDanaObjectPointerLowTable:
    .byte <MagicSparkObject, <FireballObject, <AuxiliaryObject

EnemyObjectPointerLowTable:
.repeat EnemyObjectCount, Index
    .byte <(EnemyObjects + Index * ObjectRecordSize)
.endrepeat

ObjectRecordPointerHighTable:
    .byte >DanaObject

NonDanaObjectPointerHighTable:
    .byte >MagicSparkObject, >FireballObject, >AuxiliaryObject

EnemyObjectPointerHighTable:
.repeat EnemyObjectCount, Index
    .byte >(EnemyObjects + Index * ObjectRecordSize)
.endrepeat

EnemyAiPointerTableCount = EnemyAiRecordPointerHighTable - EnemyAiRecordPointerLowTable
ObjectPointerTableCount = ObjectRecordPointerHighTable - ObjectRecordPointerLowTable

.assert EnemyAiPointerTableCount = EnemyAiStateCount, error, "unexpected enemy AI pointer count"
.assert ObjectPointerTableCount = ObjectRecordCount, error, "unexpected object pointer count"
.assert NonDanaObjectPointerLowTable = ObjectRecordPointerLowTable + 1, error, "unexpected non-Dana low pointer offset"
.assert NonDanaObjectPointerHighTable = ObjectRecordPointerHighTable + 1, error, "unexpected non-Dana high pointer offset"
.assert EnemyObjectPointerLowTable = ObjectRecordPointerLowTable + 4, error, "unexpected enemy object pointer offset"
.assert EnemyObjectPointerHighTable = ObjectRecordPointerHighTable + 4, error, "unexpected enemy object pointer offset"
