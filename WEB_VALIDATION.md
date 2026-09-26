# Browser release 1

Packages the unchanged, checksum-verified revision-10 cartridge. CRT scanlines are on by default using TSRun's shader. Archived cartridge source, previews and emulator evidence remain in the downloadable release ZIP.

Tested in headless Microsoft Edge with live upstream TSRun modules on 2026-09-26. Startup, WebGL CRT rendering and its switch, gesture-based audio activation, S button and held-key behavior, O/P controls, blur release, restart and 390-pixel mobile layout passed. No browser console errors. A ten-second steady-state sample measured 60.064 emulated frames per second; audio cut/gap counters did not increase during that sample. Startup incurred audio queue gaps while the engine warmed up. This does not establish subjective listening quality or physical-hardware behavior.

The live integration uses TSRun's frame-rate-based `initSound`, `soundWantsFrame`, queue callbacks, and full accounting of audio-driven frames against wall-clock pacing. System ROMs and emulator modules are fetched from upstream rather than distributed in this repository.

## Revision 14 cartridge

Runner aligned three pixels left; background bitmap and attribute data unchanged. All visible sprite pixels preserved. Right-edge cell exposure against rocks reduced by 42.33% across six poses. Passed 2,305 TSRun display/buffer checks, 12,000 music ticks with sound on and another 12,000 with toggles; Fuse 6,000-update maximum render cost 172,877 T-states within 179,208. Comparison and exact evidence are in the revision-14 ZIP.
