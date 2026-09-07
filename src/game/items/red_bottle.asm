; Red-bottle effect that marks every eligible enemy for retirement

.segment "PRG_RED_BOTTLE_ITEM"

RedBottleEnemyStateMinimum = $C0
RedBottleEnemyTypeBase = $50
RedBottleEnemyTypeCount = $18
RedBottleThreadCode = $50

ApplyRedBottleKillAllEnemiesItem:
    LDX #EnemyObjectCount - 1

CheckNextRedBottleEnemy:
    TXA
    JSR LoadEnemyObjectPointer
    LDY #ObjectStateOffset
    LDA (TempPointer00),Y
    CMP #RedBottleEnemyStateMinimum
    BCC AdvanceRedBottleEnemy
    INY
    LDA (TempPointer00),Y
    SBC #RedBottleEnemyTypeBase
    CMP #RedBottleEnemyTypeCount
    BCS AdvanceRedBottleEnemy
    TYA
    DEY
    ORA (TempPointer00),Y
    STA (TempPointer00),Y
    STY ItemInteractionThreadCode

AdvanceRedBottleEnemy:
    DEX
    BPL CheckNextRedBottleEnemy
    LDA ItemInteractionThreadCode
    BNE FinishRedBottleItem
    LDA #RedBottleThreadCode
    JSR StartThread
    LDA #InventoryItemInteractionThread
    STA ItemInteractionThreadCode

FinishRedBottleItem:
    RTS

; Context 5 converts every enemy marked for retirement into a drop object

.segment "PRG_ENEMY_DROP_PROCESSING"

DefeatedEnemyIndex = $02
EnemyDropTableOffset = $03
EnemyAiSecondaryStateOffset = $01
EnemyDropInactiveMarker = $80
EnemyDropObjectState = $C6
EnemyDropObjectType = $14
EnemyDropSoundEffect = $09
EnemyDropThreadIndex = $05

ProcessDefeatedEnemyDrops:
    LDA #EnemyObjectCount - 1
    STA DefeatedEnemyIndex

CheckNextDefeatedEnemy:
    LDA DefeatedEnemyIndex
    JSR LoadEnemyObjectPointer
    LDY #ObjectStateOffset
    LDA (TempPointer00),Y
    BPL AdvanceDefeatedEnemyScan
    LSR A
    BCC AdvanceDefeatedEnemyScan
    INY
    LDA (TempPointer00),Y
    LSR A
    LSR A
    SEC
    SBC #$06
    BCC AdvanceDefeatedEnemyScan
    TAX
    LDA EnemyDropTableOffsetsByTypeGroup,X
    STA EnemyDropTableOffset
    LDA DefeatedEnemyIndex
    JSR LoadEnemyAiPointer
    LDA #$00
    STA (TempPointer00),Y
    TAY
    LDA (TempPointer00),Y
    LSR A
    BCC CheckSecondLinkedEnemy
    PHA
    LDY #EnemyAiFirstLinkedSlotOffset
    LDA (TempPointer00),Y
    JSR DeactivateEnemySlot
    PLA

CheckSecondLinkedEnemy:
    LSR A
    BCC SelectEnemyDrop
    LDY #EnemyAiSecondLinkedSlotOffset
    LDA (TempPointer00),Y
    JSR DeactivateEnemySlot

SelectEnemyDrop:
    LDA #EnemyDropInactiveMarker
    STA (TempPointer00),Y
    JSR AdvanceRandomState
    AND #$07
    CLC
    ADC EnemyDropTableOffset
    TAX
    LDA EnemyDropTypeTable,X
    LDY #EnemyAiFirstLinkedSlotOffset
    STA (TempPointer00),Y
    LDA DefeatedEnemyIndex
    JSR LoadEnemyObjectPointer
    LDA #EnemyDropObjectState
    STA SpawnYPosition
    LDA #EnemyDropObjectType
    STA SpawnXPosition
    LDA #$00
    JSR InitializeObjectStateHeader

AdvanceDefeatedEnemyScan:
    DEC DefeatedEnemyIndex
    BPL CheckNextDefeatedEnemy
    LDY #EnemyDropSoundEffect
    JSR AddSoundEffect
    LDA #EnemyDropThreadIndex
    JSR StopThread

EnemyDropTableOffsetsByTypeGroup:
    .byte $00, $00, $00, $48, $08, $08, $18, $10, $18, $10, $18
    .byte $10, $18, $10, $20, $20, $20, $28, $28, $28, $30, $30, $38, $38, $40, $40, $00

EnemyDropTypeTable:
    .byte $00, $00, $00, $00, $00, $00, $00, $00, $04, $08, $08, $08, $09, $09, $09, $09
    .byte $04, $08, $08, $08, $09, $09, $09, $0A, $08, $08, $09, $09, $09, $09, $0A, $0A
    .byte $04, $0B, $0B, $0B, $0B, $0C, $0C, $0C, $0B, $0B, $0C, $0C, $0C, $0D, $0D, $02
    .byte $0B, $0B, $0B, $0C, $0C, $03, $03, $06, $04, $0B, $0C, $0C, $0D, $0D, $02, $02
    .byte $0E, $0E, $0E, $0E, $0F, $05, $05, $05, $0E, $0E, $0E, $0F, $0F, $0F, $05, $05

.assert EnemyDropTypeTable - EnemyDropTableOffsetsByTypeGroup = $1B, error, "unexpected enemy drop offset table size"
.assert * - EnemyDropTypeTable = $50, error, "unexpected enemy drop type table size"
.assert * - ProcessDefeatedEnemyDrops = $E3, error, "unexpected enemy drop processing size"

; Shared deterministic state mixer used for room placement and enemy rewards

.segment "PRG_RANDOM_STATE"

RandomMirrorStateSnapshot = $3E
RandomSeedWordLo = $04
RandomSeedWordHi = $05
RandomAccumulatorLo = $06
RandomAccumulatorHi = $07
RandomAccumulatorHighMask = $7F
RandomSeedMixRoundCount = 8

AdvanceRandomState:
    LDA DemonMirrorSpawnState
    CMP RandomMirrorStateSnapshot
    BEQ MixRandomState
    STA RandomMirrorStateSnapshot
    LDA DemonMirrorSpawnTimerLo
    STA RandomStateLo
    LDA GameplayFrameCounters
    STA RandomStateHi

MixRandomState:
    LDA RandomStateLo
    ORA #$01
    STA RandomSeedWordLo
    LDA RandomStateHi
    STA RandomSeedWordHi
    LDA #$00
    STA RandomAccumulatorLo
    STA RandomAccumulatorHi
    LDY #$7C
    JSR AccumulateRandomSeedMask
    LDY #$FC
    JSR AccumulateRandomSeedMask
    LDA RandomAccumulatorHi
    AND #RandomAccumulatorHighMask
    STA RandomStateHi
    LDA RandomAccumulatorLo
    STA RandomStateLo
    LSR A
    RTS

AccumulateRandomSeedMask:
    LDX #RandomSeedMixRoundCount

MixNextRandomSeedBit:
    TYA
    LSR A
    TAY
    BCS ShiftRandomSeedWord
    LDA RandomAccumulatorLo
    ADC RandomSeedWordLo
    STA RandomAccumulatorLo
    LDA RandomAccumulatorHi
    ADC RandomSeedWordHi
    STA RandomAccumulatorHi

ShiftRandomSeedWord:
    LSR RandomSeedWordHi
    ROR RandomSeedWordLo
    DEX
    BNE MixNextRandomSeedBit
    RTS

.assert AccumulateRandomSeedMask - AdvanceRandomState = $3E, error, "unexpected random mixer helper offset"
.assert * - AdvanceRandomState = $59, error, "unexpected random state routine size"
