# Cooperative masked-RAM waits

`src/system/thread_runtime.asm` owns CPU `$9165-$9189`. Its two entries use
the same zero-page calling convention:

```text
input:      A = bit mask
            X = zero-page address
output:     wait condition satisfied
preserved:  A, X
changed:    Y = input mask
```

`WaitForMaskedBitsClear` returns when `(A & RAM[X]) == 0`;
`WaitForMaskedBitsSet` returns when `(A & RAM[X]) != 0`. While the condition is
not satisfied, each routine saves its arguments on the current context's
hardware-stack partition, calls `SwitchThreads`, restores the arguments, and
checks again. Ten direct callers now use these names.

The second routine ends with a conditional branch rather than a trailing
`RTS`. `SwitchThreads` is statically proven to return with carry set, so the
branch always returns to the wait head after a yield. The only normal exit is
the earlier `BNE FinishMaskedRamWait`, which removes the two saved values and
returns. This unusual fall-through edge is part of the scheduler ABI and is
preserved byte-for-byte.
