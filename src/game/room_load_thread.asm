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
