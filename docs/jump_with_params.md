# Inline appendix dispatcher

`src/system/thread_runtime.asm` owns CPU `$8EA9-$8EBF`. Bisqwit's map names
the entry `JumpWithParams` and classifies it as a jump-table routine whose
parameters are appended to the caller.

Callers use this layout:

```asm
    ; A = zero-based selector
    JSR JumpWithParams
    .addr Handler0, Handler1, Handler2
```

The 6502 `JSR` leaves the address of its final operand byte on the hardware
stack. `JumpWithParams` doubles `A`, removes that return address, and reads the
selected little-endian word at `return + 1 + 2*A`. It then jumps indirectly to
the selected handler through `TempPointer00`.

The removed return address is deliberately not restored. A handler ending in
`RTS` therefore consumes the caller's next older stack frame and returns from
the dispatching routine as a whole. Bytes after the `JSR` are data, never
fallthrough instructions. The routine clobbers `A`, `Y`, and
`TempPointer00`; `X` is unchanged.

Eleven static call sites use this ABI. The 28-entry enemy AI appendix is
separately decoded and checked by `make enemy-ai-audit`; other appendices will
enter equivalent manifests as their surrounding subsystems are reconstructed.
