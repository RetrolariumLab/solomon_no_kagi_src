; NMI-driven virtual-channel sequencer and APU register publisher

AudioRegionalRamOffset = SolomonRevision = SolomonRevisionEurope
AudioChannelState = $0456 + AudioRegionalRamOffset
AudioChannelStateStride = $10
AudioVirtualChannelCount = 8
AudioHardwareChannelLastIndex = 3
AudioInitialChannelPairMask = $03
AudioPrimaryVirtualChannelBits = $55
AudioEnabledHardwareChannelMask = $0F
AudioDurationCounter = $04D6 + AudioRegionalRamOffset
AudioDurationReload = $04D7 + AudioRegionalRamOffset
AudioEnvelopeCounter = $04D8 + AudioRegionalRamOffset
AudioEnvelopeVolume = $04D9 + AudioRegionalRamOffset
AudioActiveChannelMask = $04F6 + AudioRegionalRamOffset
AudioChannelPointer = TempPointer08
AudioHardwareChannelIndex = TempPointer0A
AudioChannelMask = TempPointer0A + 1
AudioStreamPointer = TempPointer0C
AudioQueueIndex = TempPointer0C + 1
AudioScratch = TempPointer0E

.segment "PRG_AUDIO_ENGINE"

UpdateAudio:
    LDX #$02

StartNextQueuedSoundEffect:
    LDY SoundEffectQueue,X
    BEQ ContinueSoundEffectQueue
    JSR StartQueuedSoundEffect

ContinueSoundEffectQueue:
    DEX
    BPL StartNextQueuedSoundEffect
    LDA #<AudioChannelState
    STA AudioChannelPointer
    LDA #>AudioChannelState
    STA AudioChannelPointer + 1
    LDA #$00
    STA AudioHardwareChannelIndex
    LDY #AudioVirtualChannelCount
    STY AudioChannelMask

UpdateNextVirtualAudioChannel:
    LDA AudioActiveChannelMask
    LSR A
    BCC StoreRotatedActiveChannelMask
    ORA #$80

StoreRotatedActiveChannelMask:
    STA AudioActiveChannelMask
    BCC AdvanceVirtualAudioChannel
    LDX AudioHardwareChannelIndex
    DEC AudioDurationCounter,X
    BNE UpdateVirtualChannelEnvelopeTimer
    JSR DecodeAudioStream

UpdateVirtualChannelEnvelopeTimer:
    LDX AudioHardwareChannelIndex
    DEC AudioEnvelopeCounter,X
    BNE ApplyVirtualChannelEnvelope
    JSR ReloadVirtualChannelEnvelope

ApplyVirtualChannelEnvelope:
    JSR UpdateVirtualChannelEnvelope

AdvanceVirtualAudioChannel:
    CLC
    LDA #AudioChannelStateStride
    ADC AudioChannelPointer
    STA AudioChannelPointer
    LDA #$00
    ADC AudioChannelPointer + 1
    STA AudioChannelPointer + 1
    LDA #$04
    ADC AudioHardwareChannelIndex
    STA AudioHardwareChannelIndex
    DEC AudioChannelMask
    BNE UpdateNextVirtualAudioChannel
    LDA #<AudioChannelState
    STA AudioChannelPointer
    LDA #>AudioChannelState
    STA AudioChannelPointer + 1
    LDA #AudioHardwareChannelLastIndex
    STA AudioHardwareChannelIndex
    LDA #AudioInitialChannelPairMask
    STA AudioChannelMask

; Pairs 0/1, 2/3, 4/5, and 6/7 feed pulse 1, pulse 2, triangle,
; and noise. An active even-numbered primary wins; the odd secondary resumes
; automatically when its primary becomes inactive
PublishNextApuChannel:
    LDA AudioActiveChannelMask
    AND AudioChannelMask
    BEQ SelectSecondaryVirtualChannel
    AND #AudioPrimaryVirtualChannelBits
    BNE SelectPrimaryVirtualChannel

SelectSecondaryVirtualChannel:
    JSR AdvanceAudioChannelPointer
    JSR WriteCurrentApuChannel
    JMP AdvanceToNextApuChannel

SelectPrimaryVirtualChannel:
    JSR WriteCurrentApuChannel
    JSR AdvanceAudioChannelPointer

AdvanceToNextApuChannel:
    JSR AdvanceAudioChannelPointer

AdvanceApuChannelMask:
    ASL AudioChannelMask
    ASL AudioChannelMask
    DEC AudioHardwareChannelIndex
    BPL PublishNextApuChannel
    LDA #AudioEnabledHardwareChannelMask
    STA a:APU_SND_CHN
    RTS

AdvanceAudioChannelPointer:
    CLC
    LDA #AudioChannelStateStride
    ADC AudioChannelPointer
    STA AudioChannelPointer
    LDA #$00
    ADC AudioChannelPointer + 1
    STA AudioChannelPointer + 1
    RTS

WriteCurrentApuChannel:
    LDA #$03
    EOR AudioHardwareChannelIndex
    ASL A
    ASL A
    TAX
    LDY #$06
    LDA (AudioChannelPointer),Y
    DEY
    PHA
    LDA AudioHardwareChannelIndex
    CMP #$01
    BNE UseStandardChannelVolume
    PLA
    AND #$0F
    ORA #$80
    BNE WriteApuChannelVolume

UseStandardChannelVolume:
    PLA
    ORA #$30

WriteApuChannelVolume:
    STA a:APU_PL1_VOL,X
    LDA #$10
    AND (AudioChannelPointer),Y
    BNE WriteApuChannelPeriodIfDirty
    LDA #$19
    STA a:APU_PL1_SWEEP,X

WriteApuChannelPeriodIfDirty:
    LDY #$08
    LDA (AudioChannelPointer),Y
    BPL FinishApuChannelWrite
    PHA
    AND #$7F
    STA (AudioChannelPointer),Y
    DEY
    LDA (AudioChannelPointer),Y
    INY
    STA a:APU_PL1_LO,X
    LDA (AudioChannelPointer),Y
    PLA
    ORA #$20
    STA a:APU_PL1_HI,X

FinishApuChannelWrite:
    RTS

UpdateVirtualChannelEnvelope:
    LDY #$05
    LDA (AudioChannelPointer),Y
    TAX
    AND #$F0
    STA AudioScratch
    AND #$20
    BEQ UseConfiguredEnvelopeStep
    LDA #$0F
    STA AudioScratch + 1
    BNE ApplyChannelEnvelopeStep

UseConfiguredEnvelopeStep:
    TXA
    AND #$0F
    STA AudioScratch + 1

ApplyChannelEnvelopeStep:
    LDX AudioHardwareChannelIndex
    LDA AudioEnvelopeVolume,X
    SEC
    SBC AudioScratch + 1
    BCS StoreChannelVolume
    LDA #$00

StoreChannelVolume:
    ORA AudioScratch
    LDY #$06
    STA (AudioChannelPointer),Y
    RTS

ReloadVirtualChannelEnvelope:
    LDY #$02
    LDA (AudioChannelPointer),Y
    INY
    STA AudioScratch
    LDA (AudioChannelPointer),Y
    INY
    STA AudioScratch + 1
    LDA (AudioChannelPointer),Y
    PHA
    CLC
    ADC #$02
    STA (AudioChannelPointer),Y
    PLA
    TAY
    LDA (AudioScratch),Y
    INY
    STA AudioEnvelopeCounter,X
    LDA (AudioScratch),Y
    STA AudioEnvelopeVolume,X
    RTS

StartQueuedSoundEffect:
    STX AudioQueueIndex
    LDA #$00
    STA SoundEffectQueue,X
    DEY
    TYA
    ASL A
    TAY
    LDA SoundEffectPointerTable,Y
    STA AudioChannelPointer
    LDA SoundEffectPointerTable + 1,Y
    STA AudioChannelPointer + 1
    LDY #$00
    LDA (AudioChannelPointer),Y
    AND #$7F
    BPL InitializeSoundEffectChannel

ReadNextSoundEffectChannel:
    LDA (AudioChannelPointer),Y
    BPL InitializeSoundEffectChannel
    LDX AudioQueueIndex
    RTS

InitializeSoundEffectChannel:
    INY
    STA AudioStreamPointer
    ASL A
    ASL A
    ASL A
    ASL A
    TAX
    LDA (AudioChannelPointer),Y
    INY
    STA AudioChannelState,X
    LDA (AudioChannelPointer),Y
    STA AudioChannelState + 1,X
    LDA #$00
    STA AudioChannelState + 5,X
    LDA #$0F
    STA AudioChannelState + 9,X
    LDA AudioStreamPointer
    ASL A
    ASL A
    TAX
    LDA #$01
    STA AudioDurationCounter,X
    LSR A
    LDX AudioStreamPointer
    SEC

BuildActiveChannelBit:
    ROL A
    DEX
    BPL BuildActiveChannelBit
    ORA AudioActiveChannelMask
    STA AudioActiveChannelMask
    INY
    BPL ReadNextSoundEffectChannel
DecodeAudioStream:
    LDA #$CF
    LDY #$05
    AND (AudioChannelPointer),Y
    STA (AudioChannelPointer),Y
    LDY #$00
    LDA (AudioChannelPointer),Y
    INY
    STA AudioStreamPointer
    LDA (AudioChannelPointer),Y
    STA AudioStreamPointer + 1
    DEY

DecodeNextAudioToken:
    LDA (AudioStreamPointer),Y
    BPL DecodeNoteToken
    INY
    CMP #$F0
    BCC DecodeDurationToken
    JSR DispatchAudioCommand
    BPL DecodeNextAudioToken

DecodeDurationToken:
    AND #$3F
    TAX
    LDA AudioDurationTable,X
    LDX AudioHardwareChannelIndex
    STA AudioDurationCounter,X
    STA AudioDurationReload,X
    BPL DecodeNextAudioToken

DecodeNoteToken:
    INY
    PHA
    TYA
    LDY #$00
    CLC
    ADC AudioStreamPointer
    STA (AudioChannelPointer),Y
    INY
    LDA #$00
    ADC AudioStreamPointer + 1
    STA (AudioChannelPointer),Y
    PLA
    LDX #$02
    CPX AudioChannelMask
    BCC DecodePitchedNote
    CMP #$10
    BEQ MuteAudioChannel
    STA AudioStreamPointer
    LDA #$00
    STA AudioStreamPointer + 1
    BEQ StoreNotePeriod

DecodePitchedNote:
    TAX
    AND #$0F
    CMP #$0C
    BNE LookUpNotePeriod

MuteAudioChannel:
    LDY #$05
    LDA #$20
    ORA (AudioChannelPointer),Y
    STA (AudioChannelPointer),Y
    BNE FinishAudioToken

LookUpNotePeriod:
    ASL A
    TAY
    LDA AudioPeriodTable,Y
    STA AudioStreamPointer
    LDA AudioPeriodTable + 1,Y
    STA AudioStreamPointer + 1
    TXA
    AND #$F0
    LSR A
    LSR A
    LSR A
    LSR A
    TAX
    BEQ StoreNotePeriod

ShiftNotePeriodByOctave:
    LSR AudioStreamPointer + 1
    ROR AudioStreamPointer
    DEX
    BNE ShiftNotePeriodByOctave

StoreNotePeriod:
    LDY #$07
    LDA AudioStreamPointer
    STA (AudioChannelPointer),Y
    INY
    LDA AudioStreamPointer + 1
    ORA #$80
    STA (AudioChannelPointer),Y

FinishAudioToken:
    LDX AudioHardwareChannelIndex
    LDA AudioDurationReload,X
    STA AudioDurationCounter,X
    LDA #$01
    STA AudioEnvelopeCounter,X
    LDA #$00
    LDY #$04
    STA (AudioChannelPointer),Y
    RTS

DispatchAudioCommand:
    AND #$0F
    ASL A
    TAX
    LDA AudioCommandHandlerTable,X
    STA AudioScratch
    LDA AudioCommandHandlerTable + 1,X
    STA AudioScratch + 1
    JMP (AudioScratch)

AudioCommandHandlerTable:
    .word AudioCommandF0SetSequence
    .word AudioCommandF1SetControl
    .word AudioCommandF2Jump
    .word AudioCommandF3Call
    .word AudioCommandF4Return
    .word AudioCommandF5BeginLoop
    .word AudioCommandF6EndLoop
    .word AudioCommandF7SetSweep
    .word AudioCommandF8SetVolume
    .word AudioCommandF9StopChannel

AudioCommandF0SetSequence:
    LDA (AudioStreamPointer),Y
    INY
    STY AudioScratch
    ASL A
    TAX
    LDA AudioEnvelopePointerTable,X
    TAY
    LDA AudioEnvelopePointerTable + 1,X
    TAX
    TYA
    LDY #$02
    STA (AudioChannelPointer),Y
    INY
    TXA
    STA (AudioChannelPointer),Y
    LDY AudioScratch
    RTS

AudioCommandF1SetControl:
    LDA (AudioStreamPointer),Y
    INY
    STY AudioScratch
    STA AudioScratch + 1
    LDA #$F0
    LDY #$05
    AND (AudioChannelPointer),Y
    ORA AudioScratch + 1
    STA (AudioChannelPointer),Y
    LDY AudioScratch
    RTS

AudioCommandF2Jump:
    LDA (AudioStreamPointer),Y
    INY
    TAX
    LDA (AudioStreamPointer),Y
    STX AudioStreamPointer
    STA AudioStreamPointer + 1
    LDY #$00
    RTS

AudioCommandF3Call:
    LDA (AudioStreamPointer),Y
    INY
    TAX
    LDA (AudioStreamPointer),Y
    INY
    PHA
    TYA
    PHA
    LDY #$09
    LDA (AudioChannelPointer),Y
    TAY
    PLA
    CLC
    ADC AudioStreamPointer
    STA (AudioChannelPointer),Y
    DEY
    LDA #$00
    ADC AudioStreamPointer + 1
    STA (AudioChannelPointer),Y
    DEY
    TYA
    LDY #$09
    STA (AudioChannelPointer),Y
    STX AudioStreamPointer
    PLA
    STA AudioStreamPointer + 1
    LDY #$00
    RTS

AudioCommandF4Return:
    LDY #$09
    LDA (AudioChannelPointer),Y
    TAY
    INY
    LDA (AudioChannelPointer),Y
    INY
    STA AudioStreamPointer + 1
    LDA (AudioChannelPointer),Y
    STA AudioStreamPointer
    TYA
    LDY #$09
    STA (AudioChannelPointer),Y
    LDY #$00
    RTS

AudioCommandF5BeginLoop:
    LDA (AudioStreamPointer),Y
    INY
    TAX
    TYA
    PHA
    LDY #$09
    LDA (AudioChannelPointer),Y
    TAY
    PLA
    CLC
    ADC AudioStreamPointer
    STA AudioStreamPointer
    STA (AudioChannelPointer),Y
    DEY
    LDA #$00
    ADC AudioStreamPointer + 1
    STA AudioStreamPointer + 1
    STA (AudioChannelPointer),Y
    DEY
    TXA
    STA (AudioChannelPointer),Y
    DEY
    TYA
    LDY #$09
    STA (AudioChannelPointer),Y
    LDY #$00
    RTS

AudioCommandF6EndLoop:
    STY AudioScratch
    LDY #$09
    LDA (AudioChannelPointer),Y
    TAY
    INY
    LDA (AudioChannelPointer),Y
    CLC
    SBC #$00
    STA (AudioChannelPointer),Y
    BEQ FinishAudioLoop
    INY
    LDA (AudioChannelPointer),Y
    INY
    STA AudioStreamPointer + 1
    LDA (AudioChannelPointer),Y
    STA AudioStreamPointer
    LDY #$00
    RTS

FinishAudioLoop:
    INY
    INY
    TYA
    LDY #$09
    STA (AudioChannelPointer),Y
    LDY AudioScratch
    RTS

AudioCommandF7SetSweep:
    STY AudioScratch
    LDY #$05
    LDA #$10
    ORA (AudioChannelPointer),Y
    STA (AudioChannelPointer),Y
    LDA #$07
    EOR AudioChannelMask
    LSR A
    ASL A
    ASL A
    TAX
    LDY AudioScratch
    LDA (AudioStreamPointer),Y
    INY
    STA a:APU_PL1_SWEEP,X
    RTS

AudioCommandF8SetVolume:
    LDA (AudioStreamPointer),Y
    INY
    STY AudioScratch
    STA AudioScratch + 1
    LDY #$05
    LDA #$3F
    AND (AudioChannelPointer),Y
    ORA AudioScratch + 1
    STA (AudioChannelPointer),Y
    LDY AudioScratch
    RTS

AudioCommandF9StopChannel:
    LDA #$7F
    AND AudioActiveChannelMask
    STA AudioActiveChannelMask
    LDY #$05
    LDA #$0F
    STA (AudioChannelPointer),Y
    PLA
    PLA
    RTS
