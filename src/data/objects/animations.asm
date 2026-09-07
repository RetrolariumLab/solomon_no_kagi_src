; Object action descriptors, variant selectors, and sprite frame records

.macro ObjectAnimationDescriptor initial_phase, delay, frames
    .byte initial_phase, delay * 2
    .word frames
.endmacro

.macro VariantObjectAnimationDescriptor initial_phase, delay, selector
    .byte initial_phase, delay * 2 + 1
    .word selector
.endmacro

.segment "PRG_OBJECT_ANIMATION_DEFINITIONS"

ObjectAnimationDescriptorsType00:
    ObjectAnimationDescriptor $10, $40, ObjectAnimationFrames005
    ObjectAnimationDescriptor $10, $40, ObjectAnimationFrames007
    ObjectAnimationDescriptor $10, $40, ObjectAnimationFrames005
    ObjectAnimationDescriptor $10, $40, ObjectAnimationFrames007
    ObjectAnimationDescriptor $10, $40, ObjectAnimationFrames000
    ObjectAnimationDescriptor $10, $40, ObjectAnimationFrames001
    ObjectAnimationDescriptor $10, $40, ObjectAnimationFrames005
    ObjectAnimationDescriptor $10, $40, ObjectAnimationFrames007
    ObjectAnimationDescriptor $10, $40, ObjectAnimationFrames000
    ObjectAnimationDescriptor $10, $40, ObjectAnimationFrames001
    ObjectAnimationDescriptor $10, $40, ObjectAnimationFrames000
    ObjectAnimationDescriptor $10, $40, ObjectAnimationFrames001
    ObjectAnimationDescriptor $10, $40, ObjectAnimationFrames002
    ObjectAnimationDescriptor $10, $40, ObjectAnimationFrames003
    ObjectAnimationDescriptor $10, $40, ObjectAnimationFrames002
    ObjectAnimationDescriptor $10, $40, ObjectAnimationFrames003
    ObjectAnimationDescriptor $32, $06, ObjectAnimationFrames004
    ObjectAnimationDescriptor $32, $06, ObjectAnimationFrames006
    ObjectAnimationDescriptor $10, $40, ObjectAnimationFrames004
    ObjectAnimationDescriptor $10, $40, ObjectAnimationFrames006
    ObjectAnimationDescriptor $43, $03, ObjectAnimationFrames008
    ObjectAnimationDescriptor $43, $03, ObjectAnimationFrames010
    ObjectAnimationDescriptor $10, $20, ObjectAnimationFrames002
    ObjectAnimationDescriptor $10, $20, ObjectAnimationFrames003
    ObjectAnimationDescriptor $10, $20, ObjectAnimationFrames009
    ObjectAnimationDescriptor $10, $20, ObjectAnimationFrames011
    ObjectAnimationDescriptor $10, $20, ObjectAnimationFrames002
    ObjectAnimationDescriptor $10, $20, ObjectAnimationFrames003
    ObjectAnimationDescriptor $32, $05, ObjectAnimationFrames012
    ObjectAnimationDescriptor $32, $05, ObjectAnimationFrames013
    ObjectAnimationDescriptor $32, $05, ObjectAnimationFrames014
    ObjectAnimationDescriptor $32, $05, ObjectAnimationFrames015
    ObjectAnimationDescriptor $10, $20, ObjectAnimationFrames016
    ObjectAnimationDescriptor $10, $20, ObjectAnimationFrames017
    ObjectAnimationDescriptor $10, $20, ObjectAnimationFrames018
    ObjectAnimationDescriptor $10, $20, ObjectAnimationFrames018

ObjectAnimationDescriptorsType04:
    ObjectAnimationDescriptor $43, $05, ObjectAnimationFrames019
    ObjectAnimationDescriptor $32, $05, ObjectAnimationFrames020
    ObjectAnimationDescriptor $21, $06, ObjectAnimationFrames021
    ObjectAnimationDescriptor $21, $06, ObjectAnimationFrames022
    ObjectAnimationDescriptor $21, $06, ObjectAnimationFrames023
    ObjectAnimationDescriptor $21, $06, ObjectAnimationFrames024
    ObjectAnimationDescriptor $21, $06, ObjectAnimationFrames025
    ObjectAnimationDescriptor $21, $06, ObjectAnimationFrames026
    ObjectAnimationDescriptor $21, $06, ObjectAnimationFrames027
    ObjectAnimationDescriptor $10, $20, ObjectAnimationFrames020
    ObjectAnimationDescriptor $76, $04, ObjectAnimationFrames028
    ObjectAnimationDescriptor $76, $04, ObjectAnimationFrames029
    ObjectAnimationDescriptor $54, $06, ObjectAnimationFrames030
    ObjectAnimationDescriptor $21, $05, ObjectAnimationFrames055
    ObjectAnimationDescriptor $10, $20, ObjectAnimationFrames002
    ObjectAnimationDescriptor $10, $20, ObjectAnimationFrames003

ObjectAnimationDescriptorsType0C:
    ObjectAnimationDescriptor $21, $04, ObjectAnimationFrames031
    ObjectAnimationDescriptor $21, $04, ObjectAnimationFrames032
    ObjectAnimationDescriptor $21, $04, ObjectAnimationFrames033
    ObjectAnimationDescriptor $21, $04, ObjectAnimationFrames034
    ObjectAnimationDescriptor $10, $20, ObjectAnimationFrames062
    ObjectAnimationDescriptor $10, $20, ObjectAnimationFrames062
    ObjectAnimationDescriptor $10, $20, ObjectAnimationFrames062
    ObjectAnimationDescriptor $10, $20, ObjectAnimationFrames062

ObjectAnimationDescriptorsType10:
    ObjectAnimationDescriptor $21, $04, ObjectAnimationFrames035
    ObjectAnimationDescriptor $21, $04, ObjectAnimationFrames036
    ObjectAnimationDescriptor $21, $04, ObjectAnimationFrames037
    ObjectAnimationDescriptor $21, $04, ObjectAnimationFrames038
    ObjectAnimationDescriptor $10, $20, ObjectAnimationFrames062
    ObjectAnimationDescriptor $10, $20, ObjectAnimationFrames062
    ObjectAnimationDescriptor $10, $20, ObjectAnimationFrames062
    ObjectAnimationDescriptor $10, $20, ObjectAnimationFrames062

ObjectAnimationDescriptorsType14:
    ObjectAnimationDescriptor $76, $06, ObjectAnimationFrames039
    ObjectAnimationDescriptor $76, $06, ObjectAnimationFrames039
    ObjectAnimationDescriptor $10, $20, ObjectAnimationFrames040
    ObjectAnimationDescriptor $10, $20, ObjectAnimationFrames041
    ObjectAnimationDescriptor $10, $20, ObjectAnimationFrames042
    ObjectAnimationDescriptor $10, $20, ObjectAnimationFrames043
    ObjectAnimationDescriptor $10, $20, ObjectAnimationFrames044
    ObjectAnimationDescriptor $10, $20, ObjectAnimationFrames044
    ObjectAnimationDescriptor $10, $20, ObjectAnimationFrames045
    ObjectAnimationDescriptor $10, $20, ObjectAnimationFrames046
    ObjectAnimationDescriptor $10, $20, ObjectAnimationFrames047
    ObjectAnimationDescriptor $10, $20, ObjectAnimationFrames048
    ObjectAnimationDescriptor $10, $20, ObjectAnimationFrames049
    ObjectAnimationDescriptor $10, $20, ObjectAnimationFrames050
    ObjectAnimationDescriptor $10, $20, ObjectAnimationFrames051
    ObjectAnimationDescriptor $10, $20, ObjectAnimationFrames052

ObjectAnimationDescriptorsType18:
    ObjectAnimationDescriptor $10, $20, ObjectAnimationFrames053
    ObjectAnimationDescriptor $10, $20, ObjectAnimationFrames053
    ObjectAnimationDescriptor $10, $20, ObjectAnimationFrames054
    ObjectAnimationDescriptor $10, $20, ObjectAnimationFrames054

ObjectAnimationDescriptorsType1C:
    ObjectAnimationDescriptor $21, $05, ObjectAnimationFrames055
    ObjectAnimationDescriptor $21, $05, ObjectAnimationFrames055
    ObjectAnimationDescriptor $21, $05, ObjectAnimationFrames055
    ObjectAnimationDescriptor $21, $05, ObjectAnimationFrames055
    VariantObjectAnimationDescriptor $21, $04, ObjectAnimationVariantSelector00
    VariantObjectAnimationDescriptor $21, $04, ObjectAnimationVariantSelector01
    VariantObjectAnimationDescriptor $21, $04, ObjectAnimationVariantSelector00
    VariantObjectAnimationDescriptor $21, $04, ObjectAnimationVariantSelector00
    VariantObjectAnimationDescriptor $21, $04, ObjectAnimationVariantSelector00
    VariantObjectAnimationDescriptor $21, $04, ObjectAnimationVariantSelector01
    VariantObjectAnimationDescriptor $21, $04, ObjectAnimationVariantSelector00
    VariantObjectAnimationDescriptor $21, $04, ObjectAnimationVariantSelector00
    ObjectAnimationDescriptor $32, $07, ObjectAnimationFrames056
    ObjectAnimationDescriptor $43, $04, ObjectAnimationFrames057
    ObjectAnimationDescriptor $32, $06, ObjectAnimationFrames056
    ObjectAnimationDescriptor $32, $06, ObjectAnimationFrames056
    VariantObjectAnimationDescriptor $21, $04, ObjectAnimationVariantSelector00
    VariantObjectAnimationDescriptor $21, $04, ObjectAnimationVariantSelector01
    VariantObjectAnimationDescriptor $21, $04, ObjectAnimationVariantSelector00
    VariantObjectAnimationDescriptor $21, $04, ObjectAnimationVariantSelector00
    VariantObjectAnimationDescriptor $21, $04, ObjectAnimationVariantSelector00
    VariantObjectAnimationDescriptor $21, $04, ObjectAnimationVariantSelector01
    VariantObjectAnimationDescriptor $21, $04, ObjectAnimationVariantSelector00
    VariantObjectAnimationDescriptor $21, $04, ObjectAnimationVariantSelector00
    VariantObjectAnimationDescriptor $21, $04, ObjectAnimationVariantSelector00
    VariantObjectAnimationDescriptor $21, $04, ObjectAnimationVariantSelector01
    VariantObjectAnimationDescriptor $21, $04, ObjectAnimationVariantSelector00
    VariantObjectAnimationDescriptor $21, $04, ObjectAnimationVariantSelector00

ObjectAnimationVariantSelector00:
    .word ObjectAnimationFrames058, ObjectAnimationFrames060, ObjectAnimationFrames058, ObjectAnimationFrames060

ObjectAnimationVariantSelector01:
    .word ObjectAnimationFrames059, ObjectAnimationFrames061, ObjectAnimationFrames059, ObjectAnimationFrames061

ObjectAnimationDescriptorsType20:
    ObjectAnimationDescriptor $21, $04, ObjectAnimationFrames062
    ObjectAnimationDescriptor $21, $04, ObjectAnimationFrames062
    ObjectAnimationDescriptor $21, $04, ObjectAnimationFrames062
    ObjectAnimationDescriptor $21, $04, ObjectAnimationFrames062
    ObjectAnimationDescriptor $32, $05, ObjectAnimationFrames020
    ObjectAnimationDescriptor $32, $05, ObjectAnimationFrames020
    ObjectAnimationDescriptor $32, $05, ObjectAnimationFrames020
    ObjectAnimationDescriptor $32, $05, ObjectAnimationFrames020
    ObjectAnimationDescriptor $21, $04, ObjectAnimationFrames063
    ObjectAnimationDescriptor $21, $04, ObjectAnimationFrames064
    ObjectAnimationDescriptor $21, $04, ObjectAnimationFrames065
    ObjectAnimationDescriptor $21, $04, ObjectAnimationFrames066

ObjectAnimationDescriptorsType24:
    ObjectAnimationDescriptor $10, $20, ObjectAnimationFrames068
    ObjectAnimationDescriptor $10, $20, ObjectAnimationFrames070
    ObjectAnimationDescriptor $10, $20, ObjectAnimationFrames072
    ObjectAnimationDescriptor $10, $20, ObjectAnimationFrames074
    ObjectAnimationDescriptor $21, $04, ObjectAnimationFrames067
    ObjectAnimationDescriptor $21, $04, ObjectAnimationFrames069
    ObjectAnimationDescriptor $21, $04, ObjectAnimationFrames071
    ObjectAnimationDescriptor $21, $04, ObjectAnimationFrames073

ObjectAnimationDescriptorsType28:
    ObjectAnimationDescriptor $43, $04, ObjectAnimationFrames075
    ObjectAnimationDescriptor $43, $04, ObjectAnimationFrames075
    ObjectAnimationDescriptor $43, $04, ObjectAnimationFrames075
    ObjectAnimationDescriptor $43, $04, ObjectAnimationFrames075

ObjectAnimationDescriptorsType30:
    ObjectAnimationDescriptor $21, $04, ObjectAnimationFrames076
    ObjectAnimationDescriptor $21, $04, ObjectAnimationFrames077
    ObjectAnimationDescriptor $10, $04, ObjectAnimationFrames078
    ObjectAnimationDescriptor $10, $04, ObjectAnimationFrames079
    ObjectAnimationDescriptor $10, $05, ObjectAnimationFrames081
    ObjectAnimationDescriptor $10, $05, ObjectAnimationFrames083
    ObjectAnimationDescriptor $21, $0A, ObjectAnimationFrames080
    ObjectAnimationDescriptor $21, $0A, ObjectAnimationFrames082
    ObjectAnimationDescriptor $10, $0A, ObjectAnimationFrames081
    ObjectAnimationDescriptor $10, $0A, ObjectAnimationFrames083
    ObjectAnimationDescriptor $10, $0A, ObjectAnimationFrames080
    ObjectAnimationDescriptor $10, $0A, ObjectAnimationFrames082
    ObjectAnimationDescriptor $21, $04, ObjectAnimationFrames076
    ObjectAnimationDescriptor $21, $04, ObjectAnimationFrames077
    ObjectAnimationDescriptor $10, $04, ObjectAnimationFrames078
    ObjectAnimationDescriptor $10, $04, ObjectAnimationFrames079

ObjectAnimationDescriptorsType34:
    ObjectAnimationDescriptor $21, $06, ObjectAnimationFrames084
    ObjectAnimationDescriptor $21, $06, ObjectAnimationFrames084
    ObjectAnimationDescriptor $21, $06, ObjectAnimationFrames085
    ObjectAnimationDescriptor $21, $06, ObjectAnimationFrames085
    ObjectAnimationDescriptor $21, $05, ObjectAnimationFrames086
    ObjectAnimationDescriptor $21, $05, ObjectAnimationFrames086
    ObjectAnimationDescriptor $21, $05, ObjectAnimationFrames087
    ObjectAnimationDescriptor $21, $05, ObjectAnimationFrames087
    ObjectAnimationDescriptor $10, $0A, ObjectAnimationFrames088
    ObjectAnimationDescriptor $10, $0A, ObjectAnimationFrames088
    ObjectAnimationDescriptor $10, $0A, ObjectAnimationFrames089
    ObjectAnimationDescriptor $10, $0A, ObjectAnimationFrames089
    ObjectAnimationDescriptor $21, $06, ObjectAnimationFrames084
    ObjectAnimationDescriptor $21, $06, ObjectAnimationFrames084
    ObjectAnimationDescriptor $21, $06, ObjectAnimationFrames085
    ObjectAnimationDescriptor $21, $06, ObjectAnimationFrames085

ObjectAnimationDescriptorsType50:
    ObjectAnimationDescriptor $32, $06, ObjectAnimationFrames090
    ObjectAnimationDescriptor $32, $06, ObjectAnimationFrames090
    ObjectAnimationDescriptor $32, $06, ObjectAnimationFrames090
    ObjectAnimationDescriptor $32, $06, ObjectAnimationFrames090
    ObjectAnimationDescriptor $32, $06, ObjectAnimationFrames090
    ObjectAnimationDescriptor $32, $06, ObjectAnimationFrames090
    ObjectAnimationDescriptor $32, $06, ObjectAnimationFrames090
    ObjectAnimationDescriptor $32, $06, ObjectAnimationFrames090
    ObjectAnimationDescriptor $10, $20, ObjectAnimationFrames092
    ObjectAnimationDescriptor $10, $20, ObjectAnimationFrames093
    ObjectAnimationDescriptor $43, $03, ObjectAnimationFrames008
    ObjectAnimationDescriptor $10, $20, ObjectAnimationFrames091
    ObjectAnimationDescriptor $21, $04, ObjectAnimationFrames084
    ObjectAnimationDescriptor $21, $06, ObjectAnimationFrames076
    ObjectAnimationDescriptor $43, $0A, ObjectAnimationFrames094
    ObjectAnimationDescriptor $21, $0A, ObjectAnimationFrames098
    ObjectAnimationDescriptor $43, $06, ObjectAnimationFrames103
    ObjectAnimationDescriptor $32, $08, ObjectAnimationFrames107
    ObjectAnimationDescriptor $43, $0C, ObjectAnimationFrames117
    ObjectAnimationDescriptor $42, $04, ObjectAnimationFrames075
    ObjectAnimationDescriptor $43, $0A, ObjectAnimationFrames094
    ObjectAnimationDescriptor $43, $0A, ObjectAnimationFrames094
    ObjectAnimationDescriptor $43, $0A, ObjectAnimationFrames094
    ObjectAnimationDescriptor $43, $0A, ObjectAnimationFrames094
    ObjectAnimationDescriptor $43, $0A, ObjectAnimationFrames094
    ObjectAnimationDescriptor $43, $0A, ObjectAnimationFrames094
    ObjectAnimationDescriptor $43, $0A, ObjectAnimationFrames094
    ObjectAnimationDescriptor $43, $0A, ObjectAnimationFrames094

ObjectAnimationDescriptorsType5C:
    ObjectAnimationDescriptor $32, $06, ObjectAnimationFrames090
    ObjectAnimationDescriptor $32, $06, ObjectAnimationFrames090
    ObjectAnimationDescriptor $32, $06, ObjectAnimationFrames090
    ObjectAnimationDescriptor $32, $06, ObjectAnimationFrames090
    ObjectAnimationDescriptor $10, $20, ObjectAnimationFrames095
    ObjectAnimationDescriptor $10, $20, ObjectAnimationFrames096
    ObjectAnimationDescriptor $10, $20, ObjectAnimationFrames095
    ObjectAnimationDescriptor $10, $20, ObjectAnimationFrames096
    ObjectAnimationDescriptor $32, $06, ObjectAnimationFrames090
    ObjectAnimationDescriptor $32, $06, ObjectAnimationFrames090
    ObjectAnimationDescriptor $32, $06, ObjectAnimationFrames090
    ObjectAnimationDescriptor $32, $06, ObjectAnimationFrames090
    ObjectAnimationDescriptor $21, $04, ObjectAnimationFrames095
    ObjectAnimationDescriptor $21, $04, ObjectAnimationFrames096
    ObjectAnimationDescriptor $10, $20, ObjectAnimationFrames095
    ObjectAnimationDescriptor $10, $20, ObjectAnimationFrames096
    ObjectAnimationDescriptor $32, $06, ObjectAnimationFrames090
    ObjectAnimationDescriptor $32, $06, ObjectAnimationFrames090
    ObjectAnimationDescriptor $32, $06, ObjectAnimationFrames090
    ObjectAnimationDescriptor $32, $06, ObjectAnimationFrames090
    ObjectAnimationDescriptor $21, $0A, ObjectAnimationFrames098
    ObjectAnimationDescriptor $21, $0A, ObjectAnimationFrames100
    ObjectAnimationDescriptor $21, $0A, ObjectAnimationFrames098
    ObjectAnimationDescriptor $21, $0A, ObjectAnimationFrames100
    ObjectAnimationDescriptor $21, $04, ObjectAnimationFrames097
    ObjectAnimationDescriptor $21, $04, ObjectAnimationFrames099
    ObjectAnimationDescriptor $21, $04, ObjectAnimationFrames097
    ObjectAnimationDescriptor $21, $04, ObjectAnimationFrames099

ObjectAnimationDescriptorsType68:
    ObjectAnimationDescriptor $21, $04, ObjectAnimationFrames103
    ObjectAnimationDescriptor $21, $04, ObjectAnimationFrames104
    ObjectAnimationDescriptor $21, $04, ObjectAnimationFrames103
    ObjectAnimationDescriptor $21, $04, ObjectAnimationFrames104
    ObjectAnimationDescriptor $32, $06, ObjectAnimationFrames090
    ObjectAnimationDescriptor $32, $06, ObjectAnimationFrames090
    ObjectAnimationDescriptor $32, $06, ObjectAnimationFrames090
    ObjectAnimationDescriptor $32, $06, ObjectAnimationFrames090
    ObjectAnimationDescriptor $21, $04, ObjectAnimationFrames103
    ObjectAnimationDescriptor $21, $04, ObjectAnimationFrames104
    ObjectAnimationDescriptor $21, $04, ObjectAnimationFrames103
    ObjectAnimationDescriptor $21, $04, ObjectAnimationFrames104
    ObjectAnimationDescriptor $65, $04, ObjectAnimationFrames101
    ObjectAnimationDescriptor $65, $04, ObjectAnimationFrames102
    ObjectAnimationDescriptor $10, $20, ObjectAnimationFrames101
    ObjectAnimationDescriptor $10, $20, ObjectAnimationFrames102
    ObjectAnimationDescriptor $21, $04, ObjectAnimationFrames103
    ObjectAnimationDescriptor $21, $04, ObjectAnimationFrames104
    ObjectAnimationDescriptor $21, $04, ObjectAnimationFrames103
    ObjectAnimationDescriptor $21, $04, ObjectAnimationFrames104
    ObjectAnimationDescriptor $43, $06, ObjectAnimationFrames103
    ObjectAnimationDescriptor $43, $06, ObjectAnimationFrames104
    ObjectAnimationDescriptor $10, $20, ObjectAnimationFrames103
    ObjectAnimationDescriptor $10, $20, ObjectAnimationFrames104
    ObjectAnimationDescriptor $21, $04, ObjectAnimationFrames105
    ObjectAnimationDescriptor $21, $04, ObjectAnimationFrames106
    ObjectAnimationDescriptor $21, $04, ObjectAnimationFrames105
    ObjectAnimationDescriptor $21, $04, ObjectAnimationFrames106

ObjectAnimationDescriptorsType70:
    ObjectAnimationDescriptor $32, $06, ObjectAnimationFrames108
    ObjectAnimationDescriptor $32, $06, ObjectAnimationFrames110
    ObjectAnimationDescriptor $10, $04, ObjectAnimationFrames108
    ObjectAnimationDescriptor $10, $04, ObjectAnimationFrames110
    ObjectAnimationDescriptor $32, $06, ObjectAnimationFrames090
    ObjectAnimationDescriptor $32, $06, ObjectAnimationFrames090
    ObjectAnimationDescriptor $32, $06, ObjectAnimationFrames090
    ObjectAnimationDescriptor $32, $06, ObjectAnimationFrames090
    ObjectAnimationDescriptor $32, $06, ObjectAnimationFrames090
    ObjectAnimationDescriptor $32, $06, ObjectAnimationFrames090
    ObjectAnimationDescriptor $32, $06, ObjectAnimationFrames090
    ObjectAnimationDescriptor $32, $06, ObjectAnimationFrames090
    ObjectAnimationDescriptor $32, $06, ObjectAnimationFrames090
    ObjectAnimationDescriptor $32, $06, ObjectAnimationFrames090
    ObjectAnimationDescriptor $32, $06, ObjectAnimationFrames090
    ObjectAnimationDescriptor $32, $06, ObjectAnimationFrames090
    ObjectAnimationDescriptor $43, $04, ObjectAnimationFrames107
    ObjectAnimationDescriptor $43, $04, ObjectAnimationFrames109
    ObjectAnimationDescriptor $10, $20, ObjectAnimationFrames107
    ObjectAnimationDescriptor $10, $20, ObjectAnimationFrames109
    ObjectAnimationDescriptor $32, $08, ObjectAnimationFrames111
    ObjectAnimationDescriptor $32, $08, ObjectAnimationFrames112
    ObjectAnimationDescriptor $10, $20, ObjectAnimationFrames111
    ObjectAnimationDescriptor $10, $20, ObjectAnimationFrames112
    ObjectAnimationDescriptor $21, $04, ObjectAnimationFrames113
    ObjectAnimationDescriptor $21, $04, ObjectAnimationFrames114
    ObjectAnimationDescriptor $21, $04, ObjectAnimationFrames113
    ObjectAnimationDescriptor $21, $04, ObjectAnimationFrames114

ObjectAnimationDescriptorsType78:
    ObjectAnimationDescriptor $21, $04, ObjectAnimationFrames115
    ObjectAnimationDescriptor $21, $04, ObjectAnimationFrames116
    ObjectAnimationDescriptor $10, $20, ObjectAnimationFrames115
    ObjectAnimationDescriptor $10, $20, ObjectAnimationFrames116
    ObjectAnimationDescriptor $32, $06, ObjectAnimationFrames090
    ObjectAnimationDescriptor $32, $06, ObjectAnimationFrames090
    ObjectAnimationDescriptor $32, $06, ObjectAnimationFrames090
    ObjectAnimationDescriptor $32, $06, ObjectAnimationFrames090
    ObjectAnimationDescriptor $43, $0C, ObjectAnimationFrames117
    ObjectAnimationDescriptor $43, $0C, ObjectAnimationFrames118
    ObjectAnimationDescriptor $10, $20, ObjectAnimationFrames115
    ObjectAnimationDescriptor $10, $20, ObjectAnimationFrames116
    ObjectAnimationDescriptor $43, $0C, ObjectAnimationFrames117
    ObjectAnimationDescriptor $43, $0C, ObjectAnimationFrames118
    ObjectAnimationDescriptor $10, $20, ObjectAnimationFrames115
    ObjectAnimationDescriptor $10, $20, ObjectAnimationFrames116
    ObjectAnimationDescriptor $43, $0C, ObjectAnimationFrames117
    ObjectAnimationDescriptor $43, $0C, ObjectAnimationFrames118
    ObjectAnimationDescriptor $10, $20, ObjectAnimationFrames115
    ObjectAnimationDescriptor $10, $20, ObjectAnimationFrames116
    ObjectAnimationDescriptor $43, $0C, ObjectAnimationFrames117
    ObjectAnimationDescriptor $43, $0C, ObjectAnimationFrames118
    ObjectAnimationDescriptor $10, $20, ObjectAnimationFrames115
    ObjectAnimationDescriptor $10, $20, ObjectAnimationFrames116
    ObjectAnimationDescriptor $21, $04, ObjectAnimationFrames119
    ObjectAnimationDescriptor $21, $04, ObjectAnimationFrames120
    ObjectAnimationDescriptor $21, $04, ObjectAnimationFrames119
    ObjectAnimationDescriptor $21, $04, ObjectAnimationFrames120

ObjectAnimationDescriptorsType80:
    ObjectAnimationDescriptor $65, $08, ObjectAnimationFrames121
    ObjectAnimationDescriptor $65, $08, ObjectAnimationFrames121
    ObjectAnimationDescriptor $65, $08, ObjectAnimationFrames121
    ObjectAnimationDescriptor $65, $08, ObjectAnimationFrames121
    VariantObjectAnimationDescriptor $54, $02, ObjectAnimationVariantSelector02
    VariantObjectAnimationDescriptor $54, $02, ObjectAnimationVariantSelector02
    VariantObjectAnimationDescriptor $54, $02, ObjectAnimationVariantSelector02
    VariantObjectAnimationDescriptor $54, $02, ObjectAnimationVariantSelector02
    VariantObjectAnimationDescriptor $54, $02, ObjectAnimationVariantSelector02
    VariantObjectAnimationDescriptor $54, $02, ObjectAnimationVariantSelector02
    VariantObjectAnimationDescriptor $54, $02, ObjectAnimationVariantSelector02
    VariantObjectAnimationDescriptor $54, $02, ObjectAnimationVariantSelector02
    VariantObjectAnimationDescriptor $54, $02, ObjectAnimationVariantSelector02
    VariantObjectAnimationDescriptor $54, $02, ObjectAnimationVariantSelector02
    VariantObjectAnimationDescriptor $54, $02, ObjectAnimationVariantSelector02
    VariantObjectAnimationDescriptor $54, $02, ObjectAnimationVariantSelector02
    VariantObjectAnimationDescriptor $54, $02, ObjectAnimationVariantSelector03
    VariantObjectAnimationDescriptor $54, $02, ObjectAnimationVariantSelector03
    VariantObjectAnimationDescriptor $54, $02, ObjectAnimationVariantSelector03
    VariantObjectAnimationDescriptor $54, $02, ObjectAnimationVariantSelector03
    VariantObjectAnimationDescriptor $54, $02, ObjectAnimationVariantSelector02
    VariantObjectAnimationDescriptor $54, $02, ObjectAnimationVariantSelector02
    VariantObjectAnimationDescriptor $54, $02, ObjectAnimationVariantSelector02
    VariantObjectAnimationDescriptor $54, $02, ObjectAnimationVariantSelector02
    VariantObjectAnimationDescriptor $54, $02, ObjectAnimationVariantSelector02
    VariantObjectAnimationDescriptor $54, $02, ObjectAnimationVariantSelector02
    VariantObjectAnimationDescriptor $54, $02, ObjectAnimationVariantSelector02
    VariantObjectAnimationDescriptor $54, $02, ObjectAnimationVariantSelector02

ObjectAnimationVariantSelector02:
    .word ObjectAnimationFrames124, ObjectAnimationFrames125, ObjectAnimationFrames124, ObjectAnimationFrames125

ObjectAnimationVariantSelector03:
    .word ObjectAnimationFrames122, ObjectAnimationFrames123, ObjectAnimationFrames122, ObjectAnimationFrames123

.assert * - ObjectAnimationDescriptorsType00 = $0570, error, "unexpected object animation definition size"

.segment "PRG_OBJECT_ANIMATION_FRAMES"

; Each row below holds one or two three-byte sprite frame records
ObjectAnimationFrames000:
    .byte $0A, $E2, $12
ObjectAnimationFrames001:
    .byte $E2, $0A, $00
ObjectAnimationFrames002:
    .byte $02, $00, $12
ObjectAnimationFrames003:
    .byte $00, $02, $00
ObjectAnimationFrames004:
    .byte $22, $20, $12, $2A, $28, $12
ObjectAnimationFrames005:
    .byte $26, $24, $12
ObjectAnimationFrames006:
    .byte $20, $22, $00, $28, $2A, $00
ObjectAnimationFrames007:
    .byte $24, $26, $00
ObjectAnimationFrames008:
    .byte $12, $10, $12, $0E, $0C, $12
ObjectAnimationFrames009:
    .byte $0A, $08, $12, $06, $04, $12
ObjectAnimationFrames010:
    .byte $10, $12, $00, $0C, $0E, $00
ObjectAnimationFrames011:
    .byte $08, $0A, $00, $04, $06, $00
ObjectAnimationFrames012:
    .byte $16, $18, $12, $16, $18, $12
    .byte $16, $14, $12
ObjectAnimationFrames013:
    .byte $18, $16, $00, $18, $16, $00
    .byte $14, $16, $00
ObjectAnimationFrames014:
    .byte $1E, $1A, $12, $1E, $1A, $12
    .byte $1E, $1C, $12
ObjectAnimationFrames015:
    .byte $1A, $1E, $00, $1A, $1E, $00
    .byte $1C, $1E, $00
ObjectAnimationFrames016:
    .byte $BE, $BC, $12
ObjectAnimationFrames017:
    .byte $BC, $BE, $00
ObjectAnimationFrames018:
    .byte $9E, $9E, $86
ObjectAnimationFrames019:
    .byte $AE, $AE, $86, $AE, $AE, $86
    .byte $B2, $B2, $CF, $B0, $B0, $CE
ObjectAnimationFrames020:
    .byte $B6, $B6, $87, $B2, $B2, $CF
    .byte $B0, $B0, $CE
ObjectAnimationFrames021:
    .byte $DE, $9E, $86, $DE, $AE, $86
ObjectAnimationFrames022:
    .byte $9E, $DE, $86, $AE, $DE, $86
ObjectAnimationFrames023:
    .byte $9E, $DE, $86, $8C, $DE, $86
ObjectAnimationFrames024:
    .byte $DE, $9E, $86, $DE, $8C, $86
ObjectAnimationFrames025:
    .byte $B4, $B4, $86, $8C, $8C, $86
ObjectAnimationFrames026:
    .byte $B4, $B4, $86, $8C, $8C, $86
ObjectAnimationFrames027:
    .byte $B6, $B6, $86, $AE, $AE, $86
ObjectAnimationFrames028:
    .byte $82, $7E, $B7, $82, $7E, $96
    .byte $82, $80, $B7, $82, $7E, $96
    .byte $82, $80, $96, $82, $7E, $B7
    .byte $82, $7E, $96
ObjectAnimationFrames029:
    .byte $7E, $82, $A5, $7E, $82, $84
    .byte $80, $82, $A5, $7E, $82, $84
    .byte $80, $82, $84, $7E, $82, $A5
    .byte $7E, $82, $84
ObjectAnimationFrames030:
    .byte $B6, $B6, $4B, $BA, $BA, $6A
    .byte $B8, $B8, $6A, $BA, $BA, $4B
    .byte $B8, $B8, $4B
ObjectAnimationFrames031:
    .byte $86, $84, $96, $86, $84, $B7
ObjectAnimationFrames032:
    .byte $84, $86, $A5, $84, $86, $84
ObjectAnimationFrames033:
    .byte $8A, $88, $96, $88, $8A, $84
ObjectAnimationFrames034:
    .byte $88, $8A, $A5, $8A, $88, $B7
ObjectAnimationFrames035:
    .byte $86, $84, $7B, $86, $84, $96
ObjectAnimationFrames036:
    .byte $84, $86, $69, $84, $86, $84
ObjectAnimationFrames037:
    .byte $8A, $88, $5A, $88, $8A, $84
ObjectAnimationFrames038:
    .byte $8A, $88, $7B, $88, $8A, $A5
ObjectAnimationFrames039:
    .byte $D6, $D4, $DE, $D4, $D6, $CC
    .byte $D6, $D4, $DE, $D4, $D6, $CC
    .byte $D6, $D4, $DE, $A6, $A6, $CE
    .byte $8C, $8C, $8F
ObjectAnimationFrames040:
    .byte $EA, $EA, $CE
ObjectAnimationFrames041:
    .byte $E4, $E6, $84
ObjectAnimationFrames042:
    .byte $E8, $E8, $86
ObjectAnimationFrames043:
    .byte $E0, $E0, $86
ObjectAnimationFrames044:
    .byte $EC, $EE, $84
ObjectAnimationFrames045:
    .byte $A8, $AA, $48
ObjectAnimationFrames046:
    .byte $AC, $AA, $48
ObjectAnimationFrames047:
    .byte $C4, $C6, $48
ObjectAnimationFrames048:
    .byte $A8, $AA, $84
ObjectAnimationFrames049:
    .byte $AC, $AA, $84
ObjectAnimationFrames050:
    .byte $C4, $C6, $84
ObjectAnimationFrames051:
    .byte $A8, $AA, $00
ObjectAnimationFrames052:
    .byte $AC, $AA, $00
ObjectAnimationFrames053:
    .byte $FC, $FC, $CE
ObjectAnimationFrames054:
    .byte $FE, $FE, $CE
ObjectAnimationFrames055:
    .byte $B2, $B2, $CF, $B0, $B0, $CE
ObjectAnimationFrames056:
    .byte $9E, $9E, $86, $9E, $9E, $86
    .byte $8C, $8C, $87
ObjectAnimationFrames057:
    .byte $F0, $F2, $84, $F0, $F2, $CC
    .byte $F0, $F2, $84, $F0, $F2, $00
ObjectAnimationFrames058:
    .byte $CE, $CC, $12, $CA, $C8, $12
ObjectAnimationFrames059:
    .byte $CC, $CE, $00, $C8, $CA, $00
ObjectAnimationFrames060:
    .byte $CE, $DA, $DE, $CA, $D8, $DE
ObjectAnimationFrames061:
    .byte $DA, $CE, $CC, $D8, $CA, $CC
ObjectAnimationFrames062:
    .byte $8C, $8C, $A7, $8C, $8C, $86
ObjectAnimationFrames063:
    .byte $8E, $8C, $96, $8E, $8C, $B7
ObjectAnimationFrames064:
    .byte $8C, $8E, $84, $8C, $8E, $A5
ObjectAnimationFrames065:
    .byte $90, $92, $84, $92, $90, $96
ObjectAnimationFrames066:
    .byte $90, $92, $A5, $92, $90, $B7
ObjectAnimationFrames067:
    .byte $42, $40, $96
ObjectAnimationFrames068:
    .byte $42, $40, $5A
ObjectAnimationFrames069:
    .byte $40, $42, $84
ObjectAnimationFrames070:
    .byte $40, $42, $48
ObjectAnimationFrames071:
    .byte $44, $46, $84
ObjectAnimationFrames072:
    .byte $44, $46, $48
ObjectAnimationFrames073:
    .byte $44, $46, $A5
ObjectAnimationFrames074:
    .byte $44, $46, $69
ObjectAnimationFrames075:
    .byte $3C, $3E, $21, $3E, $3C, $DE
    .byte $3E, $3C, $B7, $3C, $3E, $CC
ObjectAnimationFrames076:
    .byte $9C, $94, $5A, $96, $94, $5A
ObjectAnimationFrames077:
    .byte $94, $9C, $48, $94, $96, $48
ObjectAnimationFrames078:
    .byte $9A, $98, $5A
ObjectAnimationFrames079:
    .byte $98, $9A, $48
ObjectAnimationFrames080:
    .byte $9A, $A4, $5A
ObjectAnimationFrames081:
    .byte $A2, $A0, $5A
ObjectAnimationFrames082:
    .byte $A4, $9A, $48
ObjectAnimationFrames083:
    .byte $A0, $A2, $48
ObjectAnimationFrames084:
    .byte $7C, $74, $5A, $76, $74, $5A
ObjectAnimationFrames085:
    .byte $74, $7C, $48, $74, $76, $48
ObjectAnimationFrames086:
    .byte $7A, $78, $5A, $76, $74, $5A
ObjectAnimationFrames087:
    .byte $78, $7A, $48, $74, $76, $48
ObjectAnimationFrames088:
    .byte $DC, $78, $5A
ObjectAnimationFrames089:
    .byte $78, $DC, $48
ObjectAnimationFrames090:
    .byte $B6, $B6, $4B
ObjectAnimationFrames091:
    .byte $BA, $BA, $4B, $B8, $B8, $4B
ObjectAnimationFrames092:
    .byte $FC, $FE, $48
ObjectAnimationFrames093:
    .byte $F8, $FA, $48
ObjectAnimationFrames094:
    .byte $30, $32, $CC, $2E, $2E, $CE
    .byte $32, $30, $DE, $2C, $2C, $CE
ObjectAnimationFrames095:
    .byte $36, $34, $96, $36, $34, $12
ObjectAnimationFrames096:
    .byte $34, $36, $84, $34, $36, $00
ObjectAnimationFrames097:
    .byte $C2, $34, $96
ObjectAnimationFrames098:
    .byte $36, $34, $96, $3A, $38, $96
ObjectAnimationFrames099:
    .byte $34, $C2, $84
ObjectAnimationFrames100:
    .byte $34, $36, $84, $38, $3A, $84
ObjectAnimationFrames101:
    .byte $4E, $C0, $DE, $4E, $4C, $12
    .byte $4E, $4C, $DE, $4E, $4C, $12
    .byte $4E, $4C, $DE, $4E, $4C, $12
ObjectAnimationFrames102:
    .byte $C0, $4E, $CC, $4C, $4E, $00
    .byte $4C, $4E, $CC, $4C, $4E, $00
    .byte $4C, $4E, $CC, $4C, $4E, $00
ObjectAnimationFrames103:
    .byte $4E, $4C, $DE, $52, $50, $DE
    .byte $4E, $4C, $DE, $4A, $48, $DE
ObjectAnimationFrames104:
    .byte $4C, $4E, $CC, $50, $52, $CC
    .byte $4C, $4E, $CC, $48, $4A, $CC
ObjectAnimationFrames105:
    .byte $52, $50, $FF, $4A, $48, $FF
ObjectAnimationFrames106:
    .byte $50, $52, $ED, $48, $4A, $ED
ObjectAnimationFrames107:
    .byte $5E, $5C, $DE, $5A, $58, $DE
ObjectAnimationFrames108:
    .byte $66, $64, $DE, $62, $60, $DE
    .byte $5E, $5C, $DE
ObjectAnimationFrames109:
    .byte $5C, $5E, $CC, $58, $5A, $CC
ObjectAnimationFrames110:
    .byte $64, $66, $CC, $60, $62, $CC
    .byte $5C, $5E, $CC
ObjectAnimationFrames111:
    .byte $5E, $5C, $DE, $5A, $58, $DE
    .byte $56, $54, $DE
ObjectAnimationFrames112:
    .byte $5C, $5E, $CC, $58, $5A, $CC
    .byte $54, $56, $CC
ObjectAnimationFrames113:
    .byte $5E, $5C, $FF, $5A, $58, $FF
ObjectAnimationFrames114:
    .byte $5C, $5E, $ED, $58, $5A, $ED
ObjectAnimationFrames115:
    .byte $6E, $6C, $5A, $6E, $6C, $96
ObjectAnimationFrames116:
    .byte $6C, $6E, $48, $6C, $6E, $84
ObjectAnimationFrames117:
    .byte $6E, $6C, $5A, $6A, $68, $5A
    .byte $6E, $6C, $5A, $72, $70, $5A
ObjectAnimationFrames118:
    .byte $6C, $6E, $48, $68, $6A, $48
    .byte $6C, $6E, $48, $70, $72, $48
ObjectAnimationFrames119:
    .byte $6A, $68, $7B, $6E, $6C, $7B
ObjectAnimationFrames120:
    .byte $68, $6A, $69, $6C, $6E, $69
ObjectAnimationFrames121:
    .byte $A6, $A6, $4A, $D4, $D6, $48
    .byte $A6, $A6, $4A, $D6, $D4, $DE
    .byte $A6, $A6, $86, $D4, $D6, $CC
ObjectAnimationFrames122:
    .byte $D2, $D0, $96, $D2, $D0, $DE
    .byte $D2, $D0, $5A, $D0, $D2, $CC
    .byte $D0, $D2, $84
ObjectAnimationFrames123:
    .byte $FA, $F8, $DE, $D2, $D0, $5A
    .byte $FA, $F8, $DE, $D0, $D2, $48
    .byte $F8, $FA, $CC
ObjectAnimationFrames124:
    .byte $D6, $D4, $DE, $D6, $D4, $96
    .byte $D4, $D6, $48, $D4, $D6, $CC
    .byte $D4, $D6, $84
ObjectAnimationFrames125:
    .byte $F6, $F4, $DE, $D4, $D6, $48
    .byte $F6, $F4, $DE, $F4, $F6, $CC
    .byte $D6, $D4, $5A

.assert * - ObjectAnimationFrames000 = $0339, error, "unexpected object animation frame data size"
