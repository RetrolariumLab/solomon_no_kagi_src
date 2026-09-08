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
only to project-owned evidence.

The full commit interval starts immediately after the annotated 2.0 tag. While
the manifest status is `development`, its terminal commit remains unset. It is
pinned after each accepted vertical slice and must cover every substantive
commit before the status can become `tag-ready`.

## Repository layout

Python tools and tests now occupy mirrored `authoring`, `build`, `runtime`, and
`validation` packages. Public Make targets dispatch them through the stable
`scripts/run.py` entry point, and `make lint` rejects new uncategorized Python
tools. Historical 1.0 and 2.0 manifests remain byte-for-byte unchanged;
current validators resolve their former script paths through an explicit
compatibility map.

Configuration manifests still share one directory. The release manifest keeps
this as an audited deviation because the files already have explicit owners,
validators, and release-contract references; moving them would add path churn
without strengthening the Source 2.1 preservation claim. The published 2.0
tag and its recorded tree remain immutable throughout this work.

## Gates

Use the fast contract audit while developing:

```console
make source-2-minor-audit
```

The complete compatible-minor gate first executes the accepted 2.0 regression
gate, including the transitive Source 1.0 checks, and only then validates the
2.1 delta:

```console
make source-2-minor-check
```

`source-2-minor-pre-tag-check` and `source-2-minor-tag-check` are intentionally
reserved for the clean `tag-ready` candidate and its annotated published tag.
The Japanese profile, systematic relocation, expanded ROMs, and sibling
engines remain outside this compatible release.
