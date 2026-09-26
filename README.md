# Beast Demo TS2068

[Play the demo in TSRun](https://jon0x0.github.io/beastdemo_ts2068/).

Revision 10: twelve parallax bands, a buffered six-pose character and David Whittaker's Shadow of the Beast AY title music. CRT scanlines are enabled by default. Click Play to activate browser audio. O/P adjusts speed; S toggles sound (default on). The music continues silently while muted.

The browser adapter loads live modules, shaders and system ROMs from [Josef Jelinek's TSRun](https://josef-jelinek.github.io/TSRun/). It uses the current frame-rate-based audio API with bounded queue refill and wall-clock frame accounting. No emulator or system ROM copy is distributed here.

The exact archived revision-10 cartridge is in `web/assets/`. The release ZIP contains its complete source, artwork provenance, build artifacts, documentation and emulator validation. The cartridge SHA-256 is `fecc762d6c38476da647f0eccc5b2c1d752b2a81d9d36397e17574b50e796331`.

Serve `web/` over HTTP for local testing (`python -m http.server 8765 --directory web`). Publishing uses GitHub Actions and Pages. See [credits and provenance](THIRD_PARTY.md). This is an unofficial technical demo; physical hardware remains untested.
