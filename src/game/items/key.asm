; Reveal the room door after collecting the key

.segment "PRG_KEY_ITEM"

RoomDoorPositionOffset = $05
KeyCollectedGameplayFlag = $20
KeyCollectedSound = $16
KeyObjectThreadIndex = $04
KeyInteractionThreadCode = $34

CollectRoomKey:
    LDY #RoomDoorPositionOffset
    LDA (RoomItemPointer),Y
    TAY
    LDA #RoomMapOpenDoorIdentity
    STA RoomMap,Y
    LDA FireballState
    BNE QueueKeyCollectedSound
    LDA #KeyCollectedGameplayFlag
    ORA GameplayFlags
    STA GameplayFlags

QueueKeyCollectedSound:
    LDY #KeyCollectedSound
    JSR AddSoundEffect
    LDA #KeyObjectThreadIndex
    JSR StopThread
    LDA #KeyInteractionThreadCode
    STA ItemInteractionThreadCode
    RTS

; Context-three key collection handoff and gameplay-state restoration

.segment "PRG_KEY_COLLECTION_PRESENTATION"

KeyCollectionObjectStateMask = $BF
KeyCollectionEnemyCount = EnemyObjectCount
KeyCollectionDanaState = $E0
MainGameplayThreadCode = $30

RunKeyCollectionPresentation:
    LDA DanaObject + ObjectStateOffset
    ROR A
    BCC PauseObjectsForKeyCollection
    JSR SwitchThreads
    BCS RunKeyCollectionPresentation

PauseObjectsForKeyCollection:
    ASL A
    AND #KeyCollectionObjectStateMask
    STA DanaObject + ObjectStateOffset
    LDA FireballObject + ObjectStateOffset
    STA FireballObject + ObjectCachedTypeOffset
    AND #KeyCollectionObjectStateMask
    STA FireballObject + ObjectStateOffset
    LDX #KeyCollectionEnemyCount - 1

PauseNextEnemyForKeyCollection:
    TXA
    JSR LoadEnemyObjectPointer
    LDY #ObjectStateOffset
    LDA (TempPointer00),Y
    PHA
    AND #KeyCollectionObjectStateMask
    STA (TempPointer00),Y
    LDY #ObjectCachedTypeOffset
    PLA
    STA (TempPointer00),Y
    DEX
    BPL PauseNextEnemyForKeyCollection

RemoveCollectedKeyFromRoomMap:
    LDY #RoomHeaderKeyPositionOffset
    LDA (RoomItemPointer),Y
    STA RoomMapUpdateIndex
    TAX
    LDA #EmptyRoomMapTile
    STA RoomMap,X
    STA RoomMapUpdateTile
    JSR BuildAndPublishRoomMapCellUpdate
    LDY #RoomHeaderKeyPositionOffset
    JSR AnimateKeyToDoorFromHeaderPosition
    LDX #KeyCollectionEnemyCount - 1

RestoreNextEnemyAfterKeyCollection:
    TXA
    JSR LoadEnemyObjectPointer
    LDY #ObjectCachedTypeOffset
    LDA (TempPointer00),Y
    LDY #ObjectStateOffset
    STA (TempPointer00),Y
    DEX
    BPL RestoreNextEnemyAfterKeyCollection

ResumeGameplayAfterKeyCollection:
    LDA #KeyCollectionDanaState
    STA DanaObject + ObjectStateOffset
    LDA FireballObject + ObjectCachedTypeOffset
    STA FireballObject + ObjectStateOffset
    LDA #MainGameplayThreadCode
; Starting code $30 in the current context replaces this stack and does not
; return into the physically adjacent key-flight entry
    JSR StartThread

.assert * - RunKeyCollectionPresentation = $6A, error, "key collection presentation size changed"

; Animate the collected key along a fixed-point arc to the room door

.segment "PRG_KEY_DOOR_ANIMATION"

KeyDoorDanaPositionOffset = $07
KeyFlightObjectTemplateSize = $06
KeyFlightMotionByteCount = $04
KeyFlightScratchSize = $08
KeyFlightDuration = $40
KeyFlightGravity = $08
KeyDoorOpeningPattern = $34
KeyDoorOpenPattern = RoomMapOpenDoorIdentity
KeyDoorOpenDelay = $06
KeyFlightPreviousFrame = $3E
KeyFlightMotionVector = RoomMap
KeyFlightMotionPointer = EnemyAiPointer
KeyFlightObjectPointer = EnemyObjectPointer

AnimateDoorUnlockFromDanaPosition:
    LDY #KeyDoorDanaPositionOffset

AnimateKeyToDoorFromHeaderPosition:
    LDA (RoomItemPointer),Y
    STA CoordinateY
    JSR ConvertMapIndexToPixelCoordinates
    LDA CoordinateY
    STA CoordinateOriginY
    STA AuxiliaryYPosition
    LDA CoordinateX
    STA CoordinateOriginX
    STA AuxiliaryXPosition
    LDY #RoomDoorPositionOffset
    LDA (RoomItemPointer),Y
    STA CoordinateTargetY

CopyKeyFlightObjectTemplate:
    LDA KeyFlightObjectTemplate,Y
    STA AuxiliaryObject,Y
    DEY
    BPL CopyKeyFlightObjectTemplate
    JSR ConvertMapIndexToPixelCoordinates
    JSR BuildScaledCoordinateDeltas
    DEC CoordinateOriginX
    LDX #KeyFlightMotionByteCount - 1

CopyKeyFlightMotionVector:
    LDA CoordinateOriginY,X
    STA KeyFlightMotionVector + 4,X
    DEX
    BPL CopyKeyFlightMotionVector
    INX
    STX GameplayUpdateCount

WaitForKeyFlightFrame:
    LDA GameplayUpdateCount
    CMP #KeyFlightDuration
    BCS FinishKeyFlight
    CMP KeyFlightPreviousFrame
    BEQ YieldKeyFlightThread
    STA KeyFlightPreviousFrame
    LDX #$03

CopyKeyFlightPointers:
    LDA KeyFlightPointers,X
    STA KeyFlightMotionPointer,X
    DEX
    BPL CopyKeyFlightPointers
    JSR AdvanceKeyFlightArc

YieldKeyFlightThread:
    JSR SwitchThreads
    BCS WaitForKeyFlightFrame

FinishKeyFlight:
    LDX #KeyFlightScratchSize - 1
    LDA #RoomMapImmutableTileMinimum

ClearKeyFlightScratch:
    STA KeyFlightMotionVector,X
    DEX
    BPL ClearKeyFlightScratch
    INX
    STX AuxiliaryObject + ObjectStateOffset
    STX GameplayUpdateCount
    LDA #KeyDoorOpeningPattern
    JSR PublishKeyDoorTile
    LDX #GameplayUpdateCount
    LDA #KeyDoorOpenDelay
    JSR WaitForZeroPageCounterAboveThreshold
    LDA #KeyDoorOpenPattern

PublishKeyDoorTile:
    STA RoomMapUpdateTile
    LDY #RoomDoorPositionOffset
    LDA (RoomItemPointer),Y
    STA RoomMapUpdateIndex
    JMP BuildAndPublishRoomMapCellUpdate

KeyFlightObjectTemplate:
    .byte $C2, $04, $FF, $0D, $FF, $C3

KeyFlightPointers:
    .addr KeyFlightMotionVector, AuxiliaryObject

AdvanceKeyFlightArc:
    LDY #$04
    LDA #KeyFlightGravity
    CLC
    ADC (KeyFlightMotionPointer),Y
    STA (KeyFlightMotionPointer),Y
    INY
    LDA #$00
    ADC (KeyFlightMotionPointer),Y
    STA (KeyFlightMotionPointer),Y

ApplyMotionVectorToObject:
    LDX #$00

ApplyNextMotionVectorWord:
    CLC
    JSR AddMotionVectorByteToObject
    JSR AddMotionVectorByteToObject
    CPX #KeyFlightMotionByteCount
    BNE ApplyNextMotionVectorWord
    RTS

AddMotionVectorByteToObject:
    LDY MotionVectorSourceOffsets,X
    LDA (KeyFlightMotionPointer),Y
    LDY MotionVectorDestinationOffsets,X
    ADC (KeyFlightObjectPointer),Y
    STA (KeyFlightObjectPointer),Y
    INX
    RTS

MotionVectorSourceOffsets:
    .byte $04, $05

MotionVectorDestinationOffsets:
    .byte $06, $07, $09, $0A

.assert * - AnimateDoorUnlockFromDanaPosition = $BE, error, "key-door animation size changed"
.assert KeyFlightPointers - KeyFlightObjectTemplate = KeyFlightObjectTemplateSize, error, "key-flight object template size changed"
.assert MotionVectorDestinationOffsets - MotionVectorSourceOffsets = 2, error, "motion offset tables must overlap"
