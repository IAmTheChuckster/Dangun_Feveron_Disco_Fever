#!/usr/bin/env python3
"""Dangun Feveron gameplay patcher.

Patches the 68000 program ROMs of your own `dfeveron` dump (cv01-u33.bin / cv01-u34.bin).
Input: a MAME romset zip (dfeveron.zip, or feversos.zip containing the dfeveron/ folder) or a folder
with the loose files. Output: a complete dfeveronfever.zip romset; the patched program ROMs are renamed cv01-u33fever.bin /
cv01-u34fever.bin. The CRCs in mister/Dangun Feveron Disco Fever.mra are updated to match.

    python patch.py feversos.zip                 -> dfeveronfever.zip next to this script
    python patch.py feversos.zip -o out/dfeveronfever.zip
    python patch.py --write-web                  -> copy the patch table and the MRA into index.html

The program is 16-bit: cv01-u34.bin holds the even (high) bytes, cv01-u33.bin the odd (low) bytes.
"""
import argparse, hashlib, json, os, re, sys, zipfile, zlib

# Files of the dfeveron set: name -> (size, crc32, sha1)
FILES = {
    "cv01-u33.bin":        (524288,  "e53a7db3", "ddced29f78dc3cc89038757b6577ba2ba0d8b041"),
    "cv01-u34.bin":        (524288,  "be87f19d", "595239245df3835cdf5a99a6c62480465558d8d3"),
    "cv01-u19.bin":        (4194304, "5f5514da", "53f27364aee544572a82649c9ff29bacc642b732"),
    "cv01-u25.bin":        (4194304, "a6f6a95d", "e1eb45cb5d0e6163edfd9d830633b913fb53c6ca"),
    "cv01-u26.bin":        (4194304, "32edb62a", "3def74e1316b80cc25a8c3ac162cd7bcb8cc807c"),
    "cv01-u49.bin":        (2097152, "d21cdda7", "cace4650de580c3c4a037f1f5c32bfc1846b383c"),
    "cv01-u50.bin":        (2097152, "7a344417", "828bd8f95d2fcc34407e17629ccafc904a4ea12d"),
    "eeprom-dfeveron.bin": (128,     "c3174959", "29b5c94722756481e4f84bfd75dee15fdb5c8cf7"),
}
PATCHED = ("cv01-u33.bin", "cv01-u34.bin")
# Every file the patch changes gets "fever" appended to its name in the output.
OUT_NAMES = {"cv01-u33.bin": "cv01-u33fever.bin", "cv01-u34.bin": "cv01-u34fever.bin"}
ZIP_NAME = "dfeveronfever.zip"
MRA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mister", "Dangun Feveron Disco Fever.mra")

# Build number: bump on every new build and log it in dev_notes/BUILDS.md. `--write-web` copies it to index.html.
BUILD = 15


def text_patch(addr, old, new, desc):
    """Replace a fixed-width text field; the new text is padded with spaces to the old length."""
    if len(new) > len(old):
        raise ValueError(f"{desc}: '{new}' is longer than the {len(old)}-character field")
    return (addr, old.encode().hex(), new.ljust(len(old)).encode().hex(), desc)


# Notice (warning) screen: 28-character lines, each followed by a 0 byte.
NOTICE_TEXT = ("THIS PROJECT IS UNOFFICIAL AND IS NOT AFFILIATED WITH, ENDORSED BY, OR AUTHORIZED BY CAVE. "
               "ALL RIGHTS TO THE ORIGINAL GAME AND ITS ASSOCIATED INTELLECTUAL PROPERTY REMAIN WITH THEIR "
               "RESPECTIVE RIGHTS HOLDERS.")
NOTICE_HEADER = (0x009315, "  THIS GAME IS FOR USE IN   ")
NOTICE_COUNTRIES = [(0x009332 + 0x1D * i, t) for i, t in enumerate([
    "                KOREA ONLY  ", "            HONG KONG ONLY  ", "               TAIWAN ONLY  ",
    "       SOUTHEAST ASIA ONLY  ", "               EUROPE ONLY  ", "                U.S.A ONLY  ",
    "                JAPAN ONLY  "])]
NOTICE_BODY = [(0x0093FD + 0x1D * i, t) for i, t in enumerate([
    "SALES, EXPORT OR OPERATION  ", "OUTSIDE THIS COUNTRY MAY BE ", "CONSTRUED AS COPYRIGHT AND  ",
    "TRADEMARK INFRINGEMENT AND  ", "IS STRICTLY PROHIBITED.     ", "VIOLATOR AND SUBJECT TO     ",
    "SEVERE PENALTIES AND WILL   ", "BE PROSECUTED TO THE FULL   ", "EXTENT OF THE JAM.          "])]
# Footer: "98/09/17 VER." -> "<date from the MRA name> BUILD <n>", right-aligned like the original.
FOOTER = (0x009502, "              98/09/17 VER. ")


def wrap(text, width):
    lines, cur = [], ""
    for w in text.split():
        if cur and len(cur) + 1 + len(w) > width:
            lines.append(cur); cur = w
        else:
            cur = f"{cur} {w}" if cur else w
    return lines + [cur]


def notice_patches():
    lines = wrap(NOTICE_TEXT.upper(), 27)   # 27 keeps one blank column at the right edge, like the original
    if len(lines) > len(NOTICE_BODY):
        raise ValueError("notice text does not fit in the notice body lines")
    out = [text_patch(*NOTICE_HEADER, "", "notice: header line blanked")]
    out += [text_patch(a, t, "", "notice: country line blanked") for a, t in NOTICE_COUNTRIES]
    out += [text_patch(a, t, lines[i] if i < len(lines) else "", f"notice: body line {i + 1}")
            for i, (a, t) in enumerate(NOTICE_BODY)]
    return out


# Patches: (68000 address, original bytes hex, new bytes hex, description). The original bytes are
# checked before anything is written. Keep index.html in sync with `python patch.py --write-web`.
PATCHES = [
    text_patch(0x00622D, "   SALES BY NIHON SYSTEM INC. ", "         NOT FOR SALE", "title screen: NOT FOR SALE"),
] + notice_patches()

# Hold button 1 = slowest speed. The player move code (0xA98A) puts the speed for this frame in $1A(a6)
# (from $39(a6), the selected speed from the table at 0xBFCC: 1A 1E 29 2D), calls the mover at 0x788F2 and
# then restores $1A. We redirect that call to a hook in free space that, while button 1 is held, lowers $1A by
# (selected speed - slowest speed) before jumping to the mover. Release the button and the next frame is back to
# normal. Button state: $101615 bit 4 (P1) / $101617 bit 4 (P2), the inverted inputs the IRQ copies each frame;
# $7(a5) != 0 means player 2 (same test the game uses at 0xA914).
SLOW_HOOK = 0x09E400   # start of the unused 0xFF block 0x9E400-0xAFBFF (CHECKSUM_FILL sits at its end)
SLOW_HOOK_CODE = (
    "4a2d0007"              # tst.b   $7(a5)            ; player 2?
    "660a"                  # bne.s   .p2
    "0839000400101615"      # btst    #4, $101615.l     ; P1 button 1 held
    "6008"                  # bra.s   .chk
    "0839000400101617"      # .p2: btst #4, $101617.l   ; P2 button 1 held
    "670e"                  # .chk: beq.s .go
    "102e0039"              # move.b  $39(a6), d0       ; selected speed
    "90390000bfcc"          # sub.b   $0000BFCC.l, d0   ; minus the slowest speed (table entry 0)
    "912e001a"              # sub.b   d0, $1A(a6)       ; this frame's speed -= difference
    "4ef9000788f2"          # .go: jmp $788F2.l         ; original mover
)
# BOMB-type powerful shot: up to 8 bombs in flight instead of 3. The launch code (0xAE7E) searches the player's
# shot list ($10673A P1 / $1069BA P2, 0x20-byte slots) for a free slot among the first d7+1 slots after the header.
# The update loop (0xB292) and hit check (0xA1CA) treat all 19 slots alike, using each object's own state, so
# bombs can use slots +$20..+$100. Explosion pieces (0xA2FC) take free slots from +$A0, so they share those.
PATCHES += [
    (0x00AE82, "7e02", "7e07", "bomb type: 8 bombs in flight (was 3)"),
]

# Discomen count +2 instead of +1. Each of the five pickup routines (one per discoman object kind) adds 1 to three
# counters per player: P1 $106C62 / $106C3E / $106C3C, P2 $106C82 / $106C42 / $106C40. The value popup and the points
# are read from the counter right after, so they double too (+25, +27, +29 ...). The 999 caps that follow each add
# still apply. $10402A / $10402C (a plain pickup tally) still count 1 per pickup.
# (P1, P2) start of each routine's run of three 6-byte `addq.w #1,abs.l` (routines 0x6CE70, 0x6D440, 0x6EA8E,
# 0x6EDCA, 0x6F3C6)
DISCO_ADDS = [(0x06CEEC, 0x06CE7C), (0x06D4BC, 0x06D44C), (0x06EAA2, 0x06EB14), (0x06EDDE, 0x06EE50),
              (0x06F3DC, 0x06F44E)]
for p1, p2 in DISCO_ADDS:
    for base, counters in ((p1, (0x106C62, 0x106C3E, 0x106C3C)), (p2, (0x106C82, 0x106C42, 0x106C40))):
        for k, ctr in enumerate(counters):
            PATCHES.append((base + 6 * k, f"5279{ctr:08x}", f"5479{ctr:08x}", f"discomen +2: counter ${ctr:06X}"))

def asm(base, items):
    """Tiny assembler for hand-written 68000 code: items are hex strings, ("L", name) labels, or branches
    ("b8", opcode_hex_byte, label) for 8-bit Bcc/BRA/BSR, ("dbra", reg, label). Returns the code as hex."""
    labels, pc = {}, base
    for it in items:   # pass 1: label addresses
        if isinstance(it, str):
            pc += len(it) // 2
        elif it[0] == "L":
            labels[it[1]] = pc
        else:
            pc += 2 if it[0] == "b8" else 4
    out, pc = [], base
    for it in items:   # pass 2: emit
        if isinstance(it, str):
            out.append(it); pc += len(it) // 2
        elif it[0] == "b8":
            d = labels[it[2]] - (pc + 2)
            if not -128 <= d <= 127 or d == 0:
                raise ValueError(f"short branch to {it[2]} out of range ({d})")
            out.append(f"{it[1]}{d & 0xFF:02x}"); pc += 2
        elif it[0] == "dbra":
            d = labels[it[2]] - (pc + 2)
            out.append(f"51c{8 + it[1]:x}{d & 0xFFFF:04x}"); pc += 4
    return "".join(out)


# Bomb -> discomen (Build 5). While a bomb is active ($10E722 != 0):
#  * every enemy bullet ($108572, 70 x 0x40) is removed and a discoman (kind 0, like enemy drops) is spawned at its
#    position (spawner 0x6CD0E, position in d2);
#  * every enemy the bomb destroys drops one discoman (spawner 0x6CCDE, position from a6). The bomb calls the
#    enemy-kill routine 0xA432 (a5 = bomb object $10D3B2) every frame while the enemy's HP is negative, so a byte per
#    enemy slot at BOMB_MARKS remembers it already dropped one; the marks are cleared when no bomb is active;
#  * a "pull" timer (BOMB_PULL) is held at PULL_FRAMES; while it runs, every discoman moves up to PULL_STEP per axis
#    per frame toward the bomb's owner (player object pointer at $10D3C2), and the game's normal pickup collects
#    them on contact.
# The per-frame work hooks the discoman update loop: `lea $10C5F2,a6` at 0x6CE08 becomes `jsr FRAME_HOOK`.
BOMB_PULL, BOMB_MARKS = 0x10B400, 0x10B410   # RAM, inside a block that is never used (always 0 in every dump)
BOMB_TICK = 0x10B402                         # byte, counts frames while a bomb is active (Build 6)
HIT_EVERY = 4                                # Build 6: a discoman per bomb-hit enemy every HIT_EVERY frames (power of 2)
PULL_FRAMES, PULL_STEP = 90, 0x400
KILL_HOOK, FRAME_HOOK = 0x09E440, 0x09E4C0
KILL_HOOK_CODE = asm(KILL_HOOK, [
    "bbfc0010d3b2",            # cmpa.l #$10D3B2, a5        ; called by the bomb?
    ("b8", "66", "orig"),       # bne.s  .orig
    "48e7fffe",                # movem.l d0-d7/a0-a6, -(a7)
    "200e",                    # move.l a6, d0
    "0480001075f2",            # subi.l #$1075F2, d0        ; offset into the enemy list
    ("b8", "65", "skip"),       # bcs.s  .skip
    "ea88",                    # lsr.l  #5, d0              ; slot number (0x20 per slot)
    "0c8000000078",            # cmpi.l #120, d0
    ("b8", "64", "skip"),       # bcc.s  .skip
    f"41f9{BOMB_MARKS:08x}",   # lea    BOMB_MARKS, a0
    "4a300000",                # tst.b  (a0, d0.w)          ; already dropped one?
    ("b8", "66", "skip"),       # bne.s  .skip
    "50f00000",                # st     (a0, d0.w)
    "7000",                    # moveq  #0, d0              ; kind 0
    "4eb90006ccde",            # jsr    $6CCDE              ; spawn a discoman at a6
    ("L", "skip"),
    "4cdf7fff",                # movem.l (a7)+, d0-d7/a0-a6
    ("L", "orig"),
    "2f0d", "2f00",            # move.l a5,-(a7) / move.l d0,-(a7)   ; the instructions we replaced
    "4bf90010673a",            # lea    $10673A, a5
    "4ef90000a43c",            # jmp    $A43C
])
FRAME_HOOK_CODE = asm(FRAME_HOOK, [
    "48e7fffe",                # movem.l d0-d7/a0-a6, -(a7)
    "4a390010e722",            # tst.b  $10E722             ; bomb active?
    ("b8", "67", "nobomb"),     # beq.s  .nobomb
    f"33fc{PULL_FRAMES:04x}{BOMB_PULL:08x}",  # move.w #PULL_FRAMES, BOMB_PULL
    f"5239{BOMB_TICK:08x}",    # addq.b #1, BOMB_TICK       ; frame tick for the per-hit drops
    "47f900108572",            # lea    $108572, a3         ; enemy bullets
    "7e45",                    # moveq  #69, d7
    ("L", "bl"),
    "4a53",                    # tst.w  (a3)
    ("b8", "6a", "bnext"),      # bpl.s  .bnext
    "242b0006",                # move.l $6(a3), d2          ; bullet position
    "7000",                    # moveq  #0, d0              ; kind 0
    "4eb90006cd0e",            # jsr    $6CD0E              ; spawn discoman at d2
    "4253",                    # clr.w  (a3)                ; remove the bullet
    ("L", "bnext"),
    "47eb0040",                # lea    $40(a3), a3
    ("dbra", 7, "bl"),          # dbra   d7, .bl
    ("b8", "60", "home"),       # bra.s  .home
    ("L", "nobomb"),
    f"41f9{BOMB_MARKS:08x}",   # lea    BOMB_MARKS, a0      ; clear the per-enemy marks
    "7e1d",                    # moveq  #29, d7             ; 30 longs = 120 bytes
    ("L", "cl"),
    "4298",                    # clr.l  (a0)+
    ("dbra", 7, "cl"),          # dbra   d7, .cl
    f"4a79{BOMB_PULL:08x}",    # tst.w  BOMB_PULL
    ("b8", "67", "done"),       # beq.s  .done
    f"5379{BOMB_PULL:08x}",    # subq.w #1, BOMB_PULL
    ("L", "home"),
    "22790010d3c2",            # movea.l $10D3C2, a1         ; bomb owner (player object)
    "2009",                    # move.l a1, d0
    ("b8", "67", "done"),       # beq.s  .done
    "4ca900300006",            # movem.w $6(a1), d4-d5      ; target position
    "45f90010c5f2",            # lea    $10C5F2, a2         ; discoman pool
    "7e31",                    # moveq  #49, d7
    ("L", "hl"),
    "4a52",                    # tst.w  (a2)
    ("b8", "6a", "hnext"),      # bpl.s  .hnext
    "082a00070001",            # btst   #7, $1(a2)          ; already collected (value popup)?
    ("b8", "66", "hnext"),      # bne.s  .hnext
    "3004",                    # move.w d4, d0
    "906a0006",                # sub.w  $6(a2), d0
    ("b8", "61", "clamp"),      # bsr.s  .clamp
    "d16a0006",                # add.w  d0, $6(a2)
    "3005",                    # move.w d5, d0
    "906a0008",                # sub.w  $8(a2), d0
    ("b8", "61", "clamp"),      # bsr.s  .clamp
    "d16a0008",                # add.w  d0, $8(a2)
    ("L", "hnext"),
    "45ea0020",                # lea    $20(a2), a2
    ("dbra", 7, "hl"),          # dbra   d7, .hl
    ("L", "done"),
    "4cdf7fff",                # movem.l (a7)+, d0-d7/a0-a6
    "4df90010c5f2",            # lea    $10C5F2, a6         ; the instruction we replaced
    "4e75",                    # rts
    ("L", "clamp"),
    f"0c40{PULL_STEP:04x}",    # cmpi.w #STEP, d0
    ("b8", "6f", "c1"),         # ble.s  .c1
    f"303c{PULL_STEP:04x}",    # move.w #STEP, d0
    ("L", "c1"),
    f"0c40{-PULL_STEP & 0xFFFF:04x}",  # cmpi.w #-STEP, d0
    ("b8", "6c", "c2"),         # bge.s  .c2
    f"303c{-PULL_STEP & 0xFFFF:04x}",  # move.w #-STEP, d0
    ("L", "c2"),
    "4e75",                    # rts
])

# Discoman counter starts (and resets) at 0 instead of 1, so the first pickup is +2 and the values are even
# (2, 4 ... 160), landing on round numbers. Every `move.w #1,counter` (game/stage start, and the reset when a discoman falls off the
# screen, which breaks the chain) becomes #0, plus the `moveq #1,d0` at 0x395E that sets all six counters.
DISCO_RESETS = {   # instruction address: counter
    0x0016D0: 0x106C3E, 0x0016D8: 0x106C42,
    0x008294: 0x106C3C, 0x00829C: 0x106C40, 0x0082A4: 0x106C3E, 0x0082AC: 0x106C42,
    0x00869E: 0x106C3C, 0x0086A6: 0x106C3E, 0x0086CE: 0x106C40, 0x0086D6: 0x106C42,
    0x06D004: 0x106C3C, 0x06D00C: 0x106C40, 0x06D0FE: 0x106C3C, 0x06D106: 0x106C40,
    0x06D17E: 0x106C3C, 0x06D186: 0x106C40, 0x06D1FC: 0x106C3C, 0x06D204: 0x106C40,
    0x06D320: 0x106C3C, 0x06D328: 0x106C40, 0x06D676: 0x106C3C, 0x06D67E: 0x106C40,
}
for addr, ctr in DISCO_RESETS.items():
    PATCHES.append((addr, f"33fc0001{ctr:08x}", f"33fc0000{ctr:08x}", f"discomen start at 0: ${ctr:06X}"))
PATCHES.append((0x00395E, "7001", "7000", "discomen start at 0: all six counters"))

# Build 6: every bomb hit drops discomen, not just kills. The three blast routines mark each enemy they hit with
# `move.w $24(a5),d4 / or.w d4,(a6)` (6 bytes) every frame; that pair becomes `jsr HIT_HOOK`, which does the same
# marking and, on every HIT_EVERY-th frame of the bomb (BOMB_TICK), spawns a discoman at the enemy (a6). The kill
# drop (KILL_HOOK) and the bullet conversion stay as they are.
HIT_HOOK = 0x09E5C0
HIT_HOOK_CODE = asm(HIT_HOOK, [
    "382d0024",                # move.w $24(a5), d4         ; the instructions we replaced
    "8956",                    # or.w   d4, (a6)
    "48e7fffe",                # movem.l d0-d7/a0-a6, -(a7)
    f"1039{BOMB_TICK:08x}",    # move.b BOMB_TICK, d0
    f"0200{HIT_EVERY - 1:04x}",  # andi.b #HIT_EVERY-1, d0
    ("b8", "66", "out"),        # bne.s  .out
    "7000",                    # moveq  #0, d0              ; kind 0
    "4eb90006ccde",            # jsr    $6CCDE              ; spawn a discoman at the enemy (a6)
    ("L", "out"),
    "4cdf7fff",                # movem.l (a7)+, d0-d7/a0-a6
    "4e75",                    # rts
])
assert FRAME_HOOK + len(FRAME_HOOK_CODE) // 2 <= HIT_HOOK and KILL_HOOK + len(KILL_HOOK_CODE) // 2 <= FRAME_HOOK
PATCHES += [(HIT_HOOK, "ff" * (len(HIT_HOOK_CODE) // 2), HIT_HOOK_CODE, "bomb hits drop discomen (hook)")]
PATCHES += [(a, "382d00248956", f"4eb9{HIT_HOOK:08x}", "bomb hits drop discomen: blast routine")
            for a in (0x009DE0, 0x009E92, 0x009F16)]

# Build 7: the popup/score value counter (P1 $106C3C, P2 $106C40) is capped at 9999 instead of 999, so the "+"
# values keep growing past 999 (+1000, +1002 ...). The HUD counter (P1 $106C3E, P2 $106C42, the red box) keeps its
# 999 cap. Each pickup routine clamps with `cmpi.w #1000,ctr` then `move.w #999,ctr`.
VALUE_CAPS = [  # (cmpi address, move address, counter)
    (0x06CEA6, 0x06CEB0, 0x106C40), (0x06CF16, 0x06CF20, 0x106C3C), (0x06D476, 0x06D480, 0x106C40),
    (0x06D4E6, 0x06D4F0, 0x106C3C), (0x06EACC, 0x06EAD6, 0x106C3C), (0x06EB3E, 0x06EB48, 0x106C40),
    (0x06EE08, 0x06EE12, 0x106C3C), (0x06EE7A, 0x06EE84, 0x106C40), (0x06F406, 0x06F410, 0x106C3C),
    (0x06F478, 0x06F482, 0x106C40),
]
for c, m, ctr in VALUE_CAPS:
    PATCHES.append((c, f"0c7903e8{ctr:08x}", f"0c792710{ctr:08x}", f"value cap 9999: compare ${ctr:06X}"))
    PATCHES.append((m, f"33fc03e7{ctr:08x}", f"33fc270f{ctr:08x}", f"value cap 9999: clamp ${ctr:06X}"))

# Build 7: big gold popups at multiples of 100 drawn 1.5x, at multiples of 1000 drawn 2x. The big popup draw
# (0x6FE1A, list $10DFA2, a2 = popup object) builds its zoom in d6 at 0x6FE2C: `move.l #$1000000,d6 /
# move.w $6FDBA(pc,d1.w),d6 / swap d6` (pop-in table, then 0x100 = 1.0). That becomes `jsr ZOOM_HOOK` + nops: the
# hook does the same, then scales both zoom words by the popup's BCD value ($2(a2)), and stores the digit spacing
# in the popup object's unused words $1C (between digits, stock 0x180) and $1E (after '+', stock 0x200). The four
# `subi.w #n,d4` spacing steps become `sub.w $1C(a2),d4` / `sub.w $1E(a2),d4` (same 4 bytes). The sprite routine
# 0x79E9A re-centres each zoomed sprite.
ZOOM_HOOK = 0x09E600
ZOOM_HOOK_CODE = asm(ZOOM_HOOK, [
    "2f08",                    # move.l a0, -(a7)
    "41f90006fdba",            # lea    $6FDBA, a0          ; pop-in zoom table
    "2c3c01000000",            # move.l #$1000000, d6
    "3c301000",                # move.w (a0, d1.w), d6
    "4846",                    # swap   d6                  ; d6 = table : 0x100 (as stock)
    "357c0180001c",            # move.w #$180, $1C(a2)      ; stock spacing
    "357c0200001e",            # move.w #$200, $1E(a2)
    "342a0002",                # move.w $2(a2), d2          ; popup value, BCD
    "02420fff",                # andi.w #$FFF, d2           ; multiple of 1000?
    ("b8", "67", "x2"),         # beq.s  .x2
    "342a0002",                # move.w $2(a2), d2
    "024200ff",                # andi.w #$FF, d2            ; multiple of 100?
    ("b8", "66", "done"),       # bne.s  .done
    "3406", "e24a", "dc42",    # move.w d6,d2 / lsr.w #1,d2 / add.w d2,d6   ; x1.5
    "4846",                    # swap   d6
    "3406", "e24a", "dc42",    # move.w d6,d2 / lsr.w #1,d2 / add.w d2,d6
    "4846",                    # swap   d6
    "357c0240001c",            # move.w #$240, $1C(a2)
    "357c0300001e",            # move.w #$300, $1E(a2)
    ("b8", "60", "done"),       # bra.s  .done
    ("L", "x2"),
    "dc46", "4846", "dc46", "4846",  # add.w d6,d6 / swap / add.w d6,d6 / swap   ; x2
    "357c0300001c",            # move.w #$300, $1C(a2)
    "357c0400001e",            # move.w #$400, $1E(a2)
    ("L", "done"),
    "205f",                    # movea.l (a7)+, a0
    "4e75",                    # rts
])
assert HIT_HOOK + len(HIT_HOOK_CODE) // 2 <= ZOOM_HOOK
PATCHES += [
    (ZOOM_HOOK, "ff" * (len(ZOOM_HOOK_CODE) // 2), ZOOM_HOOK_CODE, "big popups 1.5x/2x (hook)"),
    (0x06FE2C, "2c3c010000003c3b10864846", f"4eb9{ZOOM_HOOK:08x}4e714e714e71", "big popups: zoom setup"),
    (0x06FE62, "04440200", "986a001e", "big popups: spacing after '+'"),
]
PATCHES += [(a, "04440180", "986a001c", "big popups: spacing between digits") for a in (0x06FEB6, 0x06FEC8, 0x06FF08)]

# Build 8: the top-left score box shows the running total instead of the current stage's score. The game keeps a
# score per stage (P1 $103FAE[stage], P2 $103FCE[stage], BCD longs; stage index $1052D8): the live score
# ($103DE8 / $103DEC) is loaded from the current stage's slot at stage start and saved back at stage end, so the box
# restarts at 0 each stage. Display only: the box's loads `move.l $103DE8,d7` (0x64948) and `move.l $103DEC,d7`
# (0x64984) become calls that return the BCD sum of the earlier stages' slots plus the live score. Scoring, stage
# records, STAGE HIGH and the ranking are untouched.
SCORE_BUF = 0x10B408                         # RAM, 4-byte BCD work buffer
SCORE_HOOK = 0x09E680
SCORE_HOOK_CODE = asm(SCORE_HOOK, [
    "48e780e0",                # P1: movem.l d0/a0-a2, -(a7)
    "2e3900103de8",            #     move.l $103DE8, d7     ; live score
    "43f900103fae",            #     lea    $103FAE, a1     ; P1 stage slots
    ("b8", "60", "body"),       #     bra.s  .body
    ("L", "p2"),
    "48e780e0",                # P2: movem.l d0/a0-a2, -(a7)
    "2e3900103dec",            #     move.l $103DEC, d7
    "43f900103fce",            #     lea    $103FCE, a1     ; P2 stage slots
    ("L", "body"),
    f"23c7{SCORE_BUF:08x}",    # move.l d7, SCORE_BUF
    "3039001052d8",            # move.w $1052D8, d0         ; current stage index = number of earlier stages
    ("b8", "60", "chk"),        # bra.s  .chk
    ("L", "lp"),
    f"41f9{SCORE_BUF + 4:08x}",  # lea  SCORE_BUF+4, a0
    "45e90004",                # lea    $4(a1), a2
    "023c00ef",                # andi   #$EF, ccr            ; clear X for the BCD add
    "c10a", "c10a", "c10a", "c10a",  # abcd -(a2),-(a0) x4   ; SCORE_BUF += slot (BCD)
    "5889",                    # addq.l #4, a1
    ("L", "chk"),
    "5340",                    # subq.w #1, d0
    ("b8", "64", "lp"),         # bcc.s  .lp
    f"2e39{SCORE_BUF:08x}",    # move.l SCORE_BUF, d7
    "4cdf0701",                # movem.l (a7)+, d0/a0-a2
    "4e75",                    # rts
])
SCORE_HOOK_P2 = SCORE_HOOK + 18   # address of the .p2 entry (4 + 6 + 6 + 2 bytes)
assert ZOOM_HOOK + len(ZOOM_HOOK_CODE) // 2 <= SCORE_HOOK
PATCHES += [
    (SCORE_HOOK, "ff" * (len(SCORE_HOOK_CODE) // 2), SCORE_HOOK_CODE, "score box shows the running total (hook)"),
    (0x064948, "2e3900103de8", f"4eb9{SCORE_HOOK:08x}", "score box: P1 running total"),
    (0x064984, "2e3900103dec", f"4eb9{SCORE_HOOK_P2:08x}", "score box: P2 running total"),
]

# Builds 9-10: the score box fits a 7- or 8-digit running total. The frame is three sprites drawn at 0x63D24 (P1;
# P2 mirrored at 0x640E6): middle piece 0x099F, left end 0x099B, right end 0x09A1. The game moves the middle and
# right end out by 0x200 for 6+ digits but tested the stage score and had no further steps. Now:
#  * the frame's score read (`move.l $103DE8/$103DEC,d0`) calls VAL, which returns the running total (SCORE_HOOK)
#    and sets a size level in BOX7 / BOX7+1: 0 = up to 6 digits, 1 = 7 digits, 2 = 8 digits;
#  * after the middle piece, EXTRA draws one extra middle piece per level, 0x200 apart (replaces
#    `move.w #$99B,d2 / move.w #$202,d5`, which it repeats);
#  * the right end moves out 0x200 per level (replaces `move.w #$201,d5 / addi|subi.w #n,d4`).
BOX7 = 0x10B490                              # RAM: byte P1 size level, BOX7+1 for P2


def box_hooks(base, player):
    """Return (code hex, {label: address}) for one player's VAL / EXTRA / RIGHT hooks."""
    flag = BOX7 + player
    step = "06440200" if player == 0 else "04440200"        # addi / subi.w #$200, d4 (P2 grows the other way)
    right = "06440a00" if player == 0 else "04440600"       # the right-end offset the game used
    score = SCORE_HOOK if player == 0 else SCORE_HOOK_P2
    items = [
        ("L", "val"),
        "2f07", f"4eb9{score:08x}", "2007", "2e1f",          # move.l d7,-(a7) / jsr score / move.l d7,d0 / restore d7
        "2f00", f"4239{flag:08x}",                           # push d0 / clr.b level
        "02800f000000", ("b8", "67", "v1"),                   # andi.l #$0F000000,d0 / beq.s .v1   ; 7 digits?
        f"13fc0001{flag:08x}",                               # move.b #1, level
        ("L", "v1"),
        "2017", "0280f0000000", ("b8", "67", "v2"),           # move.l (a7),d0 / andi.l #$F0000000,d0 / beq.s .v2
        f"13fc0002{flag:08x}",                               # move.b #2, level              ; 8 digits
        ("L", "v2"),
        "201f", "4e75",                                      # pop d0 / rts
        ("L", "extra"),
        f"4a39{flag:08x}", ("b8", "67", "noext"),             # tst.b level / beq.s .noext
        "48a79800",                                          # movem.w d0/d3-d4, -(a7)
        step, ("b8", "61", "emit"),                           # one more middle piece, 0x200 further out
        f"0c390002{flag:08x}", ("b8", "66", "e1"),            # cmpi.b #2, level / bne.s .e1
        step, ("b8", "61", "emit"),                           # and another for 8 digits
        ("L", "e1"),
        "4c9f0019",                                          # movem.w (a7)+, d0/d3-d4
        ("L", "noext"),
        "343c099b", "3a3c0202", "4e75",                      # the instructions we replaced / rts
        ("L", "emit"),                                       # draw d2/d5 at d3,d4 the way the game does
        "48a79800",                                          # movem.w d0/d3-d4, -(a7)
        "30390010518a", "0c400600", "6504", "303c0600",      # d0 = min($10518A, 0x600)
        "9840", "d640",                                      # sub.w d0,d4 / add.w d0,d3
        "2f08", "207900101596",                              # move.l a0,-(a7) / movea.l $101596,a0
        "3083", "31440002", "31410004", "31420006",          # x, y, attr, tile (0x099F)
        "217c010001000008", "3145000c",                      # zoom 1.0, size (0x0201)
        "41e80010", "23c800101596", "205f",                  # next entry / store pointer / restore a0
        "4c9f0019", "4e75",                                  # movem.w (a7)+, d0/d3-d4 / rts
        ("L", "right"),
        "3a3c0201", right,                                   # the instructions we replaced
        f"4a39{flag:08x}", ("b8", "67", "rdone"),             # tst.b level / beq.s .rdone
        step,                                                # right end 0x200 further out
        f"0c390002{flag:08x}", ("b8", "66", "rdone"),         # cmpi.b #2, level / bne.s .rdone
        step,
        ("L", "rdone"),
        "4e75",
    ]
    if player == 1:   # P2 digits start further left by 0x200 per level (its box grows to the left)
        items += [
            ("L", "dstart"),
            f"4eb9{base:08x}",                               # jsr .val (the block start) ; d0 = total, level set
            f"4a39{flag:08x}", ("b8", "67", "dsout"),         # tst.b level / beq.s .dsout
            "04440200",                                      # subi.w #$200, d4
            f"0c390002{flag:08x}", ("b8", "66", "dsout"),     # cmpi.b #2, level / bne.s .dsout
            "04440200",
            ("L", "dsout"),
            "4e75",
        ]
    code = asm(base, items)
    labels, pc = {}, base
    for it in items:
        if isinstance(it, str):
            pc += len(it) // 2
        elif it[0] == "L":
            labels[it[1]] = pc
        else:
            pc += 2 if it[0] == "b8" else 4
    return code, labels


BOX_HOOK_P1 = 0x09E6E0
BOX_CODE_P1, BOX_L1 = box_hooks(BOX_HOOK_P1, 0)
BOX_HOOK_P2 = BOX_HOOK_P1 + len(BOX_CODE_P1) // 2 + 0x10
BOX_CODE_P2, BOX_L2 = box_hooks(BOX_HOOK_P2, 1)
assert SCORE_HOOK + len(SCORE_HOOK_CODE) // 2 <= BOX_HOOK_P1
PATCHES += [
    (BOX_HOOK_P1, "ff" * (len(BOX_CODE_P1) // 2), BOX_CODE_P1, "score box: P1 hooks"),
    (BOX_HOOK_P2, "ff" * (len(BOX_CODE_P2) // 2), BOX_CODE_P2, "score box: P2 hooks"),
    (0x063D24, "203900103de8", f"4eb9{BOX_L1['val']:08x}", "score box: P1 size by running total"),
    (0x063DA8, "343c099b3a3c0202", f"4eb9{BOX_L1['extra']:08x}4e71", "score box: P1 extra middle pieces"),
    (0x063E0A, "3a3c020106440a00", f"4eb9{BOX_L1['right']:08x}4e71", "score box: P1 right end"),
    (0x0640E6, "203900103dec", f"4eb9{BOX_L2['val']:08x}", "score box: P2 size by running total"),
    (0x064162, "343c099b3a3c0202", f"4eb9{BOX_L2['extra']:08x}4e71", "score box: P2 extra middle pieces"),
    (0x0641BC, "3a3c020104440600", f"4eb9{BOX_L2['right']:08x}4e71", "score box: P2 right end"),
]

# Build 10: score digits. The renderer (0x649C2) decides the layout from the high word of the BCD score:
# 6+ digits start half a digit left, and 7 digits go through a separate path (0x64BBE) that squeezes them (spacing
# 0x1C0, zoom 0x00E0) to fit the old frame, which pushed the first digit under the frame left end. The 8th digit
# (top nibble) was masked out and never drawn. Now:
#  * the 7-digit path uses normal spacing 0x200 and zoom 1.0, filling the widened frame;
#  * the masks include the top nibble (0x0FFF->0xFFFF, 0x0FF0->0xFFF0, 0x0F00->0xFF00), so 8-digit scores take the
#    7-digit path, where DIG8 (replacing its first `move.w d7,d2 / lsr.w #8,d2 / andi.w #$F,d2`) draws the 8th
#    digit first;
#  * P2 digits start further left per level (its `move.l $103DEC,d0` at 0x649A6 calls BOX_L2['dstart'], which
#    also returns the running total for the game's own 6-digit test).
DIG8_HOOK = BOX_HOOK_P2 + len(BOX_CODE_P2) // 2 + 0x10
DIG8_CODE = asm(DIG8_HOOK, [
    "3407", "0242f000", ("b8", "67", "no8"),   # move.w d7,d2 / andi.w #$F000,d2 / beq.s .no8
    "e95a",                                   # rol.w #4, d2               ; 8th digit
    "7001", "3206",                           # moveq #1,d0 / move.w d6,d1  ; non-zero digit colour
    "06420258",                               # addi.w #$258, d2
    "4eb900064c7c",                           # jsr $64C7C                 ; the game digit emitter
    "06440200",                               # addi.w #$200, d4
    ("L", "no8"),
    "3407", "e04a", "0242000f",               # the instructions we replaced (sets Z for the beq after)
    "4e75",
])
PATCHES += [
    (DIG8_HOOK, "ff" * (len(DIG8_CODE) // 2), DIG8_CODE, "score digits: 8th digit (hook)"),
    (0x064BBE, "3407e04a0242000f", f"4eb9{DIG8_HOOK:08x}4e71", "score digits: draw the 8th digit"),
    (0x064A04, "02420fff", "0242ffff", "score digits: include the 8th digit"),
    (0x064A10, "02420ff0", "0242fff0", "score digits: include the 8th digit"),
    (0x064A16, "02420f00", "0242ff00", "score digits: 7/8-digit path"),
    (0x064C92, "217c010000e00008", "217c010001000008", "score digits: 7-digit path full width"),
    (0x0649A6, "203900103dec", f"4eb9{BOX_L2['dstart']:08x}", "score digits: P2 start per box size"),
]
PATCHES += [(a, "064401c0", "06440200", "score digits: 7-digit path normal spacing")
            for a in (0x064BD4, 0x064BEE, 0x064C06, 0x064C26, 0x064C46, 0x064C66)]

# Build 10: remove the word "STAGE" from "STAGE HIGH /" (it would overlap the wider score box). The label is one
# sprite of 4 tiles (tile 0x0FE9, size 0x0104) drawn at 0x644E4. Draw only its last STAGE_SKIP_KEEP tiles: start
# STAGE_SKIP tiles in, shorten it, and move it along by the skipped tiles (0x400 per 16-pixel tile) so the rest stays
# where it was.
STAGE_SKIP = 2
PATCHES += [
    (0x0644E4, "343c0fe9", f"343c{0x0FE9 + STAGE_SKIP:04x}", "remove STAGE: first tile"),
    (0x0644EC, "383c0ec0", f"383c{0x0EC0 + 0x400 * STAGE_SKIP:04x}", "remove STAGE: position"),
    (0x064502, "3a3c0104", f"3a3c{0x0104 - STAGE_SKIP:04x}", "remove STAGE: width"),
]

# Build 11: an extra life every EXTEND_EVERY discomen collected (stock: once, at 2000). The pickup routine at
# 0x6D41C counts every discoman collected by either player in $10510C (not on the final stage), and when it equals
# 2000 sets the 1UP flag ($105112 bit 0); 0x6100A then drops a 1UP item that gives the life when collected. The
# compare value becomes EXTEND_EVERY, and setting the flag (`ori.w #1,$105112`, 8 bytes) becomes a call that also
# resets the counter, so it repeats.
EXTEND_EVERY = 1000
EXTEND_HOOK = DIG8_HOOK + len(DIG8_CODE) // 2 + 0x10
EXTEND_CODE = asm(EXTEND_HOOK, [
    "007900010010 5112".replace(" ", ""),   # ori.w  #1, $105112         ; the instruction we replaced (1UP flag)
    "42b90010510c",                          # clr.l  $10510C             ; count the next EXTEND_EVERY from 0
    "4e75",                                  # rts
])
PATCHES += [
    (EXTEND_HOOK, "ff" * (len(EXTEND_CODE) // 2), EXTEND_CODE, "1UP every 1000 discomen (hook)"),
    (0x06D42C, "0cb9000007d00010510c", f"0cb9{EXTEND_EVERY:08x}0010510c", "1UP every 1000 discomen: threshold"),
    (0x06D438, "0079000100105112", f"4eb9{EXTEND_HOOK:08x}4e71", "1UP every 1000 discomen: repeat"),
]

# Build 12: a bomb item every BOMB_ITEM_EVERY discomen collected. Uses the same pickup count as the 1UP ($10510C,
# incremented at 0x6D426 for every discoman collected by either player, not on the final stage). That increment
# becomes a call that does it and, when the count divides by BOMB_ITEM_EVERY, spawns item kind 3 (the bomb pickup;
# its handler at 0x6ECF4 adds 1 to the bomb stock, max 4) through the item spawner 0x6E5C0 at a fixed position
# near the 1UP drop point. The count resets every EXTEND_EVERY (a multiple of BOMB_ITEM_EVERY), so no extra counter.
BOMB_ITEM_EVERY = 100
assert EXTEND_EVERY % BOMB_ITEM_EVERY == 0
BOMB_ITEM_HOOK = EXTEND_HOOK + len(EXTEND_CODE) // 2 + 0x10
BOMB_ITEM_CODE = asm(BOMB_ITEM_HOOK, [
    "52b90010510c",            # addq.l #1, $10510C          ; the instruction we replaced
    "48e7e0e0",                # movem.l d0-d2/a0-a2, -(a7)
    "20390010510c",            # move.l $10510C, d0
    f"80fc{BOMB_ITEM_EVERY:04x}",  # divu.w #BOMB_ITEM_EVERY, d0
    "4840", "4a40",            # swap d0 / tst.w d0           ; remainder
    ("b8", "66", "out"),        # bne.s  .out
    "7003",                    # moveq  #3, d0                ; item kind 3 = bomb
    "243c54002400",            # move.l #$54002400, d2        ; drop position (1UP uses $54001E00)
    "4eb90006e5c0",            # jsr    $6E5C0                ; item spawner
    ("L", "out"),
    "4cdf0707",                # movem.l (a7)+, d0-d2/a0-a2
    "4e75",                    # rts
])
PATCHES += [
    (BOMB_ITEM_HOOK, "ff" * (len(BOMB_ITEM_CODE) // 2), BOMB_ITEM_CODE, "bomb item every 250 discomen (hook)"),
    (0x06D426, "52b90010510c", f"4eb9{BOMB_ITEM_HOOK:08x}", "bomb item every 250 discomen: pickup count"),
]

# Build 13: "DISCO FEVER" on the title screen, above PLEASE INSERT COIN. Title text is drawn by 0x650E (a0 = string,
# d1 = colour, d3 = line height, larger = higher on the rotated screen; d4 = start, 0x200 per character).
# PLEASE INSERT COIN is drawn at height 0x2200 (0x503C) and the animated PRESS START letters are set up at 0x2200
# (0x63B0); both move down to TITLE_PLEASE_Y. DISCO FEVER goes at TITLE_DISCO_Y, just below the purple Japanese
# characters, in the C BUTTON colour. It is drawn in both title states by hooking the `btst #2,$10161D` (the
# C-button check just before the C BUTTON line) at 0x4FF2 and 0x60E8: the hook draws the line, then repeats the test.
TITLE_DISCO_Y, TITLE_PLEASE_Y = 0x2400, 0x1E00
TITLE_TEXT = "DISCO FEVER"
TITLE_HOOK = BOMB_ITEM_HOOK + len(BOMB_ITEM_CODE) // 2 + 0x10
_title_str_addr = TITLE_HOOK + 48                # string placed right after the code (code is < 48 bytes)
TITLE_CODE = asm(TITLE_HOOK, [
    "48e7fffe",                                  # movem.l d0-d7/a0-a6, -(a7)
    f"41f9{_title_str_addr:08x}",                # lea    TITLE_TEXT, a0
    "323c3a30",                                  # move.w #$3A30, d1          ; C BUTTON colour
    f"363c{TITLE_DISCO_Y:04x}",                  # move.w #TITLE_DISCO_Y, d3
    f"383c{(30 - len(TITLE_TEXT)) * 0x100:04x}", # move.w #start, d4          ; centred on the 30-column line
    "4eb90000650e",                              # jsr    $650E               ; title text routine
    "4cdf7fff",                                  # movem.l (a7)+, d0-d7/a0-a6
    "083900020010161d",                          # btst   #2, $10161D         ; the instruction we replaced
    "4e75",                                      # rts
])
assert len(TITLE_CODE) // 2 <= 48
TITLE_DATA = TITLE_CODE + "4e71" * ((48 - len(TITLE_CODE) // 2) // 2) + (TITLE_TEXT.encode() + b"\0\0").hex()
PATCHES += [
    (TITLE_HOOK, "ff" * (len(TITLE_DATA) // 2), TITLE_DATA, "title: DISCO FEVER (hook + text)"),
    (0x004FF2, "083900020010161d", f"4eb9{TITLE_HOOK:08x}4e71", "title: draw DISCO FEVER (no credit)"),
    (0x0060E8, "083900020010161d", f"4eb9{TITLE_HOOK:08x}4e71", "title: draw DISCO FEVER (credit)"),
    (0x00503C, "363c2200", f"363c{TITLE_PLEASE_Y:04x}", "title: PLEASE INSERT COIN lower"),
    (0x0063B0, "337c22000000", f"337c{TITLE_PLEASE_Y:04x}0000", "title: PRESS START lower"),
]

# Build 15: the TLB (true last boss, stage index 5) is unlocked even if you died. When the final stage (index 4)
# starts, 0xF94 sets the TLB flag (`st.b $37(a5)`) only if $10E816 == 0, neither player continued ($103FA4 /
# $103FA8 still 0x100) and neither player died ($10529C / $10529E still 0; set to 1 on respawn at 0xC22A / 0xC29A).
# The two death tests' branches become nops. (The no-continue rule is left as it is.)
# NOT ENABLED YET: a test run that died still didn't reach the TLB, so this isn't proven. Set TLB_ANY_DEATHS = True
# once it is confirmed in MAME.
TLB_ANY_DEATHS = False
if TLB_ANY_DEATHS:
    PATCHES += [
        (0x000FC8, "66000010", "4e714e71", "TLB even if you died: P1 death check"),
        (0x000FD2, "66000006", "4e714e71", "TLB even if you died: P2 death check"),
    ]

PATCHES += [
    (KILL_HOOK, "ff" * (len(KILL_HOOK_CODE) // 2), KILL_HOOK_CODE, "bomb kills drop a discoman (hook)"),
    (0x00A432, "2f0d2f004bf90010673a", f"4ef9{KILL_HOOK:08x}4e714e71", "bomb kills drop a discoman: enemy-kill entry"),
    (FRAME_HOOK, "ff" * (len(FRAME_HOOK_CODE) // 2), FRAME_HOOK_CODE, "bomb: bullets -> discomen, pull discomen (hook)"),
    (0x06CE08, "4df90010c5f2", f"4eb9{FRAME_HOOK:08x}", "bomb: per-frame hook in the discoman update loop"),
    # The discoman setup (0x6DA3C) deletes any new discoman while the bomb object $10D3B2 is active, so stock
    # bombs never leave discomen. Skip that check (bpl -> bra) so bomb-made discomen survive.
    (0x06DA42, "6a08", "6008", "bomb: allow discomen to spawn during a bomb"),
]

PATCHES += [
    (SLOW_HOOK, "ff" * (len(SLOW_HOOK_CODE) // 2), SLOW_HOOK_CODE, "hold button 1: slowest speed (hook)"),
    (0x00A9A2, "4eb9000788f2", "4eb9" + f"{SLOW_HOOK:08x}", "hold button 1: player move calls the hook"),
]

# The boot ROM check adds up the even and the odd program bytes and compares them with words stored at
# 0x8CAA / 0x8CAE. Instead of changing the check, both sums are kept as they were by lowering bytes in
# this unused 0xFF area (part of the free block 0x9E400-0xAFBFF).
CHECKSUM_FILL = (0x0AF000, 0x0AFC00)


def mra_date(mra):
    """The YY/MM/DD date in the MRA <name>, e.g. 'Dangun Feveron Disco Fever (26/11/21 Build)'."""
    m = re.search(r"<name>[^<]*?(\d\d/\d\d/\d\d)[^<]*</name>", mra)
    if not m:
        raise ValueError("no YY/MM/DD date found in the MRA <name>")
    return m.group(1)


def footer_patch(date, build):
    addr, old = FOOTER
    text = f"{date} BUILD {build} "
    if len(text) > len(old):
        raise ValueError("footer text too long")
    return (addr, old.encode().hex(), text.rjust(len(old)).encode().hex(), "notice: footer date and build")


def crc(b):
    return "%08x" % (zlib.crc32(b) & 0xFFFFFFFF)


def sha1(b):
    return hashlib.sha1(b).hexdigest()


def read_input(path):
    """Return {name: bytes} for every known file found (matched by file name, then by CRC)."""
    raw = {}
    if os.path.isdir(path):
        for root, _, names in os.walk(path):
            for n in names:
                p = os.path.join(root, n)
                if os.path.getsize(p) in {v[0] for v in FILES.values()}:
                    with open(p, "rb") as f:
                        raw[os.path.relpath(p, path).replace("\\", "/")] = f.read()
    else:
        with zipfile.ZipFile(path) as z:
            for i in z.infolist():
                if not i.is_dir() and i.file_size in {v[0] for v in FILES.values()}:
                    raw[i.filename] = z.read(i)
    out = {}
    for p, data in raw.items():
        n = p.split("/")[-1].lower()
        if n in FILES and n not in out:
            out[n] = data
    for p, data in raw.items():
        c = crc(data)
        for n, (size, ecrc, _) in FILES.items():
            if n not in out and len(data) == size and c == ecrc:
                out[n] = data
    return out


def apply_patches(u33, u34, date, build=BUILD):
    """Interleave, patch, keep the ROM-check sums, split. Returns (new_u33, new_u34)."""
    prog = bytearray(len(u33) * 2)
    prog[0::2], prog[1::2] = u34, u33
    sums = (sum(prog[0::2]) & 0xFFFF, sum(prog[1::2]) & 0xFFFF)
    for addr, old, new, desc in PATCHES + [footer_patch(date, build)]:
        old, new = bytes.fromhex(old), bytes.fromhex(new)
        if len(old) != len(new):
            raise ValueError(f"{addr:06x} ({desc}): old and new lengths differ")
        if prog[addr:addr + len(old)] != old:
            raise ValueError(f"{addr:06x} ({desc}): original bytes not found; is this the right dump?")
        prog[addr:addr + len(new)] = new
    lo, hi = CHECKSUM_FILL
    if any(b != 0xFF for b in prog[lo:hi]):
        raise ValueError("checksum fill area is not empty")
    for lane in (0, 1):
        need = (sum(prog[lane::2]) - sums[lane]) & 0xFFFF
        for a in range(lo + lane, hi, 2):
            if not need:
                break
            take = min(need, 0xFF)
            prog[a] = 0xFF - take
            need -= take
        if need:
            raise ValueError("checksum fill area too small")
    assert (sum(prog[0::2]) & 0xFFFF, sum(prog[1::2]) & 0xFFFF) == sums
    return bytes(prog[1::2]), bytes(prog[0::2])


def check(files):
    ok = True
    for n, (size, ecrc, esha) in FILES.items():
        d = files.get(n)
        if d is None:
            status = "MISSING" if n in PATCHED else "not in input (copied files only)"
            ok = ok and n not in PATCHED
        elif len(d) != size or crc(d) != ecrc or sha1(d) != esha:
            status, ok = f"BAD (crc {crc(d)})", ok and n not in PATCHED
        else:
            status = "ok"
        print(f"  {n:22} {ecrc}  {status}")
    return ok


def mra_with_crcs(mra, crcs):
    """Point the program-ROM parts of the MRA at the patched file names and CRCs."""
    for n, out in OUT_NAMES.items():
        stem = n[:-4]
        mra, count = re.subn(r'<part name="' + stem + r'(?:fever)?\.bin" crc="[0-9a-fA-F]{8}"',
                             f'<part name="{out}" crc="{crcs[n]}"', mra)
        if count != 1:
            raise ValueError(f"{n} part not found in the MRA")
    return mra_with_build(mra, BUILD)


def mra_with_build(mra, build):
    """Put the build number in the MRA <name>: '... (26/11/21 Build)' -> '... (26/11/21 Build 1)'."""
    mra, count = re.subn(r"(<name>[^<]*?\bBuild)(?: \d+)?", lambda m: f"{m.group(1)} {build}", mra, count=1)
    if count != 1:
        raise ValueError("no 'Build' found in the MRA <name>")
    return mra


def write_web(html_path):
    with open(html_path, encoding="utf-8") as f:
        html = f.read()
    rows = ",\n".join(f"  [0x{a:06X}, {json.dumps(o)}, {json.dumps(n)}, {json.dumps(d)}]" for a, o, n, d in PATCHES)
    block = "const PATCHES = [   // generated by patch.py --write-web: [address, old hex, new hex, description]\n" + \
            (rows + ",\n" if rows else "") + "];"
    new, count = re.subn(r"const PATCHES = \[.*?\n\];", lambda m: block, html, flags=re.S)
    if count != 1:
        sys.exit("PATCHES block not found in index.html")
    consts = (f"const BUILD = {BUILD};   // generated by patch.py --write-web\n"
              f"const FOOTER = [0x{FOOTER[0]:06X}, {json.dumps(FOOTER[1])}];   // generated by patch.py --write-web\n"
              f"const CHECKSUM_FILL = [0x{CHECKSUM_FILL[0]:06X}, 0x{CHECKSUM_FILL[1]:06X}];   // generated by patch.py --write-web")
    new, count = re.subn(r"const BUILD = [^\n]*\nconst FOOTER = [^\n]*\nconst CHECKSUM_FILL = [^\n]*", lambda m: consts, new)
    if count != 1:
        sys.exit("BUILD / FOOTER / CHECKSUM_FILL lines not found in index.html")
    with open(MRA_PATH, encoding="utf-8") as f:
        mra = f.read()
    mra_block = "const MRA_TEMPLATE = " + json.dumps(mra) + ";   // generated by patch.py --write-web from mister/"
    new, count = re.subn(r"const MRA_TEMPLATE = .*?;   // generated by patch.py --write-web from mister/", lambda m: mra_block, new, flags=re.S)
    if count != 1:
        sys.exit("MRA_TEMPLATE line not found in index.html")
    with open(html_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(new)
    print(f"Wrote build {BUILD} and {len(PATCHES)} patch(es) to {html_path}")


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", nargs="?", help="dfeveron.zip / feversos.zip, or a folder with the files")
    ap.add_argument("-o", "--output", default=os.path.join(here, ZIP_NAME), help="output romset zip")
    ap.add_argument("--write-web", action="store_true", help="copy the PATCHES table into index.html")
    a = ap.parse_args()
    if a.write_web:
        return write_web(os.path.join(here, "index.html"))
    if not a.input:
        ap.error("give a romset zip or folder")

    files = read_input(a.input)
    print("Checking input:")
    if not check(files):
        sys.exit("cv01-u33.bin and cv01-u34.bin must both be present and match. Nothing written.")
    with open(MRA_PATH, encoding="utf-8") as f:
        date = mra_date(f.read())
    u33, u34 = apply_patches(files["cv01-u33.bin"], files["cv01-u34.bin"], date)
    files = dict(files, **{"cv01-u33.bin": u33, "cv01-u34.bin": u34})

    with zipfile.ZipFile(a.output, "w", zipfile.ZIP_DEFLATED) as z:
        for n in FILES:
            if n in files:
                z.writestr(zipfile.ZipInfo(OUT_NAMES.get(n, n), (1996, 12, 24, 23, 32, 0)), files[n], zipfile.ZIP_DEFLATED)
    print(f"\nBuild {BUILD}: {len(PATCHES) + 1} patch(es) applied (footer {date} BUILD {BUILD}), ROM-check sums kept.")
    for n in PATCHED:
        print(f"  {OUT_NAMES[n]:22} crc {crc(files[n])}  sha1 {sha1(files[n])}")
    missing = [n for n in FILES if n not in files]
    if missing:
        print("Note: not in input, so not in the output zip: " + ", ".join(missing))
    print(f"Wrote {a.output}")
    with open(MRA_PATH, encoding="utf-8") as f:
        old = f.read()
    new = mra_with_crcs(old, {n: crc(files[n]) for n in PATCHED})
    if new != old:
        with open(MRA_PATH, "w", encoding="utf-8", newline="\n") as f:
            f.write(new)
        print(f"Updated CRCs in {MRA_PATH}")


if __name__ == "__main__":
    main()
