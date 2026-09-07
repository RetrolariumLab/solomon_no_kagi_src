; Eight-context cooperative scheduler and its initial stack/entry tables

.segment "PRG_SCHEDULER"

StartThread:
    STA $00
    LSR A
    LSR A
    LSR A
    LSR A
    STA $01
    TAY
    LDA #$00
    SEC

BuildThreadMask:
    ROL A
    DEY
    BPL BuildThreadMask
    ORA ActiveThreadMask
    STA ActiveThreadMask
    LDY $01
    LDX InitialThreadStackPointers,Y
    STX ThreadStackPointers,Y
    INX
    STX $02
    LDX #$01
    STX $03
    LDA $01
    ASL A
    TAY
    LDA $00
    AND #$0F
    ASL A
    STA $04
    LDA ThreadEntryTableBases,Y
    ADC $04
    STA $04
    LDA ThreadEntryTableBases+1,Y
    ADC #$00
    STA $05
    LDY #$00

CopyThreadEntryAddress:
    LDA ($04),Y
    STA ($02),Y
    INY
    CPY #$02
    BNE CopyThreadEntryAddress
    LDA $00
    STA ($02),Y
    LDY $01
    CPY ThreadIndex
    BNE FinishStartThread
    BEQ SelectThreadContext

SwitchThreads:
    TSX
    LDY ThreadIndex
    STX ThreadStackPointers,Y
    LDY ThreadIndex
    INY
    TYA
    AND #$07
    STA ThreadIndex
    TAY

SelectThreadContext:
    LDX ThreadStackPointers,Y
    TXS

FinishStartThread:
    SEC
    RTS

StopThread:
    TAX
    LDA InitialThreadStackPointers,X
    STA ThreadStackPointers,X
    STA $00
    STA $02
    INC $00
    LDY #$01
    STY $01
    LDA #>(IdleThreadLoop - 1)
    STA ($00),Y
    DEY
    LDA #<(IdleThreadLoop - 1)
    STA ($00),Y
    TXA
    CMP ThreadIndex
    BNE StopOtherThread
    LDX $02
    TXS

StopOtherThread:
    TAX
    LDA #$FF
    CLC

BuildInactiveThreadMask:
    ROL A
    DEX
    BPL BuildInactiveThreadMask
    AND ActiveThreadMask
    STA ActiveThreadMask
    SEC
    RTS

IdleThreadLoop:
    JSR SwitchThreads
    BCS IdleThreadLoop

InitialThreadStackPointers:
    .byte $fc, $dc, $bc, $9c, $7c, $5c, $3c, $1c

ThreadEntryTableBases:
; Each base addresses one contiguous subtable below. Keeping the offsets
; relative makes the table follow the longer PAL startup without changing
; the already released USA symbol inventory
    .addr ThreadEntryTableBases + $0E
    .addr ThreadEntryTableBases + $0E
    .addr ThreadEntryTableBases + $20
    .addr ThreadEntryTableBases + $26
    .addr ThreadEntryTableBases + $32
    .addr ThreadEntryTableBases + $3A
    .addr ThreadEntryTableBases + $3C

    .addr NewGameRoomLoadThread - 1
    .addr CastOrRemoveBlock - 1
    .addr HandleDanaHeadCollision - 1
    .addr CastFireballFromInventory - 1
    .addr RoomClearThread - 1
    .addr RoomLoadThread - 1
    .addr PreparePostGameResult - 1
    .addr RunPostGameAttractThread - 1
    .addr StartDemoPlayback - 1

    .addr PublishPpuUpdateBuffer - 2
    .addr PauseGameThread - 1
    .addr RunDemoInputPlayback - 1

    .byte $ff, $9f
    .addr RunDanaDeathTransition - 1
    .addr EnterRoomDoor - 1
    .addr RunTimeOverTransition - 1
    .addr RunKeyCollectionPresentation - 1
    .addr FinalizeGameplayExit - 1

    .addr RunMapItemPresentation - 1
    .addr RunExtraLifeMapItemPresentation - 1
    .addr RunEnemyItemPresentation - 1
    .addr RunExtraLifeEnemyItemPresentation - 1

    .addr ProcessDefeatedEnemyDrops - 1

    .addr RunSpecialRoomScriptThread - 1

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

; Queue a sound-effect command while preserving the caller's accumulator

.segment "PRG_SOUND_EFFECT_QUEUE"

AddSoundEffect:
    PHA
    TYA
    PHA
    LDY #SoundEffectQueueSize - 1

FindSoundEffectQueueSlot:
    LDA SoundEffectQueue,Y
    BEQ StoreSoundEffectRequest
    DEY
    BNE FindSoundEffectQueueSlot

StoreSoundEffectRequest:
    PLA
    STA SoundEffectQueue,Y
    PLA
    RTS

; Publish the shared RAM update-program buffer for the NMI PPU writer

.segment "PRG_PPU_UPDATE_BUFFER"

PublishPpuUpdateBuffer:
    LDA #<PpuUpdateBuffer
    STA PpuUpdateStreamPointer
    LDA #>PpuUpdateBuffer
    STA PpuUpdateStreamPointer + 1
    RTS

; Dispatch through a little-endian pointer appendix following the caller's JSR

.segment "PRG_JUMP_WITH_PARAMS"

JumpWithParams:
    ASL A
    TAY
    INY
    PLA
    STA TempPointer00
    PLA
    STA TempPointer00 + 1
    LDA (TempPointer00),Y
    PHA
    INY
    LDA (TempPointer00),Y
    STA TempPointer00 + 1
    PLA
    STA TempPointer00
    JMP (TempPointer00)

; Reset and select the standard gameplay delay counter

.segment "PRG_GAMEPLAY_DELAY_SETUP"

ResetAndSelectGameplayDelayCounter:
    LDA #$00
    STA GameplayDelayCounter
    LDX #GameplayDelayCounter
    RTS

; Cooperative waits for masked zero-page state

.segment "PRG_MASKED_RAM_WAIT"

WaitForMaskedBitsClear:
    PHA
    TAY
    TXA
    PHA
    TYA
    AND WaitMaskAddressBase,X
    BEQ FinishMaskedRamWait
    JSR SwitchThreads
    PLA
    TAX
    PLA
    BCS WaitForMaskedBitsClear

FinishMaskedRamWait:
    PLA
    PLA
    RTS

WaitForMaskedBitsSet:
    PHA
    TAY
    TXA
    PHA
    TYA
    AND WaitMaskAddressBase,X
    BNE FinishMaskedRamWait
    JSR SwitchThreads
    PLA
    TAX
    PLA
    BCS WaitForMaskedBitsSet

; Stop every secondary scheduler context except the caller-selected context

.segment "PRG_SECONDARY_THREAD_RESET"

ThreadShutdownWaitMask = $02
ThreadShutdownWaitAddress = $78
SchedulerThreadIndexMask = $07
OtherSecondaryThreadCount = $07
PendingThreadStartCount = $04
TransitionGameplayFlagsMask = $FB

ResetOtherSecondaryThreads:
    TXA
    PHA
    LDA #ThreadShutdownWaitMask
    LDX #ThreadShutdownWaitAddress
    JSR WaitForMaskedBitsClear
    PLA
    STA ThreadStopIndex
    LDA #OtherSecondaryThreadCount
    STA RemainingThreadStops

StopNextSecondaryThread:
    INC ThreadStopIndex
    LDA ThreadStopIndex
    AND #SchedulerThreadIndexMask
    BEQ AdvanceSecondaryThreadReset
    JSR StopThread

AdvanceSecondaryThreadReset:
    DEC RemainingThreadStops
    BNE StopNextSecondaryThread
    LDX #PendingThreadStartCount - 1
    LDA #$00

ClearPendingThreadStart:
    STA PendingThreadStarts,X
    DEX
    BPL ClearPendingThreadStart
    LDA GameplayFlags
    AND #TransitionGameplayFlagsMask
    STA GameplayFlags
    LSR $87
    ASL $87
    RTS

; Cooperative wait for an incrementing zero-page counter

.segment "PRG_COUNTER_WAIT"

WaitForZeroPageCounterAboveThreshold:
    PHA
    TXA
    PHA
    JSR SwitchThreads
    PLA
    TAX
    PLA
    CMP ZeroPageCounterBase,X
    BCS WaitForZeroPageCounterAboveThreshold
    RTS
