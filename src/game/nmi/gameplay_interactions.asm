; NMI-side Dana/enemy interactions, fireball collision, and action requests

.segment "PRG_NMI_GAMEPLAY_INTERACTIONS"

EnemyScanIndex = $000A
EnemyCollisionFound = $000B
CollisionTargetY = $000C
CollisionTargetX = $000D
FireballPreviousCollisionMask = $000E
FireballCurrentCollisionMask = $000F

DanaActionRequestBlockMagic = $11
DanaActionRequestFireball = $13
DanaEnemyCollisionThreadCode = $31
FireballEnemyCollisionThreadCode = $50

TryStartFireballAction:
    LDA #DanaActionRequestFireball
    STA TempPointer08
    JSR TryStartDanaAction

FinishNmiGameplayInteraction:
    RTS

CheckGameplayObjectInteractions:
    LDA GameplayFlags
    EOR #$80
    STA GameplayFlags
    BPL FinishNmiGameplayInteraction
    AND #$10
    BNE FinishNmiGameplayInteraction
    LDA DanaObject + ObjectStateOffset
    CMP #$C0
    BCC FinishNmiGameplayInteraction
    LDA FireballObject + ObjectStateOffset
    CMP #$C0
    BCC BeginDanaEnemyCollisionScan
    LDA #EnemyObjectCount - 1
    STA EnemyScanIndex
    LDX FireballObject + ObjectYPositionOffset
    DEX
    DEX
    STX CollisionTargetY
    LDX FireballObject + ObjectXPositionOffset
    DEX
    STX CollisionTargetX
    LDX #$00
    STX EnemyCollisionFound

CheckNextEnemyForFireballCollision:
    LDX EnemyScanIndex
    LDA EnemyObjectPointerLowTable,X
    STA TempPointer08
    LDA EnemyObjectPointerHighTable,X
    STA TempPointer08 + 1
    LDX #$00
    JSR CheckEnemyOverlapAtCoordinates
    BCS AdvanceFireballEnemyCollisionScan
    STY EnemyCollisionFound
    LDY #ObjectStateOffset
    LDA #$01
    ORA (TempPointer08),Y
    STA (TempPointer08),Y
    LDA FireballObject + ObjectTypeOffset
    CMP #$10
    BCS AdvanceFireballEnemyCollisionScan
    STA FireballLifeCounter1Hi

AdvanceFireballEnemyCollisionScan:
    DEC EnemyScanIndex
    BPL CheckNextEnemyForFireballCollision
    LDA EnemyCollisionFound
    BEQ BeginDanaEnemyCollisionScan
    LDA #FireballEnemyCollisionThreadCode
    JSR QueuePendingThreadStart

BeginDanaEnemyCollisionScan:
    LDA #EnemyObjectCount - 1
    STA EnemyScanIndex
    LDA DanaYPosition
    SEC
    SBC #$05
    STA CollisionTargetY
    LDX DanaObject + ObjectActionOffset
    CPX #DanaCastActionBase
    LDA #$00
    BCC StoreDanaCollisionX
    TXA
    ROR A
    LDA #$03
    BCS StoreDanaCollisionX
    LDA #$FC

StoreDanaCollisionX:
    ADC DanaXPosition
    STA CollisionTargetX

CheckNextEnemyForDanaCollision:
    LDX EnemyScanIndex
    LDA EnemyObjectPointerLowTable,X
    STA TempPointer08
    LDA EnemyObjectPointerHighTable,X
    STA TempPointer08 + 1
    LDX #$01
    JSR CheckEnemyOverlapAtCoordinates
    BCS AdvanceDanaEnemyCollisionScan
    LDA #$10
    ORA GameplayFlags
    STA GameplayFlags
    LDA #DanaEnemyCollisionThreadCode
    JSR QueuePendingThreadStart
    BPL FinishEnemyCollisionScan

AdvanceDanaEnemyCollisionScan:
    DEC EnemyScanIndex
    BPL CheckNextEnemyForDanaCollision

FinishEnemyCollisionScan:
    RTS

; X selects fireball (0) or Dana (1) extents and excluded state bits
; Carry is clear only when the selected enemy overlaps the target rectangle
CheckEnemyOverlapAtCoordinates:
    SEC
    LDY #ObjectStateOffset
    LDA (TempPointer08),Y
    BPL FinishEnemyOverlapCheck
    AND EnemyOverlapExcludedStateBits,X
    BNE FinishEnemyOverlapCheck
    LDY #ObjectYPositionOffset
    LDA (TempPointer08),Y
    SBC CollisionTargetY
    ADC #$06
    CMP EnemyOverlapHeight,X
    BCS FinishEnemyOverlapCheck
    LDY #ObjectXPositionOffset
    LDA (TempPointer08),Y
    SEC
    SBC CollisionTargetX
    ADC #$05
    CMP EnemyOverlapWidth,X

FinishEnemyOverlapCheck:
    RTS

EnemyOverlapHeight:
    .byte $0F, $13

EnemyOverlapWidth:
    .byte $0E, $0D

EnemyOverlapExcludedStateBits:
    .byte $05, $03

UpdateActiveFireballCollision:
    LDA FireballActive
    BPL FinishActiveFireballCollision
    LDA FireballObject + ObjectStateOffset
    CMP #$C0
    BCC FinishActiveFireballCollision
    LDX #$03
    LDA #$00

ClearFireballCollisionCoordinates:
    STA TempPointer08,X
    DEX
    BPL ClearFireballCollisionCoordinates
    LDY FireballDirectionIndex
    STY FireballObject + ObjectActionOffset
    LDA FireballCollisionYDelta,Y
    STA TempPointer0A
    LDA FireballCollisionXDelta,Y
    STA TempPointer0A + 1
    LDA FireballObject + ObjectYFractionOffset
    CLC
    ADC TempPointer08
    STA FireballObject + ObjectYFractionOffset
    LDA FireballObject + ObjectYPositionOffset
    STA TempPointer08
    ADC TempPointer0A
    STA TempPointer0A
    LDA FireballObject + ObjectXFractionOffset
    ADC TempPointer08 + 1
    STA FireballObject + ObjectXFractionOffset
    LDA FireballObject + ObjectXPositionOffset
    STA TempPointer08 + 1
    ADC TempPointer0A + 1
    STA TempPointer0A + 1
    JSR BuildFireballRoomCollisionMask
    LDA TempPointer08 + 1
    STA FireballPreviousCollisionMask
    LDA TempPointer0A
    STA TempPointer08
    LDA TempPointer0A + 1
    STA TempPointer08 + 1
    JSR BuildFireballRoomCollisionMask
    LDA TempPointer08 + 1
    STA FireballCurrentCollisionMask
    LDX #$2F
    LDY #$03

SaveCollisionDispatcherPointers:
    LDA $00,X
    STA $06,X
    LDA FireballCollisionPointerSetup,Y
    STA $00,X
    DEX
    DEY
    BPL SaveCollisionDispatcherPointers
    LDY FireballPreviousCollisionMask
    LDX #$08
    JSR DispatchFireballCollisionMask
    LDX #$2F
    LDY #$03

RestoreCollisionDispatcherPointers:
    LDA $06,X
    STA $00,X
    DEX
    DEY
    BPL RestoreCollisionDispatcherPointers

FinishActiveFireballCollision:
    RTS

FireballCollisionYDelta:
    .byte $00, $00, $FE, $02

FireballCollisionXDelta:
    .byte $02, $FE, $00, $00

.assert FireballCollisionXDelta - FireballCollisionYDelta = FireballDirectionCount, error, "unexpected fireball Y-delta count"
.assert * - FireballCollisionXDelta = FireballDirectionCount, error, "unexpected fireball X-delta count"

; Temporarily points EnemyAiPointer at $042A and EnemyObjectPointer at the
; fireball object so the shared collision handlers can operate on both
FireballCollisionPointerSetup:
    .addr FireballActive, FireballObject

DispatchFireballCollisionMask:
    LDA FireballCollisionHandlerLowBytes,Y
    STA TempPointer08
    LDA FireballCollisionHandlerHighBytes,Y
    STA TempPointer08 + 1
    JMP (TempPointer08)

FireballCollisionHandlerCount = 16

; Mask $0F reuses the empty-path handler, matching the pathfinding dispatcher
FireballCollisionHandlerLowBytes:
    .byte <HandleType14To1BPathMask00, <HandleType14To1BPathMask01
    .byte <HandleType14To1BPathMask02, <HandleType14To1BPathMask03
    .byte <HandleType14To1BPathMask04, <HandleType14To1BPathMask05
    .byte <HandleType14To1BPathMask06, <HandleType14To1BPathMask07
    .byte <HandleType14To1BPathMask08, <HandleType14To1BPathMask09
    .byte <HandleType14To1BPathMask0A, <HandleType14To1BPathMask0B
    .byte <HandleType14To1BPathMask0C, <HandleType14To1BPathMask0D
    .byte <HandleType14To1BPathMask0E, <HandleType14To1BPathMask00

FireballCollisionHandlerHighBytes:
    .byte >HandleType14To1BPathMask00, >HandleType14To1BPathMask01
    .byte >HandleType14To1BPathMask02, >HandleType14To1BPathMask03
    .byte >HandleType14To1BPathMask04, >HandleType14To1BPathMask05
    .byte >HandleType14To1BPathMask06, >HandleType14To1BPathMask07
    .byte >HandleType14To1BPathMask08, >HandleType14To1BPathMask09
    .byte >HandleType14To1BPathMask0A, >HandleType14To1BPathMask0B
    .byte >HandleType14To1BPathMask0C, >HandleType14To1BPathMask0D
    .byte >HandleType14To1BPathMask0E, >HandleType14To1BPathMask00

.assert FireballCollisionHandlerHighBytes - FireballCollisionHandlerLowBytes = FireballCollisionHandlerCount, error, "unexpected fireball collision handler count"
.assert * - FireballCollisionHandlerHighBytes = FireballCollisionHandlerCount, error, "unexpected fireball collision handler count"

; Input is Y in TempPointer08 and X in TempPointer08+1. The returned low
; nibble in TempPointer08+1 records solid cells around the fireball bounds
BuildFireballRoomCollisionMask:
    LDA #$00
    STA CollisionTargetY
    LDA TempPointer08
    SEC
    SBC #$0C
    STA TempPointer08
    CLC
    LDA #$0A
    ADC TempPointer08
    EOR TempPointer08
    AND #$F0
    BNE RecordFireballVerticalCellSpan
    SEC

RecordFireballVerticalCellSpan:
    ROR CollisionTargetY
    LDA TempPointer08 + 1
    SEC
    SBC #$05
    STA TempPointer08 + 1
    CLC
    LDA #$0B
    ADC TempPointer08 + 1
    EOR TempPointer08 + 1
    AND #$F0
    CLC
    BNE RecordFireballHorizontalCellSpan
    SEC

RecordFireballHorizontalCellSpan:
    ROR CollisionTargetY
    LDA TempPointer08 + 1
    LSR A
    LSR A
    LSR A
    LSR A
    CMP #$0F
    STA TempPointer08 + 1
    LDA TempPointer08
    AND #$F0
    BCC BuildFireballTopLeftMapIndex
    SBC #$10

BuildFireballTopLeftMapIndex:
    ORA TempPointer08 + 1
    TAY
    LDA #$00
    STA TempPointer08 + 1
    LDA RoomMap,Y
    CLC
    BPL RecordFireballTopLeftCell
    SEC

RecordFireballTopLeftCell:
    ROR TempPointer08 + 1
    LDA CollisionTargetY
    BMI SampleFireballTopRightCell
    INY

SampleFireballTopRightCell:
    LDA RoomMap,Y
    BPL RecordFireballTopRightCell
    SEC

RecordFireballTopRightCell:
    ROR TempPointer08 + 1
    LDA #$40
    AND CollisionTargetY
    BNE SampleFireballBottomRightCell
    TYA
    ADC #$10
    TAY

SampleFireballBottomRightCell:
    LDA RoomMap,Y
    BPL RecordFireballBottomRightCell
    SEC

RecordFireballBottomRightCell:
    ROR TempPointer08 + 1
    LDA CollisionTargetY
    BMI SampleFireballBottomLeftCell
    DEY

SampleFireballBottomLeftCell:
    LDA RoomMap,Y
    BPL RecordFireballBottomLeftCell
    SEC

RecordFireballBottomLeftCell:
    LDA TempPointer08 + 1
    ROR A
    LSR A
    LSR A
    LSR A
    LSR A
    STA TempPointer08 + 1
    RTS

TryStartBlockMagicAction:
    LDA #DanaActionRequestBlockMagic
    STA TempPointer08
    JSR TryStartDanaAction
    RTS

TryStartDanaAction:
    LDA GameplayFlags
    ROR A
    BCS RejectDanaAction
    AND #$08
    BNE RejectDanaAction
    LDA DanaObject + ObjectActionOffset
    TAX
    SEC
    SBC #DanaControllableActionMinimum
    CMP #DanaControllableActionLimit - DanaControllableActionMinimum
    BCS RejectDanaAction
    STX DanaSavedAction
    CMP #DanaActionGroupSize
    TXA
    AND #DanaFacingMask
    BCS SelectDanaCastingAction
    ORA #DanaActionIdleBit

SelectDanaCastingAction:
    ORA #DanaCastActionBase
    STA DanaObject + ObjectActionOffset
    ROR A
    LDA #$04
    BCC OffsetDanaCastingPosition
    LDA #$FB

OffsetDanaCastingPosition:
    ADC DanaXPosition
    STA DanaXPosition
    LDA DanaObject + ObjectYMotionOffset
    STA DanaSavedYMotion
    INC GameplayFlags
    LDA DanaObject + ObjectStateOffset
    AND #$DE
    TAY
    INY
    STY DanaObject + ObjectStateOffset
    LDA TempPointer08
    JSR QueuePendingThreadStart

RejectDanaAction:
    SEC
    RTS

; Store A in the first free request slot from 3 down to 1, with slot 0 as
; the fallback. Startup consumes these four requests into scheduler contexts
QueuePendingThreadStart:
    LDY #$03

FindPendingThreadStartSlot:
    LDX PendingThreadStarts,Y
    BEQ StorePendingThreadStart
    DEY
    BNE FindPendingThreadStartSlot

StorePendingThreadStart:
    STA PendingThreadStarts,Y
    RTS
