; Context-6 dispatch and room-specific triggers for all 53 room indices

.segment "PRG_SPECIAL_ROOM_SCRIPTS"

SpecialRoomThreadIndex = $06
RoomsPerScriptGroup = 8
RoomScriptGroupPointerSize = 2
RoomScriptDisabledFlag = $10
RoomScriptTargetMapIndex = $88
MightyBombJackHeadHitCount = $0B
MightyBombJackObjectType = $18
RoomScriptEnemyAiFlag = $40
RoomScriptEnemyAiActive = $80
RoomScriptDanaAction = DanaWalkActionBase
TecmoBunnyFirstRevealPattern = $38
TecmoBunnyFinalRevealPattern = $39

RunSpecialRoomScriptThread:
    JSR DispatchCurrentRoomScript
    LDA #SpecialRoomThreadIndex
    JSR StopThread

DispatchCurrentRoomScript:
    LDX CurrentRoomIndex
    TXA
    LSR A
    LSR A
    LSR A
    ASL A
    TAY
    LDA SpecialRoomScriptOffsets,X
    CLC
    ADC SpecialRoomScriptGroupBases,Y
    STA TempPointer00
    LDA #$00
    ADC SpecialRoomScriptGroupBases + 1,Y
    STA TempPointer00 + 1
    JMP (TempPointer00)

SpecialRoomScriptGroupBases:
    .addr NoSpecialRoomScript
    .addr RevealRoomSealFlag01
    .addr NoGroup2RoomScript
    .addr NoGroup3RoomScript
    .addr NoGroup4RoomScript
    .addr NoGroup5RoomScript
    .addr NoGroup6RoomScript

; Each byte is relative to the base shared by its eight-room group. The final
; four values are data despite decoding as valid 6502 opcodes in isolation
SpecialRoomScriptOffsets:
    .byte $00
    .byte $00, $00, $01, $01, $00, $01, $00, $00
    .byte $06, $05, $05, $09, $05, $05, $05, $01
    .byte $2C, $2F, $37, $4E, $00, $00, $2C, $00
    .byte $00, $00, $00, $01, $06, $00, $00, $00
    .byte $00, $00, $00, $00, $27, $01, $00, $00
    .byte $00, $00, $00, $00, $01, $09, $00, $01
    .byte $85, $00, $49, $4D

SpecialRoomScriptCount = * - SpecialRoomScriptOffsets
.assert SpecialRoomScriptCount = 53, error, "unexpected special-room script count"

NoSpecialRoomScript:
    RTS

EnablePrimaryEnemyScript:
    JMP EnablePrimaryEnemyAiPhase

RevealRoomSealFlag01:
    LDA #$01
    JMP RevealCurrentRoomSeal

NoGroup1RoomScript:
    RTS

EnablePrimaryEnemyScriptGroup1:
    JMP EnablePrimaryEnemyAiPhase

RevealRoomSealFlag02:
    LDA #$02
    JMP RevealCurrentRoomSeal

NoGroup2RoomScript:
    RTS

RunRoom17MightyBombJackTrigger:
    LDA #RoomMapBatSymbolIdentity
    JSR RevealCurrentRoomSeal
    LDA #$00
    STA RoomScriptTargetMapIndex
    LDA RoomStateFlags
    AND #RoomScriptDisabledFlag
    BNE NoGroup2RoomScript

WaitForRoom17MightyBombJackHeadHit:
    JSR SwitchThreads
    LDA HeadCollisionTargetMapIndex
    CMP #$7E
    BNE WaitForRoom17MightyBombJackHeadHit
    LDA #$00
    STA HeadCollisionTargetMapIndex
    INC RoomScriptTargetMapIndex
    LDA RoomScriptTargetMapIndex
    CMP #MightyBombJackHeadHitCount
    BCC WaitForRoom17MightyBombJackHeadHit
    LDA #$6E
    STA RoomScriptTargetMapIndex
    JMP SpawnMightyBombJackAtScriptTarget

EnablePrimaryEnemyScriptGroup2:
    JMP EnablePrimaryEnemyAiPhase

RevealRoomSealFlag08AndEnableEnemy:
    LDA #$08
    JSR RevealCurrentRoomSeal
    JMP EnablePrimaryEnemyAiPhase

RunRoom20TecmoBunnyTrigger:
    JSR PrepareSpecialRoomTrigger
    LDA #<Room20SpecialBlockPlane
    STA RoomBlockDataPointer
    LDA #>Room20SpecialBlockPlane
    STA RoomBlockDataPointer + 1
    LDA #$04
    JSR ExpandRoomMapBitplane
    LDA #$20
    STA RoomScriptTargetMapIndex
    JMP RunTecmoBunnyTrigger

RevealRoomSealFlag10:
    LDA #$10
    JMP RevealCurrentRoomSeal

RunTecmoBunnyTrigger:
    LDA RoomStateFlags
    AND #RoomScriptDisabledFlag
    BNE FinishTecmoBunnyTrigger

WaitForTecmoBunnyCover:
    JSR ReadScriptTargetTileAfterYield
    BPL WaitForTecmoBunnyCover

WaitForTecmoBunnyFirstUncover:
    JSR ReadScriptTargetTileAfterYield
    BMI WaitForTecmoBunnyFirstUncover

WaitForTecmoBunnyRevealAction:
    JSR SwitchThreads
    LDA DanaObject + ObjectStateOffset
    LSR A
    BCS WaitForTecmoBunnyRevealAction
    LDA RoomScriptTargetMapIndex
    STA RoomMapUpdateIndex
    LDA #TecmoBunnyFirstRevealPattern
    STA RoomMapUpdateTile
    JSR BuildAndPublishRoomMapCellUpdate

WaitForTecmoBunnySecondCover:
    JSR ReadScriptTargetTileAfterYield
    BPL WaitForTecmoBunnySecondCover

WaitForTecmoBunnySecondUncover:
    JSR ReadScriptTargetTileAfterYield
    BMI WaitForTecmoBunnySecondUncover
    LDA HeadCollisionTargetMapIndex
    CMP RoomScriptTargetMapIndex
    BNE FinishTecmoBunnyTrigger

WaitForTecmoBunnyCollectionAction:
    JSR SwitchThreads
    LDA DanaObject + ObjectActionOffset
    CMP #RoomScriptDanaAction
    BNE WaitForTecmoBunnyCollectionAction
    LDX RoomScriptTargetMapIndex
    LDA #RoomMapTecmoBunnyRewardIdentity
    STA RoomMap,X
    LDA #TecmoBunnyFinalRevealPattern
    STA RoomMapUpdateTile
    STX RoomMapUpdateIndex
    JSR BuildAndPublishRoomMapCellUpdate

FinishTecmoBunnyTrigger:
    RTS

ReadScriptTargetTileAfterYield:
    JSR SwitchThreads
    LDX RoomScriptTargetMapIndex
    LDA RoomMap,X
    RTS

EnablePrimaryEnemyAiPhase:
    JSR WaitForDanaActive
    LDA EnemyAiState
    ORA #RoomScriptEnemyAiFlag
    STA EnemyAiState
    RTS

SpawnMightyBombJackAtScriptTarget:
    JSR SwitchThreads
    JSR FindFreeEnemySlotIndex
    BCC SpawnMightyBombJackAtScriptTarget
    LDA #RoomScriptEnemyAiActive
    STA (TempPointer04),Y
    LDA #$00
    LDY #$02
    STA (TempPointer04),Y
    INY
    STA (TempPointer04),Y
    STX SpawnSlotIndex
    LDA RoomScriptTargetMapIndex
    STA SpawnYPosition
    JSR ConvertMapIndexToPixelCoordinates
    LDA #MightyBombJackObjectType
    STA SpawnType
    JSR InitializeEnemy
    JSR ConfigureEnemyType
    RTS

NoGroup3RoomScript:
    RTS

RevealRoomSealFlag20:
    LDA #$20
    JMP RevealCurrentRoomSeal

RunRoomIndex29BlockTrigger:
    JSR PrepareSpecialRoomTrigger
    LDA #<Room30SpecialBlockPlane
    STA RoomBlockDataPointer
    LDA #>Room30SpecialBlockPlane
    STA RoomBlockDataPointer + 1
    LDA #RoomMapBlueOpalIdentity
    JSR ExpandRoomMapBitplane
    JMP EnablePrimaryEnemyAiPhase

UnusedRoomIndex29ScriptReturn:
    RTS

NoGroup4RoomScript:
    RTS

RunRoom39MightyBombJackTrigger:
    LDA #$00
    STA RoomScriptTargetMapIndex
    LDA RoomStateFlags
    AND #RoomScriptDisabledFlag
    BNE NoGroup4RoomScript

WaitForRoom39MightyBombJackHeadHit:
    JSR SwitchThreads
    LDA HeadCollisionTargetMapIndex
    CMP #$56
    BNE WaitForRoom39MightyBombJackHeadHit
    LDA #$00
    STA HeadCollisionTargetMapIndex
    INC RoomScriptTargetMapIndex
    LDA RoomScriptTargetMapIndex
    CMP #MightyBombJackHeadHitCount
    BCC WaitForRoom39MightyBombJackHeadHit
    LDA #$36
    STA RoomScriptTargetMapIndex
    JMP SpawnMightyBombJackAtScriptTarget

RunRoom38TecmoBunnyTrigger:
    LDA #$9E
    STA RoomScriptTargetMapIndex
    JMP RunTecmoBunnyTrigger

NoGroup5RoomScript:
    RTS

RevealRoomSealFlag40AndEnableEnemy:
    LDA #$40
    JSR RevealCurrentRoomSeal
    JMP EnablePrimaryEnemyAiPhase

RevealRoomSealFlag80:
    LDA #$80
    JMP RevealCurrentRoomSeal

NoGroup6RoomScript:
    RTS

RunPrincessRoomScript:
    JSR WaitForDanaActive
    LDA #RoomMapWhiteBlock
    STA RoomMap
    LDA #RoomMapBrownBlock
    LDX #$0B

HidePrincessRoomObjects:
    LDY PrincessRoomObjectMapOffsets,X
    STA RoomMap,Y
    DEX
    BPL HidePrincessRoomObjects

WaitForPrincessRoomFirstCastTarget:
    JSR SwitchThreads
    LDA BlockCastTargetMapIndex
    CMP #$AD
    BNE WaitForPrincessRoomFirstCastTarget
    LDA EnemyObjects + ObjectStateOffset
    BPL FinishPrincessRoomScript
    LDA EnemyObjects + ObjectYPositionOffset
    STA CoordinateY
    LDA EnemyObjects + ObjectXPositionOffset
    STA CoordinateX
    JSR ConvertPixelCoordinatesToMapIndex
    CPX #$AD
    BNE FinishPrincessRoomScript
    LDA #RoomMapBrownBlock
    STA RoomMap + $82

WaitForPrincessRoomSecondCastTarget:
    JSR SwitchThreads
    LDA BlockCastTargetMapIndex
    CMP #$57
    BNE WaitForPrincessRoomSecondCastTarget
    LDA #RoomMapBrownBlock
    STA RoomMap + $65

FinishPrincessRoomScript:
    RTS

RunPageOfTimeRoomScript:
    LDX #$37
    BNE MarkSolomonPageTriggerTile

RunPageOfSpaceRoomScript:
    LDX #$A7

MarkSolomonPageTriggerTile:
    LDA #RoomMapSolomonPageIdentity
    STA RoomMap,X
    JSR WaitForDanaActive
    LDA #RoomMapBrownBlock
    STA RoomMap + $97

WaitForSolomonPageRoomTrigger:
    JSR SwitchThreads
    LDA DanaObject + ObjectYPositionOffset
    STA CoordinateY
    LDA DanaObject + ObjectXPositionOffset
    STA CoordinateX
    JSR ConvertPixelCoordinatesToMapIndex
    LDA #RoomMapBrownBlock
    CPX #$57
    BEQ OpenSolomonPageRoomTiles
    LDX BlockCastTargetMapIndex
    CPX #$A1
    BNE WaitForSolomonPageRoomTrigger
    STA RoomMap + $C7
    RTS

OpenSolomonPageRoomTiles:
    LDX #$02

OpenNextSolomonPageRoomTile:
    STA RoomMap + $46,X
    DEX
    BPL OpenNextSolomonPageRoomTile
    RTS

.assert * - RunSpecialRoomScriptThread = $234, error, "unexpected special-room script module size"
