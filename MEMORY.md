# Beast Horizons revision 10 memory contract

| Physical DOCK chunk | Address | Contents / runtime mapping |
|---|---|---|
| 0 | 0000-1FFF | RST 08 gateway; hill descriptors 0100-069F; prepared assets |
| 1 | 2000-3FFF | Prepared assets, ROM |
| 2 | 4000-5FFF | Assets copied to HOME A000-BFFF at startup |
| 3 | 6000-7FFF | Assets and music copied to HOME E000-FFFF at startup |
| 4 | 8000-9FFF | AROS header, renderer, audio wrapper and tables; resident ROM |
| 5 | A000-BFFF | ROM assets or HOME cache of chunk 2 |
| 6 | C000-DFFF | ROM assets or writable HOME music driver / music stack |
| 7 | E000-FFFF | ROM assets or immutable HOME cache of chunk 3 |

AROS requests chunk 4, entry 8008. With interrupts disabled and SP=8000, HSR=1C
allows copying DOCK 4000-5FFF to HOME A000-BFFF and DOCK 6000-7FFF to HOME
E000-FFFF. HSR=F3 restores the working map; DECR=02 selects DOCK and ECM.
The music image is subsequently copied from cached HOME EB40-FD62 to C000-D222
with HSR=13. The unused two-byte wrapper at original BFFE is not loaded; public
entries are C0F6 (init, A=0) and C003 (tick). Three bytes at C86C become a JP to
the resident TS2068 output adapter; all other driver/score bytes are preserved.

Runtime rendering uses F3 for ROM sources or 53 for cached HOME A/E sources.
Both retain resident code, HOME display, working state and main stack. Source
routines write the HSR shadow BEFORE the hardware port; an interrupt between
those instructions can safely restore the intended mapping early. The ISR
selects 13, saves the main SP, switches to an independent stack below E000,
preserves all main/alternate registers and IX/IY, and runs the music scheduler.
It restores the main stack and HSR before returning. DECR never changes.

| HOME range | Use |
|---|---|
| 4000-57FF | Nonlinear visible bitmap |
| 5800-5DFF | Reserved bitmap staging; live columns 14-17 in rows 0-39 |
| 5E00-5F00 | 257-byte IM2 table, filled with 5F |
| 5F5F-5F61 | JP to resident interrupt handler |
| 5F80-5FD0 | Mixed display/buffer circular copier |
| 5FD1-5FD2 | Dummy patch slot for zero coarse scroll |
| 6000-77FF | Nonlinear visible ECM attributes |
| 7800-7DFF | Reserved attribute staging; live columns 14-17 in rows 0-39 |
| 7E00-7E3F | Renderer/music state and scratch |
| 7E40-7EC9 | Ordinary circular-copy code |
| Below 8000 | Main stack, separate from working state/code |
| A000-BFFF | Immutable cache of DOCK chunk 2 |
| C000-D222 | Original music driver and score, writable |
| Below E000 | Music/interrupt stack, above driver image |
| E000-FFFF | Immutable cache of DOCK chunk 3 |

State: tick 7E00, frame 7E01, coarse 7E02, deadline 7E03, HSR/DECR shadows
7E04/05, speed 7E06, distance 7E07/08, pose 7E09, hill position 7E0A, wait 7E0B,
fraction 7E0C, clouds 7E10-14, grass base 7E16, source 7E20, character destination
7E22, mixed patch pointer 7E24, saved display destination 7E26, audio phase 7E30,
16-bit total music ticks 7E32, saved main SP 7E34, song position 7E36, amplitude shadows 7E38-3A,
sound-off flag 7E3B (zero means enabled), S-key held latch 7E3C.

The ordinary copier patches jump low bytes at 7E41/7E87. The mixed copier writes
14 bytes to display, four to the character buffer, then 14 to display. One LDI
is replaced by RST 08 / NOP to wrap the source. DOCK 0008 holds a JP to the ROM
wrap helper, visible in F3/53/13. Setup restores the old LDI and patches the new
slot before drawing; interrupts never invoke either copier. ROM is never modified.

Hill records are three-byte pointer/bank descriptors (1,440 bytes). Upper rows
have 63-byte strips with wrap lookahead; lower rows use 32-byte circular strips.
Other bands have six-byte bitmap/attribute descriptors; fixed palettes skip
attribute copying. No data strip crosses an 8K source bank boundary.

Each runner pose occupies 480 bytes: 320 mask/bitmap bytes followed by 160
prepared attributes. Scenery colors in the character rectangle are fixed per
scanline, allowing the complete attribute overlay to be prepared offline.
BUFFER_READY means the four protected columns are complete, not the unused
remainder of the reserved full-width buffers. Publish writes 320 final bytes on
full updates and 128 on intervening rock-only updates; other scenery is direct.

Animation uses alternating two/three-refresh deadlines. Hill position advances
one pixel per update when speed is nonzero; pose and ground refresh every second
update. Distance adds speed/2 with a fractional carry. O/P adjusts speed every
eighth update, from 0 to 16, default 8. Clouds move two pixels at staggered
4/8/16/32/64-update intervals. Music advances five ticks per six video interrupts
and restarts after 5,450 ticks. Stopping the runner leaves music/clouds active.

S is sampled from bit 1 of keyboard row FDFE on every display interrupt. A new
press toggles the off flag and immediately refreshes AY R8-R10 to zero or their
shadow values. Driver writes keep the amplitude shadows current while muted;
only hardware amplitude writes are forced to zero. Other registers, envelope
retrigger writes, music phase and song position continue normally. Output wrapper
preserves the original driver-visible registers and flags.
