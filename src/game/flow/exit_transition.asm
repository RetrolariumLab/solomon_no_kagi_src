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
