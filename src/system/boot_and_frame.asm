; Vertical-blank handler, CNROM bank selection, OAM DMA, and PPU scroll commit

.segment "PRG_NMI"

ChrBankCount = 4
ChrBankIndexMask = ChrBankCount - 1
ChrBankRequestConsumed = $80
ThreadStackLocalOffsetMask = $1F
NmiGameplayServiceStackFloor = $08

NMI:
    STX NmiSavedX
    STY NmiSavedY
    PHA
    LDA PpuCtrlShadow
    AND #$7F
    TAY
    STA PpuCtrlShadow
    STA a:PPU_CTRL
    LDA PpuMaskShadow
    AND #$E7
    STA a:PPU_MASK
    LDX PpuScrollY
    JSR WritePpuScroll
    STY a:PPU_CTRL
    LDA #$00
    STA a:OAM_ADDR
    LDA #>OamBuffer
    STA a:OAM_DMA
    LDY #$01
    CPY PpuUpdateStreamPointer + 1
    BCS CheckRoomMapAttributeReadRequest
    JSR ExecutePpuUpdateStream

CheckRoomMapAttributeReadRequest:
    LDA GameplayFlags
    AND #GameplayFlagAttributeReadRequest
    BEQ ResetRoomMapAttributeReadState
    JSR ServiceRoomMapAttributeReadRequest
    JMP UpdateNmiChrBank

ResetRoomMapAttributeReadState:
    LDA #PpuAttributeReadIdleState
    STA PpuAttributeReadState

UpdateNmiChrBank:
    LDA ChrBankRequest
    BMI RestoreNmiPpuMask
    AND #ChrBankIndexMask
    TAX
    LDA ChrBankSelectValues,X
    STA ChrBankSelectValues,X
    LDA #ChrBankRequestConsumed
    STA ChrBankRequest

RestoreNmiPpuMask:
    LDA PpuMaskShadow
    STA a:PPU_MASK
    TSX
    TXA
    AND #ThreadStackLocalOffsetMask
    CMP #NmiGameplayServiceStackFloor
    BCS RunNmiGameplayServices

SkipNmiGameplayServicesForStack:
    BCC NmiRestoreRegisters

RunNmiGameplayServices:
    JSR CheckGameplayObjectInteractions
    LDA $78
    TAX
    AND #$02
    BNE AdvanceNmiFrameCounter
    LDA #$10
    AND Joypad1Cached
    BEQ UpdateNmiGameplayFrame
    TXA
    ROR A
    BCC UpdateNmiGameplayFrame
    LDA #$02
    ORA $78
    STA $78
    LDA #$21
    JSR QueuePendingThreadStart
    BPL AdvanceNmiFrameCounter

UpdateNmiGameplayFrame:
    JSR UpdateDanaControlState
    LDX #$07

IncrementGameplayFrameCounters:
    INC $20,X
    DEX
    BPL IncrementGameplayFrameCounters
    JSR UpdateActiveFireballCollision
    JSR UpdateActiveObjects
    INC FireballLifeCounter1Lo
    BNE AdvanceDemonMirrorSpawnTimer
    INC FireballLifeCounter1Hi

AdvanceDemonMirrorSpawnTimer:
    INC DemonMirrorSpawnTimerLo
    BNE HandleDanaNmiActions
    INC DemonMirrorSpawnTimerHi

HandleDanaNmiActions:
    LDA DanaObject
    CMP #$C0
    BCC ClearNmiActionRequestFlag
    ROR A
    BCS FinishNmiDanaActionRequests
    LDA Joypad1Cached
    ASL A
    BCC CheckNmiFireballInput
    JSR TryStartBlockMagicAction
    BCS FinishNmiDanaActionRequests

CheckNmiFireballInput:
    ASL A
    BCC ClearNmiActionRequestFlag
    JSR TryStartFireballAction
    BCS FinishNmiDanaActionRequests

ClearNmiActionRequestFlag:
    LDA #$FE
    AND $28
    STA $28

FinishNmiDanaActionRequests:
    JMP RunNmiPostGameplayServices

AdvanceNmiFrameCounter:
    INC NmiFrameCounter

RunNmiPostGameplayServices:
    JSR RenderGameplayObjectsToOam
    JSR ReadJoyPads
    LDA $78
    AND #$04
    BNE NmiRestoreRegisters
    JSR UpdateAudio

NmiRestoreRegisters:
    LDX NmiSavedX
    LDY NmiSavedY
    LDA PpuCtrlShadow
    ORA #$80
    STA PpuCtrlShadow
    STA a:PPU_CTRL
    PLA
    RTI

ChrBankSelectValues:
    .byte $10, $11, $12, $13

.assert * - ChrBankSelectValues = ChrBankCount, error, "unexpected CHR bank select value count"

WritePpuScroll:
    LDA a:PPU_STATUS
    LDA PpuScrollX
    STA a:PPU_SCROLL
    STX a:PPU_SCROLL
    RTS

; Two-port controller sampling and cached-input update

.segment "PRG_CONTROLLER_INPUT"

ControllerBitCount = $08
ControllerStrobeValue = $01

ReadJoyPads:
    LDA #ControllerStrobeValue
    STA a:JOYPAD1
    LSR A
    TAX
    STA a:JOYPAD1
    STA ControllerShiftRegister
    LDY #ControllerBitCount
    JSR ReadJoyPad
    STY ControllerShiftRegister
    INX
    LDY #ControllerBitCount
    JSR ReadJoyPad
    LDA GameStateFlags
    LSR A

UpdateJoypadCache:
    LDA Joypad1Raw,X
    BCS CacheCompleteJoypadState
    AND #JOY_BUTTON_START_SELECT_MASK
    STA ControllerPortSample
    LDA Joypad1Cached,X
    AND #JOY_BUTTON_GAMEPLAY_MASK
    ORA ControllerPortSample

CacheCompleteJoypadState:
    STA Joypad1Cached,X
    DEX
    BPL UpdateJoypadCache
    RTS

ReadJoyPad:
    LDA a:JOYPAD1,X
    STA ControllerPortSample
    ROR A
    ORA ControllerPortSample
    ROR A
    ROL ControllerShiftRegister
    DEY
    BNE ReadJoyPad
    LDA ControllerShiftRegister
    STA Joypad1Raw,X
    RTS

; Reset, warm-boot state, initial thread stacks, and nametable initialization

.segment "PRG_STARTUP"

WarmBootSignatureSize = 4
WarmBootDefaultStateSize = 8

Reset:
    SEI
    CLD
    LDA #$30
    STA a:PPU_CTRL
    LDX #$FF
    TXS

WaitForFirstVBlank:
    LDA a:PPU_STATUS
    BPL WaitForFirstVBlank

WaitForSecondVBlank:
    LDA a:PPU_STATUS
    BPL WaitForSecondVBlank
    LDA #$00
    STA TempPointer00
    TAY
    LDX #$07
    LDY #$F0

ClearRamPageLoop:
    STX TempPointer00+1

ClearRamByteLoop:
    DEY
    STA (TempPointer00),Y
    BNE ClearRamByteLoop
    DEX
    BPL ClearRamPageLoop
    TXS
    STA a:APU_DMC_FREQ
    STA a:APU_DMC_RAW
    STA a:APU_FRAME
    LDA #$0F
    STA a:APU_SND_CHN
    LDA #$00
    STA a:PPU_MASK
    STA PpuMaskShadow
    TAY
    LDA #$F8
    STY TempPointer00
    LDX #>OamBuffer
    STX TempPointer00+1

HideAllSpritesLoop:
    STA (TempPointer00),Y
    INY
    INY
    INY
    INY
    BNE HideAllSpritesLoop
    LDA #$20
    JSR InitializeNametable
    LDA #$28
    JSR InitializeNametable
    LDX #$F8
    STX PpuScrollX
    LDX #$00
    STX PpuScrollY
    DEX
    TXS
    LDA #$B0
    STA PpuCtrlShadow
    STA a:PPU_CTRL

WaitForNmiWarmup:
    LDA $21
    CMP #$02
    BCC WaitForNmiWarmup
    LDA #$30
    STA a:PPU_CTRL
    LDA a:PPU_STATUS

WaitForChrBankSwitch:
    LDA StartupChrBankSelectValue
    STA StartupChrBankSelectValue
    LDA #$15
    STA a:PPU_ADDR
    LDA #$80
    STA a:PPU_ADDR
    LDA a:PPU_DATA
    LDA a:PPU_DATA
    CMP #$DF
    BEQ WaitForChrBankSwitch
    LDA #$B0
    STA a:PPU_CTRL
    LDA #$1E
    STA PpuMaskShadow
    STA a:PPU_MASK
    LDX #WarmBootSignatureSize-1

CheckWarmBootSignature:
    LDA StartupWarmBootSignature,X
    CMP WarmBootSignature,X
    BNE InitializeWarmBootState
    DEX
    BPL CheckWarmBootSignature
    BMI InitializeThreadStacks

InitializeWarmBootState:
    LDX #WarmBootSignatureSize-1

CopyWarmBootSignature:
    LDA StartupWarmBootSignature,X
    STA WarmBootSignature,X
    DEX
    BPL CopyWarmBootSignature
    LDX #WarmBootDefaultStateSize-1

CopyWarmBootDefaultState:
    LDA StartupWarmBootDefaultState,X
    STA WarmBootDefaultState,X
    DEX
    BPL CopyWarmBootDefaultState
    LDA #$2F
    STA WarmBootMarker

InitializeThreadStacks:
.if SolomonRevision = SolomonRevisionEurope
    LDA #$00
    STA RegionalNewGameRoomIndex
    STA RegionalNewGameFlags + 0
    STA RegionalNewGameFlags + 1
    STA RegionalNewGameFlags + 2
    STA RegionalNewGameFlags + 3
    STA RegionalNewGameFlags + 4
.endif
    LDA #$1C
    LDX #ThreadStackPointerCount-1

InitializeThreadStackPointerLoop:
    STA ThreadStackPointers,X
    CLC
    ADC #$20
    DEX
    BNE InitializeThreadStackPointerLoop
    STX ThreadIndex
    INX
    LDA #$1D
    STA TempPointer00
    STX TempPointer00+1
    LDY #$06
    DEX
    CLC

InitializeIdleThreadFrames:
    LDA #<(IdleThreadLoop - 1)
    STA (TempPointer00,X)
    INC TempPointer00
    LDA #>(IdleThreadLoop - 1)
    STA (TempPointer00,X)
    LDA #$1F
    ADC TempPointer00
    STA TempPointer00
    DEY
    BNE InitializeIdleThreadFrames
    LDA #<RoomLoadPaletteTemplate
    STA $1A
    LDA #>RoomLoadPaletteTemplate
    STA $1B
    LDA #$17
    JSR StartThread

StartPendingThreads:
    LDY #$03

StartPendingThread:
    LDX PendingThreadStarts,Y
    BEQ NextPendingThread
    LDA #$00
    STA PendingThreadStarts,Y
    TXA
    STY $06
    JSR StartThread
    LDY $06

NextPendingThread:
    DEY
    BPL StartPendingThread
    JSR SwitchThreads
    BCS StartPendingThreads

StartupChrBankSelectValue:
    .byte $96

StartupWarmBootSignature:
    .byte $46, $55, $4b, $55

StartupWarmBootDefaultState:
    .byte $00, $00, $01, $00, $00, $00, $00, $00

InitializeNametable:
    LDX a:PPU_STATUS
    STA a:PPU_ADDR
    LDA #$00
    STA a:PPU_ADDR
    LDA #$31
    STA a:PPU_CTRL
    LDA #$24
    LDX #$04
    LDY #$C0

FillNametableTiles:
    STA a:PPU_DATA
    DEY
    BNE FillNametableTiles
    DEX
    BNE FillNametableTiles
    TXA
    LDY #$40

FillNametableAttributes:
    STA a:PPU_DATA
    DEY
    BNE FillNametableAttributes
    STY a:PPU_SCROLL
    STY a:PPU_SCROLL
    LDX a:PPU_STATUS
    RTS
