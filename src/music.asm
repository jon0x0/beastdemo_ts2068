; Original Whittaker title driver in HOME C000-D222, no relocation.
MUSIC_PHASE equ $7e30
MUSIC_COUNT equ $7e32
MUSIC_POSITION equ $7e36
AY_LEVELS equ $7e38
SOUND_OFF equ $7e3b
SOUND_HELD equ $7e3c
music_init:
ld a,$13
out ($f4),a
ld hl,music_source
ld de,$c000
ld bc,music_size
ldir
; Replace only the seven-byte Spectrum output helper with a resident JP.
ld a,$c3
ld ($c86c),a
ld hl,music_output
ld ($c86d),hl
xor a
call $c0f6
jp music_restore_bank

music_tick:
call sound_keys
; Five driver calls per six 60-Hz display interrupts, independent of scenery.
ld a,(MUSIC_PHASE)
add a,5
cp 6
jr c,music_skip
sub 6
ld (MUSIC_PHASE),a
ld hl,(MUSIC_COUNT)
inc hl
ld (MUSIC_COUNT),hl
ld a,$13
out ($f4),a
ld hl,(MUSIC_POSITION)
ld de,music_length
or a
sbc hl,de
jr nz,music_play
xor a
call $c0f6
ld hl,0
ld (MUSIC_POSITION),hl
music_play:
call $c003
ld hl,(MUSIC_POSITION)
inc hl
ld (MUSIC_POSITION),hl
music_tick_done:
ret
music_restore_bank:
ld a,(HSR)
out ($f4),a
ret
music_skip:
ld (MUSIC_PHASE),a
ret

; E=register, A=value. Preserve original helper's returned BC and flags.
; Josef Jelinek's TS Sound Player supplied the FFF5/FFF6 port reference.
; See his TS2068.groups.io post: A new TS 2068 AY music composer preview.
music_output:
push af
push hl
push bc
ld b,a
ld a,e
sub 8
cp 3
jr nc,music_output_restore
ld c,a
ld a,b
ld b,0
ld hl,AY_LEVELS
add hl,bc
ld (hl),a
ld a,(SOUND_OFF)
or a
jr z,music_output_restore
pop bc
pop hl
pop af
push af
xor a
call music_output_port
pop af
ld b,l
ret
music_output_restore:
pop bc
pop hl
pop af
music_output_port:
push bc
ld bc,$fff5
out (c),e
ld c,$f6
out (c),a
pop bc
ld b,l
ret

; S is bit 1 of the A/S/D/F/G keyboard row. One toggle per press/release.
; Zero-initialized SOUND_OFF means sound starts enabled.
sound_keys:
ld bc,$fdfe
in a,(c)
cpl
and 2
ld c,a
ld a,(SOUND_HELD)
cp c
ret z
ld a,c
ld (SOUND_HELD),a
or a
ret z
ld a,(SOUND_OFF)
xor 1
ld (SOUND_OFF),a
ld e,8
ld hl,AY_LEVELS
ld b,3
sound_refresh:
push bc
ld a,(hl)
ld c,a
ld a,(SOUND_OFF)
or a
ld a,c
jr z,sound_refresh_write
xor a
sound_refresh_write:
call music_output_port
pop bc
inc hl
inc e
djnz sound_refresh
ret
