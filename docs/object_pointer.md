# Non-Dana object pointer helper

`src/game/objects/update_pipeline.asm` owns CPU `$CA4F-$CA59`. Bisqwit's map identifies
the entry as `LoadObjectPointer`. It resolves a zero-based index in `X` through
the split pointer planes at `$B469` and `$B47E` and writes the selected address
to `TempPointer00`.

Calling convention:

```text
input:      X = non-Dana object index, 0..19
output:     TempPointer00 = address of object record X + 1
preserved:  X, Y
clobbered:  A, TempPointer00
```

The plus-one table bases are source-owned as `NonDanaObjectPointerLowTable`
and `NonDanaObjectPointerHighTable`. Index 0 therefore selects
`MagicSparkObject`, followed by the fireball, auxiliary object, and seventeen
enemy records; Dana at complete-table index 0 is deliberately excluded.

Both helper callers iterate `X` from `$13` down to zero, covering all twenty
non-Dana object records. Eight other code paths access the same plus-one table
bases directly and now use the same semantic aliases.
