; Build the two-row HUD update for packed fireball inventory slots

.segment "PRG_FIREBALL_INVENTORY_DISPLAY"

FireballInventoryFieldWidth = 10
FireballInventoryLeftCapTile = $A5
FireballInventoryBlankTile = $24
FireballInventoryTopUnusedTile = $B4
FireballInventoryBottomFillTile = $B7
FireballInventoryPpuAddressHigh = $20

BuildFireballInventoryDisplayUpdate:
    LDA #$FF
    LDX #PpuUpdateStreamPointer + 1
    JSR WaitForMaskedBitsClear
    LDA #<PpuUpdateBuffer
    STA TempPointer00
    LDA #>PpuUpdateBuffer
    STA TempPointer00 + 1
    LDY #$00
    LDA InventorySlotsHigh
    STA $04
    LDA InventorySlotsLow
    STA $05
    LDX #$02

CopyFireballInventoryTopRowHeader:
    LDA FireballInventoryTopRowHeaderReversed,X
    STA (TempPointer00),Y
    INY
    DEX
    BPL CopyFireballInventoryTopRowHeader
    LDA InventorySlotCount
    STA $02
    LDA #FireballInventoryFieldWidth
    STA $03
    LDA #FireballInventoryLeftCapTile

BuildFireballInventoryTopRow:
    STA (TempPointer00),Y
    INY
    ASL $04
    ROL $05
    ROL A
    ASL $04
    ROL $05
    ROL A
    AND #$03
    BEQ FillUnusedFireballInventorySlots
    DEC $02
    DEC $03
    TAX
    LDA FireballInventoryTopTileByValue,X
    BNE BuildFireballInventoryTopRow

FillUnusedFireballInventorySlots:
    LDA #FireballInventoryTopUnusedTile

FillNextUnusedFireballInventorySlot:
    STA (TempPointer00),Y
    INY
    DEC $03
    DEC $02
    BPL FillNextUnusedFireballInventorySlot
    LDA #FireballInventoryBlankTile

BlankRemainingFireballInventoryCells:
    STA (TempPointer00),Y
    INY
    DEC $03
    BNE BlankRemainingFireballInventoryCells
    LDX #$02

CopyFireballInventoryBottomRowHeader:
    LDA FireballInventoryBottomRowHeaderReversed,X
    STA (TempPointer00),Y
    INY
    DEX
    BPL CopyFireballInventoryBottomRowHeader
    INX

BuildFireballInventoryBottomRow:
    LDA FireballInventoryTopRowTiles,X
    BPL FillFireballInventoryBottomRowTail
    INX
    CLC
    ADC #$02
    STA (TempPointer00),Y
    INY
    BNE BuildFireballInventoryBottomRow

FillFireballInventoryBottomRowTail:
    DEY
    LDA #FireballInventoryBottomFillTile

FillNextFireballInventoryBottomCell:
    STA (TempPointer00),Y
    INY
    LDA FireballInventoryTopRowTiles,X
    INX
    CMP #FireballInventoryPpuAddressHigh
    BNE FillNextFireballInventoryBottomCell
    LDA #$00
    STA (TempPointer00),Y
    JMP PublishPpuUpdateBuffer
