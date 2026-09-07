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

; Build the NMI-consumed update program for the four timer digits

.segment "PRG_TIMER_DISPLAY"

BuildTimerDisplayUpdate:
    LDX #$02

CopyTimerDisplayWriterCall:
    LDA TimerDisplayWriterCallTemplate,X
    STA TimerDisplayUpdateBuffer,X
    DEX
    BPL CopyTimerDisplayWriterCall
    LDX #$03
    LDA #$00
    STA TimerDisplayTerminator + 1
    STA TimerDisplayNonzeroAccumulator
    TAY

CopyTimerDigits:
    LDA TimerDigit10,X
    STA TimerDisplayDigits,Y
    ORA TimerDisplayNonzeroAccumulator
    STA TimerDisplayNonzeroAccumulator
    INY
    DEX
    BPL CopyTimerDigits
    INX
    STX TimerDisplayTerminator
    LDA #$24

BlankLeadingTimerZeroes:
    LDY TimerDisplayDigits,X
    BNE PublishTimerDisplayUpdate
    STA TimerDisplayDigits,X
    INX
    CPX #$04
    BNE BlankLeadingTimerZeroes

PublishTimerDisplayUpdate:
    JMP PublishPpuUpdateBuffer

TimerDisplayWriterCallTemplate:
    .byte $20, $69, $44

; Item effects that multiply or replace the remaining room timer

.segment "PRG_TIMER_ITEM_EFFECTS"

TimerDigitCount = $04
TimerDigitBase = $0A

ApplyDoubleTimerItem:
    LDA TimerDecrementStep
    ASL A
    LDA #$04
    ROR A
    STA TimerDecrementStep

DoubleRemainingTime:
    LDX #$00
    LDY #TimerDigitCount
    CLC

DoubleNextTimerDigit:
    LDA TimerDigit10,X
    ADC TimerDigit10,X
    CMP #TimerDigitBase
    BCC StoreDoubledTimerDigit
    SBC #TimerDigitBase

StoreDoubledTimerDigit:
    STA TimerDigit10,X
    INX
    DEY
    BNE DoubleNextTimerDigit
    RTS

ApplyQuintupleTimerItem:
    LDA TimerDecrementStep
    ASL A
    ASL A
    ADC TimerDecrementStep
    STA TimerDecrementStep
    LDX #TimerDigitCount - 1

SaveTimerDigitsForQuintupling:
    LDA TimerDigit10,X
    STA TimerDigitSnapshot,X
    DEX
    BPL SaveTimerDigitsForQuintupling
    JSR DoubleRemainingTime
    JSR DoubleRemainingTime
    LDX #$00
    LDY #TimerDigitCount
    CLC

AddOriginalTimerDigit:
    LDA TimerDigit10,X
    ADC TimerDigitSnapshot,X
    CMP #TimerDigitBase
    BCC StoreQuintupledTimerDigit
    SBC #TimerDigitBase

StoreQuintupledTimerDigit:
    STA TimerDigit10,X
    INX
    DEY
    BNE AddOriginalTimerDigit
    RTS

SetTimerTo10000:
    LDA #$01
    BNE SetTimerTenThousandsDigit

SetTimerTo05000:
    LDA #$00
    JSR SetTimerTenThousandsDigit
    LDA #$05
    STA TimerDigit1000
    RTS

SetTimerTenThousandsDigit:
    LDX #TimerDigitCount - 1

StoreTimerTenThousandsAndClearLowerDigits:
    STA TimerDigit10,X
    LDA #$00
    DEX
    BPL StoreTimerTenThousandsAndClearLowerDigits
    RTS
