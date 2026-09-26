; Beast Horizons rev14: one-pixel parallax plus interrupt-driven AY music.
org $8000
db $02,$02,$08,$80,$ef,$01,0,0
TICK equ $7e00
FRAME equ $7e01
COARSE equ $7e02
LAST equ $7e03
HSR equ $7e04
DECR equ $7e05
SPEED equ $7e06
DIST equ $7e07
POSE equ $7e09
HILLPOS equ $7e0a
WAIT equ $7e0b
FRACTION equ $7e0c
POSITIONS equ $7e10
SOURCE equ $7e20
DEST equ $7e22
MIXED_PATCH equ $7e24
MIXED_DISPLAY equ $7e26
START:
di
ld sp,$8000
ld a,$1c
out ($f4),a
ld hl,$4000
ld de,$a000
ld bc,$2000
ldir
ld hl,$6000
ld de,$e000
ld bc,$2000
ldir
ld a,$f3
out ($f4),a
ld a,2
out ($ff),a
xor a
out ($fe),a
ld hl,$7e00
ld de,$7e01
ld bc,63
ld (hl),a
ldir
ld a,$f3
ld (HSR),a
ld a,2
ld (DECR),a
ld a,8
ld (SPEED),a
ld a,2
ld (WAIT),a
ld hl,circular_image
ld de,$7e40
ld bc,circular_end-circular_image
ldir
ld hl,mixed_image
ld de,$5f80
ld bc,mixed_end-mixed_image
ldir
ld hl,$5fd1
ld (MIXED_PATCH),hl
ld hl,$5e00
ld de,$5e01
ld bc,256
ld (hl),$5f
ldir
ld hl,isr_image
ld de,$5f5f
ld bc,isr_end-isr_image
ldir
ld a,$5e
ld i,a
im 2
call initialize_colors
call render_all
call music_init
ei
READY:
ld a,(WAIT)
ld c,a
ld a,(TICK)
ld b,a
ld a,(LAST)
sub b
neg
cp c
jr nc,begin_frame
halt
jr READY
begin_frame:
; Advance an absolute deadline, allowing a long update to borrow slack
; from the next 3-refresh slot without dropping any single-pixel positions.
ld a,(LAST)
add a,c
ld (LAST),a
ld a,(FRAME)
inc a
ld (FRAME),a
and 1
add a,2
ld (WAIT),a
call render_frame
FRAME_DONE:
jp READY

render_all:
xor a
ld hl,sky_gap_phases
call setup
call draw_sky_gap
xor a
ld hl,cloud0_phases
call setup
call draw_cloud0
xor a
ld hl,cloud1_phases
call setup
call draw_cloud1
xor a
ld hl,cloud2_phases
call setup
call draw_cloud2
xor a
ld hl,cloud3_phases
call setup
call draw_cloud3
xor a
ld hl,cloud4_phases
call setup
call draw_cloud4
xor a
ld hl,hill_phases
call setup_hill
call draw_hill_upper
jp render_fast

render_frame:
call controls
ld a,(SPEED)
ld b,a
ld a,(FRACTION)
add a,b
ld c,a
and 1
ld (FRACTION),a
ld a,c
srl a
ld hl,(DIST)
ld e,a
ld d,0
add hl,de
ld (DIST),hl
ld a,(SPEED)
or a
jr z,pose_done
ld a,(HILLPOS)
inc a
ld (HILLPOS),a
ld a,(FRAME)
and 1
jr nz,pose_done
ld a,(POSE)
inc a
cp 6
jr c,pose_store
xor a
pose_store:
ld (POSE),a
pose_done:
ld a,(FRAME)
and 3
cp 1
jr z,update_cloud0
ld a,(FRAME)
and 7
cp 3
jr z,update_cloud1
ld a,(FRAME)
and 15
cp 7
jr z,update_cloud2
ld a,(FRAME)
and 31
cp 15
jr z,update_cloud3
ld a,(FRAME)
and 63
cp 31
jr z,update_cloud4
jp render_fast
update_cloud0:
ld a,(POSITIONS)
add a,2
ld (POSITIONS),a
ld hl,cloud0_phases
call setup
call draw_cloud0
jp render_fast
update_cloud1:
ld a,(POSITIONS+1)
add a,2
ld (POSITIONS+1),a
ld hl,cloud1_phases
call setup
call draw_cloud1
jp render_fast
update_cloud2:
ld a,(POSITIONS+2)
add a,2
ld (POSITIONS+2),a
ld hl,cloud2_phases
call setup
call draw_cloud2
jp render_fast
update_cloud3:
ld a,(POSITIONS+3)
add a,2
ld (POSITIONS+3),a
ld hl,cloud3_phases
call setup
call draw_cloud3
jp render_fast
update_cloud4:
ld a,(POSITIONS+4)
add a,2
ld (POSITIONS+4),a
ld hl,cloud4_phases
call setup
call draw_cloud4
jp render_fast
render_fast:
ld a,(HILLPOS)
ld hl,hill_phases
call setup_hill
call draw_hill_upper
; IX now points directly to the lower rows, so reset before its helper.
ld a,(HILLPOS)
ld hl,hill_phases
call setup_hill
call draw_hill_buffer
ld a,(FRAME)
and 1
jp nz,compose_runner
ld hl,(DIST)
srl h
rr l
srl h
rr l
ld a,l
ld (POSITIONS+6),a
ld hl,grass0_phases
call setup
call draw_grass0
ld a,(POSITIONS+6)
add a,a
ld hl,grass1_phases
call setup
call draw_grass1
ld a,(POSITIONS+6)
ld b,a
add a,a
add a,b
ld hl,grass2_phases
call setup
call draw_grass2
ld a,(POSITIONS+6)
add a,a
add a,a
ld hl,grass3_phases
call setup
call draw_grass3
ld a,(POSITIONS+6)
ld b,a
add a,a
add a,a
add a,b
ld hl,fence_phases
call setup
call draw_fence
ld a,(POSITIONS+6)
ld b,a
add a,a
add a,b
add a,a
ld hl,grass4_phases
call setup
call draw_grass4
compose_runner:
call draw_runner
BUFFER_READY:
call publish
ret

controls:
ld a,(FRAME)
and 7
ret nz
ld bc,$dffe
in a,(c)
ld b,a
bit 0,b
jr nz,brake
ld a,(SPEED)
cp 16
jr nc,brake
inc a
ld (SPEED),a
brake:
bit 1,b
ret nz
ld a,(SPEED)
or a
ret z
dec a
ld (SPEED),a
ret

; A=pixel offset, HL=four phase pointers, IX=selected row records.
setup:
call setup_scroll
and 6
jr setup_phase
setup_hill:
call setup_scroll
and 7
add a,a
setup_phase:
ld e,a
ld d,0
add hl,de
ld e,(hl)
inc hl
ld d,(hl)
push de
pop ix
ret
setup_scroll:
ld c,a
rrca
rrca
rrca
and 31
ld (COARSE),a
push hl
push bc
ld hl,(MIXED_PATCH)
ld (hl),$ed
inc hl
ld (hl),$a0
add a,a
ld e,a
ld d,0
ld hl,mixed_patches
add hl,de
ld e,(hl)
inc hl
ld d,(hl)
ex de,hl
ld (MIXED_PATCH),hl
ld (hl),$cf
inc hl
ld (hl),0
pop bc
pop hl
ld a,(COARSE)
add a,a
add a,$43
ld ($7e41),a
ld a,(COARSE)
add a,a
ld b,a
ld a,$c9
sub b
ld ($7e87),a
ld a,c
ret

; Pixel-only scanline from a 63-byte strip with circular lookahead.
scanline:
call pixel_source
call copy32
ret
cloud_scanline:
ld a,(ix+2)
ld (HSR),a
out ($f4),a
ld l,(ix+0)
ld h,(ix+1)
ld (SOURCE),hl
inc ix
inc ix
inc ix
jp circular32
; Non-rock rows retain revision 07's 6-byte pixel/attribute descriptors.
fixed_scanline:
call cloud_scanline
inc ix
inc ix
inc ix
ret
color_scanline:
push de
call cloud_scanline
pop de
ld a,d
add a,$20
ld d,a
jp cloud_scanline
pixel_source:
ld a,(ix+2)
ld (HSR),a
out ($f4),a
ld l,(ix+0)
ld h,(ix+1)
inc ix
inc ix
inc ix
ld a,(COARSE)
add a,l
ld l,a
ret nc
inc h
ret
circular32:
ld a,(COARSE)
ld c,a
ld b,0
add hl,bc
jp $7e40

; Relocated to HOME 7E40. First JP enters N=32-coarse LDIs;
; second enters coarse LDIs. Patched low bytes stay within page 7E.
circular_image:
jp $7e43
rept 32
ldi
endm
ld hl,(SOURCE)
jp $7ec9
rept 32
ldi
endm
ret
circular_end:

; The four character columns go to RAM; the rest goes straight to display.
; One LDI is patched to RST 08 / NOP for the circular source wrap.
mixed_fixed_scanline:
call mixed_scanline
inc ix
inc ix
inc ix
ret
mixed_scanline:
ld a,(ix+2)
ld (HSR),a
out ($f4),a
ld l,(ix+0)
ld h,(ix+1)
ld (SOURCE),hl
inc ix
inc ix
inc ix
ld a,(COARSE)
ld c,a
ld b,0
add hl,bc
jp $5f80
mixed_wrap:
ld hl,(SOURCE)
ldi
ret
mixed_image:
rept 13
ldi
endm
ld (MIXED_DISPLAY),de
ld de,(DEST)
rept 4
ldi
endm
ld de,(MIXED_DISPLAY)
inc de
inc de
inc de
inc de
rept 15
ldi
endm
ret
mixed_end:

; All sprite writes target the two RAM buffers, including changed attributes.
draw_runner:
ld a,(POSE)
ld e,a
add a,a
add a,e
ld e,a
ld d,0
ld hl,sprite_frames
add hl,de
ld e,(hl)
inc hl
ld d,(hl)
inc hl
ld a,(hl)
ld (HSR),a
out ($f4),a
ex de,hl
ld de,$580d
ld c,40
ld a,(FRAME)
and 1
jr z,runner_row
ld c,32
runner_row:
push bc
include "src/runner_cells.inc"
ld a,e
add a,28
ld e,a
jr nc,runner_next
inc d
runner_next:
pop bc
dec c
jr nz,runner_row
ld a,(FRAME)
and 1
ret nz
; Full poses carry a prepared 4x40 attribute overlay after their bitmap masks.
; Background palettes are fixed in this strip, so no restore pass is needed.
ld de,$780d
ld b,40
runner_attribute_row:
push bc
call copy4
ld a,e
add a,28
ld e,a
jr nc,runner_attribute_next
inc d
runner_attribute_next:
pop bc
djnz runner_attribute_row
ret
copy4:
ld bc,4
rept 4
ldi
endm
ret
copy32:
ld bc,32
rept 32
ldi
endm
ret
; Row-wide ECM attributes are initialized once; only sprite cells change.
initialize_colors:
ld ix,row_colors
ld bc,$c000
init_color_row:
ld a,c
and 7
or $60
ld d,a
ld a,c
and $c0
rrca
rrca
rrca
or d
ld d,a
ld a,c
and $38
rlca
rlca
ld e,a
ld a,(ix+0)
inc ix
rept 32
ld (de),a
inc e
endm
inc c
dec b
jp nz,init_color_row
ld hl,row_colors+120
ld de,$7800
ld b,48
init_buffer_color_row:
ld a,(hl)
inc hl
rept 32
ld (de),a
inc de
endm
djnz init_buffer_color_row
ret
isr_image:
jp isr_handler
isr_end:
isr_handler:
push af
ld a,$13
out ($f4),a
ld ($7e34),sp
ld sp,$e000
ld a,(TICK)
inc a
ld (TICK),a
push bc
push de
push hl
push ix
push iy
ex af,af'
push af
exx
push bc
push de
push hl
call music_tick
pop hl
pop de
pop bc
exx
pop af
ex af,af'
pop iy
pop ix
pop hl
pop de
pop bc
ld sp,($7e34)
ld a,(HSR)
out ($f4),a
pop af
ei
reti
include "src/music.asm"
include "src/generated.inc"
