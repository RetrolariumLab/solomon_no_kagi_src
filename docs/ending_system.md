# Ending system

This guide describes the ending sequence and the special-room support it shares with late-game transitions.


---

## Ending sequence

Room index 49 dispatches to `RunEndingRoomScript` at `$BA34`. The handler owns
context 6 until it starts room-clear selector `$16` and stops itself. Its exact
864-byte extent is assembly-asserted.

The sequence proceeds through these verified stages:

1. Clear both packed inventory halves and wait for Dana to be active.
2. Watch block-cast cells `$6C` and `$67`, then stop the other secondary
   contexts and switch the room into ending state.
3. Convert all 17 enemies to type `$1C`, calculate motion vectors toward map
   cell `$67`, and advance them until gameplay counter 6 reaches `$43`.
4. Clear gameplay objects and the nametable, install the ending spark, and
   optionally run ten eight-object orbit waves.
5. Advance remaining objects until eleven are inactive; for the full ending,
   populate 17 objects repeatedly with deterministic random X/Y positions
   while the vertical scroll moves from `$EB` toward `$90`.
6. Select and publish the ending text streams, apply three palette values, and
   wait for controller input before handing control to scheduler code `$16`.

The text path uses two layers of tables. `EndingMessageSequenceStarts` chooses
a sequence from game-state flags; `EndingMessageSequence` yields text indices;
`EndingMessageTextOffsets` and `EndingMessageData` then construct PPU-buffer
commands. Initial and later messages both wait for the high byte of the active
PPU stream pointer to clear before overwriting the shared buffer.

The handler calls source-owned helpers and consumes source-owned tables in
`src/game/ending/special_room_support.asm`. That adjacent module also
classifies the complete tail through `$C0FF`, so the ending no longer depends
on numeric aliases into the preservation listing.

---

## Ending and special-room support

The contiguous `$BD94-$C0FF` range supports both the room-index 49 ending and
the context-6 special-room scripts. It is source-owned as one 876-byte module;
an assembly assertion protects the exact boundary before `$C100`.

### Ending helpers and tables

`BuildEndingPpuMessage` copies the 19-byte static PPU stream at `$95F3` into
the shared update buffer and patches its palette tile. The three-byte
`EndingPaletteValues` table drives the final reverse-order fade.

`InitializeRandomEndingObject` uses two successive outputs from
`AdvanceRandomState` as Y and doubled X coordinates. It builds a four-byte
motion vector toward `($D0,$78)`, copies that vector to the corresponding enemy
AI record, and initializes object type `$50` with a random action from
`$0C-$13`.

The ending text is represented by the same control bytes consumed by the
original PPU-buffer producer. Three terminated message-index sequences select
among ten zero-terminated messages. The source comments decode the visible
English text while retaining the exact tile bytes and destination addresses.

### Solomon's Seal state

Each special Seal room passes one bit from `$01` through `$80` to
`RevealCurrentRoomSeal`. The routine waits until room-state bit `$02` is set,
stores that bit in `$7B`, and checks it against the collected bitset at `$7A`.
For an uncollected Seal, the index of the set bit selects one of eight map
positions and writes tile `$60` there. `ApplySolomonSealItem` later merges the
current-room bit into the collected bitset and increments the Seal count.

The module also owns the twelve room-index 48 object positions and the two
24-byte special block bitplanes used by displayed rooms 20 and 30.

### Tail classification

The final `$C012-$C0FF` bytes have no references and are identified by
Bisqwit's map as `FillerBeforeC100`. They remain explicit because their exact
contents, including several nonalternating bytes, are required for a matching
ROM build.
