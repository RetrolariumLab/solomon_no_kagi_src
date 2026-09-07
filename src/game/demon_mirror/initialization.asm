; Place a newly allocated Demon Mirror placeholder at one mirror coordinate

.segment "PRG_DEMON_MIRROR_INITIALIZATION"

DemonMirrorObjectState = $C6
DemonMirrorObjectType = $04
DemonMirrorObjectAction = $0C

InitializeDemonMirrorObject:
    LDA DemonMirrorYPositions,X
    STA SpawnYPosition
    LDA DemonMirrorXPositions,X
    STA SpawnXPosition
    JSR InitializeEnemy
    LDA #DemonMirrorObjectType
    STA MapInteractionX
    LDA #DemonMirrorObjectState
    STA MapInteractionY
    LDA #DemonMirrorObjectAction
    JSR InitializeObjectStateHeader
    RTS
