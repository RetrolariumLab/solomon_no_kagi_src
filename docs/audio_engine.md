# Audio engine

`src/system/audio_engine.asm` owns CPU `$F000-$F367`. `UpdateAudio` is called
from NMI after input sampling whenever the game-state audio-disable bit is
clear. It first consumes the three pending sound-effect mailboxes, then updates
and publishes channel state.

## Virtual channels

The driver maintains eight 16-byte channel records at `$0456-$04D5`. Four
interleaved bytes per virtual channel follow at `$04D6-$04F5`: note-duration
counter, duration reload, envelope counter, and envelope volume. `$04F6` is an
eight-bit active mask. The update pass rotates that mask once per record, so
the current channel is presented in carry and later in bit 7.

The publishing pass treats the virtual records as four fixed pairs:

| APU voice | Primary virtual channel | Secondary virtual channel |
| --- | ---: | ---: |
| pulse 1 | 0 | 1 |
| pulse 2 | 2 | 3 |
| triangle | 4 | 5 |
| noise | 6 | 7 |

`AudioPrimaryVirtualChannelBits` (`$55`) selects the even-numbered member. If
that bit is active it wins; otherwise the publisher advances to the odd
secondary record. It writes volume, sweep, and a dirty period to the matching
APU register group, then enables the four ordinary voices through `$4015`.

The `audio-channel-priority` runtime scenario proves both levels of priority.
At frame 721 mailbox slot 2 starts block-create command `$07` on virtual 4,
then slot 0 starts fireball-cast command `$0A` on the same record. The later
slot-0 command leaves stream `$FB72` installed, proving that the descending
mailbox scan gives lower slots precedence when commands overlap. Virtual 4
then owns triangle until frame 737, when background virtual 5 resumes.

At frame 761 block-remove command `$08` activates virtual 6. Noise switches
from background virtual 7 to primary 6 with active mask `$CA`, then returns to
7 at frame 780 with the original `$8A` mask. No music descriptor is restarted:
the secondary streams continue advancing while hidden and become audible
again as soon as the corresponding primary stops.

## Stream interpreter

Ordinary bytes encode notes. Virtual channels 0-5, which feed both pulse
voices and triangle, split each note into a low-nibble index in the twelve-word
period table and a high-nibble octave shift. Only virtual channels 6-7, which
feed noise, treat an ordinary byte as a direct noise-register value. Keeping
that boundary at six is essential for auditioning: treating pulse 2 or
triangle notes as raw timers turns normal music into ultrasonic beeps.

`$80-$EF` select a duration through the table at
`$F380`; `$F0-$F9` dispatch through the ten-entry handler table at `$F246`:

| Opcode | Observed operation |
| --- | --- |
| `$F0` | select a two-byte sequence pointer through `$F39A` |
| `$F1` | replace the low control nibble |
| `$F2` | jump to an absolute stream pointer |
| `$F3` | call an absolute stream pointer and push a return pointer |
| `$F4` | restore a saved return pointer |
| `$F5` | push a counted-loop frame |
| `$F6` | decrement/repeat or pop a counted-loop frame |
| `$F7` | write one hardware sweep register |
| `$F8` | preserve the low six control bits and merge one control byte |
| `$F9` | clear the current active bit and leave stream decoding |

The per-channel record provides a compact stack beginning at offset 9 for
calls and loops. Note bytes index the twelve-entry period table at `$F368` and
use their upper nibble as a right-shift count. The high bit in record offset 8
marks a period awaiting publication.

## Effect call-site catalog

Sound Studio labels an effect by proven request contexts rather than guessing
a soundtrack title from its notes. These names come from every static
`AddSoundEffect` caller; a slash means that the same descriptor is deliberately
reused by more than one flow.

| Request | Call-site context |
| ---: | --- |
| 1 | Room audio A / warning return A |
| 2 | Room audio B / warning return B |
| 3 | Room transition reset |
| 4 | Timer warning |
| 5 | Post-game result |
| 6 | Extra life |
| 7 | Create breakable block |
| 8 | Remove breakable block |
| 9 | Enemy drop |
| 10 | Fireball cast |
| 11 | Paired-enemy attack |
| 12 | Pause / PAL resume |
| 13 | Item pickup / enemy reward |
| 14 | NTSC resume |
| 15 | Fairy collected |
| 16 | Ending input prompt |
| 17 | Dana head collision |
| 18 | Remove solid block |
| 19 | Room-clear countdown / ending phase |
| 20 | Room entry / ending convergence |
| 21 | Enter door |
| 22 | Collect key |
| 23 | Linked-enemy spawn |
| 24 | Title / new game / room-clear transition |
| 25 | Ending object fall |
| 26 | Ending fade |

The regional resume split is source-visible: `ResumeSoundEffect` is 14 for
NTSC and 12 for PAL. The neutral `Room audio A/B` wording is intentional;
those descriptors are selected both when a room begins and when timer-warning
audio is left, which proves their role but not a historical composition name.

## Audio data

The engine's period, duration, envelope, sound-effect, and music streams are
source-owned at `$F368-$FFF9` in `src/data/audio.asm`. Periods and all pointer
operands use symbolic words; `$F2/$F3` bytecode targets reference 114 named
stream entries. The adjacent CPU vectors are symbolic through `$FFFF`.

`make audio-data-audit` independently checks 12 periods, 26 duration values,
eight envelope pointers, 26 overlapping effect descriptors, and every stream
entry reachable through descriptor and `$F2/$F3` command pointers. All 2,664
bytes at `$F592-$FFF9` must be reachable and every decoded path must re-encode
byte-for-byte.

`python scripts/audio_data.py source --image <rom>` reproduces the reviewed
ASM representation from a matching image.

Source Reconstruction 2.0 gives the codec explicit USA and Europe layouts.
The PAL layout starts at `$EF80`, uses its duration table at `$F300`, places
the envelope pointer table at `$F342`, and covers 2,725 reachable stream bytes
at `$F53A-$FFDE`. `make audio-profile-audits` verifies both private reference
identities before decoding 26 effects and 114 reachable stream entries per
profile. The PAL audit records 2,255 commands and proves that its complete
stream range round-trips byte-for-byte; this structural evidence is the base
for the 2.0 music editor and for profile-selected stream source.

The PAL gap from `$F300` to `$F341` is not merely a 26-byte primary duration
table plus opaque padding. Stream tokens mask their duration index to six bits,
and PAL stock streams use indices through 52. Sound Studio therefore exposes
the first 64 bytes as the complete addressable PAL duration table and retains
only the final two bytes as timing tail. NTSC stock streams use indices through
24 and its envelope pointer table begins immediately after the 26 declared
duration bytes.
