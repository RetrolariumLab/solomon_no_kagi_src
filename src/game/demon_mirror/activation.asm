; Activate pending Demon Mirror objects from their cyclic enemy-set streams

.segment "PRG_DEMON_MIRROR_ACTIVATION"

DemonMirrorPendingMask = $C0
DemonMirrorTimerPhaseMask = $3F
DemonMirrorActivationPhase = $18
DemonMirrorEnemySetLoopBase = $90

ActivatePendingDemonMirrorEnemies:
    LDX DemonMirrorSpawnState
    CPX #$40
    BCC FinishDemonMirrorActivation
    LDA DemonMirrorSpawnTimerLo
    AND #DemonMirrorTimerPhaseMask
    CMP #DemonMirrorActivationPhase
    BCC FinishDemonMirrorActivation
    TXA
    AND #DemonMirrorTimerPhaseMask
    STA DemonMirrorSpawnState
    STX TempPointer02
    ASL TempPointer02
    BCC ActivateSecondDemonMirror
    LDA DemonMirrorEnemySlots + 1
    STA SpawnSlotIndex

ReadFirstDemonMirrorEnemyType:
    LDY DemonMirrorEnemySetOffsets
    LDA (DemonMirrorEnemySetPointers),Y
    INC DemonMirrorEnemySetOffsets
    CMP #DemonMirrorEnemySetLoopBase
    BCC ConfigureFirstDemonMirrorEnemy
    SBC #DemonMirrorEnemySetLoopBase
    STA DemonMirrorEnemySetOffsets
    BCS ReadFirstDemonMirrorEnemyType

ConfigureFirstDemonMirrorEnemy:
    STA SpawnType
    JSR ConfigureEnemyType

ActivateSecondDemonMirror:
    ASL TempPointer02
    BCC FinishDemonMirrorActivation
    LDA DemonMirrorEnemySlots
    STA SpawnSlotIndex

ReadSecondDemonMirrorEnemyType:
    LDY DemonMirrorEnemySetOffsets + 1
    INC DemonMirrorEnemySetOffsets + 1
    LDA (DemonMirrorEnemySetPointers + 2),Y
    CMP #DemonMirrorEnemySetLoopBase
    BCC ConfigureSecondDemonMirrorEnemy
    SBC #DemonMirrorEnemySetLoopBase
    STA DemonMirrorEnemySetOffsets + 1
    BCS ReadSecondDemonMirrorEnemyType

ConfigureSecondDemonMirrorEnemy:
    STA SpawnType
    JSR ConfigureEnemyType

FinishDemonMirrorActivation:
    RTS
