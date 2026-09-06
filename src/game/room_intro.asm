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
