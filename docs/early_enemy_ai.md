# Early enemy AI families

`src/game/enemies/early_ai.asm` owns `$A4B3-$A68B`, the first two targets of the
28-entry enemy AI dispatcher.

`RunType00To03EnemyAi` combines lifetime/action gating, map collision, motion
selection, and contact rewards. Rewards include grouped score amounts 1/2/5,
an extra life, or one of four inventory effects selected through an inline
`JumpWithParams` table.

`UpgradeSmallFireballInventory` scans the configured packed two-bit inventory
slots backwards and changes the first small-fireball entry into a large one.

`RunType04To07EnemyAi` chooses randomized motion on open paths and adjusts it
after collision. Its contact path replaces all active enemy object headers
with `$E2,$1C,$FF,$00`, clears their AI phase bytes, and deactivates the
triggering enemy. Shared helpers beyond this range retain neutral addresses
until their own reconstruction.
