# Scheduler entry tables

`StartThread` receives a packed byte: the high nibble selects one of eight
stack contexts and the low nibble selects a two-byte entry in that context's
table. The table word is an RTS return address, so the first executed address
is always the stored word plus one.

`scripts/validation/scheduler_data.py` extracts these tables from the built PRG and scans
the assembly source for immediate `StartThread` calls. `make scheduler-audit`
compares the decoded result with `config/validation/scheduler_entries.json`, including
entries independently reviewed behind dynamically selected calls. Any new
code, changed pointer, stack partition, or static/dynamic call count must be
reviewed before the manifest is updated.

The table layout is profile-selected. USA stores the initial stack pointers at
`$8E01` and context-table bases at `$8E09`; PAL stores them at `$8E10` and
`$8E18`. `config/validation/scheduler_entries_europe.json` independently records all 16
static and seven reviewed dynamic codes at their native PAL slots and targets.
`make scheduler-profile-audits` decodes both source-built ROMs while retaining
the common context roles and call-site inventory.

The currently referenced USA static entries are:

| Code | Context | Selector | Base | Slot | Stored return | Entry |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `$10` | 1 | 0 | `$8E17` | `$8E17` | `$901D` | `$901E` |
| `$14` | 1 | 4 | `$8E17` | `$8E1F` | `$8EE3` | `$8EE4` |
| `$15` | 1 | 5 | `$8E17` | `$8E21` | `$9020` | `$9021` |
| `$16` | 1 | 6 | `$8E17` | `$8E23` | `$C851` | `$C852` |
| `$17` | 1 | 7 | `$8E17` | `$8E25` | `$CA6D` | `$CA6E` |
| `$18` | 1 | 8 | `$8E17` | `$8E27` | `$CB09` | `$CB0A` |
| `$22` | 2 | 2 | `$8E29` | `$8E2D` | `$CB2A` | `$CB2B` |
| `$30` | 3 | 0 | `$8E2F` | `$8E2F` | `$9FFF` | `$A000` |
| `$31` | 3 | 1 | `$8E2F` | `$8E31` | `$C7E6` | `$C7E7` |
| `$32` | 3 | 2 | `$8E2F` | `$8E33` | `$C586` | `$C587` |
| `$33` | 3 | 3 | `$8E2F` | `$8E35` | `$C789` | `$C78A` |
| `$35` | 3 | 5 | `$8E2F` | `$8E39` | `$C831` | `$C832` |
| `$42` | 4 | 2 | `$8E3B` | `$8E3F` | `$C397` | `$C398` |
| `$43` | 4 | 3 | `$8E3B` | `$8E41` | `$C388` | `$C389` |
| `$50` | 5 | 0 | `$8E43` | `$8E43` | `$C0FF` | `$C100` |
| `$60` | 6 | 0 | `$8E45` | `$8E45` | `$B7FF` | `$B800` |

Code `$50` is now source-owned as `ProcessDefeatedEnemyDrops`. The red-bottle
item marks eligible enemy records and starts this context, which converts all
marked records into table-selected drop objects before stopping context 5.

Code `$60` is source-owned as `RunSpecialRoomScriptThread`. Context 6 uses the
current room index to dispatch a cooperative room-specific trigger, then stops
itself when that handler returns. The dispatcher covers all 53 room indices,
including the four secret rooms whose offsets follow the old disassembler's
apparent code boundary.

The gameplay-exit family is also source-owned. Code `$33` enters
`RunTimeOverTransition`, `$31` enters `RunDanaDeathTransition`, and `$35`
enters their shared `FinalizeGameplayExit` stage in context 3. When no lives
remain, code `$16` enters `PreparePostGameResult` in context 1 to calculate
and display `YOUR GDV`.

The thread selected by that flow, code `$17`, enters
`RunPostGameAttractThread`. It presents the post-game streams and title wait;
code `$18` enters the nested `StartDemoPlayback` point after the optional
normal-game setup call. Demo setup starts context-two code `$22` at
`RunDemoInputPlayback`, which replaces cached gameplay input from a recorded
duration/value stream while continuing to observe real Start/Select presses.

Context 4's complete selector family is now classified. `$40` enters
`RunMapItemPresentation`, `$41` enters
`RunExtraLifeMapItemPresentation`, `$42` enters
`RunEnemyItemPresentation`, and `$43` enters
`RunExtraLifeEnemyItemPresentation`. Only `$42/$43` appear as direct immediate
calls in the static inventory because `$40/$41` are selected through
`ItemInteractionThreadCode` after map-item dispatch.

There are 18 immediate calls using those 16 distinct codes and four sites
whose accumulator value is selected dynamically. Three use `JSR StartThread`;
the map-item path uses `JMP StartThread` as a tail call. Dynamic sites are
recorded as a count because static source inspection cannot prove every
runtime value.

Seven additional USA table slots are independently reconstructed even though
their callers select the code dynamically:

| Code | Context | Selector | Base | Slot | Stored return | Entry |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `$11` | 1 | 1 | `$8E17` | `$8E19` | `$9B79` | `CastOrRemoveBlock` (`$9B7A`) |
| `$12` | 1 | 2 | `$8E17` | `$8E1B` | `$9A6C` | `HandleDanaHeadCollision` (`$9A6D`) |
| `$13` | 1 | 3 | `$8E17` | `$8E1D` | `$9B04` | `CastFireballFromInventory` (`$9B05`) |
| `$21` | 2 | 1 | `$8E29` | `$8E2B` | `$8E46` | `PauseGameThread` (`$8E47`) |
| `$34` | 3 | 4 | `$8E2F` | `$8E37` | `$C23B` | `RunKeyCollectionPresentation` (`$C23C`) |
| `$40` | 4 | 0 | `$8E3B` | `$8E3B` | `$C394` | `RunMapItemPresentation` (`$C395`) |
| `$41` | 4 | 1 | `$8E3B` | `$8E3D` | `$C385` | `RunExtraLifeMapItemPresentation` (`$C386`) |

Together, the static and reviewed entries cover all 23 semantic entry codes
used by contexts 1 through 6. Context 0 is the startup coordinator and context
7 remains idle-only, so neither has an entry code.
