; Collision-response pointers indexed by object collision-mask low nibble

.segment "PRG_OBJECT_COLLISION_HANDLERS"

ObjectCollisionHandlerTable:
    .addr HandleObjectCollisionMask00
    .addr HandleObjectCollisionMask01
    .addr HandleObjectCollisionMask02
    .addr HandleObjectCollisionMask03
    .addr HandleObjectCollisionMask04
    .addr HandleObjectCollisionMask05
    .addr HandleObjectCollisionMask06
    .addr HandleObjectCollisionMask07
    .addr HandleObjectCollisionMask08
    .addr HandleObjectCollisionMask09
    .addr HandleObjectCollisionMask0A
    .addr HandleObjectCollisionMask0B
    .addr HandleObjectCollisionMask0C
    .addr HandleObjectCollisionMask0D
    .addr HandleObjectCollisionMask0E
    .addr HandleObjectCollisionMask00
