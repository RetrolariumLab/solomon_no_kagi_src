# Contributing

The first invariant is byte identity: the USA and European revisions must keep
building byte for byte. For each change:

```bash
make format
make test
```

Run `make test-full` (MAME) after changing control flow or anything
timing-sensitive. Data is edited in Retrolarium Studio
([`docs/retrolarium.md`](docs/retrolarium.md)).

Do not commit ROM images, extracted assets, build products, emulator states, or
screenshots containing private inputs.

## Source changes

Prefer a small semantic change followed immediately by `make verify`. When
introducing a name, record the evidence in the relevant document:

- confirmed: format, control flow, and runtime writes agree;
- high-confidence: several independent static observations agree;
- tentative: useful working hypothesis with explicit uncertainty;
- unknown: stable address-based name only.

Do not silently upgrade a tentative name to a fact. Write ROM addresses as
labels, never as numbers: a table or thread entry named by its address breaks
as soon as anything before it moves, and `make test-full` will show it.

Prefer subsystem-sized source files (roughly 300-700 lines) over one file per
small address range.

## Commit messages

Write the subject and body in English. Use a concrete result-oriented subject
without a trailing period. Follow it with two or three paragraphs that
describe the change, the affected boundary, and the checks that passed. Keep
one task per commit.

`make hooks` installs Git hooks that check commits and pushes for words that
must not be published and run `make lint` before each commit.
