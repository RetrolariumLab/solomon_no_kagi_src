; Convert an unsigned value in X to blank-padded tens in X and ones in A

.segment "PRG_TWO_DIGIT_NUMBER"

FormatTwoDigitNumberTiles:
    TXA
    LDX #$00

CountTwoDigitTens:
    CMP #$0A
    BCC SelectTwoDigitTensTile
    SBC #$0A
    INX
    BNE CountTwoDigitTens

SelectTwoDigitTensTile:
    CPX #$00
    BNE FinishTwoDigitNumberTiles
    LDX #$24

FinishTwoDigitNumberTiles:
    RTS

; Initialize the shared auxiliary object from map or pixel coordinates

.segment "PRG_AUXILIARY_EFFECT"

AuxiliaryEffectTemplateSize = $04

SpawnAuxiliaryEffectAtMapCell:
    PHA
    JSR ConvertMapIndexToPixelCoordinates
    JSR SpawnAuxiliaryEffectAtCoordinates
    PLA
    RTS

SpawnAuxiliaryEffectAtCoordinates:
    LDA SpawnYPosition
    STA AuxiliaryYPosition
    LDA SpawnXPosition
    STA AuxiliaryXPosition
    LDX #AuxiliaryEffectTemplateSize - 1

CopyAuxiliaryEffectTemplate:
    LDA AuxiliaryEffectTemplate,X
    STA AuxiliaryObject,X
    DEX
    BPL CopyAuxiliaryEffectTemplate
    RTS

AuxiliaryEffectTemplate:
    .byte $C6, $1C, $FF, $0C

.assert * - AuxiliaryEffectTemplate = AuxiliaryEffectTemplateSize, error, "auxiliary effect template size changed"

; Decimal score addition with game-state gating

.segment "PRG_SCORE_ADDITION"

ScoreDigitBase = $0A

AddScoreByAAtDigitX:
    ROR GameStateFlags
    BCS AddPendingScore
    LDA #$00

AddPendingScore:
    ROL GameStateFlags
    CLC

AddNextScoreDigit:
    ADC ScoreDigits,X
    CMP #ScoreDigitBase
    BCC StoreScoreDigit
    SBC #ScoreDigitBase

StoreScoreDigit:
    STA ScoreDigits,X
    LDA #$00
    DEX
    BPL AddNextScoreDigit
    RTS
