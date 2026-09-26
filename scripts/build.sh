#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
"../PasmoAssembler/pasmo-0.5.5/pasmo" --bin src/parallax.asm build/code.bin build/symbols.txt
