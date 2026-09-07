; Format seven score digits plus the fixed trailing zero in the HUD buffer

.segment "PRG_SCORE_DISPLAY"

ScoreDisplayDigitCount = 7
ScoreDisplayBlankTile = $24

BuildScoreDisplayUpdate:
    JSR WaitForPpuUpdateStreamIdle
    LDX #$02

CopyScoreDisplayHeader:
    LDA ScoreDisplayPpuCommandHeader,X
    STA PpuUpdateBuffer,X
    DEX
    BPL CopyScoreDisplayHeader
    CLC
    INX
    LDY #ScoreDisplayDigitCount

FormatScoreDisplayDigits:
    LDA ScoreDigits,X
    BNE MarkScoreDisplayNonzero
    BCS StoreScoreDisplayDigit
    LDA #ScoreDisplayBlankTile
    BPL StoreScoreDisplayDigit

MarkScoreDisplayNonzero:
    SEC

StoreScoreDisplayDigit:
    STA PpuUpdateBuffer + 3,X
    INX
    DEY
    BNE FormatScoreDisplayDigits
    STY PpuUpdateBuffer + 10
    STY PpuUpdateBuffer + 11
