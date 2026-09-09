# Documentation corpus review

This review treats the documentation as one reader-facing system. It records
the navigation paths, consolidation decisions, retained boundaries, and size
exceptions represented by
`config/reconstruction/documentation_corpus.json`. `make lint` checks that the
machine-readable inventory still matches every Markdown file under `docs/`.

## Reader journeys

The README leads a release user through legal inputs and the complete release
gate. `docs/index.md` then offers three deliberate paths: build and verification,
source architecture and subsystem behavior, and provenance or licensing. Each
path begins with an overview and links to specialized evidence only when the
reader needs it.

An implementer can move from architecture to source layout, RAM ownership, data
formats, and then one subsystem guide. A reviewer can move from a release
boundary to verification, runtime evidence, toolchain provenance, naming, and
unknowns without traversing an alphabetical list of routine notes.

## Consolidated subsystem material

Short routine-level files for enemies, objects, PPU updates, NMI services,
player actions, items, gameplay flow, endings, and rooms were merged into
subsystem or lifecycle guides. Their original headings remain sections so links
can target the same subject precisely. Room documentation remains in two guides:
one owns state transitions while the other owns encoded data and rendering.

This consolidation removes the flat filename clusters that obscured subsystem
ownership. It also keeps detailed static evidence near the surrounding behavior
instead of requiring readers to reconstruct a subsystem from many independent
notes. The exact source-to-destination mapping is retained in the corpus record.

## Intentionally separate documents

The `source_*` documents have separate audiences and lifecycles: source layout
maps bytes, source organization defines repository policy, and each release
document freezes a distinct accepted boundary. Combining them would mix stable
release evidence with evolving navigation policy.

The two `room_*` guides are also deliberate. Room lifecycle owns transitions and
thread state; room data pipeline owns codecs, tables, map updates, and rendering.
They cross-reference one another but do not share a data owner. Scheduler entries
remain separate from the scheduler overview because the entry table is
machine-checked evidence while the overview explains runtime behavior.

## Size and maintenance review

The revision profile guide exceeds the normal document-size target because it
is a contiguous, comparison-oriented record of three regional profiles. Its
table and address evidence are easier to review together than as independently
maintained regional copies. All other ordinary documents remain within the
reviewed limit.

Lint checks the complete Markdown inventory, line counts, local links, repeated
filename prefixes, consolidation destinations, removed source files, and the
single canonical label rename registry. A new document or a new repeated prefix
therefore requires an explicit review decision rather than silently expanding
the corpus.
