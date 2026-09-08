# Unknowns and research queue

Source Reconstruction 2.1 has no unresolved question that blocks the accepted
USA or European fixed-layout profiles. Neutral names remain where the original
developers' historical intent cannot be proven; those are evidence boundaries,
not missing binary ownership.

## Open and explicitly deferred

1. Japan is hash-identified and its private CHR has an isolated extraction
   path, but it has no complete source build or direct runtime matrix. It remains
   a planned profile rather than an accepted 2.1 artifact.
2. The USA and European runtime matrices cover critical boot, gameplay,
   pause, death/reload, audio, scheduler, and transition paths; they do not
   claim an exhaustive 53-room longplay or every ending/special-room branch.
3. Systematic relocation, expanded images, mapper changes, and sibling engines
   require a future major release because they change the fixed-layout ABI.

## Resolved questions

- USA and Europe are independent complete source builds with byte-identical
  image gates, profile-owned PAL timing/layout differences, direct runtime
  evidence, and regional authoring round trips. Japan is kept separate rather
  than borrowing conclusions from either accepted profile.

- Every PRG byte is now separated into code, data, encoded stream, padding, or
  vector by `make prg-layout-audit`; there are no generated labels or raw
  control-flow addresses left.
- All eight scheduler contexts have stable responsibilities. The manifest
  covers all 23 known entry codes, context 0's startup coordinator, and
  context 7's permanently idle reservation; `make scheduler-audit` enforces
  the complete map.
- Dana record byte 3 is a facing-preserving action selector through `$23`, and
  byte 5 is signed Y motion. `docs/dana_action_states.md` records every proven
  pair. Fireball bytes `$0430-$0431` are the current and alternate four-way
  path directions consumed through the shared synthetic AI-record pointer.
- All eight bytes of the parallel enemy AI record have shared offset names.
  Bytes 1 and 2-3 are distinct phase and lifetime accumulators, bytes 4-5 are
  Dana-relative deltas, and bytes 6-7 are family-specific linked-slot or path-
  direction fields. See `docs/enemy_ai_record.md`.
- All 20 bytes of the gameplay object record have established roles. Its six
  collision bits are geometrically mapped from upper-left through below-right,
  with bits 0-3 selecting the response table. See `docs/object_record.md`.
- Special-room selectors `$10/$20/$30` map to the Page of Time, Page of Space,
  and constellation bonus rooms. Internal rooms 48/49 are the Princess and
  Solomon ending rooms; the room 17/39 Mighty Bomb Jack and room 20/38 Tecmo
  Bunny scripts, page collectible, and Golden Wings flag now have gameplay
  names backed by code behavior and independently documented room locations.
  See `docs/special_room_scripts.md`.
- The complete CNROM policy is documented in `docs/chr_bank_policy.md`.
  `make chr-bank-audit` proves the decoded 53-room bank distribution; source
  inspection accounts for reset, intro, gameplay, transition, title, and
  ending requests.
- `RoomMap` geometry is fixed by shared assembly constants: 16 columns by 14
  stored rows, with a 16x12 playable range at indices `$10-$CF` and sentinel
  rows at `$00-$0F` and `$D0-$DF`.
- Every `RoomMap` byte is structurally classified by
  `docs/room_map_tiles.md`: low six identity bits, decoration bit 6, collision
  bit 7, and the immutable `$F8-$FF` range.
- The gameplay vocabulary for every `RoomMap` identity used by stock room
  scripts is now explicit. The source distinguishes encoded map values from
  incremental-render-only patterns, identifies the two modifiable item
  quartets, and preserves the unreachable `$23/$24` handler-table overflow as
  original behavior. See `docs/room_map_tiles.md`.
- Audio mailbox and channel priority are now runtime-proven. Commands are
  consumed from slot 2 down to slot 0, so a lower occupied slot wins an
  overlapping virtual record; even virtual channels 0/2/4/6 temporarily own
  their paired APU voice over odd background channels 1/3/5/7. See
  `docs/audio_engine.md` and the `audio-channel-priority` scenario.
- Timer-service frequency and scheduler switch rate under low and high object
  load are reproduced by the Room 1 and attract-demo runtime scenarios.
  `GameplayUpdateCount` is now proven to preserve every serviced gameplay NMI
  tick across delayed main-thread passes. The internal timer catches up, HUD
  publication may be deferred, and NMI stack-safety skips can still make game
  time lag wall time. See `docs/timer.md`.

Unknowns stay here until evidence resolves them; they are not silently removed
when a plausible name appears.
