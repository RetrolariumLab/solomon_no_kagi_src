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
