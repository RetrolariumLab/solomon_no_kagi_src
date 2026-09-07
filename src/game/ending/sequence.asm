; Room-index 49 ending sequence, object convergence, and message presentation

.segment "PRG_ENDING_SEQUENCE"

EndingObjectIndex = $07
EndingFrameSnapshot = $2B
EndingObjectPassCount = $2A
EndingActiveObjectCount = $30
EndingMotionBudget = $31
EndingRandomRange = $03
EndingMessagePass = $02
EndingMessageStreamOffset = $00

EndingObjectCount = EnemyObjectCount
EndingConvergenceMapIndex = $67
EndingObjectType = $1C
EndingObjectState = $C2
EndingObjectActionBase = $08
EndingRoomStateFlag = $08
EndingFadeStepCount = $1F

PrepareEndingPresentation = DrawTitleLogoLayer
RunEndingObjectOrbit = InitializeTransitionOrbitObject + $1A

RunEndingRoomScript:
    LDA #$00
    STA InventorySlotsHigh
    STA InventorySlotsLow
    JSR WaitForDanaActive
    LDA #RoomMapClosedDoorIdentity
    STA RoomMap + $67
    LDA #RoomMapBrownBlock
    STA RoomMap + $27
    STA RoomMap + $43
    STA RoomMap + $8C

WaitForEndingCastAt6C:
    JSR SwitchThreads
    LDA BlockCastTargetMapIndex
    CMP #$6C
    BNE WaitForEndingCastAt6C
    LDA #RoomMapBrownBlock
    STA RoomMap + $69

WaitForEndingCastAt67:
    JSR SwitchThreads
    LDA BlockCastTargetMapIndex
    CMP #EndingConvergenceMapIndex
    BNE WaitForEndingCastAt67
    LDA #$82
    STA TempPointer02
    JSR SetActiveNonDanaObjectState
    LDX #$06
    JSR ResetOtherSecondaryThreads
    LSR GameStateFlags
    ASL GameStateFlags
    LDA #EndingRoomStateFlag
    ORA RoomStateFlags
    STA RoomStateFlags
    LDA #$67
    LDX #$37
    JSR WriteEndingRoomCell
    LDA #$66
    LDX #$36
    JSR WriteEndingRoomCell
    LDA #$00
    STA MagicSparkObject + ObjectStateOffset
    LDA #$10
    JSR WaitForEndingSteps
    LDA #EndingObjectCount - 1
    STA EndingObjectIndex

PrepareNextConvergingEnemy:
    LDA EndingObjectIndex
    JSR LoadEnemyObjectPointer
    LDY #ObjectStateOffset
    LDA #$40
    ORA (TempPointer00),Y
    STA (TempPointer00),Y
    INY
    LDA #EndingObjectType
    STA (TempPointer00),Y
    TYA
    LDY #ObjectActionOffset
    STA (TempPointer00),Y
    LDY #ObjectYPositionOffset
    LDA (TempPointer00),Y
    STA CoordinateOriginY
    LDY #ObjectXPositionOffset
    LDA (TempPointer00),Y
    STA CoordinateOriginX
    LDA #EndingConvergenceMapIndex
    STA CoordinateTargetY
    JSR ConvertMapIndexToPixelCoordinates
    JSR BuildScaledCoordinateDeltas
    LDA EndingObjectIndex
    JSR LoadEnemyAiPointer
    LDX #$03
    LDY #$07

StoreNextEndingMotionByte:
    LDA CoordinateOriginY,X
    STA (TempPointer00),Y
    DEY
    DEX
    BPL StoreNextEndingMotionByte
    DEC EndingObjectIndex
    BPL PrepareNextConvergingEnemy
    LDA #$03
    JSR WaitForEndingSteps
    LDA #$80
    STA DanaObject + ObjectStateOffset
    LDY #$14
    JSR AddSoundEffect

AdvanceEndingConvergenceFrame:
    LDA #EndingObjectCount - 1
    STA EndingObjectIndex

AdvanceNextConvergingEnemy:
    LDA EndingObjectIndex
    JSR LoadEnemyAiPointer
    TXA
    LDX #$00
    JSR CopyEndingPointerPair
    JSR LoadEnemyObjectPointer
    LDX #$02
    JSR CopyEndingPointerPair
    JSR ApplyMotionVectorToObject
    DEC EndingObjectIndex
    BPL AdvanceNextConvergingEnemy

WaitForNextEndingFrame:
    LDA GameplayFrameCounters + 6
    CMP EndingFrameSnapshot
    BEQ WaitForNextEndingFrame
    STA EndingFrameSnapshot
    CMP #$43
    BCC AdvanceEndingConvergenceFrame
    LDY #$18
    JSR AddSoundEffect
    LDA #$67
    LDX #$35
    JSR WriteEndingRoomCell
    LDA #$66
    LDX #$10
    JSR WriteEndingRoomCell
    JSR ClearGameplayObjectAndEnemyState
    LDA #$40
    JSR WaitForEndingSteps
    JSR Clear32x26NametableRegion
    LDA #$03
    STA ChrBankRequest

WaitForEndingPpuBuffer:
    LDA PpuUpdateStreamPointer + 1
    BNE WaitForEndingPpuBuffer
    JSR PrepareEndingPresentation
    JSR BuildEndingPpuMessage
    LDA #$4F
    STA PpuUpdateBuffer + 2
    LDA #$0F
    STA PpuUpdateBuffer + $10
    LDA #$00
    STA PpuUpdateBuffer + $13
    JSR PublishPpuUpdateBuffer
    LDA #$EF
    STA PpuScrollY
    LDA #$D0
    STA MagicSparkObject + ObjectYPositionOffset
    LDA #$78
    STA MagicSparkObject + ObjectXPositionOffset
    LDX #$03

CopyEndingSparkTemplate:
    LDA EndingSparkTemplate,X
    STA MagicSparkObject,X
    DEX
    BPL CopyEndingSparkTemplate
    LDA #$80
    JSR WaitForEndingSteps
    LDA #$00
    STA MagicSparkObject + ObjectStateOffset
    LDA #$04
    AND RoomStateFlags
    BEQ BeginEndingObjectFall
    LDY #$13
    JSR AddSoundEffect
    LDX #$09
    STX EndingActiveObjectCount

RunNextEndingEnemyWave:
    LDX #$0C

CopyEndingEnemyAiTemplate:
    LDA EndingEnemyAiTemplate,X
    STA EnemyAiState,X
    DEX
    BPL CopyEndingEnemyAiTemplate
    LDX #$07
    STX EndingMessagePass

InitializeNextEndingWaveObject:
    LDA EndingMessagePass
    JSR LoadEnemyObjectPointer
    LDA #EndingObjectState
    STA SpawnYPosition
    LDA #EndingObjectType
    STA SpawnXPosition
    LDA #EndingObjectActionBase
    CPX #$04
    ADC #$00
    JSR InitializeObjectStateHeader
    DEC EndingMessagePass
    BPL InitializeNextEndingWaveObject
    LDA #$00
    STA $80
    JSR RunEndingObjectOrbit
    DEC EndingActiveObjectCount
    BPL RunNextEndingEnemyWave

BeginEndingObjectFall:
    LDY #$19
    JSR AddSoundEffect
    LDA #$C0
    AND GameStateFlags
    BEQ SelectEndingMessageSequence
    LDA #$F0
    STA EndingMotionBudget

WaitForEndingObjectFrame:
    LDA GameplayFrameCounters + 6
    CMP EndingFrameSnapshot
    BEQ WaitForEndingObjectFrame
    STA EndingFrameSnapshot
    LDA #$00
    STA EndingActiveObjectCount
    LDA #$0A
    STA EndingObjectPassCount

AdvanceNextEndingObject:
    JSR LoadNextEndingObject
    LDY #ObjectStateOffset
    LDA (EnemyObjectPointer),Y
    CMP #$C0
    BCS MoveEndingObject
    INC EndingActiveObjectCount
    LDA EndingActiveObjectCount
    BMI FinishEndingObjectPass
    LDA EndingMotionBudget
    BEQ FinishEndingObjectPass
    DEC EndingActiveObjectCount
    DEC EndingMotionBudget
    JSR InitializeRandomEndingObject
    ASL EndingActiveObjectCount
    SEC
    ROR EndingActiveObjectCount
    BCC FinishEndingObjectPass

MoveEndingObject:
    LDY #ObjectYPositionOffset
    LDA (EnemyObjectPointer),Y
    CMP #$D0
    BCC ApplyEndingObjectMotion
    LDA #$00
    TAY
    STA (EnemyObjectPointer),Y

ApplyEndingObjectMotion:
    JSR ApplyMotionVectorToObject

FinishEndingObjectPass:
    DEC EndingObjectPassCount
    BPL AdvanceNextEndingObject
    LDA EndingActiveObjectCount
    AND #$0F
    CMP #$0B
    BNE WaitForEndingObjectFrame

SelectEndingMessageSequence:
    LDA #$C0
    AND GameStateFlags
    CMP #$C0
    BEQ RunEndingFade
    JMP FinishEndingRandomObjects

RunEndingFade:
    LDA #$07
    JSR QueueStaticPpuUpdateStream
    LDY #$1A
    JSR AddSoundEffect
    LDA #$80
    JSR WaitForEndingSteps
    LDA #EndingFadeStepCount
    STA EndingActiveObjectCount
    LDA #$04
    STA EndingObjectPassCount
    LDA #$EB
    STA PpuScrollY

OscillateEndingScroll:
    JSR WaitOneEndingStep
    LDA PpuScrollY
    ADC EndingObjectPassCount
    STA PpuScrollY
    LDA #$FF
    EOR EndingObjectPassCount
    STA EndingObjectPassCount
    INC EndingObjectPassCount
    DEC EndingActiveObjectCount
    BPL OscillateEndingScroll
    JSR WaitOneEndingStep
    DEC EndingActiveObjectCount

PopulateEndingRandomObjects:
    LDA #EndingObjectCount - 1
    STA EndingMessagePass

PopulateNextEndingRandomObject:
    LDA EndingMessagePass
    JSR LoadEnemyObjectPointer
    LDA #$F0
    SBC PpuScrollY
    LSR A
    LSR A
    STA EndingRandomRange
    JSR AdvanceRandomState

ReduceEndingRandomY:
    CMP EndingRandomRange
    BCC StoreEndingRandomY
    SBC EndingRandomRange
    BCS ReduceEndingRandomY

StoreEndingRandomY:
    EOR #$FF
    ADC #$D8
    LDY #ObjectYPositionOffset
    STA (TempPointer00),Y
    JSR AdvanceRandomState
    ASL A
    LDY #ObjectXPositionOffset
    STA (TempPointer00),Y
    LDY #ObjectActionOffset

CopyEndingRandomObjectTemplate:
    LDA EndingRandomObjectTemplate,Y
    STA (TempPointer00),Y
    DEY
    BPL CopyEndingRandomObjectTemplate
    DEC EndingMessagePass
    BPL PopulateNextEndingRandomObject
    INC EndingActiveObjectCount
    BMI PopulateEndingRandomObjects
    LDA #$FE
    STA EndingActiveObjectCount
    DEC PpuScrollY
    LDA PpuScrollY
    CMP #$90
    BCS PopulateEndingRandomObjects
    LDY #ObjectStateOffset
    LDX #EndingObjectCount - 1

DeactivateNextEndingRandomObject:
    TXA
    JSR LoadEnemyObjectPointer
    TYA
    STA (TempPointer00),Y
    DEX
    BPL DeactivateNextEndingRandomObject

FinishEndingRandomObjects:
    LDY #$18
    JSR AddSoundEffect
    LDA #$04
    AND RoomStateFlags
    BEQ SelectEndingTextSequence
    LDX #$01
    STX EndingMessagePass

PublishInitialEndingMessage:
    LDA PpuUpdateStreamPointer + 1
    BNE PublishInitialEndingMessage
    LDY #$FF
    TAX
    LDA EndingMessagePass
    BNE CopyInitialEndingMessage
    LDY #$1A

CopyInitialEndingMessage:
    INX
    INY
    LDA EndingInitialMessageData,Y
    STA PpuUpdateBuffer + 1,X
    BNE CopyInitialEndingMessage
    LDA PpuScrollY
    CMP #$A0
    BCS CopyInitialEndingMessageAddress
    INY
    INY

CopyInitialEndingMessageAddress:
    LDX #$01

CopyNextInitialMessageAddressByte:
    INY
    LDA EndingInitialMessageData,Y
    STA PpuUpdateBuffer,X
    DEX
    BPL CopyNextInitialMessageAddressByte
    JSR PublishPpuUpdateBuffer
    DEC EndingMessagePass
    BPL PublishInitialEndingMessage

SelectEndingTextSequence:
    LDA GameStateFlags
    ROL A
    ROL A
    AND #$01
    TAX
    BCC LoadEndingMessageSequenceStart
    INX

LoadEndingMessageSequenceStart:
    LDY EndingMessageSequenceStarts,X
    STY EndingMessageStreamOffset

PublishNextEndingMessage:
    LDA PpuUpdateStreamPointer + 1
    BNE PublishNextEndingMessage
    LDY EndingMessageStreamOffset
    INC EndingMessageStreamOffset
    LDX EndingMessageSequence,Y
    BMI FinishEndingMessages
    LDY EndingMessageTextOffsets,X
    TAX

CopyEndingMessageText:
    INX
    INY
    LDA EndingMessageData,Y
    STA PpuUpdateBuffer + 1,X
    BNE CopyEndingMessageText
    CPY #$6A
    BCS CopyEndingMessageAddress
    LDA PpuScrollY
    CMP #$A0
    BCS CopyEndingMessageAddress
    INY
    INY

CopyEndingMessageAddress:
    INY
    LDA EndingMessageData,Y
    STA PpuUpdateBuffer + 1
    INY
    LDA EndingMessageData,Y
    STA PpuUpdateBuffer
    JSR PublishPpuUpdateBuffer
    BNE PublishNextEndingMessage

FinishEndingMessages:
    LDX #$02
    STX EndingObjectPassCount

RunNextEndingPaletteStep:
    LDA #$10
    JSR WaitForEndingSteps
    JSR BuildEndingPpuMessage
    LDX EndingObjectPassCount
    LDA EndingPaletteValues,X
    STA PpuUpdateBuffer + $10
    JSR PublishPpuUpdateBuffer
    DEC EndingObjectPassCount
    BPL RunNextEndingPaletteStep
    LDA #$00
    STA Joypad1Cached
    LDY #$10
    JSR AddSoundEffect

WaitForEndingInput:
    LDA Joypad1Raw
    BEQ WaitForEndingInput
    LDY #$01
    STY GameStateFlags
    LDA #$E7
    AND PpuMaskShadow
    STA PpuMaskShadow
    STA a:PPU_MASK
    LDA #$0C
    JSR QueueStaticPpuUpdateStream
    LDA #$01
    JSR QueueStaticPpuUpdateStream
    LDA #$08
    JSR QueueStaticPpuUpdateStream
    LDA #$00
    STA PpuScrollY
    LDA #$18
    ORA PpuMaskShadow
    STA PpuMaskShadow
    LDA #$16
    JSR StartThread
    LDA #$06
    JSR StopThread

.assert * - RunEndingRoomScript = $360, error, "unexpected ending-sequence size"
