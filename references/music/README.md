# Music provenance and integration

User-supplied source:
`David Whittaker - Shadow of the Beast - Title (AY) 1 (1990).ay`

SHA-256: `6bf35f961ea524fadf5c303abe86d8f3979cbd92bc3cea9f377172ff19dc4ff9`.
The ZXAYEMUL metadata identifies David Whittaker and (c) 1990 Gremlin Graphics.
The three-entry file's first entry is Shadow of the Beast - Title (AY), with
5,450 50-Hz ticks. This file is preserved unmodified as supplied by the user;
no new redistribution license for the music is asserted.

The tune's existing Z80 driver runs at C000-D222. Its output helper at C86C is
redirected to the cartridge's TS2068 FFF5/FFF6 adapter. Init C0F6 and tick C003
are otherwise called as specified by the AY file. The first two unused bytes
at BFFE are omitted from the runtime image. The song restarts at the declared
length, using its original initialization routine.

The local `../TSSoundPlayer/tssound_player_test.tap` was inspected as the hardware
reference. Its SHA-256 is
`7796e18c7917e0278b93c348230da9e4cecbf2d62dc730282308ee77ae3c88dc`.
Its PLAYER block loads at C000 and uses FFF5 register selection / FFF6 data
writes (for example its CF5A onward output routine). Its tracker-song format
is different, so that player binary is not embedded in the cartridge.

Format reference: [AY Emulator author's format documentation](https://documentation.help/AY-3-8910.12-ZX-Spectrum/ay_e04vt.htm).

## TS2068 player credit

Josef Jelinek is credited for the TS2068 AY player shared in his post, "A new TS 2068 AY music composer preview," on [TS2068.groups.io](https://ts2068.groups.io/g/main). His supplied TSSoundPlayer example provided the native AY port reference for this cartridge; the tune itself retains its original driver and David Whittaker music credit.
