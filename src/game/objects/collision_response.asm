; Coordinate, motion, and action responses for collision-mask low nibbles

.segment "PRG_OBJECT_COLLISION_RESPONSE"

ObjectCollisionVerticalDelta = $000A
ObjectCollisionHorizontalDelta = $000B

HandleObjectCollisionMask00:
    LDA ObjectCollisionActionScratch
    AND #$FC
    TAX
    SEC
    SBC #$0C
    CMP #$0C
    BCS FinishObjectCollisionMask00
    LDA ObjectCollisionMaskScratch
    AND #ObjectCollisionBelowMask
    BNE FinishObjectCollisionMask00
    LDA #$03
    AND ObjectCollisionActionScratch
    ORA #$18
    LDY #ObjectActionOffset
    STA (TempPointer08),Y

FinishObjectCollisionMask00:
    RTS

HandleObjectCollisionMask01:
    LDY #ObjectYPositionOffset
    LDA (TempPointer08),Y
    CLC
    ADC #$03
    ORA #$F0
    EOR #$FF
    STA ObjectCollisionVerticalDelta
    INC ObjectCollisionVerticalDelta
    LDY #ObjectXPositionOffset
    LDA (TempPointer08),Y
    SEC
    SBC #$04
    ORA #$F0
    EOR #$FF
    TAX
    INX
    TXA
    STA ObjectCollisionHorizontalDelta
    CMP ObjectCollisionVerticalDelta
    BCC ResolveObjectCollisionMask01X

ResolveObjectCollisionMask01Y:
    LDY #ObjectYPositionOffset
    LDA (TempPointer08),Y
    CLC
    ADC ObjectCollisionVerticalDelta
    STA (TempPointer08),Y
    LDX #$00
    TXA
    DEY
    STA (TempPointer08),Y
    DEY
    LDA (TempPointer08),Y
    ROL A
    TXA
    ROR A
    STA (TempPointer08),Y
    LDA ObjectCollisionActionScratch
    AND #$01
    ORA #$04
    LDY #ObjectActionOffset
    STA (TempPointer08),Y
    RTS

ResolveObjectCollisionMask01X:
    LDA (TempPointer08),Y
    ADC ObjectCollisionHorizontalDelta
    STA (TempPointer08),Y
    DEY
    LDX #$00
    TXA
    STA (TempPointer08),Y
    DEY
    STA (TempPointer08),Y
    LDY #ObjectYMotionOffset
    LDA (TempPointer08),Y
    ASL A
    BMI FinishObjectCollisionMask01
    LDY #ObjectActionOffset
    LDA #$09
    STA (TempPointer08),Y

FinishObjectCollisionMask01:
    RTS

HandleObjectCollisionMask02:
    LDY #ObjectYPositionOffset
    LDA (TempPointer08),Y
    CLC
    ADC #$03
    ORA #$F0
    EOR #$FF
    STA ObjectCollisionVerticalDelta
    INC ObjectCollisionVerticalDelta
    LDY #ObjectXPositionOffset
    LDA (TempPointer08),Y
    CLC
    ADC #$04
    AND #$0F
    STA ObjectCollisionHorizontalDelta
    CMP ObjectCollisionVerticalDelta
    BCC ResolveObjectCollisionMask02X
    JMP ResolveObjectCollisionMask01Y

ResolveObjectCollisionMask02X:
    LDA (TempPointer08),Y
    SEC
    SBC ObjectCollisionHorizontalDelta
    STA (TempPointer08),Y
    LDA #$00
    DEY
    STA (TempPointer08),Y
    DEY
    STA (TempPointer08),Y
    LDY #ObjectYMotionOffset
    ASL A
    BMI FinishObjectCollisionMask02
    LDA #$08
    LDY #ObjectActionOffset
    STA (TempPointer08),Y

FinishObjectCollisionMask02:
    RTS

HandleObjectCollisionMask08:
    LDY #ObjectYPositionOffset
    LDA (TempPointer08),Y
    CLC
    ADC #$10
    AND #$0F
    STA ObjectCollisionVerticalDelta
    LDY #ObjectXPositionOffset
    LDA (TempPointer08),Y
    SEC
    SBC #$04
    ORA #$F0
    EOR #$FF
    TAX
    INX
    TXA
    STA ObjectCollisionHorizontalDelta
    CMP ObjectCollisionVerticalDelta
    BCS ResolveObjectCollisionMask08Y
    LDA (TempPointer08),Y
    CLC
    ADC ObjectCollisionHorizontalDelta
    STA (TempPointer08),Y
    DEY
    LDA #$00
    STA (TempPointer08),Y
    DEY
    STA (TempPointer08),Y
    LDY #ObjectYMotionOffset
    LDA (TempPointer08),Y
    ASL A
    BMI FinishObjectCollisionMask08X
    LDY #ObjectActionOffset
    LDA #$09
    STA (TempPointer08),Y

FinishObjectCollisionMask08X:
    RTS

ResolveObjectCollisionMask08Y:
    LDY #ObjectYPositionOffset
    LDA (TempPointer08),Y
    SEC
    SBC ObjectCollisionVerticalDelta
    STA (TempPointer08),Y
    DEY
    LDA #$F0
    STA (TempPointer08),Y
    LDY #ObjectYMotionOffset
    LDA (TempPointer08),Y
    ROL A
    LDA #$00
    ROR A
    STA (TempPointer08),Y
    LDA ObjectCollisionActionScratch
    TAX
    SEC
    SBC #$10
    CMP #$08
    BCC FinishObjectCollisionMask08
    TXA
    AND #$01
    ORA #$06
    LDY #ObjectActionOffset
    STA (TempPointer08),Y

FinishObjectCollisionMask08:
    RTS

HandleObjectCollisionMask04:
    LDY #ObjectYPositionOffset
    LDA (TempPointer08),Y
    CLC
    ADC #$10
    AND #$0F
    STA ObjectCollisionVerticalDelta
    LDY #ObjectXPositionOffset
    LDA (TempPointer08),Y
    ADC #$04
    AND #$0F
    STA ObjectCollisionHorizontalDelta
    CMP ObjectCollisionVerticalDelta
    BCC ResolveObjectCollisionMask04X
    JMP ResolveObjectCollisionMask08Y

ResolveObjectCollisionMask04X:
    LDA (TempPointer08),Y
    SEC
    SBC ObjectCollisionHorizontalDelta
    STA (TempPointer08),Y
    DEY
    LDA #$00
    STA (TempPointer08),Y
    DEY
    STA (TempPointer08),Y
    LDY #ObjectYMotionOffset
    LDA (TempPointer08),Y
    ASL A
    BMI FinishObjectCollisionMask04
    LDY #ObjectActionOffset
    LDA #$08
    STA (TempPointer08),Y

FinishObjectCollisionMask04:
    RTS

HandleObjectCollisionMask03:
    JSR ObjectClampYCoordinateToThirteenInset
    LDA ObjectCollisionActionScratch
    AND #$01
    ORA #$04
    LDY #ObjectActionOffset
    STA (TempPointer08),Y
    RTS

HandleObjectCollisionMask0C:
    JSR ObjectClampYCoordinateToSurface
    LDA ObjectCollisionActionScratch
    TAX
    SEC
    SBC #$10
    CMP #$08
    BCC PreserveObjectYMotionSign
    AND #$FC
    CMP #$0C
    BEQ PreserveObjectYMotionSign
    TXA
    AND #$03
    ORA #$06
    LDY #ObjectActionOffset
    STA (TempPointer08),Y
    RTS

PreserveObjectYMotionSign:
    LDY #ObjectYMotionOffset
    LDA (TempPointer08),Y
    ASL A
    LDA #$00
    ROR A
    STA (TempPointer08),Y
    RTS

HandleObjectCollisionMask09:
    JSR ObjectClampXCoordinateToLeftSurface
    LDA #$FC
    AND ObjectCollisionActionScratch
    BEQ FinishObjectCollisionMask09
    SEC
    SBC #$10
    CMP #$08
    BCC FinishObjectCollisionMask09
    LDY #ObjectYMotionOffset
    LDA (TempPointer08),Y
    ASL A
    BMI FinishObjectCollisionMask09
    LDA #$09
    LDY #ObjectActionOffset
    STA (TempPointer08),Y

FinishObjectCollisionMask09:
    RTS

HandleObjectCollisionMask06:
    JSR ObjectClampXCoordinateToRightSurface
    LDA #$FC
    AND ObjectCollisionActionScratch
    BEQ FinishObjectCollisionMask06
    SEC
    SBC #$10
    CMP #$08
    BCC FinishObjectCollisionMask06
    LDX #ObjectXPositionOffset
    LDY #ObjectYMotionOffset
    LDA (TempPointer08),Y
    ASL A
    BMI FinishObjectCollisionMask06
    LDA #$08
    LDY #ObjectActionOffset
    STA (TempPointer08),Y

FinishObjectCollisionMask06:
    RTS

HandleObjectCollisionMask05:
    LDY #ObjectYPositionOffset
    LDA (TempPointer08),Y
    AND #$08
    BEQ HandleObjectCollisionMask0D

HandleObjectCollisionMask07:
    JSR ObjectClampYCoordinateToThirteenInset
    JSR ObjectClampXCoordinateToRightSurface
    LDY #ObjectActionOffset
    LDA #$08
    STA (TempPointer08),Y
    RTS

HandleObjectCollisionMask0A:
    LDY #ObjectYPositionOffset
    LDA (TempPointer08),Y
    AND #$08
    BEQ HandleObjectCollisionMask0E

HandleObjectCollisionMask0B:
    JSR ObjectClampYCoordinateToThirteenInset
    JSR ObjectClampXCoordinateToLeftSurface
    LDY #ObjectActionOffset
    LDA #$09
    STA (TempPointer08),Y
    RTS

HandleObjectCollisionMask0D:
    JSR ObjectClampYCoordinateToSurface
    JSR ObjectClampXCoordinateToLeftSurface
    LDX #$07
    BNE SelectCornerCollisionAction

HandleObjectCollisionMask0E:
    JSR ObjectClampYCoordinateToSurface
    JSR ObjectClampXCoordinateToRightSurface
    LDX #$06

SelectCornerCollisionAction:
    LDA ObjectCollisionActionScratch
    SEC
    SBC #$10
    CMP #$08
    BCC FinishCornerCollisionResponse
    TXA
    LDY #ObjectActionOffset
    STA (TempPointer08),Y

FinishCornerCollisionResponse:
    RTS
