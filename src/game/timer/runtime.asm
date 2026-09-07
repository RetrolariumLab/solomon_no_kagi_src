; Countdown timer arithmetic and warning-state transitions

.segment "PRG_TIMER"

PendingTimerTickCount = TempPointer02
TimerDecrementMagnitude = TempPointer02 + 1
TimerDisplayNonzeroAccumulator = TempPointer02

DecrementTimer:
    LDA #<TimerWarningState
    STA TempPointer00
    LDA #>TimerWarningState
    STA TempPointer00 + 1
    LDA GameplayUpdateCount
    STA PendingTimerTickCount
    BEQ CommitTimerDisplayUpdate
    LDA TimerDecrementStep
    AND #$7F
    STA TimerDecrementMagnitude
    STA TimerDecrementStep

ProcessPendingTimerTicks:
    LDY #$02
    LDA (TempPointer00),Y
    INY
    CLC
    ADC (TempPointer00),Y
    STA (TempPointer00),Y
    BCC NextTimerTick

DecrementTimerByOne:
    INY
    LDA (TempPointer00),Y
    SBC TimerDecrementMagnitude
    BCS StoreChangedTimerDigit
    LDX #$04
    BCC WrapTimerDigitAfterBorrow

BorrowFromNextTimerDigit:
    INY
    LDA (TempPointer00),Y
    SBC #$00
    BCS StoreChangedTimerDigit

WrapTimerDigitAfterBorrow:
    ADC #$0A
    STA (TempPointer00),Y
    CLC
    DEX
    BNE BorrowFromNextTimerDigit
    LDX #$02
    LDA #$00

ClearLowerTimerDigits:
    STA TimerDigit10,X
    DEX
    BPL ClearLowerTimerDigits

StoreChangedTimerDigit:
    STA (TempPointer00),Y
    LDA #$80
    ORA TimerDecrementStep
    STA TimerDecrementStep

NextTimerTick:
    DEC PendingTimerTickCount
    BNE ProcessPendingTimerTicks

CommitTimerDisplayUpdate:
    LDA TimerDecrementStep
    BPL UpdateTimerWarningState
    LDX PpuUpdateStreamPointer + 1
    BNE UpdateTimerWarningState
    LDA TimerDecrementStep
    AND #$7F
    STA TimerDecrementStep
    JSR BuildTimerDisplayUpdate
    LDA TimerDisplayNonzeroAccumulator
    BNE UpdateTimerWarningState
    LDA #$33
    JSR StartThread

UpdateTimerWarningState:
    LDA TimerWarningState
    TAY
    AND #$03
    TAX
    TYA
    AND #$10
    TAY
    LDA TimerDigit10000
    ASL A
    ASL A
    ASL A
    ASL A
    ORA TimerDigit1000
    CMP TimerWarningThresholds,X
    BCS LeaveTimerWarningRange
    TYA
    BNE FinishTimerUpdate
    LDA PpuUpdateStreamPointer + 1
    BNE FinishTimerUpdate
    LDA #<EnterTimerWarningPpuUpdate
    STA PpuUpdateStreamPointer
    LDA #>EnterTimerWarningPpuUpdate
    STA PpuUpdateStreamPointer + 1
    LDY #$04
    JSR AddSoundEffect
    LDA #$10
    ORA TimerWarningState
    BNE StoreTimerWarningState

LeaveTimerWarningRange:
    TYA
    BEQ FinishTimerUpdate
    LDA #<LeaveTimerWarningPpuUpdate
    STA PpuUpdateStreamPointer
    LDA #>LeaveTimerWarningPpuUpdate
    STA PpuUpdateStreamPointer + 1
    LDY #$01
    LDA FireballState
    BEQ QueueTimerWarningUpdate
    INY

QueueTimerWarningUpdate:
    JSR AddSoundEffect
    LDA #$EF
    AND TimerWarningState

StoreTimerWarningState:
    STA TimerWarningState

FinishTimerUpdate:
    RTS
