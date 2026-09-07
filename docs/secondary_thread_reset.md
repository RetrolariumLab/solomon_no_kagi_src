# Secondary-thread transition reset

`src/system/thread_runtime.asm` owns CPU `$C756-$C789` and has six
direct callers. `ResetOtherSecondaryThreads` accepts in `X` the secondary
context that must remain active during a scene transition.

The routine first waits cooperatively for `GameStateFlags & $02` to clear. It
then advances a context index seven times modulo eight. Index 0 is skipped;
the input index is excluded because seven advances return to it only after the
loop is complete. Every other index from 1 through 7 is passed to `StopThread`.

After stopping those six contexts, it clears all four bytes at
`PendingThreadStarts`, clears bit 2 of `GameplayFlags`, and clears bit 0 of the
still-unidentified RAM byte `$87`. This establishes a common transition reset
boundary without assigning meanings to those two cleared flags beyond their
observed behavior.

Calling convention:

```text
input:      X = secondary context to keep active, 1..7
output:     contexts 1..7 except X stopped; pending starts cleared
clobbered:  A, X, ThreadStopIndex, RemainingThreadStops
preserved:  Y
```
