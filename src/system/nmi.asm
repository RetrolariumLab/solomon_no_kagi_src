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
