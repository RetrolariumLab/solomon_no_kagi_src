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
