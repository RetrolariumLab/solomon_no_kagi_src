# Documentation index

Use this page as the reader-facing entry point. The guides are organized by
task and subsystem rather than by individual routines.

## Build and verify

Start with the [README](../README.md). The [revision profiles](revision_profiles.md)
describe the USA, Europe, and Japan inputs and how each revision is built and
checked.

## Understand the source

Read [architecture](architecture.md) for execution and data flow, then use
[source layout](source_layout.md) and [source organization](source_organization.md)
to locate the owning module. [RAM map](ram_map.md) defines runtime storage and
[data formats](data_formats.md) defines encoded records.
[Editing in Retrolarium](retrolarium.md) explains how the game is edited.

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
  [CHR-bank policy](chr_bank_policy.md), [audio engine](audio_engine.md), and
  the [sound-effect queue](sound_effect_queue.md).
- [Attract and demo flow](attract_demo_flow.md) for the non-gameplay presentation
  path.

## Evidence and boundaries

[Naming and evidence policy](naming.md) and [provenance](provenance.md)
separate confirmed names from hypotheses and imported knowledge.
[Unknowns](unknowns.md) records unresolved questions. [Licensing](licensing.md)
separates project tooling and documentation from reconstructed source and
private user-supplied inputs.

The reference pages describe findings made during Source Reconstruction 1.0
to 3.0; the validation targets and machine-readable contracts they cite remain
at those tags.
