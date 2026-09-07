; Expire the active fireball and retire its object after the grace counter

.segment "PRG_FIREBALL_LIFETIME"

UpdateFireballLifetime:
    LDA FireballObject
    BPL FinishFireballLifetimeUpdate

CheckActiveFireballLifetime:
    LDA FireballActive
    BEQ CheckInactiveFireballCleanup
    SEC
    LDA FireballLifetimeLo
    SBC FireballLifeCounter1Lo
    LDA FireballLifetimeHi
    SBC FireballLifeCounter1Hi
    BCS FinishFireballLifetimeUpdate
    LDA #$00
    STA FireballActive
    STA FireballLifeCounter1Lo
    LDX #$04
    STX FireballObject + $03
    BNE FinishFireballLifetimeUpdate

CheckInactiveFireballCleanup:
    LDX FireballLifeCounter1Lo
    CPX #$08
    BCC FinishFireballLifetimeUpdate
    STA FireballObject

FinishFireballLifetimeUpdate:
    RTS
