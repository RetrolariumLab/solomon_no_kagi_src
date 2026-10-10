; Collision-driven enemy AI families and linked spawn behavior

.segment "PRG_COLLISION_ENEMY_AI"

RunNuelGhostEnemyAi:
    JSR LoadEnemyActionSelector
    JSR JumpWithParams

NuelGhostActionHandlers:
    .addr UpdateNuelGhostLinkedSpawn
    .addr UpdateNuelGhostMapInteraction
    .addr UpdateNuelGhostLinkedLifetime
    .addr UpdateNuelGhostOpenPath

UpdateNuelGhostMapInteraction:
    LDY #EnemyAiPhaseOffset
    LDA (EnemyAiPointer),Y
    CMP #$0A
    BCC FinishNuelGhostMapInteraction
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
    BEQ FinishNuelGhostMapInteraction
    JSR SelectEnemyCollisionMapCoordinates
    JSR ConvertPixelCoordinatesToMapIndex
    TAY
    LDA RoomMap,Y
    CMP #$F8
    BCS FinishNuelGhostMapInteraction
    STY MapCellIndex
    JSR ApplyMapTileInteractionToObject

FinishNuelGhostMapInteraction:
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

UpdateNuelGhostLinkedSpawn:
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
    BNE AllocateNuelGhostLinkedEnemy
    LDY #ObjectXMotionOffset
    LDA (EnemyObjectPointer),Y
    LDY #ObjectYMotionOffset
    ORA (EnemyObjectPointer),Y
    BNE FinishNuelGhostLinkedSpawn
    DEY
    TYA
    STA (EnemyObjectPointer),Y
    BPL FinishNuelGhostLinkedSpawn

AllocateNuelGhostLinkedEnemy:
    LDA #$00
    LDY #ObjectYMotionOffset
    STA (EnemyObjectPointer),Y
    LDY #ObjectXMotionOffset
    STA (EnemyObjectPointer),Y
    LDY #ObjectTypeOffset
    LDA (EnemyObjectPointer),Y
    AND #$40
    BEQ ReserveNuelGhostLinkedEnemy
    LDA TempPointer04 + 3
    JSR SelectEnemyCollisionMapCoordinates
    JSR ConvertPixelCoordinatesToMapIndex
    LDA RoomMap,X
    CMP #$F8
    BCS SelectNuelGhostLinkedAction

ReserveNuelGhostLinkedEnemy:
    JSR FindFreeEnemySlotIndex
    BCC FinishNuelGhostLinkedSpawn
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

FinishNuelGhostLinkedSpawn:
    RTS

EnemyCollisionProbeOffsets:
    .byte $01, $01, $0E, $0E, $01

UpdateNuelGhostLinkedLifetime:
    LDY #EnemyAiPhaseOffset
    LDA (EnemyAiPointer),Y
    CMP #$19
    BCC FinishNuelGhostLinkedLifetime
    DEY
    LDA (EnemyAiPointer),Y
    LSR A
    BCC SelectNuelGhostLinkedAction
    ASL A
    STA (EnemyAiPointer),Y
    LDX #$01
    JSR ClearLinkedEnemySlots

SelectNuelGhostLinkedAction:
    LDY #ObjectActionOffset
    LDA #$02
    EOR (EnemyObjectPointer),Y
    AND #$03
    ORA #$0C
    STA (EnemyObjectPointer),Y

FinishNuelGhostLinkedLifetime:
    RTS

UpdateNuelGhostOpenPath:
    JSR SampleCurrentEnemyRoomMapCollision
    LDA TempPointer04 + 3
    BNE FinishNuelGhostOpenPath
    LDY #ObjectActionOffset
    LDA #$03
    AND (EnemyObjectPointer),Y
    STA (EnemyObjectPointer),Y

FinishNuelGhostOpenPath:
    RTS

RunGoblinEnemyAi:
    JSR LoadEnemyActionSelector
    JSR JumpWithParams

GoblinActionHandlers:
    .addr UpdateGoblinLinkedLifetime
    .addr UpdateLinkedEnemyDirectionState
    .addr SetEnemyMovingAction18
    .addr RunEnemyActionA55C
    .addr UpdateGoblinForwardPath
    .addr UpdateGoblinSpawn
    .addr ClearCurrentEnemyLinkedSlots

UpdateGoblinLinkedLifetime:
    LDY #EnemyAiPhaseOffset
    LDA (EnemyAiPointer),Y
    TAX
    LDY #ObjectActionOffset
    LDA (EnemyObjectPointer),Y
    AND #$02
    BNE CheckGoblinRetirement
    CPX #$0C
    BCC FinishGoblinLinkedLifetime
    LDA (EnemyObjectPointer),Y
    ORA #$02
    STA (EnemyObjectPointer),Y
    JSR ApplyForwardEnemyMapInteraction

FinishGoblinLinkedLifetime:
    RTS

CheckGoblinRetirement:
    CPX #$1B
    BCC FinishGoblinLinkedLifetime
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
    BCC KeepGoblinForwardDirection
    EOR #$01

KeepGoblinForwardDirection:
    ORA #$14
    STA (EnemyObjectPointer),Y
    RTS

UpdateGoblinForwardPath:
    LDY #ObjectActionOffset
    LDA (EnemyObjectPointer),Y
    AND #$02
    BNE UpdateGoblinBlockedPath
    JSR CheckEnemyForwardCollisionBit
    BNE HandleGoblinCollision
    LDY #ObjectActionOffset
    LDA #$01
    AND (EnemyObjectPointer),Y
    ORA #$16
    STA (EnemyObjectPointer),Y
    BNE ResetGoblinPhase

UpdateGoblinBlockedPath:
    LDY #EnemyAiPhaseOffset
    LDA (EnemyAiPointer),Y
    CMP #$0C
    BCC FinishGoblinForwardPath
    LDY #ObjectXMotionOffset
    LDA #$01
    STA (EnemyObjectPointer),Y
    LDY #ObjectActionOffset
    LDA #$FD
    AND (EnemyObjectPointer),Y
    STA (EnemyObjectPointer),Y

FinishGoblinForwardPath:
    RTS

UpdateGoblinSpawn:
    LDA #$08
    STA TempPointer00
    JSR CheckEnemyDeltaDirectionThreshold
    BCS HandleGoblinCollision
    LDY #ObjectActionOffset
    LDA (EnemyObjectPointer),Y
    TAX
    AND #$02
    BNE HandleGoblinCollision
    TXA
    AND #EnemyDirectionBit
    ORA #$12
    STA (EnemyObjectPointer),Y

ResetGoblinPhase:
    LDY #EnemyAiPhaseOffset
    LDA #$00
    STA (EnemyAiPointer),Y
    RTS

HandleGoblinCollision:
    JSR CheckEnemyForwardCollisionBit
    BEQ SelectGoblinCollisionAction
    LDY #ObjectXMotionOffset
    LDA (EnemyObjectPointer),Y
    BNE FinishGoblinCollision
    JSR FindFreeEnemySlotIndex
    BCC FinishGoblinCollision
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
    BPL ResetGoblinPhase

SelectGoblinCollisionAction:
    LDY #ObjectActionOffset
    LDA (EnemyObjectPointer),Y
    TAX
    AND #$02
    BNE CheckGoblinCollisionPhase
    TXA
    AND #EnemyDirectionBit
    ORA #$16
    STA (EnemyObjectPointer),Y
    BNE ResetGoblinPhase

CheckGoblinCollisionPhase:
    LDY #EnemyAiPhaseOffset
    LDA (EnemyAiPointer),Y
    CMP #$18
    BCC FinishGoblinCollision
    LDY #ObjectXMotionOffset
    LDA #$01
    STA (EnemyObjectPointer),Y
    LDY #ObjectActionOffset
    EOR (EnemyObjectPointer),Y
    AND #$FD
    STA (EnemyObjectPointer),Y

FinishGoblinCollision:
    RTS
