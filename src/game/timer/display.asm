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
