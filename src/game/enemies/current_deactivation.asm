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
