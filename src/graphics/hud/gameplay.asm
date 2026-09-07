; Coordinate score, fireball-inventory, and fairy-count HUD updates

.segment "PRG_GAMEPLAY_HUD"

RefreshGameplayHud:
    JSR BuildScoreDisplayUpdate
    JSR PublishPpuUpdateBuffer
    JSR BuildFireballInventoryDisplayUpdate
    JMP BuildAndPublishFairyCountDisplay

WaitForPpuUpdateStreamIdle:
    LDA #$FF
    LDX #PpuUpdateStreamPointer + 1
    JMP WaitForMaskedBitsClear

BuildAndPublishFairyCountDisplay:
    JSR WaitForPpuUpdateStreamIdle
    LDX #$04

CopyFairyCountDisplayTemplate:
    LDA FairyCountDisplayPpuUpdateTemplate,X
    STA PpuUpdateBuffer,X
    DEX
    BPL CopyFairyCountDisplayTemplate
    LDA FairiesCollected
    STA PpuUpdateBuffer + 3
    JMP PublishPpuUpdateBuffer
