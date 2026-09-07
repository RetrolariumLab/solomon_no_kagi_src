; NMI-side Dana control-state selection and non-Dana sprite composition

.segment "PRG_NMI_DANA_AND_SPRITES"

DanaControlHandlerPointer = $0008
SpriteSortGap = $0008
SpritePreviousY = $0008
SpriteOverlapDepth = $0009
SpriteSortedPosition = $000A
SpriteOrderPosition = $000B
RemainingOamObjectSlots = $000C
ObjectSpriteFlags = $000F

SortedObjectYPositions = $0040
SortedObjectOrder = $0054
ScanlineObjectAllowance = $0068

DanaHeadCollisionRequest = $12
NonDanaObjectCount = ObjectRecordCount - 1
ObjectSpriteCount = 2
ObjectOamByteCount = ObjectSpriteCount * 4

UpdateDanaControlState:
    LDA DanaObject + ObjectStateOffset
    CMP #$C0
    BCC FinishDanaControlStateUpdate
    LDA DanaObject + ObjectActionOffset
    TAX
    LSR A
    LSR A
    CMP #DanaActionGroupCount
    BCS FinishDanaControlUpdate
    TAY
    LDA DanaControlHandlerLowBytes,Y
    STA DanaControlHandlerPointer
    LDA DanaControlHandlerHighBytes,Y
    STA DanaControlHandlerPointer + 1
    LDY Joypad1Cached
    TYA
    AND #$08
    BNE DispatchDanaControlHandler
    LDA #$FD
    AND GameplayFlags
    STA GameplayFlags

DispatchDanaControlHandler:
    LDA GameplayFrameCounters
    JMP (DanaControlHandlerPointer)

DanaControlHandlerLowBytes:
    .byte <HandleDanaActionGroup0, <HandleDanaActionGroup1
    .byte <HandleDanaActionGroup2, <FinishDanaControlUpdate
    .byte <HandleDanaActionGroup4, <HandleDanaActionGroup5
    .byte <HandleDanaActionGroup6

DanaControlHandlerHighBytes:
    .byte >HandleDanaActionGroup0, >HandleDanaActionGroup1
    .byte >HandleDanaActionGroup2, >FinishDanaControlUpdate
    .byte >HandleDanaActionGroup4, >HandleDanaActionGroup5
    .byte >HandleDanaActionGroup6

HandleDanaActionGroup0:
    CMP #$05
    BCS PromoteDanaActionGroup0

FinishDanaControlStateUpdate:
    RTS

PromoteDanaActionGroup0:
    TXA
    ORA #DanaJumpAscentActionBase
    JMP StoreDanaControlAction

HandleDanaActionGroup1:
    TXA
    LSR A
    LSR A
    LDA GameplayFrameCounters
    BCS UpdateDanaActionGroup1UpperPair
    BNE WaitForDanaActionGroup1
    LDA #DanaHeadCollisionRequest
    JSR QueuePendingThreadStart
    BPL FinishDanaControlUpdate

WaitForDanaActionGroup1:
    CMP #$09
    BCC FinishDanaControlUpdate
    LDA #$80
    STA DanaObject + ObjectYMotionOffset
    TXA
    AND #DanaActionPairMask
    ORA #DanaAirborneIdleActionBase
    JMP StoreDanaControlAction

UpdateDanaActionGroup1UpperPair:
    CMP #$09
    LDY #DanaWalkActionBase
    STY DanaControlHandlerPointer
    BCS SelectDanaActionFromPair
    LDA Joypad1Cached
    AND #$0F
    BEQ FinishDanaControlUpdate

SelectDanaActionFromPair:
    TXA
    AND #$03
    ORA DanaControlHandlerPointer
    JMP StoreDanaControlAction

FinishDanaControlUpdate:
    RTS

HandleDanaActionGroup2:
    CMP #$07
    BCC FinishDanaControlUpdate
    LDY #DanaAirborneIdleActionBase
    STY DanaControlHandlerPointer
    BNE SelectDanaActionFromPair

HandleDanaActionGroup4:
    TYA
    AND #$04
    BNE SelectDanaGroup4DownAction
    TXA
    ROR A
    LDA #(DanaWalkActionBase / 2)
    ROL A
    TAX
    STX DanaObject + ObjectActionOffset
    BNE HandleDanaActionGroup5

SelectDanaGroup4DownAction:
    TYA
    AND #$03
    BNE SelectDanaGroup4HorizontalAction
    LDY #DanaCrouchIdleActionBase

StoreDanaPairBase:
    STY DanaControlHandlerPointer
    BNE SelectDanaActionFromPair

SelectDanaGroup4HorizontalAction:
    INY
    TYA
    AND #$01
    TAX
    LDY #DanaCrouchMoveActionBase
    BNE StoreDanaPairBase

HandleDanaActionGroup5:
    TYA
    AND #$0F
    TAY
    BNE SelectDanaActionGroup5Input

SelectDanaIdleAction:
    TXA
    ORA #DanaActionIdleBit
    BNE StoreDanaControlAction

SelectDanaActionGroup5Input:
    AND #$08
    BEQ SelectDanaActionGroup5Direction
    LDA #$02
    BIT GameplayFlags
    BNE SelectDanaActionGroup5Direction
    ORA GameplayFlags
    STA GameplayFlags
    LDA #$00
    STA GameplayFrameCounters
    TXA
    AND #DanaFacingMask
    JMP StoreDanaControlAction

SelectDanaActionGroup5Direction:
    TYA
    CMP #$04
    BNE SelectDanaActionGroup5Horizontal
    TXA
    AND #DanaActionPairMask
    ORA #DanaCrouchMoveActionBase
    BNE StoreDanaControlAction

SelectDanaActionGroup5Horizontal:
    TYA
    AND #$03
    BEQ SelectDanaIdleAction
    INY
    TYA
    AND #DanaFacingMask
    ORA #DanaWalkActionBase
    BNE StoreDanaControlAction

HandleDanaActionGroup6:
    TYA
    AND #$03
    BNE UpdateDanaActionGroup6Horizontal
    TXA
    ORA #$02
    BNE StoreDanaControlAction

UpdateDanaActionGroup6Horizontal:
    LDA GameplayFrameCounters
    CMP #$08
    BCC SelectDanaActionGroup6Direction
    LDA #$00
    STA GameplayFrameCounters
    STA DanaObject + ObjectCachedActionOffset

SelectDanaActionGroup6Direction:
    INY
    TYA
    AND #DanaFacingMask
    ORA #DanaAirborneMoveActionBase

StoreDanaControlAction:
    STA DanaObject + ObjectActionOffset
    RTS

RenderGameplayObjectsToOam:
    LDX #NonDanaObjectCount - 1
    LDY #ObjectYPositionOffset

LoadObjectSpriteSortKeys:
    LDA NonDanaObjectPointerLowTable,X
    STA TempPointer08
    LDA NonDanaObjectPointerHighTable,X
    STA TempPointer08 + 1
    LDA (TempPointer08),Y
    STA SortedObjectYPositions,X
    TXA
    ASL A
    STA SortedObjectOrder,X
    DEX
    BPL LoadObjectSpriteSortKeys
    LDA #$0A
    STA SpriteSortGap

RunObjectSpriteShellSortPass:
    LDX #$00
    LDY SpriteSortGap

CompareObjectSpriteSortKeys:
    LDA SortedObjectYPositions,Y
    CMP SortedObjectYPositions,X
    BCS AdvanceObjectSpriteSortPair
    STA SpriteOverlapDepth
    LDA SortedObjectYPositions,X
    STA SortedObjectYPositions,Y
    LDA SpriteOverlapDepth
    STA SortedObjectYPositions,X
    LDA SortedObjectOrder,Y
    STA SpriteOverlapDepth
    LDA SortedObjectOrder,X
    STA SortedObjectOrder,Y
    LDA SpriteOverlapDepth
    STA SortedObjectOrder,X
    TXA
    SEC
    SBC SpriteSortGap
    BCS ContinueObjectSpriteInsertion
    LDA #$00

ContinueObjectSpriteInsertion:
    TAX
    CLC
    ADC SpriteSortGap
    TAY
    BCC CompareObjectSpriteSortKeys

AdvanceObjectSpriteSortPair:
    INY
    INX
    CPY #NonDanaObjectCount
    BNE CompareObjectSpriteSortKeys
    DEC SpriteSortGap
    BNE RunObjectSpriteShellSortPass
    LDX #NonDanaObjectCount - 2
    LDY #$00
    LDA SortedObjectYPositions + NonDanaObjectCount - 1
    STA SpritePreviousY

MarkObjectSpriteOverlapGroups:
    SEC
    LDA SortedObjectYPositions + 1,X
    SBC SortedObjectYPositions,X
    CMP #$10
    BCC KeepObjectInSpriteOverlapGroup
    JSR UpdateScanlineObjectAllowance

KeepObjectInSpriteOverlapGroup:
    ROR SortedObjectOrder + 1,X
    DEY
    DEX
    BPL MarkObjectSpriteOverlapGroups
    JSR UpdateScanlineObjectAllowance
    ROR SortedObjectOrder
    LDX #NonDanaObjectCount
    STX RemainingOamObjectSlots
    DEX
    BNE SelectNextObjectForOam

MarkObjectOrderEntry:
    ROR A
    STA SortedObjectOrder,X
    LDX SpriteSortedPosition

FindPreviousSpriteOverlapGroup:
    LDA SortedObjectOrder,X
    BMI FinishPreviousSpriteOverlapGroup
    DEX
    BPL FindPreviousSpriteOverlapGroup

FinishPreviousSpriteOverlapGroup:
    DEX
    BPL SelectNextObjectForOam
    LDA #<DanaObject
    STA TempPointer08
    LDA #>DanaObject
    STA TempPointer08 + 1
    LDX #$00
    BEQ WriteObjectSpritesToOam

SelectNextObjectForOam:
    STX SpriteSortedPosition
    LDA SortedObjectYPositions,X
    LSR A
    LSR A
    LSR A
    LSR A
    TAX
    LDY ScanlineObjectAllowance,X
    TYA
    CLC
    ADC #$FD
    STA ScanlineObjectAllowance,X
    TYA
    CLC
    ADC SpriteSortedPosition
    TAX
    STA SpriteOrderPosition
    LDA #$40
    LDY SortedObjectOrder,X
    BPL MarkSelectedObjectOrderEntry
    LDA #$C0

MarkSelectedObjectOrderEntry:
    STA SortedObjectOrder,X
    TYA
    BMI FollowMarkedObjectOrderEntry
    BPL LoadSelectedObjectPointer

FindPreviousObjectOrderEntry:
    DEC SpriteOrderPosition
    LDX SpriteOrderPosition
    LDA SortedObjectOrder,X
    CMP #$40
    TAY
    BCC LoadSelectedObjectPointer

FollowMarkedObjectOrderEntry:
    ASL A
    BMI MarkObjectOrderEntry
    LSR A
    TAY
    LDX SpriteSortedPosition
    INX
    STX SpriteOrderPosition

LoadSelectedObjectPointer:
    LDA NonDanaObjectPointerLowTable,Y
    STA TempPointer08
    LDA NonDanaObjectPointerHighTable,Y
    STA TempPointer08 + 1
    LDA RemainingOamObjectSlots
    ASL A
    ASL A
    ASL A
    TAX

WriteObjectSpritesToOam:
    LDY #ObjectStateOffset
    LDA (TempPointer08),Y
    ASL A
    BCC HideObjectSprites
    LDY #ObjectYPositionOffset
    LDA (TempPointer08),Y
    STA OamBuffer,X
    STA OamBuffer + 4,X
    LDY #ObjectXPositionOffset
    LDA (TempPointer08),Y
    STA OamBuffer + 3,X
    CLC
    ADC #ObjectOamByteCount
    STA OamBuffer + 7,X
    LDY #ObjectSpriteTile1Offset
    LDA (TempPointer08),Y
    STA OamBuffer + 1,X
    INY
    LDA (TempPointer08),Y
    STA OamBuffer + 5,X
    INY
    LDA (TempPointer08),Y
    STA ObjectSpriteFlags
    ROL A
    ROL A
    AND #$C1
    BCC StoreLeftObjectSpriteAttributes
    ORA #$02

StoreLeftObjectSpriteAttributes:
    STA OamBuffer + 2,X
    LDA ObjectSpriteFlags
    ROR A
    ROR A
    AND #$83
    BCC StoreRightObjectSpriteAttributes
    ORA #$40

StoreRightObjectSpriteAttributes:
    STA OamBuffer + 6,X
    JMP AdvanceObjectOamSlot

HideObjectSprites:
    LDA #$F8
    STA OamBuffer,X
    STA OamBuffer + 4,X

AdvanceObjectOamSlot:
    DEC RemainingOamObjectSlots
    BPL FindPreviousObjectOrderEntry
    RTS

; Y tracks overlap depth. Each screen row retains an allowance used to
; distribute two-sprite objects without exceeding the scanline budget
UpdateScanlineObjectAllowance:
    LDA SpritePreviousY
    LSR A
    LSR A
    LSR A
    LSR A
    STY SpriteOverlapDepth
    DEY
    CPY #$FD
    TAY
    LDA SortedObjectYPositions,X
    STA SpritePreviousY
    LDA #$00
    BCS StoreScanlineObjectAllowance
    LDA ScanlineObjectAllowance,Y
    BEQ FinishScanlineObjectAllowance
    CMP SpriteOverlapDepth
    BCS FinishScanlineObjectAllowance
    DEC SpriteOverlapDepth

ReduceScanlineObjectAllowance:
    SEC
    SBC SpriteOverlapDepth
    BEQ StoreScanlineObjectAllowance
    CMP SpriteOverlapDepth
    BCC ReduceScanlineObjectAllowance

StoreScanlineObjectAllowance:
    STA ScanlineObjectAllowance,Y

FinishScanlineObjectAllowance:
    LDY #$01
    SEC
    RTS
