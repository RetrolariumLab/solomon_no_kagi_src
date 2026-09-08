# Source Reconstruction 2.1 candidate

Source Reconstruction 2.1 is the compatible follow-up to the published 2.0
tag. It does not redefine the USA/European preservation profiles, their ROM
identities, runtime modes, authoring schemas, or fixed-layout capacity rules.
Those contracts remain anchored by `source-reconstruction-2.0`; the 2.1
manifest hashes every inherited section and rejects silent baseline drift.

## Accepted delta

The current development history adds audible and channel-selectable Sound
Studio playback, more faithful native level previews, decoded procedural bonus
rooms, and a consolidated semantic assembly layout. Repository preparation adds
responsibility-owned Make fragments, categorized command help, a ROM-less
scaffold gate, mirrored tool/test responsibility packages behind
`scripts/run.py`, and a self-contained release manifest whose claims resolve
only to project-owned evidence. A separate workstation smoke now drives Save,
Build, Preview
or Play, and dirty-close behavior through all four public studios for both
accepted profiles.

The full commit interval starts immediately after the annotated 2.0 tag. During
development its terminal commit is advanced after each accepted vertical slice
and must cover every substantive commit before the status can become
`tag-ready`.

The compatible manifest is self-describing even though its preservation facts
remain inherited. It repeats the effective profile inventory, direct runtime
matrix, toolchain reference, artifact identities, and licensing declarations
from the immutable 2.0 manifest. Every requirement uses structured
`targets`, `files`, `scenarios`, and `artifacts` evidence; the minor aggregate
remains `partial` only until the final clean pre-tag run is recorded.

## Repository layout

Python tools and tests now occupy mirrored `authoring`, `build`, `runtime`, and
`validation` packages. Public Make targets dispatch them through the stable
`scripts/run.py` entry point, and `make lint` rejects new uncategorized Python
tools. Historical 1.0 and 2.0 manifests remain byte-for-byte unchanged;
current validators resolve their former script paths through an explicit
compatibility map.

Configuration follows the same ownership model: authoring, debugger,
reconstruction, and validation manifests live in named subdirectories, while
shared revision, toolchain, and release contracts stay at `config/` root.
`make lint` rejects a new uncategorized JSON file. The published 2.0 tag and
its recorded manifest remain immutable; current validators resolve its former
paths through the same compatibility map used for moved tools.

## Gates

Use the fast contract audit while developing:

```console
make source-2-minor-audit
```

The complete compatible-minor gate first executes the accepted 2.0 regression
gate, including the transitive Source 1.0 checks, and only then validates the
2.1 delta. It also runs `make lint` as a real public command inside a disposable
tracked-only clone, proving that the documented interface does not depend on
untracked local files or mutate a clean checkout. Before that command smoke,
the gate also exercises the editor workstation actions for USA and Europe:

```console
make source-2-minor-check
```

The editor interaction check is also available directly as
`make editor-ui-smoke-profiles`; select one revision with
`make editor-ui-smoke-profile PROFILE=usa|europe`.

`source-2-minor-pre-tag-check` and `source-2-minor-tag-check` are intentionally
reserved for the clean `tag-ready` candidate and its annotated published tag.
The Japanese profile, systematic relocation, expanded ROMs, and sibling
engines remain outside this compatible release.
