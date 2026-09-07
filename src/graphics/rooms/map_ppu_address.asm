; Convert packed RoomMap indices to nametable and attribute-table addresses

.segment "PRG_ROOM_MAP_PPU_ADDRESS"

ConvertRoomMapIndexToNametableAddress:
    LDA #$08
    STA RoomMapUpdatePpuAddressHigh
    LDA RoomMapUpdatePpuAddressLow
    CLC
    ADC #$10
    ASL A
    ROL RoomMapUpdatePpuAddressHigh
    ASL A
    ROL RoomMapUpdatePpuAddressHigh
    AND #$C0
    PHA
    LDA #$0F
    AND RoomMapUpdatePpuAddressLow
    ASL A
    AND #$1E
    STA RoomMapUpdatePpuAddressLow
    PLA
    ORA RoomMapUpdatePpuAddressLow
    STA RoomMapUpdatePpuAddressLow
    RTS

CalculateRoomMapAttributeAddressLow:
    TXA
    CLC
    ADC #$10
    TAX
    LDA #$00
    STA RoomMapUpdatePpuAddressHigh
    TXA
    AND #$10
    BEQ CalculateRoomMapAttributeIndex
    INC RoomMapUpdatePpuAddressHigh

CalculateRoomMapAttributeIndex:
    TXA
    AND #$E0
    LSR A
    LSR A
    STA RoomMapUpdatePpuAddressLow
    TXA
    LSR A
    AND #$07
    ORA RoomMapUpdatePpuAddressLow
    ROL RoomMapUpdatePpuAddressHigh
    ADC #$C0
    RTS
