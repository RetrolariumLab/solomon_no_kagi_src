# Item score lookup tables

`src/data/static_layout.asm` owns CPU `$C710-$C717` as two adjacent tables used
by the collectible-item score path at `$C480-$C497`:

| Address | Label | Values | Role |
| --- | --- | --- | --- |
| `$C710-$C714` | `ItemBonusScoreDigitIndices` | `5,4,3,2,1` | starting index passed in X |
| `$C715-$C717` | `ItemBonusScoreAmounts` | `1,2,5` | amount passed in A |

The caller divides its normalized item selector into a five-entry group index
and a three-entry remainder, then calls `AddScoreByAAtDigitX`. Assembly asserts
both table lengths so code and data cannot silently drift across their shared
boundary.
