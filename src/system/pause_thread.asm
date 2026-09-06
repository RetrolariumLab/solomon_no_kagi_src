; Context-two pause loop with Start-button debounce and release latching

.segment "PRG_PAUSE_THREAD"

PauseActiveFlag = $04
PauseFlagsClearMask = $F9
PauseDebounceFrames = $28
PauseThreadIndex = $02
PauseSoundEffect = $0C
ResumeSoundEffect = $0E - (SolomonRevision = SolomonRevisionEurope) * 2

PauseGameThread:
    LDY #PauseSoundEffect
    JSR AddSoundEffect
    LDX #$00
    STX NmiFrameCounter
    INX

WaitForPauseDebounce:
    JSR ClearStartLatchWhenReleased
    LDA NmiFrameCounter
    CMP #PauseDebounceFrames
    BCC WaitForPauseDebounce
    LDA #PauseActiveFlag
    ORA GameStateFlags
    STA GameStateFlags

WaitForInitialStartRelease:
    JSR ClearStartLatchWhenReleased
    TXA
    BNE WaitForInitialStartRelease

WaitForResumeStartPress:
    LDA Joypad1Cached
    AND #JOY_BUTTON_START
    BEQ WaitForResumeStartPress
    TAX

WaitForResumeStartRelease:
    JSR ClearStartLatchWhenReleased
    TXA
    BNE WaitForResumeStartRelease
    LDA #PauseFlagsClearMask
    AND GameStateFlags
    STA GameStateFlags
    LDY #ResumeSoundEffect
    JSR AddSoundEffect
    LDA #PauseThreadIndex
    JSR StopThread

ClearStartLatchWhenReleased:
    LDA Joypad1Cached
    AND #JOY_BUTTON_START
    BNE FinishStartLatchUpdate
    TAX

FinishStartLatchUpdate:
    RTS
