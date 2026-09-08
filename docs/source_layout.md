# Source layout

`src/main.asm` owns the CPU selection, iNES header, hardware/RAM registries, and
one include per subsystem source. The linker restores physical ROM order from
the named segments inside those sources; see
[source organization](source_organization.md). Semantic modules own NMI at `$8000-$80FE`, its enemy
overlap/fireball collision and Dana action services at `$80FF-$837C`, controller
sampling at `$837D-$83C1`, Dana control and object-to-OAM composition at
`$83C2-$863B`, and the per-frame object update pipeline at
`$863C-$87DF`, its complete collision-response dispatcher at `$87E0-$8A61`,
object surface clamping at `$8A62-$8ABF`, object motion/animation definition loading
at `$8AC0-$8B50`, NMI-side RoomMap attribute reads at
`$8B51-$8B7E`, the PPU update bytecode interpreter at `$8B7F-$8BE1`, and
classified pre-Reset filler at `$8BE2-$8BFF`. Startup begins at `$8C00-$8D5E`,
and the scheduler at
`$8D5F-$8E46`.
Context 2's pause loop is at `$8E47-$8E8C`, sound-effect request
queuing at `$8E8D-$8E9F`, PPU
update-buffer publication at `$8EA0-$8EA8`, inline appendix dispatch at
`$8EA9-$8EBF`, and the complete room-clear/load pipeline at `$8EC0-$915D`.
Standard gameplay-delay setup follows at `$915E-$9164`, cooperative
masked-RAM waits at `$9165-$9189`, room-map
coordinate conversion at `$918A-$91B8`, and initial door/key publication,
intro UI, room-entry animation, and sine-driven transition objects at
`$91B9-$9470`. Static PPU update publication starts at
`$9471-$9487`, its split pointer tables at `$9488-$94AB`, and all 18 static
update streams at `$94AC-$961A`.
The adjacent room-enemy stream loader owns `$961B-$9660`.
Direct rendering of the 16x12 RoomMap interior owns `$9661-$96DB`.
The shared direct-PPU transfer guard owns `$96DC-$970A`.
The room nametable frame renderer owns `$970B-$97A2`.
Repeated PPU byte writers own `$97A3-$97B7`, followed by their four packed
patterns at `$97B8-$97C7`.
Room item metadata/stream decoding owns `$97C8-$9952`; its runtime lookup
tables follow at `$9953-$99F1`.
Runtime room-map initialization and block-plane expansion own `$99F2-$9A6C`.
Dana's three cooperative head-collision, fireball, and block-magic actions own
`$9A6D-$9C51`.
The shared cooperative counter wait owns `$9C52-$9C5F`.
Shared RoomMap/object interactions own `$9C60-$9DB0`, followed by the
coordinate/object overlap predicate at `$9DB1-$9DCF`.
The cooperative single-cell PPU producer owns `$9DD0-$9EDF`, its nametable and
attribute address helpers own `$9EE0-$9F22`, and classified filler occupies
`$9F23-$9FFF` immediately before the main gameplay thread.
The context-three main loop owns `$A000-$A04B`; the complete Demon Mirror
schedule, allocation, initialization, enemy-set loop, and delayed activation
runtime continues through `$A15E`.
Timer logic owns `$A15F-$A225`, its overlapping threshold/PPU-stream data owns
`$A226-$A237`, and its display builder owns `$A238-$A273`, followed by the
enemy movement prepass at `$A274-$A2DB`.
The adjacent AI dispatcher owns `$A2DC-$A30B`. The packed fireball-inventory
HUD builder and its tables own `$A30C-$A3A3`.
Fireball lifetime and delayed cleanup own `$A3A4-$A3D6`.
Enemy slot position/state initialization follows at `$A3D7-$A3F7`.
Type-specific object/AI configuration owns `$A3F8-$A44D`.
Its 27-byte packed flag table follows at `$A44E-$A468`.
The inline AI handler dispatcher and its 28 pointers own `$A469-$A4A5`.
The shared current-enemy position helper owns `$A4A6-$A4B2`.
The first two enemy AI families and collision reward helpers own `$A4B3-$A68B`.
The two indexed enemy-record pointer resolvers own `$B28A-$B2A1`.
The free enemy-slot allocator owns `$B42A-$B445`.
Their split record-pool pointer tables own `$B446-$B491`.
The adjacent enemy-slot deactivation helper owns `$B492-$B4B5`.
Current selected-enemy deactivation owns `$B4B6-$B4C3`.
The context-3 key collection handoff owns `$C23C-$C2A5`.
The cooperative key-to-door flight and shared fixed-point motion helper own
`$C2A6-$C363` inside the thematic key-item module.
The shared signed coordinate-delta scaler owns `$C364-$C385`.
The gameplay HUD coordinator, fairy-count template, and score formatter own
`$C3D4-$C42D`. Dana's map-tile classifier, its complete 29-entry item
dispatcher, special item effects, key/door progression, and full object/AI
pool clear continue contiguously through `$C627`.
Timer item effects own `$C628-$C697`.
Inventory, fairy, fireball-lifetime, and score item entries own `$C698-$C70F`.
Item score tables and the shared auxiliary-effect initializer own
`$C710-$C73A`.
Shared decimal score addition owns `$C73B-$C755`.
Secondary-context transition reset owns `$C756-$C789`.
The complete cooperative gameplay-exit flow owns `$C78A-$C980`: life-loss and
`TIME OVER` presentation, `YOUR GDV` calculation, best-score replacement, and
selection of the next room or post-game thread. Its static presentation data
immediately follows at `$C981-$C9A6`.
The shared room-transition state reset owns `$C9A7-$C9BC`.
Descriptor-driven direct PPU nametable clearing owns `$C9BD-$CA32`, followed
by its three nine-byte descriptor records at `$CA33-$CA3B`.
Non-Dana object state maintenance owns `$CA3C-$CA6D`, split into two sweep
routines around the shared pointer resolver.
The attract/demo flow owns `$CA6E-$CB6E`: post-game PPU streams, title-screen
waiting, fixed demo-room setup, and a context-two recorded-input producer.
Full clearing of both physical nametables owns `$CB6F-$CBA5`.
Packed title rendering and record presentation own `$CBA6-$CD52`, including
the command decoder, both direct-PPU layers, and their small fixed templates.
The shared PPU address-latch helper owns `$CD53-$CD5E`.
The two packed title streams own `$CD5F-$CEF0`; the 34-byte demo duration and
input tables immediately follow at `$CEF1-$CF34`, followed by classified
filler through `$CFFF`.
The 58 four-byte logical RoomMap tile patterns own `$D000-$D0E7`.
No address-ordered preservation listing remains; all 32 KiB of PRG belong to
registered semantic or classified-data modules.
`src/graphics/chr.asm` includes the ignored CHR payload created by
`make split`; no CHR bytes are kept in Git.

The linker deliberately preserves the upstream segment names:

| Segment | Meaning | Output size |
| --- | --- | ---: |
| `HEADER` | 16-byte iNES header | 16 |
| `PRG_NMI` | semantic NMI and PPU commit module | 255 |
| `PRG_NMI_GAMEPLAY_INTERACTIONS` | enemy overlap, fireball collision, Dana action requests | 638 |
| `PRG_CONTROLLER_INPUT` | two-port serial controller sampling and caching | 69 |
| `PRG_NMI_DANA_AND_SPRITES` | Dana action dispatch and non-Dana OAM composition | 634 |
| `PRG_OBJECT_UPDATE` | active 21-record object traversal | 77 |
| `PRG_OBJECT_MOTION` | signed fixed-point Y/X integration | 75 |
| `PRG_OBJECT_COLLISION` | six-cell RoomMap collision sampling | 181 |
| `PRG_OBJECT_ANIMATION` | packed phase and three-byte frame sequencer | 87 |
| `PRG_OBJECT_COLLISION_DISPATCH` | state gate and mask-indexed tail dispatch | 38 |
| `PRG_OBJECT_COLLISION_HANDLERS` | 16 collision-response pointers | 32 |
| `PRG_OBJECT_COLLISION_RESPONSE` | mask-specific coordinate, motion, and action handlers | 539 |
| `PRG_OBJECT_Y_THIRTEEN_CLAMP` | align Y to the `$...D` cell inset | 33 |
| `PRG_OBJECT_Y_CLAMP` | align object Y to a 16-pixel surface | 29 |
| `PRG_OBJECT_X_LEFT_CLAMP` | clamp X against a left-side surface | 37 |
| `PRG_OBJECT_X_RIGHT_CLAMP` | clamp X against a right-side surface | 28 |
| `PRG_OBJECT_MOTION_ANIMATION` | type/action motion and animation definition loader | 145 |
| `PRG_PPU_ATTRIBUTE_READ` | NMI RoomMap attribute-byte request service | 46 |
| `PRG_PPU_UPDATE_STREAM` | compact NMI-side PPU update bytecode interpreter | 99 |
| `PRG_PRE_STARTUP_PADDING` | classified non-code filler before Reset | 30 |
| `PRG_STARTUP` | reset and startup module | 351 |
| `PRG_SCHEDULER` | cooperative scheduler and entry tables | 232 |
| `PRG_PAUSE_THREAD` | context-two pause and Start debounce loop | 70 |
| `PRG_SOUND_EFFECT_QUEUE` | three-slot sound-effect request producer | 19 |
| `PRG_PPU_UPDATE_BUFFER` | shared RAM update-program publication | 9 |
| `PRG_JUMP_WITH_PARAMS` | inline appendix tail dispatcher | 23 |
| `PRG_ROOM_LOAD_PALETTE` | room palette update template | 36 |
| `PRG_ROOM_CLEAR_THREAD` | context-one room-clear presentation and handoff | 190 |
| `PRG_ROOM_CLEAR_DATA` | overlapping AI/object templates and X positions | 14 |
| `PRG_ROOM_TIME_BONUS` | decimal timer-to-score conversion and display update | 110 |
| `PRG_ROOM_LOAD_THREAD` | new-game/common room loading pipeline | 256 |
| `PRG_ROOM_LOAD_DATA` | Dana preload, room-group colors, and palette offsets | 22 |
| `PRG_NEW_GAME_STATE_RESET` | new-game counters, flags, and score reset | 42 |
| `PRG_GAMEPLAY_DELAY_SETUP` | reset and select gameplay delay counter | 7 |
| `PRG_MASKED_RAM_WAIT` | cooperative masked zero-page condition waits | 37 |
| `PRG_COORDINATE_CONVERSION` | pixel and packed room-index conversion | 47 |
| `PRG_ROOM_DOOR_KEY_UPDATE` | publish initial door and visible key map cells | 50 |
| `PRG_ROOM_INTRO` | room/lives HUD, special-room name, marker, and spark setup | 135 |
| `PRG_ROOM_INTRO_DATA` | compact intro PPU program, spark header, and names | 55 |
| `PRG_TWO_DIGIT_NUMBER` | blank-padded decimal tens/ones formatter | 19 |
| `PRG_ROOM_ENTRY_ANIMATION` | Dana placement and timed entry presentation | 115 |
| `PRG_ROOM_ENTRY_ANIMATION_DATA` | orbit AI and entry-spark state templates | 17 |
| `PRG_TRANSITION_OBJECT_ORBIT` | `$40`-tick fifteen-object orbit controller | 120 |
| `PRG_TRANSITION_ORBIT_POSITION` | reflected-sine object coordinate placement | 113 |
| `PRG_TRANSITION_ORBIT_SCALE` | eight-round orbit component scaler | 23 |
| `PRG_QUARTER_SINE` | reflected six-bit phase lookup | 17 |
| `PRG_QUARTER_SINE_DATA` | 32 seven-bit quarter-sine magnitudes | 32 |
| `PRG_STATIC_PPU_UPDATE_QUEUE` | blocking indexed static-stream producer | 23 |
| `PRG_STATIC_PPU_UPDATE_POINTERS` | split pointers for 18 static streams | 36 |
| `PRG_STATIC_PPU_UPDATE_STREAMS` | 18 compact PPU command programs | 367 |
| `PRG_ROOM_ENEMY_LOAD` | current-room enemy stream to runtime slots | 70 |
| `PRG_ROOM_MAP_RENDER` | direct 16x12 room-map nametable rendering | 123 |
| `PRG_DIRECT_PPU_TRANSFER` | rendering-disabled direct PPU transfer guard | 47 |
| `PRG_ROOM_NAMETABLE_FRAME` | two-column/two-row room frame renderer | 152 |
| `PRG_PPU_DATA_WRITERS` | repeated four-byte pattern and single-byte writers | 21 |
| `PRG_REPEATED_PPU_PATTERNS` | four direct-PPU pattern records | 16 |
| `PRG_ROOM_ITEM_DECODE` | room metadata and compressed item-stream decoder | 395 |
| `PRG_ROOM_ITEM_DECODE_DATA` | constellation, timer, and special-room tables | 159 |
| `PRG_ROOM_BLOCK_DECODE` | 16x14 map initialization and 16x12 block expansion | 123 |
| `PRG_DANA_ACTIONS` | cooperative head collision, fireball, and block magic | 485 |
| `PRG_COUNTER_WAIT` | cooperative zero-page counter threshold wait | 14 |
| `PRG_MAP_INTERACTIONS` | RoomMap mutation and object interaction setup | 337 |
| `PRG_COORDINATE_OBJECT_OVERLAP` | active-object coordinate overlap predicate | 31 |
| `PRG_ROOM_MAP_CELL_UPDATE` | buffered two-row tile and attribute update producer | 272 |
| `PRG_ROOM_MAP_PPU_ADDRESS` | packed cell to nametable/attribute address helpers | 67 |
| `PRG_MAIN_THREAD_PADDING` | classified non-code filler before `$A000` | 221 |
| `PRG_MAIN_THREAD` | context-three gameplay loop | 76 |
| `PRG_DEMON_MIRROR_ACTIVATION` | delayed enemy-set decoding and type activation | 91 |
| `PRG_DEMON_MIRROR_SCHEDULE` | two MSB-first spawn schedule samplers | 105 |
| `PRG_DEMON_MIRROR_SPAWN` | two-placeholder enemy-slot allocation | 52 |
| `PRG_DEMON_MIRROR_INITIALIZATION` | mirror-coordinate object initialization | 27 |
| `PRG_TIMER` | countdown arithmetic and warning transitions | 199 |
| `PRG_TIMER_WARNING_DATA` | overlapping BCD thresholds and warning PPU streams | 18 |
| `PRG_TIMER_DISPLAY` | timer HUD update-program builder | 60 |
| `PRG_ENEMY_MOVEMENT` | active-enemy movement prepass | 104 |
| `PRG_ENEMY_AI_DISPATCH` | 17-slot enemy AI selector | 48 |
| `PRG_FIREBALL_INVENTORY_DISPLAY` | two-row packed fireball HUD producer | 143 |
| `PRG_FIREBALL_INVENTORY_DISPLAY_DATA` | fireball HUD tiles and reversed headers | 9 |
| `PRG_FIREBALL_LIFETIME` | fireball expiration and cleanup | 51 |
| `PRG_ENEMY_INITIALIZATION` | enemy slot coordinates and AI reset | 33 |
| `PRG_ENEMY_TYPE_CONFIGURATION` | spawn-type object/AI configuration | 86 |
| `PRG_ENEMY_TYPE_DATA` | packed enemy-type configuration flags | 27 |
| `PRG_ENEMY_AI_HANDLERS` | inline dispatcher and 28 handler pointers | 61 |
| `PRG_ENEMY_POSITION` | current-enemy position-copy helper | 13 |
| `PRG_EARLY_ENEMY_AI` | first two enemy AI families and collision rewards | 473 |
| `PRG_MID_ENEMY_AI` | four action-dispatched AI families and linked-slot allocation | 780 |
| `PRG_PATHFINDING_ENEMY_AI` | orientation actions and 16-way RoomMap path selection | 927 |
| `PRG_COLLISION_ENEMY_AI` | collision masks and linked behavior for two AI families | 549 |
| `PRG_LATE_ENEMY_AI` | final AI families and shared collision-direction helpers | 814 |
| `PRG_ENEMY_POINTERS` | indexed object/AI record pointer resolvers | 24 |
| `PRG_LINKED_ENEMY_AI` | `$50-$67` action dispatch and linked-slot support | 392 |
| `PRG_FIND_FREE_ENEMY_SLOT` | seventeen-entry free-slot allocator | 28 |
| `PRG_ENEMY_POINTER_TABLES` | split object/AI record pointer tables | 76 |
| `PRG_ENEMY_DEACTIVATION` | parallel-record enemy slot retirement | 36 |
| `PRG_CURRENT_ENEMY_DEACTIVATION` | selected enemy-record retirement | 14 |
| `PRG_ENEMY_LIFETIME` | room-configured enemy lifetime transition | 45 |
| `PRG_FILLER_BEFORE_SPECIAL_ROOMS` | classified non-code filler before `$B800` | 783 |
| `PRG_SPECIAL_ROOM_SCRIPTS` | context-6 room-index dispatcher and scripted triggers | 564 |
| `PRG_ENDING_SEQUENCE` | room-index 49 ending choreography and text presentation | 864 |
| `PRG_ENDING_SPECIAL_ROOM_SUPPORT` | ending messages, Seal reveal logic, special-room maps, and classified filler | 876 |
| `PRG_ENEMY_DROP_PROCESSING` | context-5 defeated-enemy conversion and drop tables | 227 |
| `PRG_RANDOM_STATE` | shared deterministic random-state mixer | 89 |
| `PRG_KEY_COLLECTION_PRESENTATION` | context-3 key removal, object pause, and gameplay resume | 106 |
| `PRG_KEY_DOOR_ANIMATION` | fixed-point collected-key flight and door reveal | 190 |
| `PRG_COORDINATE_DELTA` | two signed coordinate differences scaled by four | 34 |
| `PRG_ITEM_PRESENTATION` | four context-4 auxiliary item-effect lifecycles | 78 |
| `PRG_GAMEPLAY_HUD` | serialized score, inventory, and fairy HUD refresh | 42 |
| `PRG_GAMEPLAY_HUD_DATA` | collected-fairy PPU update template | 5 |
| `PRG_SCORE_DISPLAY` | leading-zero score display formatter | 43 |
| `PRG_ITEM_COLLISION` | Dana-centered map-tile classifier and item dispatch | 165 |
| `PRG_ITEM_HANDLER_TABLE` | 29 inline item-handler pointers | 58 |
| `PRG_RED_BOTTLE_ITEM` | eligible-enemy retirement sweep | 48 |
| `PRG_SPECIAL_ITEM_FLAGS` | item `$16-$1C` persistent flag handlers | 38 |
| `PRG_KEY_ITEM` | key collection and open-door map mutation | 36 |
| `PRG_DOOR_ITEM` | room advancement and room-clear transition | 135 |
| `PRG_GAMEPLAY_POOL_CLEAR` | complete object and enemy-AI pool reset | 26 |
| `PRG_TIMER_ITEM_EFFECTS` | timer multiplication and fixed-value item handlers | 112 |
| `PRG_INVENTORY_ITEM_EFFECTS` | inventory, fairy, lifetime, and score item handlers | 120 |
| `PRG_ITEM_SCORE_TABLES` | collectible score digit and amount lookups | 8 |
| `PRG_AUXILIARY_EFFECT` | shared auxiliary-object effect initializer | 35 |
| `PRG_SCORE_ADDITION` | gated unpacked-decimal score addition | 27 |
| `PRG_SECONDARY_THREAD_RESET` | stop other secondary contexts for transitions | 52 |
| `PRG_GAMEPLAY_EXIT_FLOW` | life-loss, `TIME OVER`, GDV, and exit-thread selection | 503 |
| `PRG_GAMEPLAY_EXIT_DATA` | mask cycle, `TIME OVER`, and result PPU data | 38 |
| `PRG_ROOM_TRANSITION_RESET` | shared transition context/flag/fireball reset | 22 |
| `PRG_NAMETABLE_CLEAR` | descriptor-driven tile and attribute clearing | 118 |
| `PRG_NAMETABLE_CLEAR_DATA` | three width/start/row-count descriptors | 9 |
| `PRG_SET_ACTIVE_OBJECT_STATES` | conditional non-Dana state sweep | 19 |
| `PRG_LOAD_OBJECT_POINTER` | non-Dana object pointer resolver | 11 |
| `PRG_DEACTIVATE_NON_DANA_OBJECTS` | whole non-Dana object teardown | 20 |
| `PRG_ATTRACT_DEMO_FLOW` | post-game screens, title wait, and demo input playback | 257 |
| `PRG_FULL_NAMETABLE_CLEAR` | blank both tile planes and initialize attributes | 55 |
| `PRG_TITLE_SCREEN` | packed title layers and current/best record display | 429 |
| `PRG_SET_PPU_ADDRESS` | reset the latch and write the A:X PPU address | 12 |
| `PRG_TITLE_PACKED_DATA` | record/background and logo packed streams | 402 |
| `PRG_DEMO_INPUT_DATA` | 34 duration bytes and 34 controller values | 68 |
| `PRG_FILLER_BEFORE_ROOM_TILE_PATTERNS` | classified filler before RoomMap tile patterns | 203 |
| `PRG_ROOM_TILE_PATTERNS` | 58 four-byte logical RoomMap tile patterns | 232 |
| `PRG_OBJECT_ANIMATION_DESCRIPTOR_POINTERS` | 33 object-type animation descriptor pointers | 66 |
| `PRG_OBJECT_ANIMATION_DEFINITIONS` | 340 action descriptors and four variant selectors | 1,392 |
| `PRG_OBJECT_ANIMATION_FRAMES` | 275 three-byte sprite frame records in 126 sequences | 825 |
| `PRG_OBJECT_MOTION_SELECTOR_POINTERS` | 33 object-type motion selector pointers | 66 |
| `PRG_OBJECT_MOTION_SELECTORS` | 20 shared action-selector groups | 388 |
| `PRG_OBJECT_MOTION_VALUES` | 35 paired Y/X motion vectors | 70 |
| `PRG_FILLER_BEFORE_DEMON_MIRROR_DATA` | classified pre-table filler | 33 |
| `PRG_DEMON_MIRROR_SCHEDULE_POINTERS` | 16 split schedule pointers | 32 |
| `PRG_DEMON_MIRROR_ENEMY_SET_POINTERS` | 17 split enemy-set pointers | 34 |
| `PRG_DEMON_MIRROR_SCHEDULE_DATA` | 16 eight-byte spawn schedules | 128 |
| `PRG_DEMON_MIRROR_ENEMY_SET_DATA` | 17 cyclic enemy-type streams | 42 |
| `PRG_ROOM_ENEMY_POINTERS` | 53 split room-enemy stream pointers | 106 |
| `PRG_ROOM_ENEMY_DATA` | 53 encoded-lifetime enemy streams | 726 |
| `PRG_ROOM_BLOCK_DATA` | 53 paired 24-byte block bitplanes | 2,544 |
| `PRG_ROOM_ITEM_POINTERS` | 53 split room-item stream pointers | 106 |
| `PRG_ROOM_ITEM_DATA` | 53 metadata and compressed item streams | 1,342 |
| `PRG_FILLER_BEFORE_AUDIO` | classified padding before the audio entry | 60 |
| `PRG_AUDIO_ENGINE` | virtual-channel sequencer and command handlers | 872 |
| `PRG_AUDIO_TIMING_TABLES` | 12 periods and 26 duration values | 50 |
| `PRG_AUDIO_ENVELOPES` | eight pointers and 105 duration/volume pairs | 226 |
| `PRG_SOUND_EFFECT_DATA` | 26 pointers and 75 channel assignments | 278 |
| `PRG_AUDIO_STREAMS` | complete reachable audio bytecode | 2,664 |
| `VECTORS` | NMI, Reset, and IRQ vectors | 6 |
| `PRG_BANK_1` | generated CHR payload (historical name) | 32,768 |

This unusual naming is documented in `config/linker/cnrom.cfg`. Renaming a
segment is possible, but gives no semantic benefit until the PRG and CHR data
are divided into stable modules.

Every source split must remain address-ordered and pass `make verify` after
each boundary is introduced. `config/reconstruction/reconstruction.json` records accepted
module ranges and non-regression thresholds; `make reconstruction-audit`
checks those declarations against the linker map and label file. Tables that
cross a round-number address should not be split merely to create visually
neat files.
