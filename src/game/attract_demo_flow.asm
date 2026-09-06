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
    .res 75, $FF
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

.assert * - FillerBeforeRoomTilePatterns = 203 - (SolomonRevision = SolomonRevisionEurope) * 128, error, "unexpected pre-room-tile filler size"
