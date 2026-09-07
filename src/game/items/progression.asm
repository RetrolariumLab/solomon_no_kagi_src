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

; Inventory, fairy, fireball-lifetime, and score item handlers

.segment "PRG_INVENTORY_ITEM_EFFECTS"

InventorySlotLimit = $08
InventorySlotsPerByte = $04
FirstInventorySlotMask = $C0
SmallFireballSlotPattern = $55
LargeFireballSlotPattern = $AA
FireballLifetimeCapHigh = $02

IncreaseInventorySlotLimit:
    LDA InventorySlotCount
    CMP #InventorySlotLimit
    BCS FinishInventorySlotLimitIncrease
    INC InventorySlotCount

FinishInventorySlotLimitIncrease:
    RTS

ApplySmallFireballBottleItem:
    LDA #SmallFireballSlotPattern
    STA InventoryItemSlotPattern
    JMP AddItemToScroll

QueueFairyItem:
    INC FairiesQueued
    RTS

ApplyLargeFireballBottleItem:
    LDA #LargeFireballSlotPattern
    STA InventoryItemSlotPattern
    JMP AddItemToScroll

ApplyBlueTzoItem:
    LDA #$02
    LDX #$05
    JSR AddScoreByAAtDigitX
    LDA #$04
    BPL ExtendFireballLifetime

ApplyRedTzoItem:
    LDA #$10

ExtendFireballLifetime:
    LDX FireballLifetimeHi
    CPX #FireballLifetimeCapHigh
    BCS FinishFireballLifetimeExtension
    ADC FireballLifetimeLo
    STA FireballLifetimeLo
    BCC FinishFireballLifetimeExtension
    INC FireballLifetimeHi

FinishFireballLifetimeExtension:
    RTS

AddItemToScroll:
    LDA InventorySlotCount
    STA RemainingInventorySlots
    LDX #$01

ScanNextInventoryByte:
    LDA #FirstInventorySlotMask
    STA InventorySlotMask
    LDY #InventorySlotsPerByte

ScanNextInventorySlot:
    LDA InventorySlotMask
    AND InventorySlotsHigh,X
    BEQ StoreItemInInventorySlot
    DEC RemainingInventorySlots
    BEQ InventoryCapacityReached
    LSR InventorySlotMask
    LSR InventorySlotMask
    DEY
    BNE ScanNextInventorySlot
    DEX
    BPL ScanNextInventoryByte

InventoryCapacityReached:
    RTS

StoreItemInInventorySlot:
    LDA InventorySlotMask
    AND InventoryItemSlotPattern
    ORA InventorySlotsHigh,X
    STA InventorySlotsHigh,X
    RTS

AwardBlueCrystalScore:
    LDX #$05
    TXA

AwardItemScoreAndReturn:
    JSR AddScoreByAAtDigitX
    RTS

AwardType04Or06Score:
    LDX #$04
    LDA #$02
    BNE AwardItemScoreAndReturn

; Expire the active fireball and retire its object after the grace counter

.segment "PRG_FIREBALL_LIFETIME"

UpdateFireballLifetime:
    LDA FireballObject
    BPL FinishFireballLifetimeUpdate

CheckActiveFireballLifetime:
    LDA FireballActive
    BEQ CheckInactiveFireballCleanup
    SEC
    LDA FireballLifetimeLo
    SBC FireballLifeCounter1Lo
    LDA FireballLifetimeHi
    SBC FireballLifeCounter1Hi
    BCS FinishFireballLifetimeUpdate
    LDA #$00
    STA FireballActive
    STA FireballLifeCounter1Lo
    LDX #$04
    STX FireballObject + $03
    BNE FinishFireballLifetimeUpdate

CheckInactiveFireballCleanup:
    LDX FireballLifeCounter1Lo
    CPX #$08
    BCC FinishFireballLifetimeUpdate
    STA FireballObject

FinishFireballLifetimeUpdate:
    RTS
