# Naming and evidence policy

The imported source contains generated labels and raw addresses. Renaming is a
semantic change to the research record even when it does not change bytes.

Use four confidence classes:

- **confirmed**: the exact claim made by the name is established directly and
  unambiguously by evidence appropriate to that claim. A pointer plus lossless
  codec can confirm a record boundary; exhaustive control flow can confirm a
  local transformation; timing, arbitration, and lifecycle claims require a
  repeatable runtime observation;
- **high**: multiple static observations support the interpretation and no
  conflict is known, but the role remains indirect or a plausible alternative
  has not been eliminated;
- **tentative**: the name is a useful hypothesis but alternatives remain;
- **unknown**: retain an address-based name.

Confidence applies to the wording of one symbol, not to every possible claim
about the surrounding subsystem. Runtime evidence is neither required for a
purely structural fact nor implied by confirming one. Conversely, byte identity
and readable control flow alone do not confirm dynamic cadence, priority, or
state lifetime.

Prefer verbs for routines (`DecodeRoomItems`), nouns for storage
(`CurrentRoomIndex`), and explicit suffixes for representations
(`TimerDigit1000`, `PlayerXFraction`). Do not encode an uncertain interpretation
as a confident name. Preserve the old address in the rename ledger when source
labels begin to move.
