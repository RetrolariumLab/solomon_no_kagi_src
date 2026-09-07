# Linked enemy AI support

`src/game/enemies/early_ai.asm` now owns the contiguous `$B2A2-$B429`
support range in addition to the primary handler table. The source file is 300
lines, keeping the related code together without introducing another small
assembly module.

## Action dispatch

`RunEnemyAiDispatcher` subtracts `$14` from an eligible object's type and
`DispatchEnemyAiHandler` divides that selector by four. Handler-table entries
15-17 therefore route types `$50-$5B` to `RunType50To5BEnemyAi`.

That handler first applies the room lifetime threshold, then shifts object
action byte 3 right twice. The resulting selector enters a seven-address
`JumpWithParams` appendix at `$B351`. Its locally reconstructed paths can
retire the current slot after AI phase `$11`, begin horizontal movement, or
run the single-linked-slot state machine.

The adjacent `$B178` handler is reconstructed as `RunType48To53EnemyAi` in
`src/game/enemies/late_ai.asm`; its inline appendix calls
`SetEnemyHorizontalStepAndFacing` and `UpdateLinkedEnemyPairSpawn` in this
range.

## Linked slots

Both allocation paths use the carry contract of `FindFreeEnemySlotIndex` and
its returned `TempPointer04` AI-record pointer:

- the pair path stores allocated indices in parent AI bytes 6 and 7;
- if the second allocation fails, it clears the first allocated AI state;
- the single path stores one index in byte 6 and resolves its parallel object
  record through `EnemyObjectPointerLowTable` and its high table;
- parent state/action bits record whether the linked transition is active.

The drop-conversion code consumes the same byte-6/byte-7 links when retiring
multi-slot enemies, so these offsets now live in the shared RAM registry.

## Map probe

`CalculateEnemyForwardMapCoordinates` tests action bit 0 and selects a point
24 pixels to the right or 8 pixels to the left of the object, with an
eight-pixel vertical offset. The ordinary pixel-to-map converter then lets the
linked-slot paths distinguish occupied tiles, interactive tiles below `$F8`,
and the open/sentinel range beginning at `$F8`.

AI bytes 1, 4, and 5 are named only by their observed phase/delta roles here.
Enemy-specific creature names remain deferred until runtime traces bind each
numeric type group to an observed room entity.
