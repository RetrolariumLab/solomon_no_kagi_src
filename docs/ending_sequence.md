# Ending sequence

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
