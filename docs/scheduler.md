# Cooperative scheduler

## Owned range and contexts

`src/system/thread_runtime.asm` owns CPU `$8D5F-$8E46` (232 bytes). It implements
eight cooperative contexts over the 6502 hardware stack page. The saved SP for
each context lives in `ThreadStackPointers`, and `ThreadIndex` selects the
current slot.

`InitialThreadStackPointers` contains:

```text
context 0  1  2  3  4  5  6  7
SP      FC DC BC 9C 7C 5C 3C 1C
```

The descending order gives each context a roughly `$20`-byte partition.

## Context switch

`SwitchThreads` performs the complete cooperative handoff:

1. copy the hardware SP to `ThreadStackPointers[ThreadIndex]`;
2. increment `ThreadIndex` modulo eight;
3. load the selected saved SP and execute `TXS`;
4. execute `RTS`, which returns through the continuation on the newly selected
   stack rather than the caller's original stack.

There is no register-file copy. Callers must treat A, X, Y, and flags according
to their own continuation contract; only the stack continuation is switched.

## Starting and stopping contexts

`StartThread` accepts a packed byte. Its high nibble chooses the context and its
low nibble chooses a two-byte entry from the base selected through
`ThreadEntryTableBases`. It marks the context active, resets its SP, copies the
selected return address onto its stack partition, and can immediately select
that context.

`StopThread` resets the requested SP, installs `IdleThreadLoop - 1` as its next
RTS continuation, and clears the corresponding `ActiveThreadMask` bit. If the
stopped context is current, it also restores the reset SP before returning.
Idle contexts repeatedly call `SwitchThreads`.

All 61 direct calls to the three scheduler entry points use these semantic
symbols; no source call site retains raw `$8D5F`, `$8DB4`, or `$8DCA` operands.

The packed entry table is now decoded and machine-checked. Sixteen distinct
static codes occur in 18 immediate call sites, plus four calls whose A value
is selected dynamically. One of those four is a tail `JMP StartThread`; the
source audit deliberately recognizes both call forms. Seven dynamically
selected entries have also been reconstructed independently. See
`docs/scheduler_entries.md` for the complete context/selector/return/entry
table and the important RTS-plus-one convention.

PAL preserves the same eight stack partitions, 23 known entry codes, and
context roles, but moves `InitialThreadStackPointers` and
`ThreadEntryTableBases` `$0F` bytes later. Its entry targets then follow their
own subsystem relocations. `make scheduler-profile-audits` binds both layouts
to separate reviewed manifests.

## Context responsibilities

All eight contexts now have a stable role derived from their entry tables and
callers. `make scheduler-audit` checks that every known static or reviewed
dynamic code appears under exactly one matching context.

| Context | Entry codes | Responsibility |
| ---: | :--- | :--- |
| 0 | none | Startup coordinator: drains `PendingThreadStarts` and schedules contexts |
| 1 | `$10-$18` | Room lifecycle, Dana actions, post-game, title, and attract flow |
| 2 | `$21-$22` | Pause handling and recorded demo input |
| 3 | `$30-$35` | Main gameplay and gameplay-exit transitions |
| 4 | `$40-$43` | Map-item and enemy-item presentation |
| 5 | `$50` | Defeated-enemy drop conversion |
| 6 | `$60` | Special-room scripts |
| 7 | none | Reserved idle-only context |

Context 0 begins on the reset stack and remains the coordinator instead of
being entered through `StartThread`. Startup pre-seeds idle continuations for
contexts 2 through 7, starts context 1 with code `$17`, and then context 0
repeatedly drains the four pending-start slots before yielding. Context 7 has
no known entry code or start caller and permanently follows that idle frame.

## Runtime scheduling evidence

The first 24 `SwitchThreads` entries after gameplay begins follow the strict
cycle `3,4,5,6,7,0,1,2` in both the user-started first room and the populated
attract demo. Over the first 60 gameplay frames, Room 1 records context switch
counts of `829,828,828,829,829,829,829,829`; the attract demo records exactly
205 for every context. Idle contexts therefore preserve round-robin order but
cycle substantially faster when less cooperative work is runnable.

These observations are generated and checked by `make trace-runtime`; exact
event series and counts live in `scenarios/runtime_scenarios.json`. The static
role map is complete. A deeper trace of SP, `ActiveThreadMask`, the eight saved
SP bytes, and continuation addresses would still make useful evidence for
individual suspension and resumption paths.
