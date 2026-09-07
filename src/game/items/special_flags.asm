; Flag-only handlers for item types $16-$1C

.segment "PRG_SPECIAL_ITEM_FLAGS"

GoldenWingsRoomSkipFlag = $40
PageOfTimeEndingFlag = $40
PageOfSpaceEndingFlag = $80
PageOfSpaceRoomThreshold = $1E
ConstellationCollectedFlag = $08

ApplyGoldenWingsItem:
    LDA #GoldenWingsRoomSkipFlag
    ORA GameplayFlags
    STA GameplayFlags
    RTS

ApplySolomonPageItem:
    LDA CurrentRoomIndex
    CMP #PageOfSpaceRoomThreshold
    LDA #PageOfTimeEndingFlag
    BCC StoreSolomonPageEndingFlag
    ASL A

StoreSolomonPageEndingFlag:
    ORA GameStateFlags
    STA GameStateFlags
    RTS

ApplySolomonSealItem:
    INC SolomonSealCount
    LDA CollectedSolomonSealFlags
    ORA CurrentRoomSolomonSealFlag
    STA CollectedSolomonSealFlags
    RTS

ApplyConstellationSymbolItem:
    LDA GameStateFlags
    ORA #ConstellationCollectedFlag
    STA GameStateFlags
    RTS
