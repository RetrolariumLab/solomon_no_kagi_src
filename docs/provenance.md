# Provenance

## Preservation listing

- Repository: <https://github.com/rbmichael/solomons_key_disassembly>
- Imported file: `solomonskey.asm`
- Attribution in file: `ninespaces`
- Upstream state: two commits, no explicit license observed at import time
- Role here: byte-identical address-ordered baseline

The imported comments record PRG CRC32 `0771c34f`, CHR CRC32 `fad8a464`, and
headerless combined CRC32 `40684e95`. This project's independent build produces
the known headered SHA-1 `18102689fd35c7d531a5e6241b06b748accab2f6`.

## RAM and code map

- Bisqwit map: <https://bisqwit.iki.fi/jutut/solokey.map>
- TASVideos discussion: <https://tasvideos.org/Forum/Posts/User/Bisqwit?CurrentPage=38&PageSize=25&Sort=CreateTimestamp>
- Role here: scheduler, object-pool, RAM, and initial routine hypotheses

## Room formats

- Repository: <https://github.com/kaimitai/skchain>
- ROM map: `docs/solomon's_key_rom_map.md` in that repository
- Role here: room pointers, block planes, enemy/item streams, metadata, and
  multi-region offsets; its element catalog supplies visual vocabulary which
  this reconstruction cross-checks against its own consumers and handler data

## Additional upstream links

- RHDN document 902 archive entry: <https://www.romhacking.net/documents/902/>
- Shared research spreadsheet: <https://docs.google.com/spreadsheets/d/1EKLm0fHJ-rp5udljMHu-O83MaiY2XTmdcYA7ya-KYNQ/edit?usp=sharing>
- Cartridge record: <https://nescartdb.com/profile/view/900/solomons-key>

On 2026-09-07 the user supplied a CSV export of the spreadsheet's 53-room
block table (`Solomon's Key (NES) - levelBlocks.csv`, SHA-256
`4380f0888fbbf23d65bb45e4de32e4dc9409789845a838d8f40c8489fb69271b`).
An independent comparison against the USA level document matched all 10,176
cells. The ten value-3 cells set both brown and white planes, corroborating
the loader precedence and `skchain`'s `Brown_white` representation. The CSV is
external research input and is not tracked in this repository.

Local clones used during research live beneath ignored `references/` and are
not part of the project history.

## Semantic rename ledger

`docs/provenance/label_renames.json` records every accepted ROM-label rename
with its linked address, previous identifier, confidence, and concise evidence.
`make reconstruction-audit` rejects duplicate entries, missing evidence,
missing source labels, and any disagreement with the ld65 label file.

## Source Reconstruction 1.0 confidence review

The release ledger contains 1,836 renamed labels: 1,733 `confirmed`, 102
`high`, one `tentative`, and no `unknown` entries. Two accepted original labels
complete the 1,838 semantic source-label inventory without rename records.
`make release-audit` freezes this distribution alongside the complete label
count, so confidence cannot be silently promoted or discarded.

The 1.0 review examined every `high` and `tentative` entry. The `high` group
retains names supported by converging static evidence without claiming runtime
proof. The sole tentative entry, `PreTimerWarningTableBytes`, deliberately says
only where the three bytes lie; their resemblance to a timer PPU command is
recorded as a hypothesis because no direct consumer has been proved.

Large confirmed groups such as room streams, animation-frame boundaries, and
audio bytecode entries assert exact structural identities established by their
reviewed pointers and lossless codecs. They do not claim that every record is
observed during the runtime scenarios. Behavioral names are confirmed only
where exhaustive local code or a focused trace directly establishes the stated
effect, consistent with `docs/naming.md`.
