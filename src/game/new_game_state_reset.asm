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
