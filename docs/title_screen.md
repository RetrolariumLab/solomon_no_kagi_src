# Title-screen renderer

`src/graphics/title_screen.asm` owns CPU `$CBA6-$CD52`. It contains a packed
direct-PPU renderer, two callers that compose the title/record screen, and the
small fixed tile and buffered-update templates consumed by those callers.

## Packed stream format

`RenderPackedTitleData` receives a 16-bit source pointer in `TempPointer00`.
It maintains a logical column in `$02` and row in `$03` and interprets each
nonnegative byte as a cursor command:

| Value | Meaning |
| ---: | --- |
| `$00-$3F` | replace the logical column |
| `$40-$5F` | replace the logical row |
| `$60-$7E` | add `(value & $1F) + 1` to the row |
| `$7F` | terminate and return |
| `$80-$FF` | literal tile byte written to `PPU_DATA` |

The extra one in the relative-row command comes from the carry left set by
`CPX #$60`; the decoder deliberately does not clear it before `ADC`. Literal
runs are followed by a positive command. At that boundary the routine advances
the base source pointer by Y, resets Y, and interprets the command without
losing it.

`SetPackedTitlePpuAddress` converts the logical row and column into the two PPU
address bytes. Its shifts, masks, and rotates carry the row's nametable bits
into the high bits of the low address byte, allowing one stream to address the
mirrored title layout.

## Record/background layer

`DrawTitleRecordLayer` renders `TitleRecordPackedData` at USA `$CD5F` /
Europe `$CCEF`, writes a
21-byte fixed tail in reverse order, then queues static PPU streams `$09-$0B`.
It reuses `BuildScoreDisplayUpdate` three times with local headers to publish:

- the current seven-digit score;
- the seven-digit warm-RAM best score;
- the two-digit warm-RAM best GDV.

Leading zeroes in the best score become blank tile `$24`, matching the normal
HUD formatter. The best GDV passes through `FormatTwoDigitNumberTiles`.
Each buffered update waits for `PpuUpdateStreamPointer` to become idle before
reusing the shared buffer.

## Logo layer

`DrawTitleLogoLayer` waits for vblank, queues static stream `$05`, and renders
`TitleLogoPackedData` at USA `$CDFA` / Europe `$CD8A`. It then writes three
fixed direct-PPU patterns: 16 alternating `$DF/$DE` pairs, eight `$F5` tiles,
one `$CF` accent, and a seven-byte attribute sequence.

Both packed streams are source-owned in `PRG_TITLE_PACKED_DATA`. The first is
155 bytes and ends at `$CDF9`; the second is 247 bytes and ends at `$CEF0`.
Each includes its `$7F` terminator, and assembly assertions preserve their
exact adjacency and sizes.

`make title-data-audit` independently decodes the two streams into semantic
cursor commands and literal runs, reproduces the carry-dependent PPU address
calculation, and re-encodes all 402 bytes. The reviewed manifest records 25
commands, 17 literal runs, 377 literal tiles, exact boundaries, and SHA-1
fingerprints in `config/authoring/title_data.json`. `make title-data-report` exposes the
decoded commands, target PPU addresses, and tiles as JSON.

The same adjacent-data audit includes the attract demo's 34 duration and
controller bytes at `$CEF1-$CF34`. Controller masks are decoded to named NES
buttons before re-encoding; see `docs/attract_demo_flow.md` for playback
semantics.

The European layout moves both packed streams and the demo tables `$70` bytes
earlier: title data occupies `$CCEF-$CE80` and demo input occupies
`$CE81-$CEC4`. Their hashes and decoded records are identical to USA. The
separate `config/authoring/title_data_europe.json` manifest makes that conclusion an
independent ROM-backed contract. `make title-data-profile-audits` round-trips
all 470 bytes from both source-built images.
