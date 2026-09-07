; Convert between pixel coordinates and the packed 16-column room-map index

.segment "PRG_COORDINATE_CONVERSION"

RoomMapLeftPixel = $08
RoomMapTopPixel = $10
RoomMapCellSize = $10

ConvertPixelCoordinatesToMapIndex:
    LDA CoordinateY
    SEC
    SBC #RoomMapTopPixel
    AND #RoomMapRowMask
    STA MapCellIndex
    LDA CoordinateX
    SEC
    SBC #RoomMapLeftPixel
    LSR A
    LSR A
    LSR A
    LSR A
    CLC
    ORA MapCellIndex
    STA MapCellIndex
    TAX
    RTS

ConvertMapIndexToPixelCoordinates:
    LDA #RoomMapColumnMask
    AND MapCellIndex
    ASL A
    ASL A
    ASL A
    ASL A
    ADC #RoomMapLeftPixel
    STA CoordinateX
    LDA #RoomMapRowMask
    AND MapCellIndex
    CLC
    ADC #RoomMapTopPixel
    STA CoordinateY
    RTS

.assert RoomMapCellSize = 16, error, "room map cells must remain 16 pixels"
.assert RoomMapWidth = 16, error, "room map rows must remain 16 cells"
