; Object-type action selectors and paired fixed-point motion values

.macro ObjectMotionVectorSelector index
    .byte index
.endmacro

.macro ObjectRoomStateMotionSelector mask
    .byte mask
.endmacro

.macro ObjectMotionVector ntsc_y_velocity, ntsc_x_velocity, pal_y_velocity, pal_x_velocity
    .if SolomonRevision = SolomonRevisionEurope
        .byte pal_y_velocity, pal_x_velocity
    .else
        .byte ntsc_y_velocity, ntsc_x_velocity
    .endif
.endmacro

.segment "PRG_OBJECT_MOTION_SELECTOR_POINTERS"

ObjectMotionSelectorPointers:
    .word ObjectMotionSelectorsType00
    .word ObjectMotionSelectorsType04
    .word ObjectMotionSelectorsType00
    .word ObjectMotionSelectorsType04
    .word ObjectMotionSelectorsType04
    .word ObjectMotionSelectorsType14
    .word ObjectMotionSelectorsType18
    .word ObjectMotionSelectorsType1C
    .word ObjectMotionSelectorsType20
    .word ObjectMotionSelectorsType24
    .word ObjectMotionSelectorsType28
    .word ObjectMotionSelectorsType28
    .word ObjectMotionSelectorsType30
    .word ObjectMotionSelectorsType34
    .word ObjectMotionSelectorsType38
    .word ObjectMotionSelectorsType3C
    .word ObjectMotionSelectorsType30
    .word ObjectMotionSelectorsType34
    .word ObjectMotionSelectorsType38
    .word ObjectMotionSelectorsType3C
    .word ObjectMotionSelectorsType50
    .word ObjectMotionSelectorsType54
    .word ObjectMotionSelectorsType58
    .word ObjectMotionSelectorsType50
    .word ObjectMotionSelectorsType54
    .word ObjectMotionSelectorsType64
    .word ObjectMotionSelectorsType68
    .word ObjectMotionSelectorsType50
    .word ObjectMotionSelectorsType70
    .word ObjectMotionSelectorsType74
    .word ObjectMotionSelectorsType78
    .word ObjectMotionSelectorsType50
    .word ObjectMotionSelectorsType24

.segment "PRG_OBJECT_MOTION_SELECTORS"

ObjectMotionSelectorsType00:
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $01
    ObjectMotionVectorSelector $01
    ObjectMotionVectorSelector $01
    ObjectMotionVectorSelector $01
    ObjectMotionVectorSelector $02
    ObjectMotionVectorSelector $02
    ObjectMotionVectorSelector $02
    ObjectMotionVectorSelector $02
    ObjectMotionVectorSelector $04
    ObjectMotionVectorSelector $05
    ObjectMotionVectorSelector $03
    ObjectMotionVectorSelector $03
    ObjectMotionVectorSelector $06
    ObjectMotionVectorSelector $07
    ObjectMotionVectorSelector $03
    ObjectMotionVectorSelector $03
    ObjectMotionVectorSelector $08
    ObjectMotionVectorSelector $09
    ObjectMotionVectorSelector $01
    ObjectMotionVectorSelector $01
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00

ObjectMotionSelectorsType50:
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $11
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $17
    ObjectMotionVectorSelector $18
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $03
    ObjectMotionVectorSelector $03
    ObjectMotionVectorSelector $03
    ObjectMotionVectorSelector $03

ObjectMotionSelectorsType14:
    ObjectMotionVectorSelector $02
    ObjectMotionVectorSelector $0E
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00

ObjectMotionSelectorsType1C:
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $0E
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00

ObjectMotionSelectorsType20:
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00

ObjectMotionSelectorsType28:
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $0A
    ObjectMotionVectorSelector $0B
    ObjectMotionVectorSelector $0C
    ObjectMotionVectorSelector $0D

ObjectMotionSelectorsType18:
    ObjectMotionVectorSelector $0E
    ObjectMotionVectorSelector $0E
    ObjectMotionVectorSelector $0E
    ObjectMotionVectorSelector $0E

ObjectMotionSelectorsType30:
    ObjectMotionVectorSelector $10
    ObjectMotionVectorSelector $10
    ObjectMotionVectorSelector $0F
    ObjectMotionVectorSelector $0F
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $10
    ObjectMotionVectorSelector $10
    ObjectMotionVectorSelector $0F
    ObjectMotionVectorSelector $0F

ObjectMotionSelectorsType34:
    ObjectMotionVectorSelector $11
    ObjectMotionVectorSelector $11
    ObjectMotionVectorSelector $12
    ObjectMotionVectorSelector $12
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $11
    ObjectMotionVectorSelector $11
    ObjectMotionVectorSelector $12
    ObjectMotionVectorSelector $12

ObjectMotionSelectorsType38:
    ObjectMotionVectorSelector $14
    ObjectMotionVectorSelector $14
    ObjectMotionVectorSelector $13
    ObjectMotionVectorSelector $13
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $14
    ObjectMotionVectorSelector $14
    ObjectMotionVectorSelector $13
    ObjectMotionVectorSelector $13

ObjectMotionSelectorsType3C:
    ObjectMotionVectorSelector $15
    ObjectMotionVectorSelector $15
    ObjectMotionVectorSelector $16
    ObjectMotionVectorSelector $16
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $15
    ObjectMotionVectorSelector $15
    ObjectMotionVectorSelector $16
    ObjectMotionVectorSelector $16

ObjectMotionSelectorsType54:
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $1F
    ObjectMotionVectorSelector $20
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $03
    ObjectMotionVectorSelector $03
    ObjectMotionVectorSelector $03
    ObjectMotionVectorSelector $03

ObjectMotionSelectorsType58:
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00

ObjectMotionSelectorsType04:
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $19
    ObjectMotionVectorSelector $1A
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $03
    ObjectMotionVectorSelector $03
    ObjectMotionVectorSelector $03
    ObjectMotionVectorSelector $03

ObjectMotionSelectorsType64:
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $21
    ObjectMotionVectorSelector $22
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $03
    ObjectMotionVectorSelector $03
    ObjectMotionVectorSelector $03
    ObjectMotionVectorSelector $03

ObjectMotionSelectorsType68:
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $1B
    ObjectMotionVectorSelector $1C
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $03
    ObjectMotionVectorSelector $03
    ObjectMotionVectorSelector $03
    ObjectMotionVectorSelector $03

ObjectMotionSelectorsType70:
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $17
    ObjectMotionVectorSelector $18
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $1B
    ObjectMotionVectorSelector $1C
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $03
    ObjectMotionVectorSelector $03
    ObjectMotionVectorSelector $03
    ObjectMotionVectorSelector $03

ObjectMotionSelectorsType74:
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $1D
    ObjectMotionVectorSelector $1E
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $17
    ObjectMotionVectorSelector $18
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $03
    ObjectMotionVectorSelector $03
    ObjectMotionVectorSelector $03
    ObjectMotionVectorSelector $03

ObjectMotionSelectorsType78:
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $1B
    ObjectMotionVectorSelector $1C
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $03
    ObjectMotionVectorSelector $03
    ObjectMotionVectorSelector $03
    ObjectMotionVectorSelector $03

ObjectMotionSelectorsType24:
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $00
    ObjectMotionVectorSelector $03
    ObjectMotionVectorSelector $03
    ObjectMotionVectorSelector $03
    ObjectMotionVectorSelector $03
    ObjectMotionVectorSelector $03
    ObjectMotionVectorSelector $03
    ObjectMotionVectorSelector $03
    ObjectMotionVectorSelector $03
    ObjectMotionVectorSelector $03
    ObjectMotionVectorSelector $03
    ObjectMotionVectorSelector $03
    ObjectMotionVectorSelector $03

.assert * - ObjectMotionSelectorsType00 = $0184, error, "unexpected object motion selector data size"

.segment "PRG_OBJECT_MOTION_VALUES"

ObjectMotionValues:
    ObjectMotionVector $00, $00, $00, $00
    ObjectMotionVector $40, $00, $40, $00
    ObjectMotionVector $C3, $00, $C4, $00
    ObjectMotionVector $80, $00, $80, $00
    ObjectMotionVector $80, $10, $80, $13
    ObjectMotionVector $80, $70, $80, $6D
    ObjectMotionVector $80, $18, $80, $1C
    ObjectMotionVector $80, $68, $80, $64
    ObjectMotionVector $40, $18, $40, $1C
    ObjectMotionVector $40, $68, $40, $64
    ObjectMotionVector $00, $30, $00, $39
    ObjectMotionVector $00, $41, $00, $47
    ObjectMotionVector $41, $00, $41, $00
    ObjectMotionVector $30, $00, $30, $00
    ObjectMotionVector $40, $40, $40, $40
    ObjectMotionVector $1C, $00, $21, $00
    ObjectMotionVector $64, $00, $5F, $00
    ObjectMotionVector $00, $1C, $00, $21
    ObjectMotionVector $00, $64, $00, $5F
    ObjectMotionVector $2E, $00, $3E, $00
    ObjectMotionVector $52, $00, $49, $00
    ObjectMotionVector $00, $27, $00, $2E
    ObjectMotionVector $00, $52, $00, $52
    ObjectMotionVector $80, $13, $80, $16
    ObjectMotionVector $80, $6D, $80, $6A
    ObjectMotionVector $80, $2B, $80, $33
    ObjectMotionVector $80, $55, $80, $4D
    ObjectMotionVector $80, $0C, $80, $0E
    ObjectMotionVector $80, $74, $80, $72
    ObjectMotionVector $80, $26, $80, $2D
    ObjectMotionVector $80, $5A, $80, $53
    ObjectMotionVector $80, $1C, $80, $21
    ObjectMotionVector $80, $64, $80, $5F
    ObjectMotionVector $80, $27, $80, $2E
    ObjectMotionVector $80, $52, $80, $52

.assert * - ObjectMotionValues = 35 * 2, error, "unexpected object motion vector count"

.segment "PRG_FILLER_BEFORE_DEMON_MIRROR_DATA"

FillerBeforeDemonMirrorData:
.if SolomonRevision = SolomonRevisionEurope
    .res 33, $FF
.else
    .byte $00, $00, $FF, $00
    .byte $FF, $00, $FF, $00, $FF, $00, $FF, $00
    .byte $FF, $00, $FF, $00, $FF, $FF, $00, $FF
    .byte $00, $FF, $00, $FF, $00, $FF, $00, $FF
    .byte $00, $FF, $00, $FF, $00
.endif

.assert * - FillerBeforeDemonMirrorData = 33, error, "unexpected pre-Demon-Mirror filler size"
