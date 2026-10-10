; Directional enemy actions and RoomMap path selection

.segment "PRG_PATHFINDING_ENEMY_AI"

PathDirectionOffset = EnemyAiPathDirectionOffset
PathAlternateDirectionOffset = EnemyAiAlternateDirectionOffset
TempPointer03 = TempPointer02 + 1
TempPointer05 = TempPointer04 + 1
TempPointer06 = TempPointer04 + 2
TempPointer07 = TempPointer04 + 3

UpdateFairyPhaseAction:
    LDY #EnemyAiPhaseOffset
    LDA (EnemyAiPointer),Y
    CMP #$20
    BCC FinishFairyPhaseAction
    LDY #ObjectActionOffset
    LDA #$18
    ORA (EnemyObjectPointer),Y
    STA (EnemyObjectPointer),Y

FinishFairyPhaseAction:
    RTS

UpdateFairyHorizontalOrientation:
    LDY #PathDirectionOffset
    LDA (EnemyAiPointer),Y
    ASL A
    TAX
    LDY #ObjectActionOffset
    LDA (EnemyObjectPointer),Y
    AND #$02
    CLC
    BNE RotateFairyHorizontalDirection
    SEC

RotateFairyHorizontalDirection:
    TXA
    ROR A
    STA TempPointer00
    LDY #ObjectXMotionOffset
    LDA (EnemyObjectPointer),Y
    EOR TempPointer00
    AND #$40
    BNE ReverseFairyHorizontalDirection
    LDY #EnemyAiFlagsOffset
    LDA (EnemyAiPointer),Y
    AND #$10
    BNE MergeFairyHorizontalDirection
    LDA #$80

MergeFairyHorizontalDirection:
    AND #$80
    ROL TempPointer00
    ROR A
    BCC StoreFairyHorizontalDirection

ReverseFairyHorizontalDirection:
    LDA #$40
    EOR TempPointer00

StoreFairyHorizontalDirection:
    LDY #PathDirectionOffset
    STA (EnemyAiPointer),Y
    LDY #EnemyAiFlagsOffset
    LDA (EnemyAiPointer),Y
    AND #$F7
    STA TempPointer00
    LDY #ObjectActionOffset
    LDA #$02
    AND (EnemyObjectPointer),Y
    BEQ MergeFairyHorizontalFlag
    LDA #$08

MergeFairyHorizontalFlag:
    LDY #EnemyAiFlagsOffset
    ORA TempPointer00
    STA (EnemyAiPointer),Y
    JMP SetFairyMovingAction

UpdateFairyVerticalOrientation:
    LDY #PathDirectionOffset
    LDA (EnemyAiPointer),Y
    AND #$BF
    TAX
    LDY #ObjectActionOffset
    LDA (EnemyObjectPointer),Y
    LSR A
    TXA
    BCS CompareFairyVerticalDirection
    ORA #$40

CompareFairyVerticalDirection:
    STA TempPointer00
    LDY #ObjectYMotionOffset
    LDA (EnemyObjectPointer),Y
    ASL A
    EOR TempPointer00
    BPL ReverseFairyVerticalDirection
    LDY #EnemyAiFlagsOffset
    LDA (EnemyAiPointer),Y
    AND #$08
    BNE MergeFairyVerticalDirection
    LDA #$80

MergeFairyVerticalDirection:
    AND #$80
    ASL TempPointer00
    ASL A
    LDA TempPointer00
    ROR A
    BCC StoreFairyVerticalDirection

ReverseFairyVerticalDirection:
    LDA #$80
    EOR TempPointer00

StoreFairyVerticalDirection:
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
    BCC MergeFairyVerticalFlag
    LDA #$10

MergeFairyVerticalFlag:
    LDY #EnemyAiFlagsOffset
    ORA TempPointer00
    STA (EnemyAiPointer),Y

SetFairyMovingAction:
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

RunSlowSparkBallEnemyAi:
    LDX #$00
    BEQ UpdateSparkBallPathSelection

RunFastSparkBallEnemyAi:
    LDX #$04

UpdateSparkBallPathSelection:
    LDY #EnemyAiPhaseOffset
    LDA (EnemyAiPointer),Y
    BNE BuildSparkBallPathSelection
    RTS

BuildSparkBallPathSelection:
    LDA #$00
    STA (EnemyAiPointer),Y
    STX TempPointer00
    LDX #$06

ClearSparkBallPathScratch:
    STA TempPointer00 + 1,X
    DEX
    BPL ClearSparkBallPathScratch
    LDY #PathDirectionOffset
    LDA (EnemyAiPointer),Y
    CLC
    ADC TempPointer00
    TAX
    LDA SparkBallYFractionDeltas,X
    STA TempPointer00
    LDA SparkBallXFractionDeltas,X
    STA TempPointer00 + 1
    LDX #$01

ExpandSparkBallPositionDelta:
    ASL TempPointer00,X
    BCC ShiftSparkBallPositionDelta
    DEC TempPointer02,X

ShiftSparkBallPositionDelta:
    ASL TempPointer00,X
    ROL TempPointer02,X
    ASL TempPointer00,X
    ROL TempPointer02,X
    DEX
    BPL ExpandSparkBallPositionDelta
    LDX #$01
    LDY #ObjectXFractionOffset

ApplySparkBallPositionDelta:
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
    BPL ApplySparkBallPositionDelta
    LDX #$01
    STX TempPointer06

SampleSparkBallPathMask:
    LDY #$00
    STY TempPointer07
    LDY #$03

SampleNextSparkBallPathCell:
    LDA TempPointer06
    ASL A
    TAX
    LDA SparkBallProbeYOffsets,Y
    CLC
    ADC TempPointer00,X
    STA CoordinateY
    LDA SparkBallProbeXOffsets,Y
    CLC
    ADC TempPointer00 + 1,X
    STA CoordinateX
    JSR ConvertPixelCoordinatesToMapIndex
    LDA RoomMap,X
    ASL A
    ROL TempPointer07
    DEY
    BPL SampleNextSparkBallPathCell
    LDA TempPointer07
    PHA
    DEC TempPointer06
    BPL SampleSparkBallPathMask
    PLA
    STA TempPointer06
    PLA
    STA TempPointer07
    LDA TempPointer06
    LDX #$00
    JSR JumpWithParams

SparkBallPathMaskHandlers:
    .addr HandleSparkBallPathMask00, HandleSparkBallPathMask01
    .addr HandleSparkBallPathMask02, HandleSparkBallPathMask03
    .addr HandleSparkBallPathMask04, HandleSparkBallPathMask05
    .addr HandleSparkBallPathMask06, HandleSparkBallPathMask07
    .addr HandleSparkBallPathMask08, HandleSparkBallPathMask09
    .addr HandleSparkBallPathMask0A, HandleSparkBallPathMask0B
    .addr HandleSparkBallPathMask0C, HandleSparkBallPathMask0D
    .addr HandleSparkBallPathMask0E, CommitSparkBallPathCoordinates

SparkBallYFractionDeltas:
    .byte $00, $00, $DE, $22, $00, $00, $B4, $4C

SparkBallXFractionDeltas:
    .byte $22, $DE, $00, $00, $4C, $B4, $00, $00

SparkBallProbeYOffsets:
    .byte $04, $04, $0E, $0E

SparkBallProbeXOffsets:
    .byte $03, $0E, $0E, $03

HandleSparkBallPathMask00:
    LDY #PathAlternateDirectionOffset
    LDA #$00
    CMP TempPointer07,X
    BEQ CommitSparkBallPathSelection
    LDA (EnemyAiPointer),Y
    STA TempPointer05,X
    DEY
    LDA (EnemyAiPointer),Y
    STA TempPointer04,X
    LDY #$00
    LDA TempPointer07,X

FindSparkBallPathDirectionBit:
    INY
    LSR A
    BCC FindSparkBallPathDirectionBit
    BEQ MatchSparkBallPathDirection
    LDY #PathDirectionOffset
    LDA TempPointer05,X
    STA (EnemyAiPointer),Y
    BPL CommitSparkBallPathSelection

MatchSparkBallPathDirection:
    DEY
    TYA
    ASL A
    TAY
    LDA TempPointer04,X
    CMP #$02
    BCC CompareSparkBallPathDirection
    INY

CompareSparkBallPathDirection:
    LDA TempPointer05,X
    CMP SparkBallExpectedDirections,Y
    BNE CommitSparkBallPathSelection
    PHA
    LDA SparkBallReplacementDirections,Y
    LDY #PathAlternateDirectionOffset
    STA (EnemyAiPointer),Y
    PLA
    DEY
    STA (EnemyAiPointer),Y

CommitSparkBallPathSelection:
    JMP CommitSparkBallPathCoordinates

SparkBallExpectedDirections:
    .byte $02, $01, $02, $00, $03, $00, $03, $01

SparkBallReplacementDirections:
    .byte $00, $03, $01, $03, $01, $02, $00, $02

HandleSparkBallPathMask01:
    LDY #PathDirectionOffset
    LDA (EnemyAiPointer),Y
    CMP #$02
    BCS SetSparkBallPathMask01XDirection
    JSR SetSparkBallYLowNibble0B
    BNE SelectSparkBallPathMask01Directions

SetSparkBallPathMask01XDirection:
    JSR SetSparkBallXLowNibble04

SelectSparkBallPathMask01Directions:
    LDA TempPointer07,X
    BNE CommitSparkBallPathCoordinatesFromMask01
    LDA #$01
    BCS StoreSparkBallPathMask01Direction
    LDA #$02

StoreSparkBallPathMask01Direction:
    STA (EnemyAiPointer),Y
    EOR #$02
    INY
    STA (EnemyAiPointer),Y
    RTS

CommitSparkBallPathCoordinatesFromMask01:
    JMP CommitSparkBallPathCoordinates

HandleSparkBallPathMask02:
    LDY #PathDirectionOffset
    LDA (EnemyAiPointer),Y
    CMP #$02
    BCS SetSparkBallPathMask02XDirection
    JSR SetSparkBallYLowNibble0B
    BNE SelectSparkBallPathMask02Directions

SetSparkBallPathMask02XDirection:
    JSR SetSparkBallXLowNibble0A

SelectSparkBallPathMask02Directions:
    LDA TempPointer07,X
    BNE CommitSparkBallPathCoordinatesFromMask01
    LDA #$00
    BCS StoreSparkBallPathMask02Direction
    LDA #$02

StoreSparkBallPathMask02Direction:
    STA (EnemyAiPointer),Y
    INY
    EOR #$03
    STA (EnemyAiPointer),Y
    RTS

HandleSparkBallPathMask04:
    LDY #PathDirectionOffset
    LDA (EnemyAiPointer),Y
    CMP #$02
    BCS SetSparkBallPathMask04XDirection
    JSR SetSparkBallYLowNibble02
    BNE SelectSparkBallPathMask04Directions

SetSparkBallPathMask04XDirection:
    JSR SetSparkBallXLowNibble0A

SelectSparkBallPathMask04Directions:
    LDA TempPointer07,X
    BNE CommitSparkBallPathCoordinatesFromMask01
    LDA #$00
    BCS StoreSparkBallPathMask04Direction
    LDA #$03

StoreSparkBallPathMask04Direction:
    STA (EnemyAiPointer),Y
    INY
    EOR #$02
    STA (EnemyAiPointer),Y
    RTS

HandleSparkBallPathMask08:
    LDY #PathDirectionOffset
    LDA (EnemyAiPointer),Y
    CMP #$02
    BCS SetSparkBallPathMask08XDirection
    JSR SetSparkBallYLowNibble02
    BNE SelectSparkBallPathMask08Directions

SetSparkBallPathMask08XDirection:
    JSR SetSparkBallXLowNibble04

SelectSparkBallPathMask08Directions:
    LDA TempPointer07,X
    BNE CommitSparkBallPathCoordinates
    LDA #$01
    BCS StoreSparkBallPathMask08Direction
    LDA #$03

StoreSparkBallPathMask08Direction:
    STA (EnemyAiPointer),Y
    INY
    EOR #$03
    STA (EnemyAiPointer),Y
    RTS

HandleSparkBallPathMask03:
    LDY #PathDirectionOffset
    LDA (EnemyAiPointer),Y
    CMP #$02
    BCS ClassifySparkBallPathMask03Direction
    JSR SetSparkBallYLowNibble0B
    INY
    LDA #$03
    STA (EnemyAiPointer),Y
    BPL CommitSparkBallPathCoordinates

ClassifySparkBallPathMask03Direction:
    LSR A
    BCS CommitSparkBallPathCoordinates

SelectSparkBallHorizontalDirection:
    LDY #ObjectXPositionOffset
    LDA (EnemyObjectPointer),Y
    AND #$0F
    CMP #$08
    LDA #$00
    BCC StoreSparkBallHorizontalDirection
    LDA #$01

StoreSparkBallHorizontalDirection:
    LDY #PathDirectionOffset
    STA (EnemyAiPointer),Y
    RTS

ClassifySparkBallPathMask0C:
    LSR A
    BCC CommitSparkBallPathCoordinates
    BCS SelectSparkBallHorizontalDirection

HandleSparkBallPathMask0C:
    LDY #PathDirectionOffset
    LDA (EnemyAiPointer),Y
    CMP #$02
    BCS ClassifySparkBallPathMask0C
    JSR SetSparkBallYLowNibble02
    INY
    LDA #$02
    STA (EnemyAiPointer),Y

CommitSparkBallPathCoordinates:
    LDY #ObjectYPositionOffset
    LDA TempPointer02,X
    STA (EnemyObjectPointer),Y
    LDY #ObjectXPositionOffset
    LDA TempPointer03,X
    STA (EnemyObjectPointer),Y
    RTS

HandleSparkBallPathMask09:
    LDY #PathDirectionOffset
    LDA (EnemyAiPointer),Y
    CMP #$02
    BCC ClassifySparkBallPathMask09Direction
    JSR SetSparkBallXLowNibble04
    INY
    LDA #$00
    STA (EnemyAiPointer),Y

CommitSparkBallPathMask09Coordinates:
    BPL CommitSparkBallPathCoordinates

ClassifySparkBallPathMask09Direction:
    LSR A
    BCC CommitSparkBallPathMask09Coordinates
    BCS SelectSparkBallVerticalDirection

HandleSparkBallPathMask06:
    LDY #PathDirectionOffset
    LDA (EnemyAiPointer),Y
    CMP #$02
    BCC ClassifySparkBallPathMask06Direction
    JSR SetSparkBallXLowNibble0A
    LDY #PathAlternateDirectionOffset
    LDA #$01
    STA (EnemyAiPointer),Y

CommitSparkBallPathMask06Coordinates:
    BPL CommitSparkBallPathCoordinates

ClassifySparkBallPathMask06Direction:
    LSR A
    BCS CommitSparkBallPathMask06Coordinates

SelectSparkBallVerticalDirection:
    LDY #PathAlternateDirectionOffset
    LDA (EnemyAiPointer),Y
    AND #$0F
    CMP #$0B
    LDA #$02
    BCS StoreSparkBallVerticalDirection
    LDA #$03

StoreSparkBallVerticalDirection:
    DEY
    STA (EnemyAiPointer),Y
    RTS

HandleSparkBallPathMask0B:
    LDY #PathDirectionOffset
    LDA (EnemyAiPointer),Y
    TAY
    LDA SparkBallDirectionMap0B,Y
    BMI CommitSparkBallPathCoordinates
    LDY #PathDirectionOffset
    STA (EnemyAiPointer),Y
    EOR #$03
    INY
    STA (EnemyAiPointer),Y
    RTS

HandleSparkBallPathMask07:
    LDY #PathDirectionOffset
    LDA (EnemyAiPointer),Y
    TAY
    LDA SparkBallDirectionMap07,Y
    BMI CommitSparkBallPathCoordinates
    LDY #PathDirectionOffset
    STA (EnemyAiPointer),Y
    EOR #$02
    INY
    STA (EnemyAiPointer),Y
    RTS

HandleSparkBallPathMask0D:
    LDY #PathDirectionOffset
    LDA (EnemyAiPointer),Y
    TAY
    LDA SparkBallDirectionMap0D,Y

StoreMappedSparkBallPathDirection02:
    BMI CommitSparkBallPathCoordinates
    LDY #PathDirectionOffset
    STA (EnemyAiPointer),Y
    EOR #$02
    INY
    STA (EnemyAiPointer),Y
    RTS

HandleSparkBallPathMask0E:
    LDY #PathDirectionOffset
    LDA (EnemyAiPointer),Y
    TAY
    LDA SparkBallDirectionMap0E,Y
    BMI StoreMappedSparkBallPathDirection02
    LDY #PathDirectionOffset
    STA (EnemyAiPointer),Y
    EOR #$03
    INY
    STA (EnemyAiPointer),Y
    RTS

HandleSparkBallPathMask05:
    LDA TempPointer02,X
    ADC #$01
    AND #$08
    BNE HandleSparkBallPathMask07
    BEQ HandleSparkBallPathMask0D

HandleSparkBallPathMask0A:
    LDA TempPointer02,X
    ADC #$01
    AND #$08
    BNE HandleSparkBallPathMask0B
    BEQ HandleSparkBallPathMask0E

SetSparkBallYLowNibble0B:
    LDA #$F0
    AND TempPointer02,X
    ORA #$0B
    STA TempPointer02,X
    RTS

SetSparkBallYLowNibble02:
    LDA #$F0
    AND TempPointer02,X
    ORA #$02
    STA TempPointer02,X
    RTS

SetSparkBallXLowNibble04:
    LDA #$F0
    AND TempPointer03,X
    ORA #$04
    STA TempPointer03,X
    RTS

SetSparkBallXLowNibble0A:
    LDA #$F0
    AND TempPointer03,X
    ORA #$0A
    STA TempPointer03,X
    RTS

SparkBallDirectionMap0B:
    .byte $80, $03, $00, $80

SparkBallDirectionMap07:
    .byte $03, $80, $01, $80

SparkBallDirectionMap0D:
    .byte $80, $02, $80, $00

SparkBallDirectionMap0E:
    .byte $02, $80, $80, $01
