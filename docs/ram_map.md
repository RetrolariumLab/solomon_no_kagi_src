# RAM map

This is the initial evidence registry, not a claim that every byte in each
range is understood.

| Address / range | Working meaning | Confidence |
| --- | --- | --- |
| `$0000-$000F` | temporary pointers and scratch values | high |
| `$0004-$0007` | spawn Y, X, slot index, and type calling convention | high |
| `$0004-$0005` | room-map conversion Y/index and X calling convention | confirmed |
| `$0000-$0006` | map-interaction object pointer, direction/update bytes, Y/X, and overlap pointer | high |
| `$0012-$0019` | saved SP values for eight cooperative contexts | high |
| `$001A-$001B` | NMI-consumed PPU update-stream pointer | confirmed |
| `$001C` | requested attribute address low byte, replaced by the NMI-read value | confirmed |
| `$0020-$0027` | independently incremented active-gameplay frame counters | confirmed |
| `$0021` | standard gameplay delay counter | confirmed |
| `$0022` | NMI-incremented frame counter used by pause debounce | confirmed |
| `$0023` | shared pending gameplay/timer update count | high |
| `$0024` | NMI-incremented frame counter selected by context-4 item presentations | confirmed |
| `$0028` | gameplay flags; bit 2 requests an NMI RoomMap attribute read | high |
| `$0029` | attribute-read state: `$00` idle, `$80+` complete/timeout age | confirmed |
| `$002C-$002D` | current room enemy stream pointer during room loading | confirmed |
| `$0030-$0031` | current room item/header stream pointer | confirmed |
| `$0036-$0039` | two resolved Demon Mirror schedule pointers | confirmed |
| `$003A-$003D` | two resolved Demon Mirror enemy-set pointers | confirmed |
| `$0040-$0053` | 20 non-Dana object Y sort keys used by the NMI OAM composer | confirmed |
| `$0054-$0067` | parallel sorted object order and overlap-group markers | confirmed |
| `$0068-$0077` | per-row object allowances used for scanline sprite selection | high |
| `$007C-$007D` | room-state flags and one-shot CHR-bank request | confirmed |
| `$007E` | most recent block-cast target map index | high |
| `$007F` | most recent head-collision target map index | high |
| `$0078` | global game-state flags; pause thread modifies bits 1-2 | high |
| `$0079` | collected Solomon Seal count | confirmed |
| `$007A` | bitset of Solomon Seals already collected | confirmed |
| `$007B` | Solomon Seal flag assigned to the current scripted room | confirmed |
| `$0082-$0083` | raw controller values in A/B/Select/Start/Up/Down/Left/Right bit order | confirmed |
| `$0087` | mixed state flags; bit 0 gates item effects and brackets auxiliary map cleanup | high |
| `$0210-$030F` | OAM shadow buffer, 64 four-byte sprites | high |
| `$0302` | current scheduler context index | high |
| `$0304-$03E3` | 16x14 room map: 16x12 interior plus two sentinel rows; `$0304-$030B` temporarily hold key-flight motion and return to `$F8` | confirmed |
| `$0406-$041E` | constellation position and expanded 24-byte pattern | confirmed |
| `$041F-$0422` | four pending scheduler start requests, drained by startup | confirmed |
| `$03E4-$03E5` | cached controller state with game-state-dependent filtering | confirmed |
| `$03E6-$03F9` | shared RAM PPU update-program buffer extent used by room palette loading | confirmed |
| `$0423-$0425` | three sound-effect request slots | confirmed |
| `$0426-$0427` | split enemy spawn-lifetime threshold | high |
| `$0428` | zero-based current room index | confirmed |
| `$0429` (USA), `$042A` (Europe) onward | fireball, inventory, and lifetime state; the first byte temporarily saves the prior room index during special-room loading | mixed/high |
| `$0429` (Europe only) | preserved starting-room index consumed by the PAL new-game reset | high |
| `$008B-$008F` (Europe only) | five PAL startup values copied to global game-state bytes `$0078-$007C` | high |
| `$042B` | number of usable two-bit fireball inventory slots, maximum 8 | confirmed |
| `$042E-$042F` | eight packed two-bit fireball inventory slots | confirmed |
| `$0430` | four-way fireball direction index: right, left, up, down | confirmed |
| `$0431` | fireball alternate path direction: initially up or down | confirmed |
| `$0434-$043B` | timer warning state, step, fraction, and decimal digits | high |
| `$043C-$043D` | NMI-incremented Demon Mirror spawn timer | confirmed |
| `$043E` | Demon Mirror phase/loop state and two pending bits | confirmed |
| `$043F-$0440` | independent Demon Mirror enemy-set stream offsets | confirmed |
| `$0441-$0444` | two Demon Mirror Y/X coordinate pairs | confirmed |
| `$0445-$0446` | allocated enemy slots for the two Demon Mirrors | confirmed |
| `$0447` | active enemy count produced by the movement prepass | high |
| `$0448-$0449` | deterministic random state used by room placement, enemy AI, and item drops | confirmed |
| `$044A-$0451` | eight unpacked decimal score digits, most significant first | confirmed |
| `$0452` | remaining lives | high |
| `$0453-$0454` | collected and queued fairies | high |
| `$0456-$04D5` (USA), `$0457-$04D6` (Europe) | eight 16-byte virtual audio-channel records | confirmed |
| `$04D6-$04F5` (USA), `$04D7-$04F6` (Europe) | eight interleaved duration/reload/envelope/volume records | confirmed |
| `$04F6` (USA), `$04F7` (Europe) | rotating active virtual-channel bitset | confirmed |
| `$05BE` | total extra lives acquired; overlaps auxiliary-object byte 3 | high |
| `$04F7-$057E` (USA), `$04F8-$057F` (Europe) | 17 eight-byte enemy AI records; complete shared layout documented | confirmed |
| `$057F-$070F` (USA), `$0580-$0710` (Europe) | 21 `$14`-byte gameplay object records; complete shared layout documented | confirmed |

The last object base is `$070F`; a full `$14`-byte record therefore reaches
`$0722`. Exact ownership above that boundary still needs write-watch evidence.

Important object fields observed on Dana include integer Y at `$0586`, integer
X at `$0589`, and adjacent fractional/movement fields. Equivalent offsets are
expected across the object pool, but each field should be proven before global
renaming.

Dana's byte 3 at `$0582` is the action-state selector. Bit 0 is right/left
facing; paired states cover jump startup, surface contact, crouching, walking,
airborne movement, casting, and death presentation. The full encoding and its
source evidence are in `docs/player_actions.md#dana-action-state-encoding`.

Across shared object helpers, byte 5 is signed Y motion, byte 6 is the Y
fraction, and byte 7 is integer Y. The surface clamp aligns byte 7 to 16 pixels
and preserves only byte 5's sign bit. Bytes 8-10 are the corresponding X
motion, fraction, and integer coordinate. The two horizontal clamps clear
bytes 8-9 and align integer X to low nibble `$4` or `$C`.
On a type/action transition, bytes 12-16 receive the animation counter, reload
delay, packed phase, and little-endian animation-data pointer.
The per-frame sampler stores six RoomMap solidity tests in collision-mask byte
11. Bits 0-5 are upper-left, upper-right, lower-right, lower-left, below-left,
and below-right. The animation sequencer writes its selected three-byte sprite
frame to bytes 17-19. The complete record is tabulated in
`docs/object_system.md#gameplay-object-record-layout`.
For records in state `$E0+`, collision byte 11's low nibble indexes the
response table at `$8806`; upper bits also participate in the mask-0/F handler.
The shared auxiliary record at `$05BB` uses the same confirmed integer Y/X
offsets. `SpawnAuxiliaryEffectAtCoordinates` writes them from zero-page
`$04/$05` before replacing object bytes 0 through 3 from a fixed template.

During `RoomClearThread`, `$04FB-$0503` receives a nine-byte overlapping
template spanning the tail of AI record 0 and the head of AI record 1. The
first four AI bytes are then seeded from converted room coordinates through
the selector table at `$933C`. Exact per-byte AI meanings remain pending.

`ResetNewGameState` clears `$0079-$007C`, all eight score digits
`$044A-$0451`, and seeds `$0078`, `$0080`, and `$0433` with one. The room-clear
presentation writes `$01` or `$05` to `$0080`; its exact long-term ownership
still requires tracing.

Room-entry and room-clear presentations temporarily use `$04F7-$050F` as 25
bytes of orbit state. Bytes `$04FB-$04FE` become two little-endian center
accumulators, `$04FF-$0502` hold a radius accumulator and delta, and `$0503`
holds the six-bit phase. The same memory returns to enemy-AI ownership after
the transition clears it.
