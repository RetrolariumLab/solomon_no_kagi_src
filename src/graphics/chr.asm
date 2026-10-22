; Private CHR payload extracted by make split
; Segment PRG_BANK_1 is the upstream disassembly's name; cnrom.cfg loads it into CHR

.segment "PRG_BANK_1"

    .incbin "../../assets/generated/chr/solomons_key.chr"
