# Beast Horizons - TS2068 cartridge demo, revision 10

A Shadow of the Beast scenery and running-character study with David Whittaker's
AY title music. Five cloud planes, rose-shaded rocks, thin grass bands and a
foreground fence scroll in 256x192 extended color mode. The scenery and six
running poses are pixel-identical to revision 08.

The rocks still move one pixel per update, crossing the screen in **10.68 seconds
in Fuse with music playing**. A 6,000-update run averaged 10.67 seconds per crossing.

## Run

Select the **Timex Sinclair 2068** machine in Fuse, insert
`build/beast_horizons_rev10.dck` as the DOCK cartridge, enable sound, then reset.
The demo starts at medium running speed and plays the title tune automatically.

| Key | Action |
|---|---|
| O | Reduce running speed, down to a complete stop |
| P | Increase running speed, up to maximum |
| S | Toggle sound off/on (default on) |

Releasing a key retains the selected speed. Press and release S once per toggle; holding it does not repeat. The tune keeps
advancing while muted and returns at its current position when enabled.
The music and clouds continue when
the character stops. There is no jumping, collision, enemy or joystick logic.

## AY playback

The supplied ZXAYEMUL file contains three entries; this cartridge uses entry 0,
**Shadow of the Beast - Title (AY)**. Its original Z80 driver and score run from
HOME RAM at their original addresses. Only the Spectrum output helper is redirected
to the TS2068's FFF5 register-select / FFF6 data ports, as used by the supplied
TSSoundPlayer example. This is native AY synthesis, not sampled music.

Josef Jelinek is credited for the TS2068 AY player shared in his post, "A new TS 2068 AY music composer preview," on [TS2068.groups.io](https://ts2068.groups.io/g/main). His supplied TSSoundPlayer example provided the native AY port reference for this cartridge; the tune itself retains its original driver and David Whittaker music credit.

Playback advances on five of every six display interrupts (approximately 50 Hz),
independently of animation speed. After the file's 5,450-tick duration (about
109 seconds), the driver is reinitialized and the title repeats. Register writes,
including envelope retriggers, are checked against the original driver over
12,000 ticks and two restarts. Registers R14/R15 are never written.

`build/beast_horizons_rev10_audio.wav` is a 30-second emulator-rendered preview.
The original file and provenance are retained under `references/music/`.

## Buffered character and performance

The character occupies X=112-143, Y=120-159. Background pixels for those four
byte-columns are composed in HOME RAM, then the runner is masked over them.
Only the completed pixels and attributes are published. Scenery outside the
character rectangle goes straight to display, avoiding a redundant full-width
copy and recovering CPU time for music.

Full updates publish 160 character bitmap bytes and 160 attribute bytes.
Intervening rock-only updates publish 128 bitmap bytes while retaining the
unchanged pose attributes. The test checks the protected rectangle remains
unchanged until composition completes and every published byte is final.
There is no visible character erase pass. Copies still take time; live raster
tearing is not ruled out and physical hardware has not been tested.

Rocks use eight prepared phases with a fixed rose/white scanline palette and
rigidly shifted Sierra Lite dithering. Other planes retain their revision-08
four-phase artwork. ECM permits two colors per 8x1 cell, so partly covered sprite
cells share the runner's blue/white attributes. The conversion uses the project's
offline encoder, not RetroPixelConverter itself.

## Build and validation

Requirements: Python 3.10+, Pillow, Pasmo under WSL at
`../PasmoAssembler/pasmo-0.5.5/pasmo`, Node.js 22+, the sibling TSRun checkout,
stock TS2068 ROMs, and Fuse. Use a modern Node executable.

```powershell
python scripts/build.py
node scripts/trace_music.mjs
node scripts/validate.mjs
node scripts/validate_music.mjs
node scripts/validate_music.mjs --toggle
python scripts/validate_fuse.py
python scripts/validate_fuse_cycle.py
python scripts/validate_fuse_cycle.py --long
python scripts/validate_fuse_music.py
python scripts/render_capture.py
python scripts/compare_revisions.py
```

The cartridge is 65,545 bytes: a DCK header plus eight read-only 8K chunks.
Code/tables occupy 7,760 bytes, shared assets including music occupy 54,627 bytes,
and hill descriptors occupy 1,440 bytes. See MEMORY.md for banking and RAM use.

Validation of the shipped cartridge:

- TSRun: 2,305 updates with exact complete-display and protected-buffer checks,
  controls, one-pixel movement, wrapping, immutable scenery caches and banking.
- Music: 12,000 ticks (about four minutes), every AY write compared with the
  unmodified source driver plus the documented restart schedule.
- Fuse: boot, IM2 interrupts, update 1,024; 1,000 music ticks / 10,996 writes
  match the reference. A 6,000-update maximum-speed run peaks at 173,475 T-states,
  below the 179,208 three-refresh budget, with both tune restarts included.
- S-key checks cover default-on, press/release, held-key suppression, all three
  muted amplitudes, uninterrupted tune position and muting across a tune restart.
- Independent DCK inspection matches the physical 65,536-byte BIN. Reports carry
  the final cartridge SHA-256.

The GIF is reconstructed from actual display RAM with measured update intervals;
it has no sound and jumps when looping. The WAV uses TSRun's AY emulation.
No system ROMs or emulator binaries are included.

Revision 09 was checksum-verified before editing. Earlier revisions remain
preserved. Revision 10 and its release ZIP include source, music, previews and
validation evidence; `build/` is working output. Never overwrite a populated
revision directory.
