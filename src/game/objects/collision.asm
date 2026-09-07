; Sample six surrounding RoomMap cells into an object's collision mask

.segment "PRG_OBJECT_COLLISION"

ObjectCollisionSampleMask = $000A
ObjectCollisionColumn = $000B
ObjectBoundaryCrossingFlags = $000C

SampleObjectRoomMapCollision:
    LDA #$00
    STA ObjectBoundaryCrossingFlags
    LDY #ObjectYPositionOffset
    LDA (TempPointer08),Y
    SEC
    SBC #$0D
    STA ObjectCollisionSampleMask
    CLC
    LDA #$0C
    ADC ObjectCollisionSampleMask
    TAX
    EOR ObjectCollisionSampleMask
    AND #$F0
    BNE RecordObjectLeadingRowSpan
    SEC

RecordObjectLeadingRowSpan:
    ROR ObjectBoundaryCrossingFlags
    INX
    TXA
    EOR ObjectCollisionSampleMask
    AND #$F0
    BNE RecordObjectTrailingRowSpan
    SEC

RecordObjectTrailingRowSpan:
    ROR ObjectBoundaryCrossingFlags
    LDY #ObjectXPositionOffset
    LDA (TempPointer08),Y
    SEC
    SBC #$04
    STA ObjectCollisionColumn
    CLC
    LDA #$07
    ADC ObjectCollisionColumn
    CLC
    EOR ObjectCollisionColumn
    AND #$F0
    BNE RecordObjectColumnSpan
    SEC

RecordObjectColumnSpan:
    ROR ObjectBoundaryCrossingFlags
    LDA ObjectCollisionColumn
    LSR A
    LSR A
    LSR A
    LSR A
    CMP #$0F
    STA ObjectCollisionColumn
    LDA ObjectCollisionSampleMask
    AND #$F0
    BCC BuildObjectCollisionMapIndex
    SBC #$10

BuildObjectCollisionMapIndex:
    ORA ObjectCollisionColumn
    TAY
    TAX
    LDA #$00
    STA ObjectCollisionSampleMask
    LDA RoomMap,Y
    CLC
    BPL ShiftFirstObjectCollisionBit
    SEC

ShiftFirstObjectCollisionBit:
    ROR ObjectCollisionSampleMask
    LDA ObjectBoundaryCrossingFlags
    BMI SampleSecondObjectCollisionCell
    INY

SampleSecondObjectCollisionCell:
    LDA RoomMap,Y
    BPL ShiftSecondObjectCollisionBit
    SEC

ShiftSecondObjectCollisionBit:
    ROR ObjectCollisionSampleMask
    LDA #$20
    AND ObjectBoundaryCrossingFlags
    BNE SampleThirdObjectCollisionCell
    TYA
    ADC #$10
    TAY

SampleThirdObjectCollisionCell:
    LDA RoomMap,Y
    BPL ShiftThirdObjectCollisionBit
    SEC

ShiftThirdObjectCollisionBit:
    ROR ObjectCollisionSampleMask
    LDA ObjectBoundaryCrossingFlags
    BMI SampleFourthObjectCollisionCell
    DEY

SampleFourthObjectCollisionCell:
    LDA RoomMap,Y
    BPL ShiftFourthObjectCollisionBit
    SEC

ShiftFourthObjectCollisionBit:
    ROR ObjectCollisionSampleMask
    LDA #$40
    AND ObjectBoundaryCrossingFlags
    BNE SampleFifthObjectCollisionCell
    TXA
    ADC #$10
    TAY

SampleFifthObjectCollisionCell:
    LDA RoomMap,Y
    BPL ShiftFifthObjectCollisionBit
    SEC

ShiftFifthObjectCollisionBit:
    ROR ObjectCollisionSampleMask
    LDA ObjectBoundaryCrossingFlags
    BMI SampleSixthObjectCollisionCell
    INY

SampleSixthObjectCollisionCell:
    LDA RoomMap,Y
    BPL MergeSixthObjectCollisionBit
    SEC

MergeSixthObjectCollisionBit:
    LDA ObjectCollisionSampleMask
    ROR A
    ROR A
    ROR A
    LDY #ObjectCollisionMaskOffset
    STA (TempPointer08),Y
    RTS
