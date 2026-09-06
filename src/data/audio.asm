; Audio lookup tables, effects, bytecode streams, and CPU vectors

.macro AudioChannelStart selector, stream
    .byte selector
    .word stream
.endmacro

.macro AudioJump stream
    .byte $F2
    .word stream
.endmacro

.macro AudioCall stream
    .byte $F3
    .word stream
.endmacro

.segment "PRG_AUDIO_TIMING_TABLES"

AudioPeriodTable:
    .word $06AE, $064E, $05F3, $059E, $054D, $0501
    .word $04B9, $0475, $0435, $03F8, $03BF, $0389

AudioDurationTable:
    .byte $01, $02, $04, $06, $08, $0C, $10, $18, $20, $30, $40, $60, $80
    .byte $C0, $05, $0A, $0F, $14, $19, $1E, $28, $32, $3C, $46, $50, $50

.assert * - AudioPeriodTable = $0032, error, "unexpected audio timing table size"

.segment "PRG_AUDIO_ENVELOPES"

AudioEnvelopePointerTable:
    .word AudioEnvelope00, AudioEnvelope01
    .word AudioEnvelope02, AudioEnvelope03
    .word AudioEnvelope04, AudioEnvelope05
    .word AudioEnvelope06, AudioEnvelope07

AudioEnvelope00:
; (duration, volume) pairs
    .byte $02, $0F, $02, $0E, $02, $0D, $02, $0C, $02, $0B, $02, $0A, $02, $09, $02, $08
    .byte $02, $07, $02, $06, $02, $05, $02, $04, $02, $03, $02, $02, $02, $01, $FF, $00

AudioEnvelope01:
; (duration, volume) pairs
    .byte $01, $0F, $01, $0E, $01, $0D, $01, $0C, $01, $0B, $01, $0A, $01, $09, $01, $08
    .byte $01, $07, $01, $06, $01, $05, $01, $04, $01, $03, $01, $02, $01, $01, $FF, $00

AudioEnvelope02:
; (duration, volume) pairs
    .byte $01, $0F, $01, $0D, $01, $0B, $01, $09, $01, $07, $01, $05, $01, $03, $01, $01
    .byte $FF, $00

AudioEnvelope03:
; (duration, volume) pairs
    .byte $01, $0B, $01, $0C, $01, $0D, $01, $0E, $02, $0F, $02, $0E, $02, $0D, $02, $0C
    .byte $02, $0B, $02, $0A, $02, $09, $02, $08, $02, $07, $02, $06, $02, $05, $02, $04
    .byte $02, $03, $02, $02, $02, $01, $FF, $00

AudioEnvelope04:
; (duration, volume) pairs
    .byte $02, $04, $02, $05, $02, $06, $02, $07, $02, $08, $02, $09, $02, $0A, $02, $08
    .byte $02, $06, $02, $04, $02, $02, $01, $02, $FF, $00

AudioEnvelope05:
; (duration, volume) pairs
    .byte $01, $04, $01, $05, $01, $06, $01, $07, $01, $08, $01, $09, $01, $0A, $01, $08
    .byte $01, $06, $01, $04, $01, $02, $01, $01, $FF, $00

AudioEnvelope06:
; (duration, volume) pairs
    .byte $FF, $0F, $FF, $00

AudioEnvelope07:
; (duration, volume) pairs
    .byte $05, $0F, $05, $0E, $05, $0D, $05, $0B, $05, $0A, $05, $09, $05, $09, $05, $08
    .byte $05, $07, $05, $06, $05, $05, $05, $04, $05, $03, $05, $02, $05, $01, $FF, $00

.assert * - AudioEnvelopePointerTable = $00E2, error, "unexpected audio envelope data size"

.segment "PRG_SOUND_EFFECT_DATA"

SoundEffectPointerTable:
    .word SoundEffectDescriptor01, SoundEffectDescriptor02
    .word SoundEffectDescriptor03, SoundEffectDescriptor04
    .word SoundEffectDescriptor05, SoundEffectDescriptor06
    .word SoundEffectDescriptor07, SoundEffectDescriptor08
    .word SoundEffectDescriptor09, SoundEffectDescriptor10
    .word SoundEffectDescriptor11, SoundEffectDescriptor12
    .word SoundEffectDescriptor13, SoundEffectDescriptor14
    .word SoundEffectDescriptor15, SoundEffectDescriptor16
    .word SoundEffectDescriptor17, SoundEffectDescriptor18
    .word SoundEffectDescriptor19, SoundEffectDescriptor20
    .word SoundEffectDescriptor21, SoundEffectDescriptor22
    .word SoundEffectDescriptor23, SoundEffectDescriptor24
    .word SoundEffectDescriptor25, SoundEffectDescriptor26

SoundEffectDescriptor01:
    AudioChannelStart $81, AudioStream000
    AudioChannelStart $03, AudioStream007
    AudioChannelStart $07, AudioStream020

SoundEffectDescriptor02:
    AudioChannelStart $81, AudioStream024
    AudioChannelStart $03, AudioStream029
    AudioChannelStart $07, AudioStream105

SoundEffectDescriptor03:
    AudioChannelStart $80, AudioStream034
    AudioChannelStart $02, AudioStream035
    AudioChannelStart $06, AudioStream036
    AudioChannelStart $01, AudioStream098
    AudioChannelStart $03, AudioStream099
    AudioChannelStart $07, AudioStream101

SoundEffectDescriptor04:
    AudioChannelStart $81, AudioStream037
    AudioChannelStart $03, AudioStream039
    AudioChannelStart $07, AudioStream041

SoundEffectDescriptor05:
    AudioChannelStart $80, AudioStream043
    AudioChannelStart $02, AudioStream044
    AudioChannelStart $04, AudioStream045
    AudioChannelStart $07, AudioStream046

SoundEffectDescriptor06:
    AudioChannelStart $80, AudioStream047
    AudioChannelStart $02, AudioStream048
    AudioChannelStart $04, AudioStream049

SoundEffectDescriptor07:
    AudioChannelStart $84, AudioStream050

SoundEffectDescriptor08:
    AudioChannelStart $86, AudioStream051

SoundEffectDescriptor09:
    AudioChannelStart $84, AudioStream052
    AudioChannelStart $06, AudioStream053

SoundEffectDescriptor10:
    AudioChannelStart $84, AudioStream054

SoundEffectDescriptor11:
    AudioChannelStart $86, AudioStream055

SoundEffectDescriptor12:
    AudioChannelStart $80, AudioStream056
    AudioChannelStart $02, AudioStream057
    AudioChannelStart $04, AudioStream058
    AudioChannelStart $06, AudioStream059

SoundEffectDescriptor13:
    AudioChannelStart $84, AudioStream060

SoundEffectDescriptor14:
    AudioChannelStart $84, AudioStream061

SoundEffectDescriptor15:
    AudioChannelStart $80, AudioStream062
    AudioChannelStart $02, AudioStream064
    AudioChannelStart $06, AudioStream066

SoundEffectDescriptor16:
    AudioChannelStart $81, AudioStream067
    AudioChannelStart $03, AudioStream069
    AudioChannelStart $05, AudioStream072
    AudioChannelStart $07, AudioStream078

SoundEffectDescriptor17:
    AudioChannelStart $84, AudioStream081

SoundEffectDescriptor18:
    AudioChannelStart $84, AudioStream082

SoundEffectDescriptor19:
    AudioChannelStart $81, AudioStream083
    AudioChannelStart $03, AudioStream085

SoundEffectDescriptor20:
    AudioChannelStart $81, AudioStream087
    AudioChannelStart $03, AudioStream088
    AudioChannelStart $05, AudioStream089
    AudioChannelStart $07, AudioStream090

SoundEffectDescriptor21:
    AudioChannelStart $80, AudioStream091
    AudioChannelStart $02, AudioStream092
    AudioChannelStart $04, AudioStream093
    AudioChannelStart $01, AudioStream098
    AudioChannelStart $03, AudioStream099
    AudioChannelStart $07, AudioStream101

SoundEffectDescriptor22:
    AudioChannelStart $80, AudioStream094
    AudioChannelStart $02, AudioStream095
    AudioChannelStart $06, AudioStream096

SoundEffectDescriptor23:
    AudioChannelStart $84, AudioStream097

SoundEffectDescriptor24:
    AudioChannelStart $80, AudioStream098
    AudioChannelStart $02, AudioStream099
    AudioChannelStart $04, AudioStream100
    AudioChannelStart $06, AudioStream101
    AudioChannelStart $01, AudioStream102
    AudioChannelStart $03, AudioStream103
    AudioChannelStart $05, AudioStream104
    AudioChannelStart $07, AudioStream105

SoundEffectDescriptor25:
    AudioChannelStart $80, AudioStream106
    AudioChannelStart $02, AudioStream107
    AudioChannelStart $04, AudioStream108
    AudioChannelStart $07, AudioStream109

SoundEffectDescriptor26:
    AudioChannelStart $80, AudioStream110
    AudioChannelStart $02, AudioStream111
    AudioChannelStart $04, AudioStream112
    AudioChannelStart $07, AudioStream113
    .byte $FF

.assert * - SoundEffectPointerTable = $0116, error, "unexpected sound-effect data size"

.segment "PRG_AUDIO_STREAMS"

AudioStream000:
    .byte $F0, $06, $F1, $09, $F8, $00, $88, $13, $84, $15, $13, $88, $12, $84, $13, $12
    .byte $88, $11, $84, $12, $11, $88, $10, $84, $11, $10, $87, $0B, $10, $12, $13
    .byte $F1, $0B, $83, $F5, $08, $08, $07, $F6
AudioStream001:
    .byte $F0, $00, $F1, $07, $F8, $00, $85
    AudioCall AudioStream002
    AudioCall AudioStream002
    AudioCall AudioStream003
    AudioCall AudioStream003
    AudioCall AudioStream002
    AudioCall AudioStream002
    AudioCall AudioStream003
    AudioCall AudioStream003
    AudioCall AudioStream004
    AudioCall AudioStream005
    AudioCall AudioStream004
    AudioCall AudioStream006
    AudioJump AudioStream001
AudioStream002:
    .byte $10, $13, $17, $13, $12, $15, $18, $12, $13, $17, $20, $13, $15, $18, $22, $15
    .byte $13, $17, $20, $13, $12, $15, $18, $12, $10, $13, $17, $10, $0B, $12, $15, $0B
    .byte $F4
AudioStream003:
    .byte $09, $10, $14, $09, $0B, $12, $15, $0B, $10, $14, $17, $10, $12, $15, $19, $12
    .byte $14, $17, $20, $14, $12, $15, $1B, $12, $10, $14, $19, $10, $0B, $12, $17, $0B
    .byte $F4
AudioStream004:
    .byte $10, $14, $19, $14, $0B, $12, $17, $12, $12, $16, $1B, $16, $14, $18, $1B, $18
    .byte $10, $14, $19, $14, $0B, $12, $17, $12, $09, $10, $15, $10, $F4
AudioStream005:
    .byte $08, $0B, $14, $0B, $F4
AudioStream006:
    .byte $0B, $12, $17, $12, $F4
AudioStream007:
    .byte $F0, $03, $F1, $03, $F8, $00, $85, $20, $27, $0C, $27, $26, $0C, $27, $27
    .byte $F0, $05, $F1, $02, $28, $27, $26, $27, $30, $27, $26, $27, $F0, $03, $F1, $04
    .byte $84, $22, $23, $25, $27, $28, $2B, $30, $2B, $28, $27, $25, $23, $F0, $05
    .byte $F1, $03, $85, $22, $1B, $1B, $22, $1B, $1B, $22, $1B
AudioStream008:
    .byte $F0, $03, $F1, $04, $F8, $00, $85
    AudioCall AudioStream009
    AudioCall AudioStream010
    AudioCall AudioStream009
    AudioCall AudioStream011
    AudioCall AudioStream012
    AudioCall AudioStream013
    AudioCall AudioStream012
    AudioCall AudioStream014
    AudioCall AudioStream015
    AudioCall AudioStream016
    AudioCall AudioStream017
    AudioCall AudioStream016
    AudioCall AudioStream018
    AudioCall AudioStream016
    AudioCall AudioStream017
    AudioCall AudioStream016
    AudioCall AudioStream019
    AudioJump AudioStream008
AudioStream009:
    .byte $0C, $0C, $30, $30, $2B, $0C, $30, $30, $32, $0C, $30, $2B, $30, $0C, $0C, $0C
    .byte $0C, $0C, $30, $30, $2B, $0C, $30, $30, $F4
AudioStream010:
    .byte $27, $0C, $23, $0C, $22, $0C, $27, $0C, $F4
AudioStream011:
    .byte $27, $0C, $23, $0C, $22, $0C, $20, $0C, $F4
AudioStream012:
    .byte $0C, $0C, $29, $29, $28, $0C, $29, $29, $2B, $0C, $29, $28, $29, $0C, $2B, $30
    .byte $F4
AudioStream013:
    .byte $32, $0C, $30, $2B, $30, $0C, $32, $34, $35, $0C, $34, $0C, $0C, $0C, $0C, $0C
    .byte $F4
AudioStream014:
    .byte $32, $30, $2B, $29, $30, $2B, $29, $28, $29, $0C, $0C, $0C, $0C, $0C, $0C, $0C
    .byte $F4
AudioStream015:
    .byte $F0, $03, $F1, $06, $85, $F5, $02, $30, $33, $37, $40, $3B, $38, $35, $32, $F6
    .byte $85, $27, $30, $33, $37, $84, $35, $42, $40, $3B, $38, $37, $33, $37, $40, $37
    .byte $33, $30, $83, $2B, $30, $32, $33, $32, $30, $2B, $28, $84, $F5, $03, $37, $36
    .byte $F6, $35, $37, $38, $3B, $40, $42, $83, $43, $42, $40, $3B, $38, $37, $35, $33
    .byte $32, $30, $2B, $28, $27, $25, $23, $22, $85, $37, $30, $33, $37, $38, $32, $35
    .byte $38, $40, $33, $37, $40, $84, $F5, $03, $3B, $35, $F6, $85, $40, $39, $34, $30
    .byte $84, $38, $35, $34, $32, $34, $35, $87, $34, $84, $0C, $32, $30, $2B, $29, $28
    .byte $25, $24, $22, $F5, $03, $24, $30, $F6, $F5, $03, $25, $32, $F6, $34, $32, $30
    .byte $20, $22, $24, $83, $32, $30, $2B, $29, $22, $24, $25, $28, $29, $2B, $30, $32
    .byte $34, $35, $38, $39, $3B, $39, $38, $85, $35, $83, $38, $35, $34, $84, $F5, $03
    .byte $39, $30, $F6, $85, $39, $32, $39, $32, $84, $39, $34, $39, $34, $39, $34, $83
    .byte $3B, $38, $35, $32, $38, $35, $32, $2B, $87, $F1, $08, $29, $F1, $09, $30, $89
    .byte $F1, $0A, $2B, $F4
AudioStream016:
    .byte $F0, $03, $F1, $04, $F8, $00, $87, $0C, $39, $37, $81, $32, $31, $30, $2B, $2A
    .byte $29, $28, $27, $26, $25, $24, $23, $F4
AudioStream017:
    .byte $85, $36, $32, $36, $87, $34, $85, $0C, $36, $38, $F4
AudioStream018:
    .byte $85, $35, $40, $39, $35, $F1, $06, $34, $38, $3B, $38, $F4
AudioStream019:
    .byte $85, $35, $40, $39, $35, $F1, $07, $37, $3B, $42, $3B, $F4
AudioStream020:
    .byte $F0, $02, $F1, $06, $89, $F5, $08, $00, $F6, $85
AudioStream021:
    AudioCall AudioStream022
    AudioCall AudioStream022
    AudioCall AudioStream022
    AudioCall AudioStream023
    AudioCall AudioStream023
    AudioJump AudioStream021
AudioStream022:
    .byte $F0, $04, $F1, $04, $87, $04, $F0, $02, $F1, $04, $85, $07, $07, $F4
AudioStream023:
    .byte $F0, $05, $F1, $04, $85, $04, $F0, $02, $F1, $04, $85, $07, $F4
AudioStream024:
    .byte $F0, $03, $F8, $40, $84, $F1, $0C
    AudioCall AudioStream026
    .byte $F1, $0A
    AudioCall AudioStream026
    .byte $F1, $08
    AudioCall AudioStream026
    .byte $F1, $06
    AudioCall AudioStream026
AudioStream025:
    AudioCall AudioStream027
    AudioCall AudioStream027
    AudioCall AudioStream027
    AudioCall AudioStream028
    AudioJump AudioStream025
AudioStream026:
    .byte $35, $37, $35, $37, $35, $37, $F4
AudioStream027:
    .byte $42, $32, $47, $37, $45, $35, $42, $32, $3A, $2A, $40, $30, $F4
AudioStream028:
    .byte $41, $31, $45, $35, $48, $38, $47, $37, $43, $33, $40, $30, $41, $31, $3A, $2A
    .byte $36, $26, $35, $25, $39, $29, $40, $30, $3A, $2A, $42, $32, $45, $35, $48, $38
    .byte $45, $35, $42, $32, $47, $37, $43, $33, $40, $30, $39, $29, $37, $27, $39, $29
    .byte $3A, $2A, $42, $32, $45, $35, $4A, $3A, $3A, $2A, $4A, $3A, $F4
AudioStream029:
    .byte $F0, $03, $F8, $00, $84, $F1, $0C
    AudioCall AudioStream031
    .byte $F1, $0A
    AudioCall AudioStream031
    .byte $F1, $08
    AudioCall AudioStream031
    .byte $F1, $06
    AudioCall AudioStream031
AudioStream030:
    .byte $F1, $08, $84
    AudioCall AudioStream032
    AudioCall AudioStream032
    AudioCall AudioStream032
    AudioCall AudioStream033
    AudioJump AudioStream030
AudioStream031:
    .byte $32, $33, $32, $33, $32, $33, $F4
AudioStream032:
    .byte $07, $0A, $17, $1A, $27, $2A, $05, $0A, $15, $1A, $25, $2A, $F4
AudioStream033:
    .byte $08, $11, $18, $21, $28, $31, $07, $10, $17, $20, $27, $30, $06, $0A, $16, $1A
    .byte $26, $2A, $05, $09, $15, $19, $25, $29, $02, $05, $12, $15, $22, $25, $05, $0A
    .byte $15, $1A, $25, $2A, $07, $10, $17, $20, $27, $30, $05, $09, $15, $19, $25, $29
    .byte $02, $05, $12, $15, $22, $25, $06, $0A, $16, $1A, $26, $2A, $F4
AudioStream034:
    .byte $F0, $03, $F1, $00, $F8, $00, $80, $17, $18, $19, $1A, $1B, $20, $85, $23, $83
    .byte $22, $85, $1B, $20, $80, $18, $19, $1A, $1B, $20, $21, $22, $23, $24, $25, $26
    .byte $27, $85, $28, $27, $F9
AudioStream035:
    .byte $F0, $03, $F1, $00, $F8, $00, $80, $37, $38, $39, $3A, $3B, $40, $85, $43, $83
    .byte $42, $85, $3B, $40, $80, $38, $39, $3A, $3B, $40, $41, $42, $43, $44, $45, $46
    .byte $47, $85, $48, $47, $F9
AudioStream036:
    .byte $F0, $02, $83, $F5, $02, $F1, $04, $04, $04, $F1, $02, $08, $08, $F6, $F1, $04
    .byte $04, $04, $85, $F1, $01, $08, $08, $F9
AudioStream037:
    .byte $F0, $03, $F8, $00, $84, $F1, $09
    AudioCall AudioStream038
    .byte $F1, $08
    AudioCall AudioStream038
    .byte $F1, $07
    AudioCall AudioStream038
    .byte $F1, $06
    AudioCall AudioStream038
    .byte $F1, $05
    AudioCall AudioStream038
    .byte $F1, $04
    AudioCall AudioStream038
    .byte $F1, $02, $81
    AudioCall AudioStream038
    .byte $84, $08, $F1, $04, $81
    AudioCall AudioStream038
    .byte $84, $08, $F1, $06, $81
    AudioCall AudioStream038
    .byte $84, $08, $F1, $08, $81
    AudioCall AudioStream038
    .byte $84, $08
    AudioJump AudioStream037
AudioStream038:
    .byte $05, $05, $06, $07, $F4
AudioStream039:
    .byte $F0, $03, $F8, $00, $84, $F1, $0B
    AudioCall AudioStream040
    .byte $F1, $0A
    AudioCall AudioStream040
    .byte $F1, $09
    AudioCall AudioStream040
    .byte $F1, $08
    AudioCall AudioStream040
    .byte $F1, $07
    AudioCall AudioStream040
    .byte $F1, $06
    AudioCall AudioStream040
    .byte $F1, $05, $81
    AudioCall AudioStream040
    .byte $84, $28, $F1, $07, $81
    AudioCall AudioStream040
    .byte $84, $28, $F1, $09, $81
    AudioCall AudioStream040
    .byte $84, $28, $F1, $0B, $81
    AudioCall AudioStream040
    .byte $84, $28
    AudioJump AudioStream039
AudioStream040:
    .byte $24, $25, $26, $27, $F4
AudioStream041:
    .byte $F0, $02, $84
    AudioCall AudioStream042
    .byte $F1, $09, $08, $F1, $09, $04
    AudioCall AudioStream042
    .byte $F1, $08, $08, $F1, $08, $04
    AudioCall AudioStream042
    .byte $F1, $07, $08, $F1, $07, $04
    AudioCall AudioStream042
    .byte $F1, $06, $08, $F1, $06, $04
    AudioCall AudioStream042
    .byte $F1, $05, $08, $F1, $05, $04
    AudioCall AudioStream042
    .byte $F1, $04, $08, $F1, $04, $04, $F1, $0A, $01, $F1, $02, $08, $F1, $0A, $01
    .byte $F1, $04, $08, $F1, $0A, $01, $F1, $06, $08, $F1, $0A, $01, $F1, $08, $08
    AudioJump AudioStream041
AudioStream042:
    .byte $F1, $0A, $01, $F1, $0A, $01, $F4
AudioStream043:
    .byte $F0, $03, $F1, $02, $F8, $00, $85, $35, $38, $3B, $40, $42, $40, $3B, $38, $42
    .byte $40, $3B, $38, $37, $35, $37, $38, $37, $35, $83, $F5, $05, $34, $35, $34, $35
    .byte $F6, $87, $32, $34, $F0, $06, $F1, $06, $8B, $35, $F9
AudioStream044:
    .byte $F0, $06, $F1, $06, $F8, $00, $89, $30, $2B, $30, $2B, $8B, $27, $27, $25, $F9
AudioStream045:
    .byte $F8, $80, $89, $15, $15, $15, $15, $8B, $10, $10, $09, $F9
AudioStream046:
    .byte $F0, $00, $F1, $0F, $80, $01, $F9
AudioStream047:
    .byte $F0, $06, $F1, $08, $F8, $00, $82, $10, $13, $17, $84, $18, $82, $20, $84, $21
    .byte $25, $26, $82, $28, $F9
AudioStream048:
    .byte $F0, $06, $F1, $08, $F8, $40, $82, $30, $33, $37, $84, $38, $82, $40, $84, $41
    .byte $45, $46, $82, $48, $F9
AudioStream049:
    AudioCall AudioStream048
    .byte $F9
AudioStream050:
    .byte $F0, $00, $F8, $C0, $80, $62, $63, $64, $65, $66, $67, $68, $69, $6A, $6B, $70
    .byte $71, $F9
AudioStream051:
    .byte $F0, $01, $F1, $00, $80, $0C, $0B, $0A, $82, $09, $85, $F1, $04, $06, $F9
AudioStream052:
    .byte $F0, $06, $F1, $00, $F8, $C0, $80, $27, $32, $26, $31, $25, $30, $24, $2B, $23
    .byte $2A, $22, $29, $21, $28, $20, $27, $1B, $26, $20, $21, $22, $23, $24, $25, $F9
AudioStream053:
    .byte $F0, $06, $F1, $00, $80, $09, $08, $07, $06, $05, $04, $03, $02, $F5, $05, $01
    .byte $02, $F6, $F9
AudioStream054:
    .byte $F0, $06, $F1, $00, $80, $71, $73, $71, $73, $71, $73, $71, $73, $61, $63, $61
    .byte $63, $61, $63, $61, $63, $F9
AudioStream055:
    .byte $F0, $06, $F1, $00, $88, $05, $F9
AudioStream056:
    .byte $F0, $06, $F8, $00, $94, $0C, $F9
AudioStream057:
    .byte $F0, $06, $F8, $00, $94, $0C, $F9
AudioStream058:
    .byte $F0, $06, $F1, $00, $8F, $32, $0C, $0C, $0C, $F9
AudioStream059:
    .byte $F0, $06, $F1, $0F, $94, $00, $F9
AudioStream060:
    .byte $F0, $06, $F1, $00, $80, $56, $57, $58, $59, $56, $53, $50, $49, $46, $43, $40
    .byte $39, $36, $33, $30, $29, $2B, $31, $33, $35, $37, $39, $3B, $41, $F9
AudioStream061:
    .byte $F0, $06, $F1, $00, $80, $0C, $F9
AudioStream062:
    .byte $F0, $03, $F8, $80, $81, $F1, $02
    AudioCall AudioStream063
    .byte $F1, $04
    AudioCall AudioStream063
    .byte $F1, $06
    AudioCall AudioStream063
    .byte $F1, $08
    AudioCall AudioStream063
    .byte $F9
AudioStream063:
    .byte $F5, $02, $27, $37, $47, $29, $39, $49, $F6, $F4
AudioStream064:
    .byte $F0, $03, $F8, $80, $81, $F1, $02
    AudioCall AudioStream065
    .byte $F1, $04
    AudioCall AudioStream065
    .byte $F1, $06
    AudioCall AudioStream065
    .byte $F1, $08
    AudioCall AudioStream065
    .byte $F9
AudioStream065:
    .byte $F5, $02, $24, $34, $44, $25, $35, $45, $F6, $F4
AudioStream066:
    .byte $F0, $00, $F1, $0F, $87, $F5, $07, $00, $F6, $F9
AudioStream067:
    .byte $F0, $03, $F1, $02, $F8, $40
    AudioCall AudioStream068
    .byte $94, $35, $34
    AudioCall AudioStream068
    .byte $94, $32, $34, $98, $F5, $07, $0C, $F6, $94, $28, $27, $F0, $00, $F5, $02, $93
    .byte $35, $8F, $35, $93, $35, $8F, $35, $0C, $35, $0C, $35, $91, $3A, $40, $F6
    .byte $F5, $02, $91, $19, $8F, $1A, $20, $0C, $35, $35, $35, $F6, $91, $22, $24, $25
    .byte $8F, $27, $29, $0C, $27, $0C, $25, $91, $29, $27, $F0, $07, $F5, $02, $93, $3A
    .byte $8F, $39, $94, $39, $93, $37, $8F, $39, $94, $39, $93, $3A, $8F, $40, $F0, $07
    .byte $98, $40, $94, $0C, $F6, $96, $42, $8F, $42, $42, $94, $44, $91, $40, $44, $8F
    .byte $49, $47, $45, $47, $45, $44, $45, $44, $98, $42, $8F, $3A, $40, $42, $44, $45
    .byte $44, $42, $44, $49, $47, $45, $47, $45, $44, $42, $44, $42, $44, $45, $47, $91
    .byte $49, $4A, $94, $48, $47
    AudioJump AudioStream067
AudioStream068:
    .byte $8F, $3A, $3A, $3A, $91, $39, $8F, $39, $39, $39, $37, $37, $37, $91, $39, $8F
    .byte $39, $39, $39, $35, $35, $35, $91, $37, $8F, $37, $37, $37, $F4
AudioStream069:
    .byte $F0, $03, $F1, $02, $F8, $40
    AudioCall AudioStream070
    .byte $94, $30, $30
    AudioCall AudioStream070
    .byte $94, $2A, $30
    AudioCall AudioStream071
    .byte $F0, $00, $F5, $02, $93, $30, $8F, $30, $93, $30, $8F, $30, $0C, $30, $0C, $30
    .byte $91, $35, $37, $F6, $F5, $02, $94, $0C, $8F, $0C, $30, $30, $30, $F6, $91, $1A
    .byte $1A, $1A, $8F, $1A, $20, $0C, $20, $0C, $20, $91, $1A, $20, $F5, $02, $93, $35
    .byte $8F, $35, $94, $35, $93, $34, $8F, $35, $94, $35, $93, $35, $8F, $37, $F0, $07
    .byte $98, $37, $94, $0C, $F6, $F1, $04
    AudioCall AudioStream071
    AudioJump AudioStream069
AudioStream070:
    .byte $8F, $35, $35, $35, $91, $35, $8F, $35, $35, $35, $34, $34, $34, $91, $35, $8F
    .byte $35, $35, $35, $32, $32, $32, $91, $34, $8F, $34, $34, $34, $F4
AudioStream071:
    .byte $F0, $07, $F1, $02, $96, $12, $8F, $0A, $12, $94, $14, $91, $10, $09, $93, $19
    .byte $1A, $91, $19, $93, $17, $95, $15, $96, $1A, $8F, $19, $17, $94, $15, $14, $96
    .byte $15, $8F, $12, $15, $91, $18, $1A, $8F, $20, $93, $19, $F4
AudioStream072:
    .byte $F0, $06, $F1, $00, $F8, $80
    AudioCall AudioStream073
    .byte $98, $20
    AudioCall AudioStream073
    .byte $94, $1A, $20
    AudioCall AudioStream074
    AudioCall AudioStream075
    AudioCall AudioStream076
    AudioCall AudioStream077
    AudioCall AudioStream074
    AudioCall AudioStream075
    AudioCall AudioStream077
    .byte $98, $40, $F5, $02, $8F, $29, $0C, $0C, $29, $29, $0C, $0C, $29, $0C, $29, $0C
    .byte $29, $91, $32, $34, $F6, $F5, $02, $91, $19, $8F, $1A, $93, $20, $8F, $19, $20
    .byte $F6, $94, $22, $91, $1A, $8F, $22, $24, $0C, $24, $0C, $24, $91, $20, $24
    .byte $F5, $02, $98, $25, $96, $25, $8F, $24, $22, $93, $1A, $8F, $1B, $98, $20, $8F
    .byte $20, $20, $22, $24, $F6
    AudioCall AudioStream074
    AudioCall AudioStream075
    AudioCall AudioStream076
    AudioCall AudioStream077
    AudioCall AudioStream074
    AudioCall AudioStream075
    AudioCall AudioStream077
    .byte $98, $20
    AudioJump AudioStream072
AudioStream073:
    .byte $98, $25, $25, $93, $22, $95, $24, $F4
AudioStream074:
    .byte $F5, $04, $84, $42, $83, $3A, $35, $F6, $F4
AudioStream075:
    .byte $F5, $04, $84, $44, $83, $40, $37, $F6, $F4
AudioStream076:
    .byte $F5, $04, $84, $44, $83, $40, $39, $F6, $F4
AudioStream077:
    .byte $F5, $04, $84, $45, $83, $40, $39, $F6, $F4
AudioStream078:
    .byte $F0, $01, $98, $00, $00, $00, $95, $00, $F1, $00, $8F, $09, $09, $09
AudioStream079:
    AudioCall AudioStream080
    .byte $04, $F0, $01, $09, $F0, $02, $04, $F0, $01, $09
    AudioCall AudioStream080
    .byte $04, $F0, $01, $09, $09, $09
    AudioJump AudioStream079
AudioStream080:
    .byte $F5, $03, $F0, $02, $04, $04, $F0, $01, $09, $F0, $02, $04, $F6, $F4
AudioStream081:
    .byte $F0, $06, $F8, $80, $80, $20, $40, $60, $70, $75, $70, $75, $70, $75, $F9
AudioStream082:
    .byte $F0, $06, $F8, $80, $80, $46, $56, $66, $76, $F9
AudioStream083:
    .byte $F0, $04, $F1, $01, $F8, $80, $8F
AudioStream084:
    .byte $34, $35
    AudioJump AudioStream084
AudioStream085:
    .byte $F0, $04, $F1, $01, $F8, $80, $8F
AudioStream086:
    .byte $37, $39
    AudioJump AudioStream086
AudioStream087:
    .byte $F0, $07, $F1, $08, $F8, $80, $93, $57, $50, $57, $50, $F9
AudioStream088:
    .byte $F0, $07, $F1, $08, $F8, $80, $90, $0C, $93, $54, $49, $54, $49, $F9
AudioStream089:
    .byte $F0, $06, $F1, $00, $F8, $80, $81, $6B, $67, $6A, $66, $69, $65, $68, $64, $67
    .byte $63, $66, $62, $65, $61, $64, $60, $63, $5B, $62, $5A, $61, $59, $60, $58, $5B
    .byte $57, $5A, $56, $59, $55, $20, $21, $22, $23, $24, $25, $26, $27, $28, $29, $2A
    .byte $2B, $30, $31, $32, $33, $34, $35, $36, $37, $38, $39, $3A, $3B, $40, $41, $42
    .byte $43, $44, $45, $F9
AudioStream090:
    .byte $F0, $00, $F1, $0F, $80, $01, $F9
AudioStream091:
    .byte $F0, $07, $F1, $02, $F8, $40, $90, $24, $8E, $25, $8F, $27, $24, $8E, $25, $24
    .byte $25, $27, $91, $25, $F9
AudioStream092:
    .byte $F0, $07, $F1, $03, $F8, $80, $90, $34, $8E, $35, $8F, $37, $34, $8E, $35, $34
    .byte $35, $37, $91, $35, $F9
AudioStream093:
    .byte $F0, $06, $F1, $00, $F8, $80, $91, $20, $1A, $8F, $19, $17, $91, $15, $F9
AudioStream094:
    .byte $F0, $07, $F1, $03, $F8, $80, $84, $20, $1B, $20, $23, $85, $28, $25, $28, $25
    .byte $F9
AudioStream095:
    .byte $F0, $00, $F1, $03, $F8, $40, $84, $30, $2B, $30, $33, $85, $38, $35, $38, $35
    .byte $F9
AudioStream096:
    .byte $F0, $00, $F1, $0F, $88, $00, $89, $00, $F9
AudioStream097:
    .byte $F0, $06, $F1, $00, $F8, $80, $80, $11, $12, $21, $22, $31, $32, $41, $42, $41
    .byte $40, $3B, $3A, $39, $38, $37, $36, $F9
AudioStream098:
    .byte $F0, $00, $F8, $00, $80, $0C, $F9
AudioStream099:
    .byte $F0, $00, $F8, $00, $80, $0C, $F9
AudioStream100:
    .byte $F0, $00, $F8, $00, $80, $0C, $F9
AudioStream101:
    .byte $F0, $00, $F1, $0F, $80, $00, $F9
AudioStream102:
    AudioCall AudioStream098
    .byte $F9
AudioStream103:
    AudioCall AudioStream099
    .byte $F9
AudioStream104:
    AudioCall AudioStream100
    .byte $F9
AudioStream105:
    AudioCall AudioStream101
    .byte $F9
AudioStream106:
    .byte $F1, $08, $F0, $00, $F8, $80, $81, $07, $12, $06, $11, $05, $10
    AudioJump AudioStream106
AudioStream107:
    .byte $F1, $08, $F0, $00, $F8, $80, $81, $02, $09, $01, $08, $00, $07
    AudioJump AudioStream107
AudioStream108:
    .byte $F1, $00, $F0, $06, $F8, $C0, $81, $12, $19, $11, $18, $10, $17
    AudioJump AudioStream108
AudioStream109:
    .byte $F0, $00, $F1, $0F, $80, $01, $F9
AudioStream110:
    AudioJump AudioStream106
AudioStream111:
    AudioJump AudioStream107
AudioStream112:
    .byte $F1, $00, $F0, $06, $F8, $C0, $81, $22, $29, $21, $28, $20, $27
    AudioJump AudioStream112
AudioStream113:
    .byte $F0, $00, $F1, $0F, $80, $01, $F9

.assert * - AudioStream000 = $0A68, error, "unexpected audio stream data size"

.if SolomonRevision = SolomonRevisionEurope
; Temporary layout compensation while PAL audio data is reconstructed
; The European room/audio region begins $80 bytes earlier, while vectors keep
; their fixed CPU addresses at $FFFA-$FFFF
    .res $80, $FF
.endif

.segment "VECTORS"

CpuVectors:
    .word NMI, Reset, $00FF

.assert * - CpuVectors = 6, error, "unexpected CPU vector size"
