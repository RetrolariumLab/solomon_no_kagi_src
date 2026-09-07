; Convert two coordinate differences to signed 16-bit values scaled by four

.segment "PRG_COORDINATE_DELTA"

CoordinateAxisCount = 2

BuildScaledCoordinateDeltas:
    LDX #CoordinateAxisCount - 1

ScaleNextCoordinateDelta:
    LDY #$00
    SEC
    LDA CoordinateTargetY,X
    SBC CoordinateOriginY,X
    BCS ScaleCoordinateDeltaByFour
    DEY

ScaleCoordinateDeltaByFour:
    STY CoordinateTargetY,X
    ASL A
    ROL CoordinateTargetY,X
    ASL A
    ROL CoordinateTargetY,X
    STA CoordinateOriginY,X
    DEX
    BPL ScaleNextCoordinateDelta
    LDA CoordinateOriginX
    LDX CoordinateTargetY
    STA CoordinateTargetY
    STX CoordinateOriginX
    RTS
