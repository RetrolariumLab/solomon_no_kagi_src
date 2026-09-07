; Place Dana and run the object-orbit presentation at room entry

.segment "PRG_ROOM_ENTRY_ANIMATION"

RoomHeaderDanaPositionOffset = $07

RunRoomEntryAnimation:
    LDY #$14
    JSR AddSoundEffect
    LDA #$78
    STA TempPointer02
    STA $03
    LDY #RoomHeaderDanaPositionOffset
    LDA (RoomItemPointer),Y
    PHA
    STA CoordinateY
    JSR ConvertMapIndexToPixelCoordinates
    JSR BuildScaledCoordinateDeltas
    LDY #$03

SeedRoomEntryAiCoordinates:
    LDX TransitionAiCoordinateSourceOffsets,Y
    LDA TempPointer02,X
    STA EnemyAiState,Y
    DEY
    BPL SeedRoomEntryAiCoordinates
    LDX #$08

CopyRoomEntryAiStateTemplate:
    LDA RoomEntryAiStateTemplate,X
    STA EnemyAiState + 4,X
    DEX
    BPL CopyRoomEntryAiStateTemplate
    JSR RunTransitionObjectOrbit
    PLA
    STA CoordinateY
    JSR ConvertMapIndexToPixelCoordinates
    LDA CoordinateY
    STA DanaYPosition
    STA MagicSparkObject + ObjectYPositionOffset
    LDA CoordinateX
    STA DanaXPosition
    STA MagicSparkObject + ObjectXPositionOffset
    LDX #$03

CopyRoomEntrySparkHeader:
    LDA RoomEntrySparkHeader,X
    STA MagicSparkObject,X
    DEX
    BPL CopyRoomEntrySparkHeader
    JSR ResetAndSelectGameplayDelayCounter
    LDA #$10
    JSR WaitForZeroPageCounterAboveThreshold
    LDA MagicSparkObject + ObjectXPositionOffset
    ROL A
    LDA #$07
    ROL A
    STA MagicSparkObject + ObjectActionOffset
    LDA #$04
    STA MagicSparkObject + ObjectTypeOffset
    JSR ResetAndSelectGameplayDelayCounter
    LDA #$10
    JMP WaitForZeroPageCounterAboveThreshold
