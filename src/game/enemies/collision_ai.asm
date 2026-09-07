; Collision-driven enemy AI families and linked spawn behavior

.segment "PRG_COLLISION_ENEMY_AI"

RunType1CTo37EnemyAi:
    JSR LoadEnemyActionSelector
    JSR JumpWithParams

Type1CTo37ActionHandlers:
    .addr UpdateType1CTo37LinkedSpawn
    .addr UpdateType1CTo37MapInteraction
    .addr UpdateType1CTo37LinkedLifetime
    .addr UpdateType1CTo37OpenPath

UpdateType1CTo37MapInteraction:
    LDY #EnemyAiPhaseOffset
    LDA (EnemyAiPointer),Y
    CMP #$0A
    BCC FinishType1CTo37MapInteraction
    LDY #ObjectActionOffset
    LDA (EnemyObjectPointer),Y
    AND #$03
    ORA #$08
    STA (EnemyObjectPointer),Y
    JSR SampleCurrentEnemyRoomMapCollision
    LDY #EnemyAiFirstLinkedSlotOffset
    LDA (EnemyAiPointer),Y
    JSR LoadEnemyObjectPointer
    LDA TempPointer04 + 3
    BEQ FinishType1CTo37MapInteraction
    JSR SelectEnemyCollisionMapCoordinates
    JSR ConvertPixelCoordinatesToMapIndex
    TAY
    LDA RoomMap,Y
    CMP #$F8
    BCS FinishType1CTo37MapInteraction
    STY MapCellIndex
    JSR ApplyMapTileInteractionToObject

FinishType1CTo37MapInteraction:
    RTS

SampleCurrentEnemyRoomMapCollision:
    LDY #ObjectYPositionOffset
    LDA (EnemyObjectPointer),Y
    STA TempPointer02
    LDY #ObjectXPositionOffset
    LDA (EnemyObjectPointer),Y
    STA TempPointer02 + 1
    LDA #$00
    STA TempPointer04 + 3
    LDY #$03

SampleNextCurrentEnemyRoomMapCell:
    LDA EnemyCollisionProbeOffsets,Y
    CLC
    ADC TempPointer02
    STA CoordinateY
    LDA EnemyCollisionProbeOffsets + 1,Y
    CLC
    ADC TempPointer02 + 1
    STA CoordinateX
    JSR ConvertPixelCoordinatesToMapIndex
    LDA RoomMap,X
    ASL A
    ROL TempPointer04 + 3
    DEY
    BPL SampleNextCurrentEnemyRoomMapCell
    RTS

UpdateType1CTo37LinkedSpawn:
    LDY #ObjectActionOffset
    LDA (EnemyObjectPointer),Y
    LSR A
    STA TempPointer00
    LDY #EnemyAiHorizontalDeltaOffset
    LDA (EnemyAiPointer),Y
    ROL A
    LDA TempPointer00
    ROL A
    LDY #ObjectActionOffset
    STA (EnemyObjectPointer),Y
    JSR SampleCurrentEnemyRoomMapCollision
    LDA TempPointer04 + 3
    BNE AllocateType1CTo37LinkedEnemy
    LDY #ObjectXMotionOffset
    LDA (EnemyObjectPointer),Y
    LDY #ObjectYMotionOffset
    ORA (EnemyObjectPointer),Y
    BNE FinishType1CTo37LinkedSpawn
    DEY
    TYA
    STA (EnemyObjectPointer),Y
    BPL FinishType1CTo37LinkedSpawn

AllocateType1CTo37LinkedEnemy:
    LDA #$00
    LDY #ObjectYMotionOffset
    STA (EnemyObjectPointer),Y
    LDY #ObjectXMotionOffset
    STA (EnemyObjectPointer),Y
    LDY #ObjectTypeOffset
    LDA (EnemyObjectPointer),Y
    AND #$40
    BEQ ReserveType1CTo37LinkedEnemy
    LDA TempPointer04 + 3
    JSR SelectEnemyCollisionMapCoordinates
    JSR ConvertPixelCoordinatesToMapIndex
    LDA RoomMap,X
    CMP #$F8
    BCS SelectType1CTo37LinkedAction

ReserveType1CTo37LinkedEnemy:
    JSR FindFreeEnemySlotIndex
    BCC FinishType1CTo37LinkedSpawn
    TXA
    LDY #EnemyAiFirstLinkedSlotOffset
    STA (EnemyAiPointer),Y
    LDY #EnemyAiFlagsOffset
    LDA #EnemyAiActiveState
    STA (TempPointer04),Y
    INY
    ASL A
    STA (EnemyAiPointer),Y
    DEY
    LDA #$01
    ORA (EnemyAiPointer),Y
    STA (EnemyAiPointer),Y
    LDY #ObjectActionOffset
    LDA (EnemyObjectPointer),Y
    AND #$03
    ORA #$04
    STA (EnemyObjectPointer),Y

FinishType1CTo37LinkedSpawn:
    RTS

EnemyCollisionProbeOffsets:
    .byte $01, $01, $0E, $0E, $01

UpdateType1CTo37LinkedLifetime:
    LDY #EnemyAiPhaseOffset
    LDA (EnemyAiPointer),Y
    CMP #$19
    BCC FinishType1CTo37LinkedLifetime
    DEY
    LDA (EnemyAiPointer),Y
    LSR A
    BCC SelectType1CTo37LinkedAction
    ASL A
    STA (EnemyAiPointer),Y
    LDX #$01
    JSR ClearLinkedEnemySlots

SelectType1CTo37LinkedAction:
    LDY #ObjectActionOffset
    LDA #$02
    EOR (EnemyObjectPointer),Y
    AND #$03
    ORA #$0C
    STA (EnemyObjectPointer),Y

FinishType1CTo37LinkedLifetime:
    RTS

UpdateType1CTo37OpenPath:
    JSR SampleCurrentEnemyRoomMapCollision
    LDA TempPointer04 + 3
    BNE FinishType1CTo37OpenPath
    LDY #ObjectActionOffset
    LDA #$03
    AND (EnemyObjectPointer),Y
    STA (EnemyObjectPointer),Y

FinishType1CTo37OpenPath:
    RTS

RunType5CTo63EnemyAi:
    JSR LoadEnemyActionSelector
    JSR JumpWithParams

Type5CTo63ActionHandlers:
    .addr UpdateType5CTo63LinkedLifetime
    .addr UpdateLinkedEnemyDirectionState
    .addr SetEnemyMovingAction18
    .addr RunEnemyActionA55C
    .addr UpdateType5CTo63ForwardPath
    .addr UpdateType5CTo63Spawn
    .addr ClearCurrentEnemyLinkedSlots

UpdateType5CTo63LinkedLifetime:
    LDY #EnemyAiPhaseOffset
    LDA (EnemyAiPointer),Y
    TAX
    LDY #ObjectActionOffset
    LDA (EnemyObjectPointer),Y
    AND #$02
    BNE CheckType5CTo63Retirement
    CPX #$0C
    BCC FinishType5CTo63LinkedLifetime
    LDA (EnemyObjectPointer),Y
    ORA #$02
    STA (EnemyObjectPointer),Y
    JSR ApplyForwardEnemyMapInteraction

FinishType5CTo63LinkedLifetime:
    RTS

CheckType5CTo63Retirement:
    CPX #$1B
    BCC FinishType5CTo63LinkedLifetime
    LDY #EnemyAiFlagsOffset
    LDA #$FE
    AND (EnemyAiPointer),Y
    STA (EnemyAiPointer),Y
    LDX #$01
    JSR ClearLinkedEnemySlots
    JSR CalculateEnemyForwardMapCoordinates
    JSR ConvertPixelCoordinatesToMapIndex
    TAX
    LDA RoomMap,X
    STA TempPointer00
    LDY #ObjectXMotionOffset
    LDA #$01
    STA (EnemyObjectPointer),Y
    LDY #ObjectActionOffset
    AND (EnemyObjectPointer),Y
    ROL TempPointer00
    BCC KeepType5CTo63ForwardDirection
    EOR #$01

KeepType5CTo63ForwardDirection:
    ORA #$14
    STA (EnemyObjectPointer),Y
    RTS

UpdateType5CTo63ForwardPath:
    LDY #ObjectActionOffset
    LDA (EnemyObjectPointer),Y
    AND #$02
    BNE UpdateType5CTo63BlockedPath
    JSR CheckEnemyForwardCollisionBit
    BNE HandleType5CTo63Collision
    LDY #ObjectActionOffset
    LDA #$01
    AND (EnemyObjectPointer),Y
    ORA #$16
    STA (EnemyObjectPointer),Y
    BNE ResetType5CTo63Phase

UpdateType5CTo63BlockedPath:
    LDY #EnemyAiPhaseOffset
    LDA (EnemyAiPointer),Y
    CMP #$0C
    BCC FinishType5CTo63ForwardPath
    LDY #ObjectXMotionOffset
    LDA #$01
    STA (EnemyObjectPointer),Y
    LDY #ObjectActionOffset
    LDA #$FD
    AND (EnemyObjectPointer),Y
    STA (EnemyObjectPointer),Y

FinishType5CTo63ForwardPath:
    RTS

UpdateType5CTo63Spawn:
    LDA #$08
    STA TempPointer00
    JSR CheckEnemyDeltaDirectionThreshold
    BCS HandleType5CTo63Collision
    LDY #ObjectActionOffset
    LDA (EnemyObjectPointer),Y
    TAX
    AND #$02
    BNE HandleType5CTo63Collision
    TXA
    AND #EnemyDirectionBit
    ORA #$12
    STA (EnemyObjectPointer),Y

ResetType5CTo63Phase:
    LDY #EnemyAiPhaseOffset
    LDA #$00
    STA (EnemyAiPointer),Y
    RTS

HandleType5CTo63Collision:
    JSR CheckEnemyForwardCollisionBit
    BEQ SelectType5CTo63CollisionAction
    LDY #ObjectXMotionOffset
    LDA (EnemyObjectPointer),Y
    BNE FinishType5CTo63Collision
    JSR FindFreeEnemySlotIndex
    BCC FinishType5CTo63Collision
    TXA
    LDY #EnemyAiFirstLinkedSlotOffset
    STA (EnemyAiPointer),Y
    LDY #EnemyAiFlagsOffset
    LDA #$01
    ORA (EnemyAiPointer),Y
    STA (EnemyAiPointer),Y
    LDA #EnemyAiActiveState
    STA (TempPointer04),Y
    LDA #$01
    ORA (EnemyAiPointer),Y
    STA (EnemyAiPointer),Y
    LDA #$01
    LDY #ObjectActionOffset
    AND (EnemyObjectPointer),Y
    STA (EnemyObjectPointer),Y
    BPL ResetType5CTo63Phase

SelectType5CTo63CollisionAction:
    LDY #ObjectActionOffset
    LDA (EnemyObjectPointer),Y
    TAX
    AND #$02
    BNE CheckType5CTo63CollisionPhase
    TXA
    AND #EnemyDirectionBit
    ORA #$16
    STA (EnemyObjectPointer),Y
    BNE ResetType5CTo63Phase

CheckType5CTo63CollisionPhase:
    LDY #EnemyAiPhaseOffset
    LDA (EnemyAiPointer),Y
    CMP #$18
    BCC FinishType5CTo63Collision
    LDY #ObjectXMotionOffset
    LDA #$01
    STA (EnemyObjectPointer),Y
    LDY #ObjectActionOffset
    EOR (EnemyObjectPointer),Y
    AND #$FD
    STA (EnemyObjectPointer),Y

FinishType5CTo63Collision:
    RTS
