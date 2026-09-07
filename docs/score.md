# Score addition

`src/game/scoring.asm` owns CPU `$C73B-$C755`. `AddScoreByAAtDigitX` has six
direct callers and uses the following contract:

```text
input:      A = amount for the selected decimal digit
            X = index into ScoreDigits, 0..7
output:     decimal carry propagated toward lower indices
preserved:  Y and GameStateFlags
clobbered:  A, X, processor flags
```

`ScoreDigits` stores eight unpacked decimal digits from most significant at
index 0 to least significant at index 7. The routine adds at index `X`, wraps
values of ten or more, and propagates carry by decrementing `X`. Carry beyond
index 0 is discarded.

Before the addition, the routine rotates bit 0 of `GameStateFlags` into carry.
When that bit is clear it replaces the requested amount with zero; when set it
keeps the caller's amount. A matching rotate restores the flags byte exactly
before arithmetic begins. This proves that bit 0 gates score updates, matching
its already observed role in selecting complete controller-cache refreshes.
