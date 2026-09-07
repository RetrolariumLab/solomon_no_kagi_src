; Load object motion and animation definitions after a type or action change

.segment "PRG_OBJECT_MOTION_ANIMATION"

PreserveObjectMotionValue = $40

ObjectDefinitionPointer = $000A
ObjectRoomStateMotionMask = $000C
ObjectTypeDefinitionOffset = $000E
ObjectAnimationPhaseScratch = $000E
ObjectActionDefinitionOffset = $000F
ObjectAnimationDelayScratch = $000F

LoadObjectMotionAndAnimationDefinition:
    STA (TempPointer08),Y
    STA ObjectActionDefinitionOffset
    TXA
    LSR A
    AND #$FE
    STA ObjectTypeDefinitionOffset
    TAY
    LDA ObjectMotionSelectorPointers,Y
    STA ObjectDefinitionPointer
    LDA ObjectMotionSelectorPointers + 1,Y
    STA ObjectDefinitionPointer + 1
    LDY ObjectActionDefinitionOffset
    LDA (ObjectDefinitionPointer),Y
    BPL LoadObjectMotionValues

ResolveRoomStateMotionSelector:
    AND a:RoomStateFlags
    STA ObjectRoomStateMotionMask
    LDY #ObjectTypeOffset
    LDA (TempPointer08),Y
    AND #$03
    ORA ObjectRoomStateMotionMask
    TAY
    LDA (ObjectDefinitionPointer),Y

LoadObjectMotionValues:
    ASL A
    TAX
    LDY #ObjectYMotionOffset
    LDA ObjectMotionValues,X
    CMP #PreserveObjectMotionValue
    BEQ LoadObjectXMotionValue
    STA (TempPointer08),Y

LoadObjectXMotionValue:
    LDY #ObjectXMotionOffset
    LDA ObjectMotionValues + 1,X
    CMP #PreserveObjectMotionValue
    BEQ LoadObjectAnimationDescriptor
    STA (TempPointer08),Y

LoadObjectAnimationDescriptor:
    LDY ObjectTypeDefinitionOffset
    LDA ObjectAnimationDescriptorPointers,Y
    STA ObjectDefinitionPointer
    LDA ObjectAnimationDescriptorPointers + 1,Y
    STA ObjectDefinitionPointer + 1
    LDA ObjectActionDefinitionOffset
    ASL A
    ASL A
    TAY
    LDA (ObjectDefinitionPointer),Y
    INY
    STA ObjectAnimationPhaseScratch
    LDA (ObjectDefinitionPointer),Y
    INY
    LSR A
    STA ObjectAnimationDelayScratch
    BCC StoreObjectAnimationPointer

ResolveVariantAnimationPointer:
    LDA (ObjectDefinitionPointer),Y
    INY
    TAX
    LDA (ObjectDefinitionPointer),Y
    STX ObjectDefinitionPointer
    STA ObjectDefinitionPointer + 1
    LDY #ObjectTypeOffset
    LDA (TempPointer08),Y
    AND #$03
    ASL A
    TAY

StoreObjectAnimationPointer:
    LDA (ObjectDefinitionPointer),Y
    INY
    TAX
    LDA (ObjectDefinitionPointer),Y
    LDY #ObjectAnimationPointerHighOffset
    STA (TempPointer08),Y
    DEY
    TXA
    STA (TempPointer08),Y
    DEY
    LDA ObjectAnimationPhaseScratch
    STA (TempPointer08),Y
    DEY
    LDA ObjectAnimationDelayScratch
    STA (TempPointer08),Y
    DEY
    LDA #$00
    STA (TempPointer08),Y
    RTS

.segment "PRG_OBJECT_ANIMATION_DESCRIPTOR_POINTERS"

ObjectAnimationDescriptorPointerCount = 33

ObjectAnimationDescriptorPointers:
    .word ObjectAnimationDescriptorsType00
    .word ObjectAnimationDescriptorsType04
    .word ObjectAnimationDescriptorsType00
    .word ObjectAnimationDescriptorsType0C
    .word ObjectAnimationDescriptorsType10
    .word ObjectAnimationDescriptorsType14
    .word ObjectAnimationDescriptorsType18
    .word ObjectAnimationDescriptorsType1C
    .word ObjectAnimationDescriptorsType20
    .word ObjectAnimationDescriptorsType24
    .word ObjectAnimationDescriptorsType28
    .word ObjectAnimationDescriptorsType28
    .word ObjectAnimationDescriptorsType30
    .word ObjectAnimationDescriptorsType34
    .word ObjectAnimationDescriptorsType30
    .word ObjectAnimationDescriptorsType34
    .word ObjectAnimationDescriptorsType30
    .word ObjectAnimationDescriptorsType34
    .word ObjectAnimationDescriptorsType30
    .word ObjectAnimationDescriptorsType34
    .word ObjectAnimationDescriptorsType50
    .word ObjectAnimationDescriptorsType50
    .word ObjectAnimationDescriptorsType50
    .word ObjectAnimationDescriptorsType5C
    .word ObjectAnimationDescriptorsType5C
    .word ObjectAnimationDescriptorsType5C
    .word ObjectAnimationDescriptorsType68
    .word ObjectAnimationDescriptorsType68
    .word ObjectAnimationDescriptorsType70
    .word ObjectAnimationDescriptorsType70
    .word ObjectAnimationDescriptorsType78
    .word ObjectAnimationDescriptorsType78
    .word ObjectAnimationDescriptorsType80

.assert * - ObjectAnimationDescriptorPointers = ObjectAnimationDescriptorPointerCount * 2, error, "unexpected animation descriptor pointer count"
