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
scaffold gate, and a self-contained release manifest whose claims resolve only
to project-owned evidence.

The full commit interval starts immediately after the annotated 2.0 tag. While
the manifest status is `development`, its terminal commit remains unset. It is
pinned after each accepted vertical slice and must cover every substantive
commit before the status can become `tag-ready`.

## Remaining repository work

Two temporary layout deviations remain explicit:

- Python tools and tests still occupy flat roots rather than mirrored
  responsibility packages;
- configuration manifests still share one directory rather than owner-based
  `authoring`, `debugger`, and `reconstruction` groups.

They will be migrated as complete vertical slices, updating imports,
`Path(__file__)` roots, Make commands, subprocess paths, manifests, tests, and
documentation together. The published 2.0 tag and its recorded tree remain
immutable throughout this work.

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
