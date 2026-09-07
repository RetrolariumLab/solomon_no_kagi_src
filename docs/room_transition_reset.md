# Room-transition state reset

`src/game/rooms/transition_reset.asm` owns CPU `$C981-$C9BC`: the presentation
data immediately before the reset helper and the helper itself. Both reset
callers are named in the source-owned gameplay-exit flow beginning at `$C78A`.

The data block contains the four-value PPU-mask cycle used by the life-loss
animation, the direct PPU program that displays `TIME OVER.`, and a 15-byte
post-game result template. The result flow copies that final template into the
shared buffer and patches two value bytes before publication.

`ResetRoomTransitionState` performs four operations:

1. keeps scheduler context 3 active while resetting the other secondary
   contexts through `ResetOtherSecondaryThreads`;
2. clears bits 6 and 2 of `GameplayFlags` with mask `$BB`;
3. clears `FireballActive`;
4. queues sound-effect command 3.

The helper exposes a repeated room-transition boundary while the preceding
animation, life handling, score comparison, and PPU control flow remains the
next reconstruction range.
