# Enemy type configuration

`src/game/enemies/type_configuration.asm` owns CPU `$A3F8-$A44D`. Five call
sites supply `SpawnSlotIndex` and `SpawnType`; three complete spawn paths call
it immediately after `InitializeEnemy`, while two gameplay paths reconfigure
already allocated slots from encoded type streams.

The routine resolves the object record through `$B28A`. The low two type bits
select a variant, while `(SpawnType - $18) / 4` indexes the 27-byte
`EnemyTypeConfigurationTable` at `$A44E-$A468`. Types `$80/$81` present in the
original room streams require the final index 26 and therefore prove that
`$A468` belongs to this table.
Decoded table bits determine a `$C0`/`$E0` base, a derived value passed through
scratch byte `$04`, whether object offset 5 receives `$80`, and which X value
is passed to the helper at `$9D99`.

One decoded flag causes the matching AI record to be selected through
`LoadEnemyAiPointer`. The low two type bits seed `EnemyAiPathDirectionOffset`;
an XOR/mask transform chooses horizontal or vertical opposition for
`EnemyAiAlternateDirectionOffset`. The shared path-mask handlers establish
both fields as direction indices. The behavior of `$9D99` and the remaining
individual table bits stays unnamed until their consumers provide equivalent
evidence.
