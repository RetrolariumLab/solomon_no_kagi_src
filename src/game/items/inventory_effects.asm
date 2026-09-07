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
