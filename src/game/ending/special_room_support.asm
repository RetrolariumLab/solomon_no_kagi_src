; Shared ending helpers, Solomon's Seal reveal logic, and special-room data

.segment "PRG_ENDING_SPECIAL_ROOM_SUPPORT"

EndingPpuTemplateLastIndex = $12
EndingPaletteUpdateTile = $4F
EndingDelayCounter = $26
EndingRandomActionMask = $07
EndingRandomActionBase = $0C
EndingRandomObjectState = $C0
EndingRandomObjectType = $50
EndingRandomTargetY = $D0
EndingRandomTargetX = $78
EndingRandomVelocity = $50
RoomReadyFlag = $02

; Three palette values are consumed in reverse order by the ending fade
EndingPaletteValues:
    .byte $2C, $1C, $0C

BuildEndingPpuMessage:
    LDX #EndingPpuTemplateLastIndex

CopyNextEndingPpuTemplateByte:
    LDA StaticPpuUpdateStream05,X
    STA PpuUpdateBuffer,X
    DEX
    BPL CopyNextEndingPpuTemplateByte
    INX
    STX PpuUpdateBuffer + $13
    LDA #EndingPaletteUpdateTile
    STA PpuUpdateBuffer + $02
    RTS

InitializeRandomEndingObject:
    JSR AdvanceRandomState
    LDY #ObjectYPositionOffset
    STA (EnemyObjectPointer),Y
    STA CoordinateOriginY
    JSR AdvanceRandomState
    ASL A
    LDY #ObjectXPositionOffset
    STA (EnemyObjectPointer),Y
    STA CoordinateOriginX
    LDA #EndingRandomTargetY
    STA CoordinateTargetY
    LDA #EndingRandomTargetX
    STA CoordinateTargetX
    JSR BuildScaledCoordinateDeltas
    LDX #$03
    LDY #$07

CopyNextRandomEndingMotionByte:
    LDA CoordinateOriginY,X
    STA (EnemyAiPointer),Y
    DEY
    DEX
    BPL CopyNextRandomEndingMotionByte
    JSR AdvanceRandomState
    CLC
    AND #EndingRandomActionMask
    ADC #EndingRandomActionBase
    LDX #EndingRandomVelocity
    STX CoordinateTargetX
    LDX #EndingRandomObjectState
    STX CoordinateTargetY
    JSR InitializeObjectStateHeader
    RTS

WaitForDanaActive:
    JSR SwitchThreads
    LDA DanaObject + ObjectStateOffset
    BPL WaitForDanaActive
    RTS

LoadNextEndingObject:
    LDA EndingObjectPassCount
    JSR LoadEnemyAiPointer
    LDX #$00
    JSR CopyEndingPointerPair
    LDA EndingObjectPassCount
    JSR LoadEnemyObjectPointer
    LDX #$02
    JSR CopyEndingPointerPair
    RTS

; Copy TempPointer00 into EnemyAiPointer when X=0 or EnemyObjectPointer when X=2
CopyEndingPointerPair:
    LDY TempPointer00
    STY EnemyAiPointer,X
    LDY TempPointer00 + 1
    STY EnemyAiPointer + 1,X
    RTS

WaitOneEndingStep:
    LDA #$04

WaitForEndingSteps:
    LDX #$00
    STX EndingDelayCounter
    LDX #EndingDelayCounter
    JSR WaitForZeroPageCounterAboveThreshold
    RTS

WriteEndingRoomCell:
    STA RoomMapUpdateIndex
    STX RoomMapUpdateTile
    JSR BuildAndPublishRoomMapCellUpdate
    RTS

; These unreferenced bytes sit between the support code and active templates
UnusedEndingSetupData:
    .byte $E0, $00, $50, $01, $08, $03, $D0, $07, $20
    .byte $0A, $E0, $14, $50, $15
    .byte $09, $17, $D0, $1B, $30, $1E

; Four object-header bytes copied to MagicSparkObject
EndingSparkTemplate:
    .byte $C0, $50, $FF, $0A

; Thirteen bytes copied to the first enemy AI record for each orbit wave
EndingEnemyAiTemplate:
    .byte $A0, $00, $FE, $00, $00, $00, $D0
    .byte $78, $00, $80, $02, $00, $1F

; Object state, type, cached type, and action for the scrolling object field
EndingRandomObjectTemplate:
    .byte $C0, $50, $FF, $0B

UnusedEndingObjectData:
    .byte $1F, $1E, $2B, $00, $07, $50, $00

; Zero-terminated "FAIRIES WERE RELEASED", followed by alternate PPU addresses
EndingInitialMessageData:
    .byte $54
    .byte $0F, $0A, $12, $1B, $12, $0E, $1C, $24
    .byte $20, $0E, $1B, $0E, $24
    .byte $1B, $0E, $15, $0E, $0A, $1C, $0E, $0D
    .byte $00
    .byte $64, $28
    .byte $A4, $22

; Zero-terminated "AND FLEW AROUND THE WORLD", with alternate PPU addresses
    .byte $58
    .byte $0A, $17, $0D, $24
    .byte $0F, $15, $0E, $20, $24
    .byte $0A, $1B, $18, $1E, $17, $0D, $24
    .byte $1D, $11, $0E, $24
    .byte $20, $18, $1B, $15, $0D
    .byte $00
    .byte $A2, $28
    .byte $E2, $22

; Offsets select one of three sequences according to the ending flags
EndingMessageSequenceStarts:
    .byte $00, $04, $0B

; Each sequence terminates with bit 7 set
EndingMessageSequence:
    .byte $00, $01, $02, $80
    .byte $00, $01, $03, $04, $05, $06, $80
    .byte $00, $01, $03, $07, $08, $09, $80

; Each value points one byte before a message because the consumer increments Y
EndingMessageTextOffsets:
    .byte $FF, $20, $31, $4D, $6A
    .byte $7A, $99, $B5, $BC, $DC

EndingMessageData:
; "THE POWER OF SOLOMON'S KEY:"
    .byte $5A
    .byte $1D, $11, $0E, $24
    .byte $19, $18, $20, $0E, $1B, $24
    .byte $18, $0F, $28
    .byte $1C, $18, $15, $18, $16, $18, $17, $3B, $1C, $24
    .byte $14, $0E, $22, $3A
    .byte $00, $E2, $28, $22, $23

; "SEALED AWAY"
    .byte $4A
    .byte $1C, $0E, $0A, $15, $0E, $0D, $24
    .byte $0A, $20, $0A, $22
    .byte $00, $29, $29, $69, $23

; "THE DEVILS UNDERGROUND"
    .byte $55
    .byte $1D, $11, $0E, $24
    .byte $0D, $0E, $1F, $12, $15, $1C, $24
    .byte $1E, $17, $0D, $0E, $1B, $10, $1B, $18, $1E, $17, $0D
    .byte $00, $64, $29, $A4, $23

; "ALL OF THE EVIL SPIRITS"
    .byte $56
    .byte $0A, $15, $15, $24
    .byte $18, $0F, $24
    .byte $1D, $11, $0E, $24
    .byte $0E, $1F, $12, $15, $24
    .byte $1C, $19, $12, $1B, $12, $1D, $1C
    .byte $00, $63, $29, $A3, $23

; "IN THE WORLD"
    .byte $4B
    .byte $12, $17, $24
    .byte $1D, $11, $0E, $24
    .byte $20, $18, $1B, $15, $0D
    .byte $00, $A9, $29

; "HOWEVER, A SMALL POSSIBILITY"
    .byte $5A
    .byte $11, $18, $20, $0E, $1F, $0E, $1B, $25, $0A, $24
    .byte $1C, $16, $0A, $15, $15, $24
    .byte $19, $18, $1C, $1C, $12, $0B, $12, $15, $12, $1D, $22
    .byte $00, $E2, $29

; "OF THEIR REVIVAL REMAINS"
    .byte $57
    .byte $18, $0F, $24
    .byte $1D, $11, $0E, $12, $1B, $24
    .byte $1B, $0E, $1F, $12, $1F, $0A, $15, $24
    .byte $1B, $0E, $16, $0A, $12, $17, $1C
    .byte $00, $23, $2A

; "AND"
    .byte $42
    .byte $0A, $17, $0D
    .byte $00, $2D, $28

; "THE CONSTELLATION WAS RUINED"
    .byte $5B
    .byte $1D, $11, $0E, $24
    .byte $0C, $18, $17, $1C, $1D, $0E, $15, $15, $0A, $1D, $12, $18, $17, $24
    .byte $20, $0A, $1C, $24
    .byte $1B, $1E, $12, $17, $0E, $0D
    .byte $00, $61, $28

; "PEACE WILL BE OURS FOREVER"
    .byte $5A
    .byte $19, $0E, $0A, $0C, $0E, $24
    .byte $20, $12, $15, $15, $24
    .byte $0B, $0E, $24
    .byte $18, $1E, $1B, $3B, $1C, $24
    .byte $0F, $18, $1B, $0E, $1F, $0E, $1B
    .byte $00, $A2, $28

RevealCurrentRoomSeal:
    PHA
    JSR PrepareSpecialRoomTrigger
    PLA
    STA CurrentRoomSolomonSealFlag
    AND CollectedSolomonSealFlags
    BNE FinishCurrentRoomSealReveal
    LDX #$FF
    LDA CurrentRoomSolomonSealFlag

FindCurrentRoomSealIndex:
    INX
    LSR A
    BCC FindCurrentRoomSealIndex
    LDY SolomonSealRoomMapOffsets,X
    LDA #RoomMapHiddenSolomonSeal
    STA RoomMap,Y

FinishCurrentRoomSealReveal:
    RTS

; Map positions for Seal flags $01-$80: rooms 9, 13, 17, 19, 21, 29, 46, 47
SolomonSealRoomMapOffsets:
    .byte $89, $97, $2D, $54, $6B, $B7, $1D, $1E

PrepareSpecialRoomTrigger:
    LDA #RoomReadyFlag
    LDX #RoomStateFlags
    JSR WaitForMaskedBitsSet
    RTS

; Princess-room cells hidden until its scripted object conditions are met
PrincessRoomObjectMapOffsets:
    .byte $41, $51, $61, $71, $81
    .byte $4D, $5D, $6D, $7D, $8D
    .byte $46, $48

; Room index 19 (displayed room 20) special 12-row block bitplane
Room20SpecialBlockPlane:
    .byte $FE, $FE, $60, $CC, $5E, $F4, $7F, $CC
    .byte $DF, $78, $F7, $DC, $79, $B6, $2F, $BC
    .byte $7D, $D8, $57, $7C, $7F, $F6, $DB, $BE

; Room index 29 (displayed room 30) special 12-row block bitplane
Room30SpecialBlockPlane:
    .byte $00, $00, $54, $54, $00, $00, $AA, $AA
    .byte $00, $00, $55, $54, $00, $00, $AA, $AA
    .byte $00, $00, $15, $50, $00, $00, $00, $00

; Bisqwit's map identifies this unreferenced tail as the filler before $C100
FillerBeforeC100:
.if SolomonRevision = SolomonRevisionEurope
    .res $6E, $FF
.else
    .byte $FF
    .byte $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $00, $FF, $00
    .byte $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $FF, $00, $FF
    .byte $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $55, $FF, $00
    .byte $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $FD, $00, $FF
    .byte $01, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $00, $FF, $00
    .byte $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $FF, $00, $FF
    .byte $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $58, $FF, $00
    .byte $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $6F, $00, $FF
    .byte $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $00, $FF, $00
    .byte $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $FF, $00, $FF
    .byte $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $48, $FF, $00
    .byte $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $FE, $02, $FF
    .byte $02, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $00, $FF, $00
    .byte $BF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $FF, $00, $FF
    .byte $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00
.endif

.assert * - EndingPaletteValues = $36C - (SolomonRevision = SolomonRevisionEurope) * $80, error, "unexpected ending support size"
