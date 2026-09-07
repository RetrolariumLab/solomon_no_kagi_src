; Convert the remaining decimal timer to score in chunks of eight

.segment "PRG_ROOM_TIME_BONUS"

SubtractTimerBy8:
    LDA TimerDigit10
    SEC
    SBC #$08
    LDY #$04
    LDX #$00
    BEQ PropagateTimerBonusBorrow

SubtractTimerBonusDigits:
    LDA TimerDigit10,X
    SBC #$00

PropagateTimerBonusBorrow:
    BCS StoreTimerBonusDigit
    ADC #$0A
    CLC

StoreTimerBonusDigit:
    STA TimerDigit10,X
    INX
    DEY
    BNE SubtractTimerBonusDigits
    BCS AddFullTimerBonusChunk
    LDA TimerDigit10
    SBC #$01
    TAX
    TYA
    LDY #$03

ClearExhaustedTimerDigits:
    STA TimerDigit10,Y
    DEY
    BPL ClearExhaustedTimerDigits
    TXA
    LDX #$06
    JMP AddTimerBonusChunkToScore

AddFullTimerBonusChunk:
    LDX #$06
    LDA #$08
    JSR AddTimerBonusChunkToScore
    BNE SubtractTimerBy8

AddTimerBonusChunkToScore:
    JSR AddScoreByAAtDigitX
    JSR BuildScoreDisplayUpdate
    LDA #$24
    STA PpuUpdateBuffer + $0B
    CLC
    LDX #$03
    LDY #$00
    STY PpuUpdateBuffer + $10
    STY PpuUpdateBuffer + $11

CopyTimerBonusDisplayDigits:
    LDA TimerDigit10,X
    BNE MarkNonzeroTimerBonusDigit
    BCS StoreTimerBonusDisplayDigit
    LDA #$24
    BPL StoreTimerBonusDisplayDigit

MarkNonzeroTimerBonusDigit:
    SEC

StoreTimerBonusDisplayDigit:
    STA PpuUpdateBuffer + $0C,Y
    INY
    DEX
    BPL CopyTimerBonusDisplayDigits
    LDA #$4D
    STA PpuUpdateBuffer + $02
    JMP PublishPpuUpdateBuffer
