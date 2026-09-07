; NMI-side interpreter for compact PPU update streams

.segment "PRG_PPU_UPDATE_STREAM"

PpuCtrlIncrement32 = $04
PpuCtrlIncrement1Mask = $FB
PpuUpdateLiteralCarryMarker = $02
PaletteAddressHigh = $3F

ExecutePpuUpdateStream:
    DEY
    LDA (PpuUpdateStreamPointer),Y

DecodeNextPpuUpdateCommand:
    LDX a:PPU_STATUS
    STA a:PPU_ADDR
    INY
    LDA (PpuUpdateStreamPointer),Y
    STA a:PPU_ADDR
    INY
    LDA (PpuUpdateStreamPointer),Y
    INY
    ASL A
    TAX
    LDA PpuCtrlShadow
    ORA #PpuCtrlIncrement32
    BCS SelectPpuUpdateAddressIncrement
    AND #PpuCtrlIncrement1Mask

SelectPpuUpdateAddressIncrement:
    STA a:PPU_CTRL
    TXA
    ASL A
    BCC DecodePpuUpdateLength
    ORA #PpuUpdateLiteralCarryMarker

DecodePpuUpdateLength:
    LSR A
    LSR A
    TAX
    INX

WriteNextPpuUpdateByte:
    LDA (PpuUpdateStreamPointer),Y
    STA a:PPU_DATA
    BCC AdvancePpuUpdateWrite
    INY

AdvancePpuUpdateWrite:
    DEX
    BNE WriteNextPpuUpdateByte
    BCS CheckNextPpuUpdateCommand
    INY

CheckNextPpuUpdateCommand:
    LDA (PpuUpdateStreamPointer),Y
    BNE DecodeNextPpuUpdateCommand

FinishPpuUpdateStream:
    LDA #PaletteAddressHigh
    STA a:PPU_ADDR
    LDA #$00
    STA a:PPU_ADDR
    STA a:PPU_ADDR
    STA a:PPU_ADDR
    STA PpuUpdateStreamPointer + 1

RestorePpuStateAfterUpdate:
    LDX a:PPU_STATUS
    LDA PpuScrollX
    STA a:PPU_SCROLL
    LDA PpuScrollY
    STA a:PPU_SCROLL
    LDA PpuCtrlShadow
    STA a:PPU_CTRL
    RTS

; NMI-side reader for the requested RoomMap attribute-table byte

.segment "PRG_PPU_ATTRIBUTE_READ"

RoomMapAttributeAddressHigh = $23

ServiceRoomMapAttributeReadRequest:
    LDA PpuAttributeReadState
    BPL ReadRequestedRoomMapAttributeByte

AdvanceRoomMapAttributeReadTimeout:
    INC PpuAttributeReadState
    CMP #PpuAttributeReadTimeoutState
    BCC FinishRoomMapAttributeReadRequest
    LDA #GameplayFlagAttributeReadRequestMask
    AND GameplayFlags
    STA GameplayFlags
    BCS FinishRoomMapAttributeReadRequest

ReadRequestedRoomMapAttributeByte:
    LDX a:PPU_STATUS
    LDA #RoomMapAttributeAddressHigh
    STA a:PPU_ADDR
    LDA PpuAttributeAddressOrValue
    STA a:PPU_ADDR
    LDA a:PPU_DATA
    LDA a:PPU_DATA
    STA PpuAttributeAddressOrValue
    LDA #PpuAttributeReadCompleteState
    STA PpuAttributeReadState

FinishRoomMapAttributeReadRequest:
    JMP RestorePpuStateAfterUpdate

; Reset the PPU address latch and write the address supplied in A:X

.segment "PRG_SET_PPU_ADDRESS"

SetPpuAddressAX:
    PHA
    LDA a:PPU_STATUS
    PLA
    STA a:PPU_ADDR
    STX a:PPU_ADDR
    RTS

; Enter and leave the rendering-disabled state used by direct PPU transfers

.segment "PRG_DIRECT_PPU_TRANSFER"

PpuMaskRenderingEnableBits = $18
PpuMaskRenderingDisableMask = $E7
PpuCtrlNmiEnableBit = $80
PpuCtrlDirectTransferMask = $7B

EndDirectPpuTransfer:
    LDA #PpuMaskRenderingEnableBits
    ORA PpuMaskShadow
    STA PpuMaskShadow
    LDA PpuCtrlShadow
    ORA #PpuCtrlNmiEnableBit
    STA PpuCtrlShadow
    STA a:PPU_CTRL
    RTS

BeginDirectPpuTransfer:
    LDX #PpuUpdateStreamPointer + 1
    LDA #$FF
    JSR WaitForMaskedBitsClear
    LDA PpuCtrlShadow
    AND #PpuCtrlDirectTransferMask
    STA PpuCtrlShadow
    STA a:PPU_CTRL
    LDA #PpuMaskRenderingDisableMask
    AND PpuMaskShadow
    STA a:PPU_MASK
    RTS

; Repeated direct writes to PPU_DATA

.segment "PRG_PPU_DATA_WRITERS"

RepeatedPpuPatternSize = $04

WriteRepeatedFourBytePpuPattern:
    LDY #RepeatedPpuPatternSize - 1

WriteNextPpuPatternByte:
    LDA (TempPointer00),Y
    STA a:PPU_DATA
    DEY
    BPL WriteNextPpuPatternByte
    DEX
    BNE WriteRepeatedFourBytePpuPattern
    RTS

WriteRepeatedPpuByte:
    STY a:PPU_DATA
    DEX
    BNE WriteRepeatedPpuByte
    RTS

; Cooperative producer for ROM-resident PPU update streams

.segment "PRG_STATIC_PPU_UPDATE_QUEUE"

QueueStaticPpuUpdateStream:
    LDX PpuUpdateStreamPointer + 1
    BEQ PublishSelectedStaticPpuUpdateStream
    PHA
    JSR SwitchThreads
    PLA
    BCS QueueStaticPpuUpdateStream

PublishSelectedStaticPpuUpdateStream:
    TAX
    LDA StaticPpuUpdatePointerLowTable,X
    STA PpuUpdateStreamPointer
    LDA StaticPpuUpdatePointerHighTable,X
    STA PpuUpdateStreamPointer + 1
    RTS

; Descriptor-driven direct PPU nametable clearing

.segment "PRG_NAMETABLE_CLEAR"

NametableClearDescriptorSize = $03
NametableBlankTile = $24
NametableAttributeAddressHigh = $23
NametableAttributeAddressLow = $C8
NametableAttributeClearCount = $30

Clear30x24NametableRegion:
    LDX #NametableClearDescriptorSize * 2
    JSR ClearNametableRegionFromDescriptor
    JMP EndDirectPpuTransfer

Clear32x26NametableRegion:
    LDX #NametableClearDescriptorSize
    JSR ClearNametableRegionFromDescriptor
    JMP EndDirectPpuTransfer

ClearNametableRegionFromDescriptor:
    TXA
    PHA
    JSR BeginDirectPpuTransfer
    PLA
    LDX a:PPU_STATUS
    TAX
    LDA NametableClearDescriptors,X
    INX
    STA NametableClearWidth
    LDA NametableClearDescriptors,X
    INX
    STA TempPointer00
    LDY NametableClearDescriptors,X

ClearNextNametableRow:
    LDA TempPointer00
    ASL A
    ROL TempPointer00 + 1
    ASL A
    ROL TempPointer00 + 1
    TAX
    LDA TempPointer00 + 1
    AND #$03
    ORA #$20
    STA a:PPU_ADDR
    STX a:PPU_ADDR
    LDA PpuCtrlShadow
    STA a:PPU_CTRL
    LDX NametableClearWidth
    LDA #NametableBlankTile

WriteBlankNametableTile:
    STA a:PPU_DATA
    DEX
    BNE WriteBlankNametableTile
    LDA #$08
    CLC
    ADC TempPointer00
    STA TempPointer00
    DEY
    BNE ClearNextNametableRow
    LDA #NametableAttributeAddressHigh
    STA a:PPU_ADDR
    LDA #NametableAttributeAddressLow
    STA a:PPU_ADDR
    LDA PpuCtrlShadow
    STA a:PPU_CTRL
    LDX #NametableAttributeClearCount
    LDA #$00

ClearNametableAttributeByte:
    STA a:PPU_DATA
    DEX
    BNE ClearNametableAttributeByte
    LDX a:PPU_STATUS
    RTS

; Fill both physical nametables with blank tiles and reset their attributes

.segment "PRG_FULL_NAMETABLE_CLEAR"

FirstNametableAddressHigh = $20
SecondNametableAddressHigh = $28
FullNametableBlankTile = $24
InitialNametableTileCount = $C0
NametableAttributeByteCount = $40
NametableAttributeFill = $FF
NametableFillChunkCounter = $04

ClearBothNametables:
    JSR BeginDirectPpuTransfer
    LDA #FirstNametableAddressHigh
    JSR ClearFullNametable
    LDA #SecondNametableAddressHigh
    JSR ClearFullNametable
    JSR EndDirectPpuTransfer
    RTS

ClearFullNametable:
    LDX #$00
    JSR SetPpuAddressAX
    LDA PpuCtrlShadow
    STA a:PPU_CTRL
    LDA #FullNametableBlankTile
    LDY #InitialNametableTileCount
    LDX #NametableFillChunkCounter

WriteFullNametableByte:
    STA a:PPU_DATA
    DEY
    BNE WriteFullNametableByte
    DEX
    BPL SelectNametableFillPhase
    LDX a:PPU_STATUS
    RTS

SelectNametableFillPhase:
    BNE WriteFullNametableByte
    LDY #NametableAttributeByteCount
    LDA #NametableAttributeFill
    BMI WriteFullNametableByte
