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

; Convert the remaining decimal timer to score in chunks of eight

.segment "PRG_ROOM_TIME_BONUS"

SubtractTimerBy8:
    LDA TimerDigit10
    SEC
    SBC #$08
    LDY #$04
    LDX #$00
    BEQ PropagateTimerBonusBorrow

SubtractTimerBonusDigits:
    LDA TimerDigit10,X
    SBC #$00

PropagateTimerBonusBorrow:
    BCS StoreTimerBonusDigit
    ADC #$0A
    CLC

StoreTimerBonusDigit:
    STA TimerDigit10,X
    INX
    DEY
    BNE SubtractTimerBonusDigits
    BCS AddFullTimerBonusChunk
    LDA TimerDigit10
    SBC #$01
    TAX
    TYA
    LDY #$03

ClearExhaustedTimerDigits:
    STA TimerDigit10,Y
    DEY
    BPL ClearExhaustedTimerDigits
    TXA
    LDX #$06
    JMP AddTimerBonusChunkToScore

AddFullTimerBonusChunk:
    LDX #$06
    LDA #$08
    JSR AddTimerBonusChunkToScore
    BNE SubtractTimerBy8

AddTimerBonusChunkToScore:
    JSR AddScoreByAAtDigitX
    JSR BuildScoreDisplayUpdate
    LDA #$24
    STA PpuUpdateBuffer + $0B
    CLC
    LDX #$03
    LDY #$00
    STY PpuUpdateBuffer + $10
    STY PpuUpdateBuffer + $11

CopyTimerBonusDisplayDigits:
    LDA TimerDigit10,X
    BNE MarkNonzeroTimerBonusDigit
    BCS StoreTimerBonusDisplayDigit
    LDA #$24
    BPL StoreTimerBonusDisplayDigit

MarkNonzeroTimerBonusDigit:
    SEC

StoreTimerBonusDisplayDigit:
    STA PpuUpdateBuffer + $0C,Y
    INY
    DEX
    BPL CopyTimerBonusDisplayDigits
    LDA #$4D
    STA PpuUpdateBuffer + $02
    JMP PublishPpuUpdateBuffer

; Context-one new-game and room-transition loading pipeline

.segment "PRG_ROOM_LOAD_THREAD"

SpecialRoomSelectorMask = $30
PageOfTimeRoomSelector = $10
PageOfSpaceRoomSelector = $20
ConstellationBonusRoomSelector = $30
ConstellationBonusRoomIndex = $32
PageOfTimeRoomIndex = $33
PageOfSpaceRoomIndex = $34

.assert PageOfTimeRoomIndex = ConstellationBonusRoomIndex + 1, error, "unexpected Page of Time room index"
.assert PageOfSpaceRoomIndex = PageOfTimeRoomIndex + 1, error, "unexpected Page of Space room index"

NewGameRoomLoadThread:
    JSR ResetNewGameState

RoomLoadThread:
    LDA #$FD
    AND RoomStateFlags
    STA RoomStateFlags
    JSR DrawRoomNametableFrame
    LDA #SpecialRoomSelectorMask
    AND GameStateFlags
    BEQ LoadSelectedRoom
    LDX CurrentRoomIndex
    STX SpecialRoomSourceIndex
    LDX #ConstellationBonusRoomIndex
    CMP #ConstellationBonusRoomSelector
    BEQ StoreSpecialRoomIndex
    CMP #PageOfSpaceRoomSelector
    BCC AdvanceSpecialRoomIndex
    INX

AdvanceSpecialRoomIndex:
    INX

StoreSpecialRoomIndex:
    STX CurrentRoomIndex

LoadSelectedRoom:
    JSR InitializeRoomBlockMap
    LDA #$60
    JSR StartThread
    LDA #$00
    STA $7E
    STA $7F
    JSR QueueStaticPpuUpdateStream
    LDA #$01
    JSR QueueStaticPpuUpdateStream
    JSR RefreshGameplayHud
    JSR PrepareRoomIntro
    JSR ResetAndSelectGameplayDelayCounter
    LDA #$80
    JSR WaitForZeroPageCounterAboveThreshold
    LDA #$00
    STA MagicSparkObject + ObjectStateOffset
    JSR Clear30x24NametableRegion
    JSR LoadRoomItemsAndMetadata
    LDA #$02
    ORA RoomStateFlags
    STA RoomStateFlags
    JSR PublishRoomDoorAndKeyUpdates
    JSR ResetAndSelectGameplayDelayCounter
    LDA #$40
    JSR WaitForZeroPageCounterAboveThreshold
    JSR RunRoomEntryAnimation
    LDA #$20
    AND GameplayFlags
    BEQ LoadRoomEnemyStream
    JSR AnimateDoorUnlockFromDanaPosition

LoadRoomEnemyStream:
    JSR LoadRoomEnemies
    LDA #$AF
    AND GameplayFlags
    STA GameplayFlags
    JSR DrawRoomMapToNametable

WaitForRoomMapTransfer:
    LDA PpuUpdateStreamPointer + 1
    BNE WaitForRoomMapTransfer
    LDX #$12

CopyRoomPaletteTemplate:
    LDA RoomLoadPaletteTemplate,X
    STA PpuUpdateBuffer,X
    DEX
    BPL CopyRoomPaletteTemplate
    LDX CurrentRoomIndex
    LDA #SpecialRoomSelectorMask
    AND GameStateFlags
    BEQ SelectRoomPaletteGroup
    LDY SpecialRoomSourceIndex
    STY CurrentRoomIndex
    DEY
    CMP #$30
    BNE SelectRoomPaletteGroup
    TYA
    TAX

SelectRoomPaletteGroup:
    TXA
    LSR A
    LSR A
    TAX
    LDA RoomPaletteColorByRoomGroup,X
    BPL ApplyRoomPaletteColor
    LDA #$16
    STA PpuUpdateBuffer + $0D
    LDA #$00

ApplyRoomPaletteColor:
    LDX #$03

ApplyRoomPaletteColorCopies:
    LDY RoomPaletteColorOffsets,X
    STA PpuUpdateBuffer + $03,Y
    DEX
    BPL ApplyRoomPaletteColorCopies
    INX
    STX PpuUpdateBuffer + $13
    LDA #$4F
    STA PpuUpdateBuffer + $02
    JSR PublishPpuUpdateBuffer
    LDA #$C7
    AND GameStateFlags
    STA GameStateFlags
    LDA DanaXPosition
    ROL A
    LDA #(DanaWalkActionBase / 2)
    ROL A
    LDY #ObjectActionOffset

InitializeDanaForLoadedRoom:
    STA DanaObject,Y
    LDA RoomLoadDanaHeaderPredecessors,Y
    DEY
    BPL InitializeDanaForLoadedRoom
    INY
    STY MagicSparkObject + ObjectStateOffset
    LDA GameStateFlags
    ROR A
    BCC StartLoadedRoomGameplay
    INY
    LDA FireballState
    BEQ SelectRoomEntrySound
    INY

SelectRoomEntrySound:
    JSR AddSoundEffect

StartLoadedRoomGameplay:
    LDA #$30
    JSR StartThread
    LDA #$01
    JSR StopThread

; Publish the current room's initial door and optional key map cells

.segment "PRG_ROOM_DOOR_KEY_UPDATE"

RoomHeaderFlagsOffset = $04
RoomHeaderDoorPositionOffset = $05
RoomHeaderKeyPositionOffset = $06

PublishRoomDoorAndKeyUpdates:
    LDY #RoomHeaderDoorPositionOffset
    LDA (RoomItemPointer),Y
    BEQ FinishRoomDoorAndKeyUpdates
    STA RoomMapUpdateIndex
    LDX #RoomMapClosedDoorIdentity
    INY
    LDA (RoomItemPointer),Y
    BNE PublishInitialDoorCell
    LDX #RoomMapDeferredDoorIdentity

PublishInitialDoorCell:
    STX RoomMapUpdateTile
    JSR BuildAndPublishRoomMapCellUpdate
    LDA #$20
    AND GameplayFlags
    BNE FinishRoomDoorAndKeyUpdates
    LDY #RoomHeaderFlagsOffset
    LDA #$C0
    AND (RoomItemPointer),Y
    BNE FinishRoomDoorAndKeyUpdates
    LDY #RoomHeaderKeyPositionOffset
    LDA (RoomItemPointer),Y
    STA RoomMapUpdateIndex
    LDA #RoomMapKeyIdentity
    STA RoomMapUpdateTile
    JMP BuildAndPublishRoomMapCellUpdate

FinishRoomDoorAndKeyUpdates:
    RTS

; Build room-number/lives UI, special-room text, marker, and intro spark

.segment "PRG_ROOM_INTRO"

PrepareRoomIntro:
    LDA #$FF
    LDX #$1B
    JSR WaitForMaskedBitsClear
    LDX #$1A

CopyRoomIntroPpuTemplate:
    LDA RoomIntroPpuTemplate,X
    STA PpuUpdateBuffer,X
    DEX
    BPL CopyRoomIntroPpuTemplate
    LDX CurrentRoomIndex
    INX
    JSR FormatTwoDigitNumberTiles
    STA PpuUpdateBuffer + $13
    STX PpuUpdateBuffer + $12
    LDX RemainingLives
    JSR FormatTwoDigitNumberTiles
    STA PpuUpdateBuffer + $19
    STX PpuUpdateBuffer + $18
    JSR PublishPpuUpdateBuffer
    LDA CurrentRoomIndex
    CMP #$30
    BCC SelectRoomIntroMarker
    SBC #$30
    ASL A
    ASL A
    ASL A
    CMP #$10
    BCC CopySpecialRoomName
    LDA #$10

CopySpecialRoomName:
    LDY #$00
    TAX

CopySpecialRoomNameTile:
    LDA SpecialRoomNameTiles,X
    STA PpuUpdateBuffer + $0C,Y
    INX
    INY
    CPY #$08
    BNE CopySpecialRoomNameTile
    LDX FireballState
    BNE UseSavedRoomIntroMarker
    LDX CurrentRoomIndex
    INX

UseSavedRoomIntroMarker:
    DEX
    TXA

SelectRoomIntroMarker:
    AND #$3C
    LSR A
    LSR A
    PHA
    AND #$03
    ADC #$1C
    STA RoomMapUpdateTile
    LDA #$49
    STA RoomMapUpdateIndex
    JSR BuildAndPublishRoomMapCellUpdate
    PLA
    LSR A
    LSR A
    STA ChrBankRequest
    LDA #$94
    STA MagicSparkObject + ObjectYPositionOffset
    LDA #$70
    STA MagicSparkObject + ObjectXPositionOffset
    LDX #$03

InitializeRoomIntroSpark:
    LDA RoomIntroSparkHeader,X
    STA MagicSparkObject,X
    DEX
    BPL InitializeRoomIntroSpark
    RTS

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

; Gameplay-exit presentation data and shared room-transition reset

.segment "PRG_GAMEPLAY_EXIT_DATA"

LifeLossPpuMaskCycle:
    .byte $00, $21, $00, $81

; Static PPU program displaying "TIME OVER."
TimeOverPpuUpdateStream:
    .byte $21, $EA, $48
    .byte $1D, $12, $16, $0E, $24, $18, $1F, $0E, $1B, $23
    .byte $DA, $42, $C0, $F0, $F0, $00

; Copied to PpuUpdateBuffer and patched with the calculated result value
PostGameResultPpuTemplate:
    .byte $21, $E9, $4A
    .byte $22, $18, $1E, $1B, $24, $10, $0D, $1F, $24, $24, $24
    .byte $00

.assert * - LifeLossPpuMaskCycle = $26, error, "unexpected gameplay-exit data size"

.segment "PRG_ROOM_TRANSITION_RESET"

RoomTransitionWorkerContext = $03
RoomTransitionGameplayFlagsMask = $BB
RoomTransitionSoundEffect = $03

ResetRoomTransitionState:
    LDX #RoomTransitionWorkerContext
    JSR ResetOtherSecondaryThreads
    LDA GameplayFlags
    AND #RoomTransitionGameplayFlagsMask
    STA GameplayFlags
    LDA #$00
    STA FireballActive
    LDY #RoomTransitionSoundEffect
    JSR AddSoundEffect
    RTS
