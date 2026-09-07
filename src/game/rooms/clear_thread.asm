; Context-one room-clear sequence and remaining-time bonus handoff

.segment "PRG_ROOM_CLEAR_THREAD"

RoomClearThread:
    LDX #$01
    JSR ResetOtherSecondaryThreads
    LDA #$FF
    LDX #$1B
    JSR WaitForMaskedBitsClear
    JSR BuildTimerDisplayUpdate
    LDX #$08

CopyRoomClearAiStateTemplate:
    LDA RoomClearAiStateTemplate,X
    STA EnemyAiState + 4,X
    DEX
    BPL CopyRoomClearAiStateTemplate
    LDY #$05
    LDA (RoomItemPointer),Y
    STA CoordinateY
    JSR ConvertMapIndexToPixelCoordinates
    LDX #$01

CopyRoomClearOriginCoordinates:
    LDA CoordinateY,X
    STA TempPointer02,X
    STA EnemyAiState + 6,X
    DEX
    BPL CopyRoomClearOriginCoordinates
    LDA #$78
    STA CoordinateY
    STA CoordinateX
    JSR BuildScaledCoordinateDeltas
    LDY #$03

SeedRoomClearAiCoordinates:
    LDX TransitionAiCoordinateSourceOffsets,Y
    LDA TempPointer02,X
    STA EnemyAiState,Y
    DEY
    BPL SeedRoomClearAiCoordinates
    LDX GameplayFlags
    TXA
    LDY #$01
    AND #$40
    BEQ SelectRoomClearRotationStep
    LDY #$05

SelectRoomClearRotationStep:
    STY $80
    TXA
    AND #$BF
    STA GameplayFlags
    JSR RunTransitionObjectOrbit
    JSR Clear30x24NametableRegion
    LDA #$03
    STA ChrBankRequest
    LDX #$01

InitializeRoomClearObjects:
    TXA
    JSR LoadEnemyObjectPointer
    LDY #ObjectYPositionOffset
    LDA #$50
    STA (TempPointer00),Y
    LDY #ObjectXPositionOffset
    LDA RoomClearObjectXPositions,X
    STA (TempPointer00),Y
    LDY #ObjectActionOffset
    CPX #$01
    LDA #$0C
    ROL A

CopyRoomClearObjectHeader:
    STA (TempPointer00),Y
    LDA RoomClearObjectHeaderPredecessors,Y
    DEY
    BPL CopyRoomClearObjectHeader
    DEX
    BPL InitializeRoomClearObjects
    LDX #$02

QueueRoomClearMessages:
    TXA
    JSR QueueStaticPpuUpdateStream
    INX
    CPX #$05
    BCC QueueRoomClearMessages
    JSR ResetAndSelectGameplayDelayCounter
    LDA #$40
    JSR WaitForZeroPageCounterAboveThreshold
    LDY #$13
    JSR AddSoundEffect
    JSR SubtractTimerBy8
    JSR ResetAndSelectGameplayDelayCounter
    LDA #$A0
    JSR WaitForZeroPageCounterAboveThreshold
    LDA #$00
    STA EnemyObjects + ObjectStateOffset
    STA EnemyObjects + ObjectRecordSize + ObjectStateOffset
    JSR Clear30x24NametableRegion
    LDY #$18
    JSR AddSoundEffect
    LDA #$15
    JSR StartThread
