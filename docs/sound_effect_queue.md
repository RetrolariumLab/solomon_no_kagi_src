# Sound-effect request queue

`src/system/thread_runtime.asm` owns CPU `$8E8D-$8E9F`. Bisqwit's map
names its entry `AddSoundEffect`; all 34 static callers now use that symbol.

Calling convention:

```text
input:      Y = sound-effect command
preserved:  A, X
output:     Y = selected queue index
clobbered:  one byte of SoundEffectQueue
```

`SoundEffectQueue` is the three-byte range `$0423-$0425`. The routine searches
for an empty byte from index 2 downward. Slot 0 is a fallback rather than a
tested free slot: if slots 2 and 1 are occupied, the new request overwrites
slot 0. Consequently this is not a FIFO; it is a small set of pending command
mailboxes.

`UpdateAudio` at `$F000` scans slots 2 through 0 once per NMI audio tick. A
nonzero command is cleared before `StartQueuedSoundEffect` indexes the pointer
table at `$F47C`. Each descriptor activates one or more of the eight virtual
channels. Because later descriptors overwrite the selected virtual-channel
records, lower-numbered occupied slots win when two commands target the same
channel. The `audio-channel-priority` trace proves this with commands `$07`
and `$0A`: slot 2 is consumed first and slot 0 last, leaving command `$0A`'s
stream installed in virtual channel 4.

The routine saves the caller's `A`, pushes the incoming `Y` command, performs
the slot search with `Y`, then restores and stores the command before restoring
`A`. This stack order explains both the preserved accumulator and the selected
slot returned in `Y`.
