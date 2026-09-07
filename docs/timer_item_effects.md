# Timer item effects

`src/game/timer/runtime.asm` owns CPU `$C628-$C697`. The four public item
handlers are entries in the still-unreconstructed item dispatch data; Bisqwit's
map identifies them as the double-time, fivefold-time, `10000`, and `05000`
effects.

The remaining time is stored as four unpacked decimal digits from
`TimerDigit10` through `TimerDigit10000`. `DoubleRemainingTime` walks from the
least-significant digit upward, propagating decimal carry. The double-item
handler uses it once. The fivefold handler saves the original digits, doubles
twice to obtain four times the value, then adds the saved value. Carry beyond
the ten-thousands digit is discarded, so both operations are modulo 10000.

The item handlers also update `TimerDecrementStep`:

- the double handler preserves bit 7 and replaces the low rate with 2;
- the fivefold handler performs the original `ASL`, `ASL`, `ADC` sequence. For
  the observed small low-rate values, this preserves bit 7 and multiplies the
  rate by 5.

`SetTimerTenThousandsDigit` stores its input in `TimerDigit10000` and clears
all lower digits. `SetTimerTo10000` branches directly into that helper with
`A=1`; `SetTimerTo05000` first clears all four digits and then writes 5 to
`TimerDigit1000`.
