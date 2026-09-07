; Context-three gameplay service loop entered by scheduler code $30

.segment "PRG_MAIN_THREAD"

MainGameplayThread:
    JSR DecrementTimer
    JSR UpdateEnemiesMovement
    JSR UpdateDemonMirrorSpawnSchedule
    JSR ActivatePendingDemonMirrorEnemies
    JSR SwitchThreads
    JSR RunEnemyAiDispatcher
    JSR SwitchThreads
    JSR CheckDanaMapTileInteraction
    JSR SwitchThreads
    JSR UpdateFireballLifetime
    JSR SwitchThreads
    LDA FairiesQueued
    BEQ ContinueMainGameplayThread
    JSR FindFreeEnemySlotIndex
    BCC ContinueMainGameplayThread
    DEC FairiesQueued
    LDA #$80
    LDY #$00
    STA ($04),Y
    STX $06
    LDY #$05
    LDA ($30),Y
    STA $04
    JSR ConvertMapIndexToPixelCoordinates
    LDA #$1C
    STA $07
    JSR InitializeEnemy
    JSR ConfigureEnemyType

ContinueMainGameplayThread:
    JMP MainGameplayThread
