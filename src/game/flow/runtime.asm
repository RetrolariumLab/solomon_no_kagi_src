; Establish the persistent counters and flags for a new game

.segment "PRG_NEW_GAME_STATE_RESET"

ResetNewGameState:
.if SolomonRevision = SolomonRevisionEurope
    LDA RegionalNewGameRoomIndex
    STA CurrentRoomIndex
    LDA #$00
.else
    LDA #$00
    STA CurrentRoomIndex
.endif
    STA InventorySlotsLow
    STA FireballDirectionIndex
    LDX #$03
    STX RemainingLives
    STX InventorySlotCount
    INX

ClearNewGameStateFlags:
.if SolomonRevision = SolomonRevisionEurope
    LDA RegionalNewGameFlags,X
    STA GameStateFlags,X
    DEX
    BPL ClearNewGameStateFlags
    LDA #$00
.else
    STA GameStateFlags,X
    DEX
    BNE ClearNewGameStateFlags
.endif
    LDX #$08

ClearNewGameScoreDigits:
    STA ScoreDigits - 1,X
    DEX
    BNE ClearNewGameScoreDigits
    INX
.if SolomonRevision = SolomonRevisionEurope
    LDA #$01
    ORA GameStateFlags
    STA GameStateFlags
.else
    STX GameStateFlags
.endif
    STX $80
    STX FireballLifetimeHi
    RTS

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

; Post-game attract screens, demo setup, and recorded demo input playback

.segment "PRG_ATTRACT_DEMO_FLOW"

AttractContextToKeep = $01
AttractSoundEffect = $18
AttractScrollY = $EF
AttractChrBank = $03
PostGameFirstPpuStream = $0D
PostGamePpuStreamEnd = $12
PostGameWaitHigh = $01
TitleWaitHigh = $02
DemoPlaybackThreadCode = $18
NewGameSetupThreadCode = $10
DemoInputThreadCode = $22
RoomLoadThreadCode = $15
GameplayExitThreadCode = $35
DemoInputContext = $02
DemoRoomIndex = $02
DemoInventorySlotCount = $03
DemoRemainingLives = $03
DemoInventoryBits = $54
DemoStateFlag = $80
DemoInputCount = $22

AttractWaitCounterLo = RoomItemRuntimeData
AttractWaitCounterHi = RoomItemRuntimeData + 1
DemoPlaybackMode = $0080
DemoInputIndex = $0081
; Context 1 entry $17. A negative RoomStateFlags value means a demo was
; interrupted, so the post-game summary is skipped and the title is rebuilt
RunPostGameAttractThread:
    LDX #AttractContextToKeep
    JSR ResetOtherSecondaryThreads
    LDY #AttractSoundEffect
    JSR AddSoundEffect
    LDA #AttractScrollY
    STA PpuScrollY
    LDA #AttractChrBank
    STA ChrBankRequest
    LDA RoomStateFlags
    BPL ShowPostGameSummary
    LDA #$7F
    AND RoomStateFlags
    STA RoomStateFlags
    BPL PrepareTitleScreen

ShowPostGameSummary:
    JSR ClearBothNametables
    LDX #PostGameFirstPpuStream

QueueNextPostGamePpuStream:
    TXA
    JSR QueueStaticPpuUpdateStream
    INX
    CPX #PostGamePpuStreamEnd
    BNE QueueNextPostGamePpuStream
    LDA #$00
    STA GameplayFlags
    STA AttractWaitCounterLo
    STA AttractWaitCounterHi

WaitForPostGameSummary:
    LDA AttractWaitCounterHi
    CMP #PostGameWaitHigh
    BCS PrepareTitleScreen
    LDA Joypad1Cached
    AND #JOY_BUTTON_START_SELECT_MASK
    BEQ WaitForPostGameSummary

WaitForPostGameButtonRelease:
    LDA Joypad1Cached
    AND #JOY_BUTTON_START_SELECT_MASK
    BNE WaitForPostGameButtonRelease

PrepareTitleScreen:
    LDX #AttractContextToKeep
    JSR ResetOtherSecondaryThreads
    LDY #AttractSoundEffect
    JSR AddSoundEffect
    LDA #AttractScrollY
    STA PpuScrollY
    LDA #AttractChrBank
    STA ChrBankRequest
    LDA #$00
    STA GameplayFlags
    JSR ClearBothNametables
    JSR DrawTitleLogoLayer
    JSR DrawTitleRecordLayer
    LDA #$00
    STA AttractWaitCounterLo
    STA AttractWaitCounterHi

WaitForTitleInput:
    LDA AttractWaitCounterHi
    CMP #TitleWaitHigh
    BCC CheckTitleInput
    LDA #$00
    STA PpuScrollY
    LDA #DemoPlaybackThreadCode
    JSR StartThread

CheckTitleInput:
    LDA Joypad1Cached
    AND #JOY_BUTTON_START_SELECT_MASK
    BEQ WaitForTitleInput

WaitForTitleButtonRelease:
    LDA Joypad1Cached
    AND #JOY_BUTTON_START_SELECT_MASK
    BNE WaitForTitleButtonRelease
    LDA #$00
    STA PpuScrollY
    JSR ClearBothNametables

; The title-input path also starts normal room services before joining context
; 1 entry $18, which begins at the recorded controller producer
    LDA #NewGameSetupThreadCode
    JSR StartThread

StartDemoPlayback:
    LDA #DemoInputThreadCode
    JSR StartThread
    LDX #$01
    STX FireballLifetimeHi
    STX DemoPlaybackMode
    INX
    STX CurrentRoomIndex
    INX
    STX InventorySlotCount
    STX RemainingLives
    LDX #DemoInventoryBits
    STX InventorySlotsLow
    LDA #RoomLoadThreadCode
    JSR StartThread

; Context 2 entry $22 starts by resetting its timing and stream position
RunDemoInputPlayback:
    LDA #$00
    STA NmiFrameCounter
    STA DemoInputIndex

; Each duration is inclusive: the next input byte is installed only after
; NmiFrameCounter grows strictly larger than its value
PollDemoInputPlayback:
    JSR SwitchThreads
    LDA Joypad1Cached
    AND #JOY_BUTTON_START_SELECT_MASK
    BEQ AdvanceDemoInput
    LDA #DemoStateFlag
    ORA RoomStateFlags
    STA RoomStateFlags
    BMI WaitForDemoExitButtonRelease

AdvanceDemoInput:
    LDX DemoInputIndex
    LDA DemoInputDurations,X
    CMP NmiFrameCounter
    BCS PollDemoInputPlayback
    CPX #DemoInputCount
    BCS FinishDemoInputPlayback
    LDA DemoInputValues,X
    STA Joypad1Cached
    INC DemoInputIndex
    LDA #$00
    STA NmiFrameCounter
    BEQ PollDemoInputPlayback

WaitForDemoExitButtonRelease:
    LDA Joypad1Cached
    AND #JOY_BUTTON_START_SELECT_MASK
    BNE WaitForDemoExitButtonRelease

FinishDemoInputPlayback:
    LDA #GameplayExitThreadCode
    JSR StartThread
    LDA #DemoInputContext
    JSR StopThread

.assert * - RunPostGameAttractThread = $101, error, "unexpected attract/demo flow size"

.segment "PRG_DEMO_INPUT_DATA"

DemoInputDurations:
    .byte $C0, $20, $80, $80, $20, $30, $40, $20, $03, $08, $20, $10, $20, $10, $20, $10, $68
    .byte $20, $10, $40, $20, $18, $10, $20, $20, $18, $80, $18, $20, $20, $20, $20, $03, $20

DemoInputValues:
    .byte $00, $00, $40, $00, $02, $01, $80, $09, $00, $09, $89, $01, $80, $01, $80, $01, $84
    .byte $01, $00, $80, $01, $04, $86, $00, $02, $00, $02, $80, $0A, $80, $0A, $00, $0A, $00

.assert DemoInputValues - DemoInputDurations = DemoInputCount, error, "unexpected demo duration count"
.assert * - DemoInputValues = DemoInputCount, error, "unexpected demo input count"

.segment "PRG_FILLER_BEFORE_ROOM_TILE_PATTERNS"

; Bisqwit's map classifies this complete gap as FillerBeforeD000_203bytes
FillerBeforeRoomTilePatterns:
.if SolomonRevision = SolomonRevisionEurope
    .res 187, $FF
.else
    .byte $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $04, $FF, $00
    .byte $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $FE, $20, $FF
    .byte $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $00, $FF, $00
    .byte $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $FF, $00, $FF
    .byte $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $88, $FF, $00
    .byte $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $EF, $02, $FF
    .byte $01, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $00, $FF, $00
    .byte $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $FF, $00, $FF
    .byte $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $87, $FF, $00
    .byte $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $E3, $00, $FF
    .byte $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $00, $FF, $00
    .byte $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $FF, $00, $FF
    .byte $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00
.endif

.assert * - FillerBeforeRoomTilePatterns = 203 - (SolomonRevision = SolomonRevisionEurope) * 16, error, "unexpected pre-room-tile filler size"

; Cooperative life-loss, TIME OVER, and post-game result transitions

.segment "PRG_GAMEPLAY_EXIT_FLOW"

GameplayExitWorkerContext = $03
GameplayExitCounter = GameplayUpdateCount
GameplayExitObjectState = TempPointer02
GameplayExitChrBank = $03
GameplayExitMaskStepCount = $18
GameplayExitMaskStepDelay = $04
TimeOverDisplayDelay = $64
DanaDeathGameplayFlag = $10
DanaDeathObjectState = $80
DanaDeathActiveObjectState = $C0
DanaDeathYMotion = $C3
DanaDeathYLimit = $D1
DanaDeathSetupDelay = $09
DanaDeathFinishDelay = $30
GameplayExitRoomStateFlag = $10
GameplayExitGameStateMask = $01
PostGameRoomStateFlag = $04
PostGameAlternateBonusFlag = $08
PostGameResultBase = $2F
PostGameResultTemplateSize = $0F
PostGameResultTensOffset = $0C
PostGameResultOnesOffset = $0D
PostGameSoundEffect = $05
NewGameSoundEffect = $18
PostGamePpuStreamIndex = $06
PostGamePpuWaitMask = $FF
PostGamePpuWaitAddress = PpuUpdateStreamPointer + 1
PostGameInputCode = $C8
PostGameMinimumWaitHigh = $02
PostGameThreadCode = $17
NewRoomThreadCode = $15
NewGameLives = $03
LastRegularRoomIndex = $28
RoomStateNewGameMask = $EE
GameplayFlagsNewGameMask = $DF

; Context 3 entry $33. Replace active object states, then cycle emphasis bits
; in PPUMASK before publishing the TIME OVER update stream
RunTimeOverTransition:
    JSR ResetRoomTransitionState
    LDA DanaObject + ObjectActionOffset
    AND #$01
    ORA #$20
    STA DanaObject + ObjectActionOffset
    LDA #$00
    PHA
    STA GameplayExitObjectState
    JSR SetActiveNonDanaObjectState
    INX

AdvanceTimeOverMaskCycle:
    STX GameplayExitCounter
    LDX #GameplayExitCounter
    LDA #GameplayExitMaskStepDelay
    JSR WaitForZeroPageCounterAboveThreshold
    PLA
    CMP #GameplayExitMaskStepCount
    BCS ShowTimeOverMessage
    ADC #$01
    PHA
    AND #$03
    TAX
    LDA PpuMaskShadow
    AND #$5E
    ORA LifeLossPpuMaskCycle,X
    STA PpuMaskShadow
    LDX #$00
    BEQ AdvanceTimeOverMaskCycle

ShowTimeOverMessage:
    LDA PpuUpdateStreamPointer + 1
    BNE ShowTimeOverMessage
    LDA #$1E
    STA PpuMaskShadow
    STA a:PPU_MASK
    JSR Clear30x24NametableRegion
    LDA #GameplayExitChrBank
    STA ChrBankRequest
    LDA #<TimeOverPpuUpdateStream
    STA PpuUpdateStreamPointer
    LDA #>TimeOverPpuUpdateStream
    STA PpuUpdateStreamPointer + 1
    LDX #GameplayExitCounter
    LDA #TimeOverDisplayDelay
    JSR WaitForZeroPageCounterAboveThreshold
    BCC FinalizeGameplayExit

; Context 3 entry $31. Configure Dana for the death fall and wait until the
; object reaches the lower Y limit before the shared exit cleanup
RunDanaDeathTransition:
    JSR ResetRoomTransitionState
    LDA #DanaDeathGameplayFlag
    ORA GameplayFlags
    STA GameplayFlags
    LDA DanaObject + ObjectActionOffset
    LSR A
    LDA #(DanaDeathFallActionBase / 2)
    ROL A
    STA DanaObject + ObjectActionOffset
    LDA #DanaDeathObjectState
    STA GameplayExitObjectState
    ASL A
    STA GameplayExitCounter
    JSR SetActiveNonDanaObjectState
    LDX #GameplayExitCounter
    LDA #DanaDeathSetupDelay
    JSR WaitForZeroPageCounterAboveThreshold
    LDA #DanaDeathActiveObjectState
    STA DanaObject + ObjectStateOffset
    LDA #DanaDeathYMotion
    STA DanaObject + ObjectYMotionOffset

WaitForDanaDeathFall:
    LDA DanaYPosition
    CMP #DanaDeathYLimit
    BCS FinishDanaDeathAnimation
    JSR SwitchThreads
    BCS WaitForDanaDeathFall

FinishDanaDeathAnimation:
; $20/$21 preserve facing during the fall; adding two selects $22/$23
    INC DanaObject + ObjectActionOffset
    INC DanaObject + ObjectActionOffset
    LDA #$00
    STA GameplayExitCounter
    LDX #GameplayExitCounter
    LDA #DanaDeathFinishDelay
    JSR WaitForZeroPageCounterAboveThreshold

; Context 3 entry $35. Both presentation paths converge here to clear the
; gameplay pools and choose between reload, result, and post-game threads
FinalizeGameplayExit:
    JSR DeactivateAllNonDanaObjects
    JSR Clear30x24NametableRegion
    JSR ClearGameplayObjectAndEnemyState
    LDA #GameplayExitRoomStateFlag
    ORA RoomStateFlags
    STA RoomStateFlags
    LDA GameStateFlags
    LSR A
    BCS CheckRemainingLivesAfterExit
    JMP SelectPostGameThread

CheckRemainingLivesAfterExit:
    LDX RemainingLives
    DEX
    BEQ PreparePostGameResult
    JMP ReloadRoomAfterLifeLoss

; Context 1 entry $16. The three zero-page factors are accumulated with seal,
; room-state, fairy, and score inputs into the two-digit value displayed by
; the literal "YOUR GDV" PPU template
PreparePostGameResult:
    LDA GameStateFlags
    ROL A
    ROL A
    AND #$01
    ADC #$00
    SEC
    ADC GdvFactor2
    STA TempPointer00
    LDA RoomStateFlags
    AND #PostGameRoomStateFlag
    CLC
    BEQ AccumulatePostGameRoomFactor
    SEC

AccumulatePostGameRoomFactor:
    LDA #$00
    ADC TempPointer00
    ASL A
    STA TempPointer00
    LDA GdvFactor1
    ADC SolomonSealCount
    ADC TempPointer00
    ASL A
    ADC GdvFactor0
    LSR A
    LSR A
    LSR A
    STA TempPointer00
    LDA ScoreDigits
    ORA ScoreDigits + 1
    BNE SelectMaximumScoreFactor
    LDX ScoreDigits + 2
    CPX #$05
    BCC AddScoreFactorToGdv

SelectMaximumScoreFactor:
    LDX #$05

AddScoreFactorToGdv:
    TXA
    CLC
    ADC TempPointer00
    STA TempPointer00
    LDA RoomStateFlags
    AND #PostGameAlternateBonusFlag
    CLC
    BEQ FinishGdvCalculation
    SEC

FinishGdvCalculation:
    LDA #$00
    ADC TempPointer00
    ADC #PostGameResultBase
    CMP BestGdvValue
    BCC StoreCurrentGdv
    STA BestGdvValue

StoreCurrentGdv:
    STA CurrentGdvValue
    LDX #$02
    LDA #$00

ClearGdvFactors:
    STA GdvFactor0,X
    DEX
    BPL ClearGdvFactors
    LDX #$07
    SEC

CompareScoreWithBest:
    LDA ScoreDigits,X
    SBC BestScoreDigits,X
    DEX
    BPL CompareScoreWithBest
    BCC FinishBestScoreUpdate
    LDY #$08

CopyNewBestScore:
    LDA ScoreDigits - 1,Y
    STA BestScoreDigits - 1,Y
    DEY
    BNE CopyNewBestScore

FinishBestScoreUpdate:
    STY FairiesCollected
    LDX #$03
    TYA

ResetPostGameCounters:
    STA FireballLifeCounter1Lo,X
    DEX
    BPL ResetPostGameCounters
    STY FireballLifetimeLo
    INY
    STY FireballLifetimeHi
    LDX #$03
    STX InventorySlotCount
    STX ChrBankRequest
    LDY #PostGameSoundEffect
    JSR AddSoundEffect
    LDA #PostGamePpuStreamIndex
    JSR QueueStaticPpuUpdateStream
    LDA #PostGamePpuWaitMask
    LDX #PostGamePpuWaitAddress
    JSR WaitForMaskedBitsClear
    LDX #PostGameResultTemplateSize - 1

CopyPostGameResultTemplate:
    LDA PostGameResultPpuTemplate,X
    STA PpuUpdateBuffer,X
    DEX
    BPL CopyPostGameResultTemplate
    LDX CurrentGdvValue
    JSR FormatTwoDigitNumberTiles
    STX PpuUpdateBuffer + PostGameResultTensOffset
    STA PpuUpdateBuffer + PostGameResultOnesOffset
    JSR PublishPpuUpdateBuffer

.if SolomonRevision = SolomonRevisionEurope
    LDA CurrentRoomIndex
    STA RegionalNewGameRoomIndex
    LSR GameStateFlags
    ASL GameStateFlags
.endif

WaitForPostGameDecision:
    LDA Joypad1Cached
.if SolomonRevision = SolomonRevisionEurope
    AND #JOY_BUTTON_START
    BNE :++
.else
    CMP #PostGameInputCode
    BEQ ResetForNewGameAfterResult
.endif
    JSR SwitchThreads
    LDA FireballLifeCounter1Hi
    CMP #PostGameMinimumWaitHigh
    BCC WaitForPostGameDecision

.if SolomonRevision = SolomonRevisionEurope
    LDX #RegionalNewGameFlagCount - 1

    :
    LDA GameStateFlags,X
    STA RegionalNewGameFlags,X
    DEX
    BPL :-
.endif

StartPostGameThread:
    LSR GameStateFlags
    ASL GameStateFlags

SelectPostGameThread:
    LDA #PostGameThreadCode
    BNE StartGameplayExitThread

.if SolomonRevision = SolomonRevisionEurope
    :
    LDA Joypad1Cached
    AND #JOY_BUTTON_START
    BNE :-
    LDA #$01
    ORA GameStateFlags
    STA GameStateFlags
.endif

ResetForNewGameAfterResult:
    LDA #RoomStateNewGameMask
    AND RoomStateFlags
    STA RoomStateFlags
    LDY #NewGameSoundEffect
    JSR AddSoundEffect
    LDX #$07
    LDA #$00

ClearScoreForNewGame:
    STA ScoreDigits,X
    DEX
    BPL ClearScoreForNewGame
    LDA #GameplayFlagsNewGameMask
    AND GameplayFlags
    STA GameplayFlags
.if SolomonRevision <> SolomonRevisionEurope
    LDX #LastRegularRoomIndex
    CPX CurrentRoomIndex
    BCS SelectNewGameLives
    LDA #PostGameAlternateBonusFlag
    BIT RoomStateFlags
    BNE StartPostGameThread
    STX CurrentRoomIndex
.endif

SelectNewGameLives:
    LDX #NewGameLives

ReloadRoomAfterLifeLoss:
    LDA FireballState
    BEQ SelectRoomLoadThread
    LDA #RoomStateNewGameMask
    AND RoomStateFlags
    STA RoomStateFlags

SelectRoomLoadThread:
    LDA #NewRoomThreadCode

StartGameplayExitThread:
    STX RemainingLives
    PHA
    JSR Clear30x24NametableRegion
    PLA
    JSR StartThread
    LDA #$00
    STA FireballState
    STA DanaObject + ObjectStateOffset
    STA FireballActive
    LDA #GameplayExitWorkerContext
    JSR StopThread

.assert * - RunTimeOverTransition = $1F7 + (SolomonRevision = SolomonRevisionEurope) * $10, error, "unexpected gameplay-exit flow size"
