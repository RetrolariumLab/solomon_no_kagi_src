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
