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
