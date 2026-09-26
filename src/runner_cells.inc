ld a,(hl)
inc hl
cp 255
jr z,runner_transparent_0
ld b,a
ld a,(de)
and b
or (hl)
inc hl
ld (de),a
jr runner_cell_done_0
runner_transparent_0:
inc hl
runner_cell_done_0:
inc de
ld a,(hl)
inc hl
cp 255
jr z,runner_transparent_1
ld b,a
ld a,(de)
and b
or (hl)
inc hl
ld (de),a
jr runner_cell_done_1
runner_transparent_1:
inc hl
runner_cell_done_1:
inc de
ld a,(hl)
inc hl
cp 255
jr z,runner_transparent_2
ld b,a
ld a,(de)
and b
or (hl)
inc hl
ld (de),a
jr runner_cell_done_2
runner_transparent_2:
inc hl
runner_cell_done_2:
inc de
ld a,(hl)
inc hl
cp 255
jr z,runner_transparent_3
ld b,a
ld a,(de)
and b
or (hl)
inc hl
ld (de),a
jr runner_cell_done_3
runner_transparent_3:
inc hl
runner_cell_done_3:
inc de
