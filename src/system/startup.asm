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
