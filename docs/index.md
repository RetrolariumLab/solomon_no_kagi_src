# Documentation index

Use this page as the reader-facing entry point. The guides are organized by
task and subsystem rather than by individual routines. The machine-readable
[documentation corpus](../config/reconstruction/documentation_corpus.json) and
[corpus review](documentation_review.md) record ownership, consolidation, and
the few intentionally retained filename families.

## Build and verify a release

Start with the [README](../README.md), then use the
[verification contract](verification.md) for the complete command sequence.
The [toolchain contract](toolchain.md), [runtime evidence](runtime_evidence.md),
and [debugger workflow](debugger_workflow.md) explain the pinned tools and the
evidence produced by those commands.

Release boundaries are recorded separately for
[Source Reconstruction 1.0](source_reconstruction_1_0.md),
[2.0](source_reconstruction_2_0.md), and the
[2.1 candidate](source_reconstruction_2_1.md). The
[revision profiles](revision_profiles.md) describe the USA, Europe, and Japan
inputs and capabilities. [Code quality](code_quality.md) and the
[roadmap](roadmap.md) distinguish accepted behavior from later work.

## Understand the source

Read [architecture](architecture.md) for execution and data flow, then use
[source layout](source_layout.md) and [source organization](source_organization.md)
to locate the owning module. [RAM map](ram_map.md) defines runtime storage and
[data formats](data_formats.md) defines encoded records and authoring tools.

The runtime is documented by subsystem:

- [Startup](startup.md), [NMI runtime](nmi_runtime.md),
  [cooperative scheduling](scheduler.md), and the machine-oriented
  [scheduler entry table](scheduler_entries.md).
- [Gameplay runtime](gameplay_runtime.md), [player actions](player_actions.md),
  [objects](object_system.md), [enemies](enemy_system.md), and
  [items, timer, and score](item_system.md).
- [Room lifecycle](room_lifecycle.md), [room data pipeline](room_data_pipeline.md),
  [map interactions](map_interactions.md), [special-room scripts](special_room_scripts.md),
  [Demon Mirror runtime](demon_mirror_runtime.md), and the
  [ending system](ending_system.md).
- [PPU update pipeline](ppu_pipeline.md), [title screen](title_screen.md),
  [CHR-bank policy](chr_bank_policy.md), and [audio engine](audio_engine.md).
- [Attract and demo flow](attract_demo_flow.md) for the non-gameplay presentation
  path.

## Evaluate evidence and project boundaries

[Naming and evidence policy](naming.md), [provenance](provenance.md), and the
canonical [label rename registry](../config/reconstruction/label_renames.json)
separate confirmed names from hypotheses and imported knowledge.
[Unknowns](unknowns.md) records unresolved questions. [Licensing](licensing.md)
separates project tooling and documentation from reconstructed source and
private user-supplied inputs.
