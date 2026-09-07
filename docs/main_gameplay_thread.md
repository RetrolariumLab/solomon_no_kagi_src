# Main gameplay thread

`src/game/flow/runtime.asm` owns CPU `$A000-$A04B`. Scheduler code `$30`
selects context 3, selector 0. Its table slot contains `$9FFF`; because the
scheduler enters the context with `RTS`, this proves `$A000` is the entry point.

The loop invokes four groups of services and yields through `SwitchThreads`
after each group. It then checks `FairiesQueued`, attempts to allocate and
initialize the next fairy when one is pending, and returns to
`MainGameplayThread`. Both the no-fairy path and the failed-allocation path
converge at `ContinueMainGameplayThread`.

The first two services are now source-owned as
`UpdateDemonMirrorSpawnSchedule` and `ActivatePendingDemonMirrorEnemies`.
Together they sample both room schedules, allocate mirror placeholders, and
later configure their saved enemy slots from cyclic enemy sets. The former raw
service at `$C432` is now `CheckDanaMapTileInteraction`; it samples the map
cell under Dana and dispatches collectible effects. See
`docs/demon_mirror_runtime.md` and `docs/item_interactions.md`.
