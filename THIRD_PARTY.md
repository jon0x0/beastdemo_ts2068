# Reference artwork

The scenery and six runner poses are adapted from the user-supplied
[shadow-of-the-beast-html5](https://github.com/spleennooname/shadow-of-the-beast-html5)
repository, pinned at commit `c4db4001d00ca9d37926cc057460859ab96398cc`.
Original downloaded files and the repository's Apache-2.0 license are in
`references/beast/`. Shadow of the Beast was created by Reflections and
published by Psygnosis; this is an unofficial technical demo. The repository
license is preserved without asserting separate ownership of the game artwork.

Conversion resizes the assets, brightens the runner, and applies serpentine
Sierra Lite coverage-error diffusion under TS2068 extended-color constraints.
Each 8x1 cell has two colors sharing one BRIGHT bit. This uses the project's
offline encoder, not RetroPixelConverter itself.

Revision 08 remaps rock luminance to rose/white shading and shifts one-time

Sierra Lite patterns rigidly. Grass uses dominant scanline pairs and the fence

uses black/white to reduce attribute traffic; cloud conversion is unchanged.

## Revision 09 music

The user-supplied David Whittaker title AY file is preserved unmodified in
`references/music/`. Its metadata credits David Whittaker and (c) 1990 Gremlin
Graphics. The original driver and score are used with an output-port adapter;
this demo makes no new licensing claim over the music. TSSoundPlayer supplied
the local TS2068 port reference; its player binary is not embedded. See
`references/music/README.md` for source hashes and integration details.

## TS2068 AY player credit

Josef Jelinek is credited for the TS2068 AY player shared in his post, "A new TS 2068 AY music composer preview," on [TS2068.groups.io](https://ts2068.groups.io/g/main). His supplied TSSoundPlayer example provided the native AY port reference for this cartridge; the tune itself retains its original driver and David Whittaker music credit.

## Browser emulation

Browser emulation, CRT shader and audio mixing are provided by Josef Jelinek's [TSRun](https://github.com/josef-jelinek/TSRun). Modules, shaders and system ROMs load from its live site and are not redistributed here. The browser adapter is adapted from the [speech2ay web demo](https://github.com/jon0x0/speech2ay/tree/main/web), updated for TSRun's current frame-rate-based sound API.
