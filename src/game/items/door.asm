; Enter an opened door, select the next room, and start room-clear context 1

.segment "PRG_DOOR_ITEM"

DanaDoorInactiveState = $80
DoorGameplayThreadIndex = $03
DoorEnteredSound = $15
DoorSkipRoomsFlag = $40
DoorSkipRoomCount = $05
DoorConstellationFlag = $08
DoorPageOfTimeSelector = $10
DoorPageOfSpaceSelector = $20
DoorConstellationBonusSelector = $30
PageOfTimeSealThreshold = $04
PageOfSpaceSealThreshold = $06
PageOfTimeSourceRoomIndex = $14
PageOfSpaceSourceRoomIndex = $2C
KeyCollectedGameplayFlagMask = $DF
RoomStateAfterDoorMask = $EE
RoomClearThreadCode = $14

EnterRoomDoor:
    LDA #DanaDoorInactiveState
    STA DanaObject
    LDX #DoorGameplayThreadIndex
    JSR ResetOtherSecondaryThreads
    LDY #DoorEnteredSound
    JSR AddSoundEffect
    INC $85
    LDA #DoorSkipRoomsFlag
    AND GameplayFlags
    BEQ CheckDoorRoomProgression
    CLC
    LDA #DoorSkipRoomCount
    ADC CurrentRoomIndex
    STA CurrentRoomIndex

CheckDoorRoomProgression:
    LDY SolomonSealCount
    LDA FireballState
    BNE ApplyDoorSpecialRoomFlags
    LDX CurrentRoomIndex
    CPX #$0A
    BCC CheckDoorRoom47
    LDA RoomStateFlags
    AND #$10
    BNE CheckDoorRoom47
    INC $84

CheckDoorRoom47:
    LDX CurrentRoomIndex
    CPX #$2F
    BNE AdvanceDoorRoom
    CPY #$08
    BCS AdvanceDoorRoom
    INX

AdvanceDoorRoom:
    INX
    STX CurrentRoomIndex

ApplyDoorSpecialRoomFlags:
    LDA #DoorConstellationFlag
    AND GameStateFlags
    BEQ FinishDoorSpecialRoomFlags
    CPY #PageOfTimeSealThreshold
    BCC SelectDefaultDoorSpecialRoomFlags
    LDA #DoorPageOfTimeSelector
    LDX CurrentRoomIndex
    CPX #PageOfTimeSourceRoomIndex
    BEQ StoreDoorSpecialRoomFlags
    CPY #PageOfSpaceSealThreshold
    BCC SelectDefaultDoorSpecialRoomFlags
    ASL A  ; Page of Time selector $10 becomes Page of Space selector $20
    CPX #PageOfSpaceSourceRoomIndex
    BEQ StoreDoorSpecialRoomFlags

SelectDefaultDoorSpecialRoomFlags:
    LDA #DoorConstellationBonusSelector

StoreDoorSpecialRoomFlags:
    ORA GameStateFlags
    STA GameStateFlags

FinishDoorSpecialRoomFlags:
    LDA #KeyCollectedGameplayFlagMask
    AND GameplayFlags
    STA GameplayFlags
    JSR ClearGameplayObjectAndEnemyState
    STA FireballActive
    STA FireballState
    LDA #RoomStateAfterDoorMask
    AND RoomStateFlags
    STA RoomStateFlags
    LDA #RoomClearThreadCode
    JSR StartThread
    LDA #DoorGameplayThreadIndex
    JSR StopThread
