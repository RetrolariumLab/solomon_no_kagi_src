; Directional enemy actions and RoomMap path selection

.segment "PRG_PATHFINDING_ENEMY_AI"

PathDirectionOffset = EnemyAiPathDirectionOffset
PathAlternateDirectionOffset = EnemyAiAlternateDirectionOffset
TempPointer03 = TempPointer02 + 1
TempPointer05 = TempPointer04 + 1
TempPointer06 = TempPointer04 + 2
TempPointer07 = TempPointer04 + 3

UpdateType08To0BPhaseAction:
    LDY #EnemyAiPhaseOffset
    LDA (EnemyAiPointer),Y
    CMP #$20
    BCC FinishType08To0BPhaseAction
    LDY #ObjectActionOffset
    LDA #$18
    ORA (EnemyObjectPointer),Y
    STA (EnemyObjectPointer),Y

FinishType08To0BPhaseAction:
    RTS

UpdateType08To0BHorizontalOrientation:
    LDY #PathDirectionOffset
    LDA (EnemyAiPointer),Y
    ASL A
    TAX
    LDY #ObjectActionOffset
    LDA (EnemyObjectPointer),Y
    AND #$02
    CLC
    BNE RotateType08To0BHorizontalDirection
    SEC

RotateType08To0BHorizontalDirection:
    TXA
    ROR A
    STA TempPointer00
    LDY #ObjectXMotionOffset
    LDA (EnemyObjectPointer),Y
    EOR TempPointer00
    AND #$40
    BNE ReverseType08To0BHorizontalDirection
    LDY #EnemyAiFlagsOffset
    LDA (EnemyAiPointer),Y
    AND #$10
    BNE MergeType08To0BHorizontalDirection
    LDA #$80

MergeType08To0BHorizontalDirection:
    AND #$80
    ROL TempPointer00
    ROR A
    BCC StoreType08To0BHorizontalDirection

ReverseType08To0BHorizontalDirection:
    LDA #$40
    EOR TempPointer00

StoreType08To0BHorizontalDirection:
    LDY #PathDirectionOffset
    STA (EnemyAiPointer),Y
    LDY #EnemyAiFlagsOffset
    LDA (EnemyAiPointer),Y
    AND #$F7
    STA TempPointer00
    LDY #ObjectActionOffset
    LDA #$02
    AND (EnemyObjectPointer),Y
    BEQ MergeType08To0BHorizontalFlag
    LDA #$08

MergeType08To0BHorizontalFlag:
    LDY #EnemyAiFlagsOffset
    ORA TempPointer00
    STA (EnemyAiPointer),Y
    JMP SetType08To0BMovingAction

UpdateType08To0BVerticalOrientation:
    LDY #PathDirectionOffset
    LDA (EnemyAiPointer),Y
    AND #$BF
    TAX
    LDY #ObjectActionOffset
    LDA (EnemyObjectPointer),Y
    LSR A
    TXA
    BCS CompareType08To0BVerticalDirection
    ORA #$40

CompareType08To0BVerticalDirection:
    STA TempPointer00
    LDY #ObjectYMotionOffset
    LDA (EnemyObjectPointer),Y
    ASL A
    EOR TempPointer00
    BPL ReverseType08To0BVerticalDirection
    LDY #EnemyAiFlagsOffset
    LDA (EnemyAiPointer),Y
    AND #$08
    BNE MergeType08To0BVerticalDirection
    LDA #$80

MergeType08To0BVerticalDirection:
    AND #$80
    ASL TempPointer00
    ASL A
    LDA TempPointer00
    ROR A
    BCC StoreType08To0BVerticalDirection

ReverseType08To0BVerticalDirection:
    LDA #$80
    EOR TempPointer00

StoreType08To0BVerticalDirection:
    LDY #PathDirectionOffset
    STA (EnemyAiPointer),Y
    LDY #EnemyAiFlagsOffset
    LDA (EnemyAiPointer),Y
    AND #$EF
    STA TempPointer00
    LDY #ObjectActionOffset
    LDA (EnemyObjectPointer),Y
    ROR A
    LDA #$00
    BCC MergeType08To0BVerticalFlag
    LDA #$10

MergeType08To0BVerticalFlag:
    LDY #EnemyAiFlagsOffset
    ORA TempPointer00
    STA (EnemyAiPointer),Y

SetType08To0BMovingAction:
    LDY #ObjectActionOffset
    LDA (EnemyObjectPointer),Y
    AND #EnemyDirectionBit
    ORA #$18
    STA (EnemyObjectPointer),Y
    RTS

CheckEnemyAiDeltaRange:
    LDY #EnemyAiVerticalDeltaOffset

CheckNextEnemyAiDelta:
    LDA (EnemyAiPointer),Y
    ASL A
    ADC #$08
    CMP #$11
    BCS FinishEnemyAiDeltaRangeCheck
    INY
    CPY #PathDirectionOffset
    BNE CheckNextEnemyAiDelta
    CLC

FinishEnemyAiDeltaRangeCheck:
    RTS

RunType14To17EnemyAi:
    LDX #$00
    BEQ UpdateType14To1BPathSelection

RunType18To1BEnemyAi:
    LDX #$04

UpdateType14To1BPathSelection:
    LDY #EnemyAiPhaseOffset
    LDA (EnemyAiPointer),Y
    BNE BuildType14To1BPathSelection
    RTS

BuildType14To1BPathSelection:
    LDA #$00
    STA (EnemyAiPointer),Y
    STX TempPointer00
    LDX #$06

ClearType14To1BPathScratch:
    STA TempPointer00 + 1,X
    DEX
    BPL ClearType14To1BPathScratch
    LDY #PathDirectionOffset
    LDA (EnemyAiPointer),Y
    CLC
    ADC TempPointer00
    TAX
    LDA Type14To1BYFractionDeltas,X
    STA TempPointer00
    LDA Type14To1BXFractionDeltas,X
    STA TempPointer00 + 1
    LDX #$01

ExpandType14To1BPositionDelta:
    ASL TempPointer00,X
    BCC ShiftType14To1BPositionDelta
    DEC TempPointer02,X

ShiftType14To1BPositionDelta:
    ASL TempPointer00,X
    ROL TempPointer02,X
    ASL TempPointer00,X
    ROL TempPointer02,X
    DEX
    BPL ExpandType14To1BPositionDelta
    LDX #$01
    LDY #ObjectXFractionOffset

ApplyType14To1BPositionDelta:
    LDA (EnemyObjectPointer),Y
    CLC
    ADC TempPointer00,X
    STA (EnemyObjectPointer),Y
    INY
    LDA (EnemyObjectPointer),Y
    STA TempPointer00,X
    ADC TempPointer02,X
    STA TempPointer02,X
    LDY #ObjectYFractionOffset
    DEX
    BPL ApplyType14To1BPositionDelta
    LDX #$01
    STX TempPointer06

SampleType14To1BPathMask:
    LDY #$00
    STY TempPointer07
    LDY #$03

SampleNextType14To1BPathCell:
    LDA TempPointer06
    ASL A
    TAX
    LDA Type14To1BProbeYOffsets,Y
    CLC
    ADC TempPointer00,X
    STA CoordinateY
    LDA Type14To1BProbeXOffsets,Y
    CLC
    ADC TempPointer00 + 1,X
    STA CoordinateX
    JSR ConvertPixelCoordinatesToMapIndex
    LDA RoomMap,X
    ASL A
    ROL TempPointer07
    DEY
    BPL SampleNextType14To1BPathCell
    LDA TempPointer07
    PHA
    DEC TempPointer06
    BPL SampleType14To1BPathMask
    PLA
    STA TempPointer06
    PLA
    STA TempPointer07
    LDA TempPointer06
    LDX #$00
    JSR JumpWithParams

Type14To1BPathMaskHandlers:
    .addr HandleType14To1BPathMask00, HandleType14To1BPathMask01
    .addr HandleType14To1BPathMask02, HandleType14To1BPathMask03
    .addr HandleType14To1BPathMask04, HandleType14To1BPathMask05
    .addr HandleType14To1BPathMask06, HandleType14To1BPathMask07
    .addr HandleType14To1BPathMask08, HandleType14To1BPathMask09
    .addr HandleType14To1BPathMask0A, HandleType14To1BPathMask0B
    .addr HandleType14To1BPathMask0C, HandleType14To1BPathMask0D
    .addr HandleType14To1BPathMask0E, CommitType14To1BPathCoordinates

Type14To1BYFractionDeltas:
    .byte $00, $00, $DE, $22, $00, $00, $B4, $4C

Type14To1BXFractionDeltas:
    .byte $22, $DE, $00, $00, $4C, $B4, $00, $00

Type14To1BProbeYOffsets:
    .byte $04, $04, $0E, $0E

Type14To1BProbeXOffsets:
    .byte $03, $0E, $0E, $03

HandleType14To1BPathMask00:
    LDY #PathAlternateDirectionOffset
    LDA #$00
    CMP TempPointer07,X
    BEQ CommitType14To1BPathSelection
    LDA (EnemyAiPointer),Y
    STA TempPointer05,X
    DEY
    LDA (EnemyAiPointer),Y
    STA TempPointer04,X
    LDY #$00
    LDA TempPointer07,X

FindType14To1BPathDirectionBit:
    INY
    LSR A
    BCC FindType14To1BPathDirectionBit
    BEQ MatchType14To1BPathDirection
    LDY #PathDirectionOffset
    LDA TempPointer05,X
    STA (EnemyAiPointer),Y
    BPL CommitType14To1BPathSelection

MatchType14To1BPathDirection:
    DEY
    TYA
    ASL A
    TAY
    LDA TempPointer04,X
    CMP #$02
    BCC CompareType14To1BPathDirection
    INY

CompareType14To1BPathDirection:
    LDA TempPointer05,X
    CMP Type14To1BExpectedDirections,Y
    BNE CommitType14To1BPathSelection
    PHA
    LDA Type14To1BReplacementDirections,Y
    LDY #PathAlternateDirectionOffset
    STA (EnemyAiPointer),Y
    PLA
    DEY
    STA (EnemyAiPointer),Y

CommitType14To1BPathSelection:
    JMP CommitType14To1BPathCoordinates

Type14To1BExpectedDirections:
    .byte $02, $01, $02, $00, $03, $00, $03, $01

Type14To1BReplacementDirections:
    .byte $00, $03, $01, $03, $01, $02, $00, $02

HandleType14To1BPathMask01:
    LDY #PathDirectionOffset
    LDA (EnemyAiPointer),Y
    CMP #$02
    BCS SetType14To1BPathMask01XDirection
    JSR SetType14To1BYLowNibble0B
    BNE SelectType14To1BPathMask01Directions

SetType14To1BPathMask01XDirection:
    JSR SetType14To1BXLowNibble04

SelectType14To1BPathMask01Directions:
    LDA TempPointer07,X
    BNE CommitType14To1BPathCoordinatesFromMask01
    LDA #$01
    BCS StoreType14To1BPathMask01Direction
    LDA #$02

StoreType14To1BPathMask01Direction:
    STA (EnemyAiPointer),Y
    EOR #$02
    INY
    STA (EnemyAiPointer),Y
    RTS

CommitType14To1BPathCoordinatesFromMask01:
    JMP CommitType14To1BPathCoordinates

HandleType14To1BPathMask02:
    LDY #PathDirectionOffset
    LDA (EnemyAiPointer),Y
    CMP #$02
    BCS SetType14To1BPathMask02XDirection
    JSR SetType14To1BYLowNibble0B
    BNE SelectType14To1BPathMask02Directions

SetType14To1BPathMask02XDirection:
    JSR SetType14To1BXLowNibble0A

SelectType14To1BPathMask02Directions:
    LDA TempPointer07,X
    BNE CommitType14To1BPathCoordinatesFromMask01
    LDA #$00
    BCS StoreType14To1BPathMask02Direction
    LDA #$02

StoreType14To1BPathMask02Direction:
    STA (EnemyAiPointer),Y
    INY
    EOR #$03
    STA (EnemyAiPointer),Y
    RTS

HandleType14To1BPathMask04:
    LDY #PathDirectionOffset
    LDA (EnemyAiPointer),Y
    CMP #$02
    BCS SetType14To1BPathMask04XDirection
    JSR SetType14To1BYLowNibble02
    BNE SelectType14To1BPathMask04Directions

SetType14To1BPathMask04XDirection:
    JSR SetType14To1BXLowNibble0A

SelectType14To1BPathMask04Directions:
    LDA TempPointer07,X
    BNE CommitType14To1BPathCoordinatesFromMask01
    LDA #$00
    BCS StoreType14To1BPathMask04Direction
    LDA #$03

StoreType14To1BPathMask04Direction:
    STA (EnemyAiPointer),Y
    INY
    EOR #$02
    STA (EnemyAiPointer),Y
    RTS

HandleType14To1BPathMask08:
    LDY #PathDirectionOffset
    LDA (EnemyAiPointer),Y
    CMP #$02
    BCS SetType14To1BPathMask08XDirection
    JSR SetType14To1BYLowNibble02
    BNE SelectType14To1BPathMask08Directions

SetType14To1BPathMask08XDirection:
    JSR SetType14To1BXLowNibble04

SelectType14To1BPathMask08Directions:
    LDA TempPointer07,X
    BNE CommitType14To1BPathCoordinates
    LDA #$01
    BCS StoreType14To1BPathMask08Direction
    LDA #$03

StoreType14To1BPathMask08Direction:
    STA (EnemyAiPointer),Y
    INY
    EOR #$03
    STA (EnemyAiPointer),Y
    RTS

HandleType14To1BPathMask03:
    LDY #PathDirectionOffset
    LDA (EnemyAiPointer),Y
    CMP #$02
    BCS ClassifyType14To1BPathMask03Direction
    JSR SetType14To1BYLowNibble0B
    INY
    LDA #$03
    STA (EnemyAiPointer),Y
    BPL CommitType14To1BPathCoordinates

ClassifyType14To1BPathMask03Direction:
    LSR A
    BCS CommitType14To1BPathCoordinates

SelectType14To1BHorizontalDirection:
    LDY #ObjectXPositionOffset
    LDA (EnemyObjectPointer),Y
    AND #$0F
    CMP #$08
    LDA #$00
    BCC StoreType14To1BHorizontalDirection
    LDA #$01

StoreType14To1BHorizontalDirection:
    LDY #PathDirectionOffset
    STA (EnemyAiPointer),Y
    RTS

ClassifyType14To1BPathMask0C:
    LSR A
    BCC CommitType14To1BPathCoordinates
    BCS SelectType14To1BHorizontalDirection

HandleType14To1BPathMask0C:
    LDY #PathDirectionOffset
    LDA (EnemyAiPointer),Y
    CMP #$02
    BCS ClassifyType14To1BPathMask0C
    JSR SetType14To1BYLowNibble02
    INY
    LDA #$02
    STA (EnemyAiPointer),Y

CommitType14To1BPathCoordinates:
    LDY #ObjectYPositionOffset
    LDA TempPointer02,X
    STA (EnemyObjectPointer),Y
    LDY #ObjectXPositionOffset
    LDA TempPointer03,X
    STA (EnemyObjectPointer),Y
    RTS

HandleType14To1BPathMask09:
    LDY #PathDirectionOffset
    LDA (EnemyAiPointer),Y
    CMP #$02
    BCC ClassifyType14To1BPathMask09Direction
    JSR SetType14To1BXLowNibble04
    INY
    LDA #$00
    STA (EnemyAiPointer),Y

CommitType14To1BPathMask09Coordinates:
    BPL CommitType14To1BPathCoordinates

ClassifyType14To1BPathMask09Direction:
    LSR A
    BCC CommitType14To1BPathMask09Coordinates
    BCS SelectType14To1BVerticalDirection

HandleType14To1BPathMask06:
    LDY #PathDirectionOffset
    LDA (EnemyAiPointer),Y
    CMP #$02
    BCC ClassifyType14To1BPathMask06Direction
    JSR SetType14To1BXLowNibble0A
    LDY #PathAlternateDirectionOffset
    LDA #$01
    STA (EnemyAiPointer),Y

CommitType14To1BPathMask06Coordinates:
    BPL CommitType14To1BPathCoordinates

ClassifyType14To1BPathMask06Direction:
    LSR A
    BCS CommitType14To1BPathMask06Coordinates

SelectType14To1BVerticalDirection:
    LDY #PathAlternateDirectionOffset
    LDA (EnemyAiPointer),Y
    AND #$0F
    CMP #$0B
    LDA #$02
    BCS StoreType14To1BVerticalDirection
    LDA #$03

StoreType14To1BVerticalDirection:
    DEY
    STA (EnemyAiPointer),Y
    RTS

HandleType14To1BPathMask0B:
    LDY #PathDirectionOffset
    LDA (EnemyAiPointer),Y
    TAY
    LDA Type14To1BDirectionMap0B,Y
    BMI CommitType14To1BPathCoordinates
    LDY #PathDirectionOffset
    STA (EnemyAiPointer),Y
    EOR #$03
    INY
    STA (EnemyAiPointer),Y
    RTS

HandleType14To1BPathMask07:
    LDY #PathDirectionOffset
    LDA (EnemyAiPointer),Y
    TAY
    LDA Type14To1BDirectionMap07,Y
    BMI CommitType14To1BPathCoordinates
    LDY #PathDirectionOffset
    STA (EnemyAiPointer),Y
    EOR #$02
    INY
    STA (EnemyAiPointer),Y
    RTS

HandleType14To1BPathMask0D:
    LDY #PathDirectionOffset
    LDA (EnemyAiPointer),Y
    TAY
    LDA Type14To1BDirectionMap0D,Y

StoreMappedType14To1BPathDirection02:
    BMI CommitType14To1BPathCoordinates
    LDY #PathDirectionOffset
    STA (EnemyAiPointer),Y
    EOR #$02
    INY
    STA (EnemyAiPointer),Y
    RTS

HandleType14To1BPathMask0E:
    LDY #PathDirectionOffset
    LDA (EnemyAiPointer),Y
    TAY
    LDA Type14To1BDirectionMap0E,Y
    BMI StoreMappedType14To1BPathDirection02
    LDY #PathDirectionOffset
    STA (EnemyAiPointer),Y
    EOR #$03
    INY
    STA (EnemyAiPointer),Y
    RTS

HandleType14To1BPathMask05:
    LDA TempPointer02,X
    ADC #$01
    AND #$08
    BNE HandleType14To1BPathMask07
    BEQ HandleType14To1BPathMask0D

HandleType14To1BPathMask0A:
    LDA TempPointer02,X
    ADC #$01
    AND #$08
    BNE HandleType14To1BPathMask0B
    BEQ HandleType14To1BPathMask0E

SetType14To1BYLowNibble0B:
    LDA #$F0
    AND TempPointer02,X
    ORA #$0B
    STA TempPointer02,X
    RTS

SetType14To1BYLowNibble02:
    LDA #$F0
    AND TempPointer02,X
    ORA #$02
    STA TempPointer02,X
    RTS

SetType14To1BXLowNibble04:
    LDA #$F0
    AND TempPointer03,X
    ORA #$04
    STA TempPointer03,X
    RTS

SetType14To1BXLowNibble0A:
    LDA #$F0
    AND TempPointer03,X
    ORA #$0A
    STA TempPointer03,X
    RTS

Type14To1BDirectionMap0B:
    .byte $80, $03, $00, $80

Type14To1BDirectionMap07:
    .byte $03, $80, $01, $80

Type14To1BDirectionMap0D:
    .byte $80, $02, $80, $00

Type14To1BDirectionMap0E:
    .byte $02, $80, $80, $01
