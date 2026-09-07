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

; Resolve an enemy slot index to its parallel runtime records

.segment "PRG_ENEMY_POINTERS"

LoadEnemyObjectPointer:
    TAX
    LDA EnemyObjectPointerLowTable,X
    STA TempPointer00
    LDA EnemyObjectPointerHighTable,X
    STA TempPointer00 + 1
    RTS

LoadEnemyAiPointer:
    TAX
    LDA EnemyAiRecordPointerLowTable,X
    STA TempPointer00
    LDA EnemyAiRecordPointerHighTable,X
    STA TempPointer00 + 1
    RTS

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

; Deactivate one enemy slot and move its object record offscreen

.segment "PRG_ENEMY_DEACTIVATION"

DeactivateEnemySlot:
    TAX
    LDY #$00
    LDA EnemyAiRecordPointerLowTable,X
    STA TempPointer04
    LDA EnemyAiRecordPointerHighTable,X
    STA TempPointer04 + 1
    TYA
    STA (TempPointer04),Y
    LDA EnemyObjectPointerLowTable,X
    STA TempPointer04
    LDA EnemyObjectPointerHighTable,X
    STA TempPointer04 + 1
    TYA
    STA (TempPointer04),Y
    LDY #$07
    LDA #$F8
    STA (TempPointer04),Y
    RTS

; Selected-enemy retirement, lifetime transition, and pre-script filler

.segment "PRG_CURRENT_ENEMY_DEACTIVATION"

DeactivateCurrentEnemy:
    LDA #$00
    TAY
    STA (EnemyAiPointer),Y
    STA (EnemyObjectPointer),Y
    LDY #$07
    LDA #$F8
    STA (EnemyObjectPointer),Y
    RTS

.segment "PRG_ENEMY_LIFETIME"

EnemyAiLifetimeFlagMask = $03
ExpiredEnemyObjectFlag = $02

ApplyEnemyLifetimeThreshold:
    LDY #$00
    LDA (EnemyAiPointer),Y
    AND #EnemyAiLifetimeFlagMask
    BNE FinishEnemyLifetimeThreshold
    LDY #EnemyAiLifetimeLowOffset
    LDA (EnemyAiPointer),Y
    SBC EnemySpawnLifetimeThresholdLo
    INY
    LDA (EnemyAiPointer),Y
    SBC EnemySpawnLifetimeThresholdHi
    BCC FinishEnemyLifetimeThreshold
    LDY #ObjectActionOffset
    LDA (EnemyObjectPointer),Y
    BEQ FinishEnemyLifetimeThreshold
    LDA #$00
    STA (EnemyObjectPointer),Y
    LDY #EnemyAiPhaseOffset
    STA (EnemyAiPointer),Y
    TAY
    LDA #ExpiredEnemyObjectFlag
    ORA (EnemyObjectPointer),Y
    STA (EnemyObjectPointer),Y

FinishEnemyLifetimeThreshold:
    RTS

.segment "PRG_FILLER_BEFORE_SPECIAL_ROOMS"

; Bisqwit's map identifies this unreferenced tail as the filler before $B800
FillerBeforeB800:
.if SolomonRevision = SolomonRevisionEurope
    .res $30F, $FF
.else
    .byte $00, $FF
    .byte $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $00, $FF, $00
    .byte $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $FF, $00, $FF
    .byte $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $00, $FF, $00
    .byte $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $FF, $00, $FF
    .byte $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $00, $FF, $00
    .byte $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $FF, $00, $FF
    .byte $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $00, $FF, $00
    .byte $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $FF, $00, $FF
    .byte $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $00, $FF, $00
    .byte $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $FF, $00, $FF
    .byte $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $00, $FF, $00
    .byte $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $FF, $00, $FF
    .byte $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $00, $FF, $00
    .byte $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $FF, $00, $FF
    .byte $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $00, $FF, $00
    .byte $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $FF, $00, $FF
    .byte $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $00, $FF, $00
    .byte $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $FF, $00, $FF
    .byte $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $00, $FF, $00
    .byte $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $FF, $00, $FF
    .byte $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $00, $FF, $00
    .byte $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $FF, $00, $FF
    .byte $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $00, $FF, $00
    .byte $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $FF, $00, $FF
    .byte $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $00, $FF, $00
    .byte $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $FF, $00, $FF
    .byte $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $00, $FF, $00
    .byte $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $FF, $00, $FF
    .byte $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $00, $FF, $00
    .byte $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $FF, $00, $FF
    .byte $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $00, $FF, $00
    .byte $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $FF, $00, $FF
    .byte $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $00, $FF, $00
    .byte $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $FF, $00, $FF
    .byte $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $00, $FF, $00
    .byte $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $FF, $00, $FF
    .byte $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $00, $FF, $00
    .byte $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $FF, $00, $FF
    .byte $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $00, $FF, $00
    .byte $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $FF, $00, $FF
    .byte $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $00, $FF, $00
    .byte $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $FF, $00, $FF
    .byte $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $00, $FF, $00
    .byte $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $FF, $00, $FF
    .byte $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $00, $FF, $00
    .byte $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $FF, $00, $FF
    .byte $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $00, $FF, $00
    .byte $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $FF, $00, $FF
    .byte $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00
.endif

.assert FillerBeforeB800 - ApplyEnemyLifetimeThreshold = $2D, error, "unexpected enemy-lifetime size"
.assert * - FillerBeforeB800 = $30F, error, "unexpected pre-special-room filler size"
