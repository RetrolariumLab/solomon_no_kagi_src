# Inventory and item effects

`src/game/items/inventory_effects.asm` owns CPU `$C698-$C70F`. Bisqwit's map
identifies the public entries as Scroll Extender, two fireball bottles, Fairy
Bell, blue/red Tzo, Blue Crystal, and the shared type-04/type-06 score effect.

The fireball inventory uses eight two-bit slots packed into
`InventorySlotsHigh` and `InventorySlotsLow`. `AddItemToScroll` scans from mask
`$C0` downward in two-bit steps. It stops at the first zero slot within the
`InventorySlotCount` usable entries, then merges the selected bits from
`InventoryItemSlotPattern`. The small-bottle pattern `$55` supplies `01` in
every slot; the large-bottle pattern `$AA` supplies `10`. If every usable slot
is occupied, the routine returns without changing the inventory. The Scroll
Extender increments the usable count up to eight.

The Fairy Bell handler increments `FairiesQueued`, which the main gameplay
thread later consumes. The Tzo handlers reach `ExtendFireballLifetime` with
`A=$04` or `A=$10`; the helper skips the addition when
`FireballLifetimeHi >= 2`, otherwise adds through the low byte and propagates
carry to the high byte. The exact incoming-carry contract is still tied to the
item dispatcher and remains a runtime-trace item.

The complete selector mapping is now reconstructed in
`src/data/item_handlers.asm`; see `docs/item_interactions.md`. The three
score-producing paths call `AddScoreByAAtDigitX` at `$C73B`.
Bisqwit's map confirms that entry and all six direct control-flow references
use its symbol. Its decimal arithmetic and game-state gate are reconstructed
in `src/game/score.asm`; see `docs/score.md`.
