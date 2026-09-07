; Solomon's Key NES ROM Disassembly
; PRG CRC32 checksum: 0771c34f
; CHR CRC32 checksum: fad8a464
; Overall CRC32 checksum: 40684e95
; Code base address: $8000
; author: ninespaces
; ROM map info from https://www.romhacking.net/documents/902/
; see also: https://docs.google.com/spreadsheets/d/1EKLm0fHJ-rp5udljMHu-O83MaiY2XTmdcYA7ya-KYNQ/edit?usp=sharing
; preservation baseline imported from:
; https://github.com/rbmichael/solomons_key_disassembly

.setcpu "6502x"

SolomonRevisionUsa = 0
SolomonRevisionEurope = 1

.ifndef SolomonRevision
SolomonRevision = SolomonRevisionUsa
.endif

.assert SolomonRevision = SolomonRevisionUsa .or SolomonRevision = SolomonRevisionEurope, error, "unsupported Solomon's Key revision profile"

.segment "HEADER"

    .byte "NES", $1a  ; Magic string that always begins an iNES header
    .byte $02  ; Number of 16KB PRG-ROM banks
    .byte $04  ; Number of 8KB CHR-ROM banks
    .byte $30  ; Control bits 1
    .byte $00  ; Control bits 2
    .byte $00  ; Number of 8KB PRG-RAM banks
    .byte $00  ; Video format NTSC/PAL

.include "memory/hardware.inc"
.include "memory/ram.inc"

.include "data/static_layout.asm"
.include "system/boot_and_frame.asm"
.include "system/thread_runtime.asm"
.include "game/nmi/gameplay_interactions.asm"
.include "game/nmi/dana_and_sprites.asm"
.include "game/objects/update_pipeline.asm"
.include "game/objects/collision_and_motion.asm"
.include "game/enemies/runtime.asm"
.include "game/enemies/early_ai.asm"
.include "game/enemies/mid_ai.asm"
.include "game/enemies/pathfinding_ai.asm"
.include "game/enemies/collision_ai.asm"
.include "game/enemies/late_ai.asm"
.include "game/rooms/lifecycle.asm"
.include "game/rooms/decoding.asm"
.include "game/rooms/mechanics.asm"
.include "game/items/collection.asm"
.include "game/items/progression.asm"
.include "game/demon_mirror/runtime.asm"
.include "game/ending/sequence.asm"
.include "game/ending/special_room_support.asm"
.include "game/flow/runtime.asm"
.include "game/timer/runtime.asm"
.include "game/transitions/orbit.asm"
.include "game/dana_actions.asm"
.include "game/scoring.asm"
.include "graphics/ppu/runtime.asm"
.include "graphics/rooms/rendering.asm"
.include "graphics/hud/runtime.asm"
.include "graphics/title_screen.asm"
.include "data/enemies/tables.asm"
.include "data/objects/animations.asm"
.include "data/objects/motion.asm"
.include "data/rooms/metadata.asm"
.include "data/rooms/blocks.asm"
.include "data/rooms/enemies.asm"
.include "data/rooms/items.asm"
.include "audio/engine.asm"
.include "audio/data.asm"
.include "graphics/chr.asm"
