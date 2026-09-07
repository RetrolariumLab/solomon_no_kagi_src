; Per-frame traversal of all gameplay object records

.segment "PRG_OBJECT_UPDATE"

LastObjectRecordIndex = ObjectRecordCount - 1
CurrentObjectUpdateIndex = $000D

UpdateActiveObjects:
    LDA #LastObjectRecordIndex
    STA CurrentObjectUpdateIndex

UpdateNextObject:
    LDX CurrentObjectUpdateIndex
    LDA ObjectRecordPointerLowTable,X
    STA TempPointer08
    LDA ObjectRecordPointerHighTable,X
    STA TempPointer08 + 1
    LDY #ObjectStateOffset
    LDA (TempPointer08),Y
    CMP #ActiveObjectStateMinimum
    BCC AdvanceObjectUpdateLoop
    INY
    LDA (TempPointer08),Y
    TAX
    INY
    CMP (TempPointer08),Y
    BEQ CheckObjectActionChange
    STA (TempPointer08),Y
    INY
    LDA (TempPointer08),Y
    INY
    BPL ReloadObjectMotionAndAnimation

CheckObjectActionChange:
    INY
    LDA (TempPointer08),Y
    INY
    CMP (TempPointer08),Y
    BEQ UpdateCurrentObject

ReloadObjectMotionAndAnimation:
    JSR LoadObjectMotionAndAnimationDefinition

UpdateCurrentObject:
    JSR UpdateObjectMotionAndCollision
    JSR DispatchObjectCollisionResponse
    JSR AdvanceObjectAnimation

AdvanceObjectUpdateLoop:
    DEC CurrentObjectUpdateIndex
    BPL UpdateNextObject
    LDA DanaCollisionMask
    AND #ObjectCollisionResponseMask
    BEQ FinishActiveObjectUpdate
    LDA #$00
    STA GameplayFrameCounters

FinishActiveObjectUpdate:
    RTS

; Signed fixed-point Y/X motion integration for one object record

.segment "PRG_OBJECT_MOTION"

ObjectMotionScratch = $000A

UpdateObjectMotionAndCollision:
    LDY #ObjectYMotionOffset
    LDA (TempPointer08),Y
    STA ObjectMotionScratch
    ASL A
    BCC IntegrateObjectYMotion
    TAX
    CLC
    ADC #$06
    BVC IntegrateObjectYMotion
    TXA

IntegrateObjectYMotion:
    TAX
    ROL ObjectMotionScratch
    ROR A
    STA (TempPointer08),Y
    TXA
    LDX #$00
    ASL A
    BCC SignExtendObjectYDelta
    DEX

SignExtendObjectYDelta:
    STX ObjectMotionScratch
    ASL A
    ROL ObjectMotionScratch
    INY
    CLC
    ADC (TempPointer08),Y
    STA (TempPointer08),Y
    INY
    LDA ObjectMotionScratch
    ADC (TempPointer08),Y
    STA (TempPointer08),Y

IntegrateObjectXMotion:
    INY
    LDA (TempPointer08),Y
    ASL A
    ASL A
    LDX #$00
    BCC SignExtendObjectXDelta
    DEX

SignExtendObjectXDelta:
    STX ObjectMotionScratch
    ROL A
    ROL ObjectMotionScratch
    CLC
    INY
    ADC (TempPointer08),Y
    STA (TempPointer08),Y
    INY
    LDA ObjectMotionScratch
    ADC (TempPointer08),Y
    STA (TempPointer08),Y

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

; Advance one object's packed animation phase and three-byte sprite record

.segment "PRG_OBJECT_ANIMATION"

ObjectAnimationDataPointer = $000A
ObjectAnimationFrameByte = $000C

AdvanceObjectAnimation:
    LDY #ObjectAnimationCounterOffset
    LDA (TempPointer08),Y
    CLC
    SBC #$00
    STA (TempPointer08),Y
    BPL FinishObjectAnimationUpdate
    INY
    LDA (TempPointer08),Y
    DEY
    STA (TempPointer08),Y
    LDY #ObjectAnimationPhaseOffset
    LDA (TempPointer08),Y
    CLC
    ADC #$F0
    STA (TempPointer08),Y
    BCS SelectObjectAnimationFrame

NormalizeObjectAnimationPhase:
    AND #$0F
    STA ObjectAnimationDataPointer
    ASL A
    ASL A
    ASL A
    ASL A
    ORA ObjectAnimationDataPointer
    STA (TempPointer08),Y

SelectObjectAnimationFrame:
    LSR A
    LSR A
    LSR A
    STA ObjectAnimationDataPointer
    LSR A
    CLC
    ADC ObjectAnimationDataPointer
    TAX
    INY
    LDA (TempPointer08),Y
    STA ObjectAnimationDataPointer
    INY
    LDA (TempPointer08),Y
    STA ObjectAnimationDataPointer + 1
    TXA
    TAY
    LDA (ObjectAnimationDataPointer),Y
    INY
    STA ObjectAnimationFrameByte
    LDA (ObjectAnimationDataPointer),Y
    INY
    TAX
    LDA (ObjectAnimationDataPointer),Y
    LDY #ObjectSpriteFlagsOffset
    STA (TempPointer08),Y
    DEY
    TXA
    STA (TempPointer08),Y
    DEY
    LDA ObjectAnimationFrameByte
    STA (TempPointer08),Y

FinishObjectAnimationUpdate:
    RTS

; Dispatch active object collision responses by the low collision-mask nibble

.segment "PRG_OBJECT_COLLISION_DISPATCH"

CollisionDispatchStateMinimum = $E0
ObjectCollisionMaskScratch = $000E
ObjectCollisionActionScratch = $000F

DispatchObjectCollisionResponse:
    LDY #ObjectStateOffset
    LDA (TempPointer08),Y
    CMP #CollisionDispatchStateMinimum
    BCS SelectObjectCollisionResponse
    RTS

SelectObjectCollisionResponse:
    LDY #ObjectActionOffset
    LDA (TempPointer08),Y
    STA ObjectCollisionActionScratch
    LDY #ObjectCollisionMaskOffset
    LDA (TempPointer08),Y
    STA ObjectCollisionMaskScratch
    AND #ObjectCollisionResponseMask
    ASL A
    TAX
    LDA ObjectCollisionHandlerTable,X
    STA TempPointer0A
    LDA ObjectCollisionHandlerTable + 1,X
    STA TempPointer0A + 1
    JMP (TempPointer0A)

; Replace byte 0 for every active non-Dana object record

.segment "PRG_SET_ACTIVE_OBJECT_STATES"

SetActiveNonDanaObjectState:
    LDX #ObjectRecordCount - 2

SetNextActiveNonDanaObjectState:
    JSR LoadObjectPointer
    LDY #$00
    LDA (TempPointer00),Y
    BPL SkipInactiveNonDanaObject
    LDA $02
    STA (TempPointer00),Y

SkipInactiveNonDanaObject:
    DEX
    BPL SetNextActiveNonDanaObjectState
    RTS

; Resolve a non-Dana object index to its runtime record

.segment "PRG_LOAD_OBJECT_POINTER"

LoadObjectPointer:
    LDA NonDanaObjectPointerLowTable,X
    STA TempPointer00
    LDA NonDanaObjectPointerHighTable,X
    STA TempPointer00 + 1
    RTS

; Clear and move every non-Dana object record offscreen

.segment "PRG_DEACTIVATE_NON_DANA_OBJECTS"

DeactivateAllNonDanaObjects:
    LDX #ObjectRecordCount - 2

DeactivateNextNonDanaObject:
    JSR LoadObjectPointer
    LDY #$00
    TYA
    STA (TempPointer00),Y
    LDY #$07
    LDA #$F8
    STA (TempPointer00),Y
    DEX
    BPL DeactivateNextNonDanaObject
    RTS

; Clear all 21 object records and all 17 parallel enemy AI records

.segment "PRG_GAMEPLAY_POOL_CLEAR"

ObjectPoolFirstPageSize = $100
ObjectPoolTailSize = ObjectRecordCount * ObjectRecordSize - ObjectPoolFirstPageSize
EnemyAiStateSize = EnemyAiStateCount * EnemyAiStateStride

ClearGameplayObjectAndEnemyState:
    LDA #$00
    LDY #ObjectPoolTailSize

ClearObjectPoolTail:
    DEY
    STA DanaObject + ObjectPoolFirstPageSize,Y
    BNE ClearObjectPoolTail
    TAY

ClearObjectPoolFirstPage:
    STA DanaObject,Y
    DEY
    BNE ClearObjectPoolFirstPage
    LDY #EnemyAiStateSize

ClearEnemyAiStatePool:
    DEY
    STA EnemyAiState,Y
    BNE ClearEnemyAiStatePool
    RTS

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

; Test a point-like interaction coordinate against one active object record

.segment "PRG_COORDINATE_OBJECT_OVERLAP"

CheckCoordinateOverlapWithObject:
    SEC
    LDY #$00
    LDA (OverlapObjectPointer),Y
    BPL FinishCoordinateObjectOverlapCheck
    LDY #ObjectXPositionOffset
    LDA MapInteractionX
    SEC
    SBC (OverlapObjectPointer),Y
    ADC #$09
    CMP #$15
    BCS FinishCoordinateObjectOverlapCheck
    LDY #ObjectYPositionOffset
    LDA MapInteractionY
    SBC (OverlapObjectPointer),Y
    ADC #$0D
    CMP #$1D

FinishCoordinateObjectOverlapCheck:
    RTS
