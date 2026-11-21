# Dangun Feveron patch: handover

Read this first if you're picking up the project or rebuilding it from scratch. Keep it current: update it whenever
tools, addresses, findings or the build process change. The build history is in [BUILDS.md](BUILDS.md). Builds are
numbered from 0.

## Repository
GitHub: https://github.com/IAmTheChuckster/Dangun_Feveron_Disco_Fever (renamed from `Dangun_Feveron` on 2026-11-21;
the local working folder is still `D:\GitHub\Dangun_Feveron`, which the tool scripts' WSL paths refer to).

## Goal
A patch for **Dangun Feveron (Japan, 98/09/17 VER.)**, MAME set `dfeveron`, released as "Dangun Feveron More
Fever". The repo holds only source, tools and notes. **Never commit ROM data.** `.gitignore` excludes ROM archives (`*.zip`, `*.7z`, `roms/`,
`mameset/`), raw dumps (`*.bin`, `*.sos`, `*.rom`, `*.dis`) and MAME output (`*.sta`, `*.png`, nvram/cfg/snap,
`error.log`). Put research dumps in a scratch folder, not the repo. The only ROM-derived bytes in the repo are
the short "original bytes" in `PATCHES`, which the patchers use to check they're patching the right dump.

## Hardware / ROM facts
- Cave 68000 hardware (MAME `cave.cpp`), vertical screen. Not CV1000.
- The owner's dump is `feversos.zip`. `dfeveron` is the parent set, and its own program ROMs sit in a
  `dfeveron/` subfolder inside that zip. Both patchers match files by base name, so `dfeveron/cv01-u33.bin` is
  picked over `cv01-u33.sos` (feversos).
- The program is 1 MB, split across two 512 KB ROMs: **`cv01-u34.bin` holds the even (high) bytes** and
  **`cv01-u33.bin` the odd (low) bytes**. Interleave them (u34 first) to get the 68000 address space starting at 0.
  An early version had this backwards; the giveaway is `rts` reading as `75 4E` instead of `4E 75`.
- 68000 map: work RAM 0x100000-0x10FFFF, sprite RAM 0x400000, layer 0 VRAM 0x500000, layer 1 0x600000,
  palette 0x708000.
- **Text** is plain ASCII in the program, in fixed-width fields padded with spaces and ended by a 0 byte. On screen
  it's drawn as sprites, with tile code = ASCII + 0x60; spaces are skipped. `tools/find_text.py` finds a string.
- **Boot ROM check** (code around 0x8D94): sums the even bytes and the odd bytes of the whole 1 MB program
  separately (16-bit) and compares them with words at 0x8CAA / 0x8CAE. If they don't match, the game hangs on a
  black screen. The patchers keep both sums unchanged by lowering bytes in an unused `0xFF` area,
  `CHECKSUM_FILL` = 0xAF000-0xAFBFF (inside a free block at 0x9E400-0xAFBFF). The stock MiSTer MRA skips the check
  with `<patch offset="0x00008d94">`; the patched ROMs don't need that.
- **Buttons (3):** 1 = secondary shot, 2 = bomb, 3 = rapid fire.
- **Inputs:** the IRQ at 0xB00 reads IN0 (`$B00000`) and IN1 (`$B00002`), inverts them (1 = pressed), and stores
  them at `$101614` (P1) / `$101616` (P2). Low byte bits: 0 up, 1 down, 2 left, 3 right, 4 button 1, 5 button 2,
  6 button 3, 7 start. Coin edges end up in `$10172E/F`. **Credits = `$101730`** (max 9); coin routine 0x6103C.
- **Player object:** P1 at `$105A16`. Offsets: `$06/$08` position (screen is rotated, so `$08` is the horizontal
  axis), `$1A` speed used this frame, `$1B` direction, `$20` ship type, `$21` speed index 0-3, `$39` selected
  speed. **Speed table at 0xBFCC: `1A 1E 29 2D`** (row 1 slowest ... row 4 fastest; menu default is row 2). The
  speed is set at 0xA7E2. The player move code is at 0xA98A: it saves `$1A`, lowers it by 1 for some directions,
  calls the generic mover 0x788F2, then restores it. `$7(a5) != 0` means the object is player 2.
- **Powerful shot:** type is `$1E(a6)` in the player object (0x00 LOCK, 0x08 BOMB, 0x10 ROLL). It's fired by
  holding button 1 (taps give the normal shot). The handler table is at 0xA0C2 (`jmp` per type). Each player has a
  shot list (P1 `$10673A`, P2 `$1069BA`): a 0x20-byte header + 19 slots of 0x20. Slot word 0 bit 15 = in use;
  `$2` = 0 flying, otherwise exploding. BOMB launch at 0xAE5A: a timer at header `$2/$3`, then a free-slot search
  from +$20 with `moveq #n,d7` at 0xAE82 (stock n=2, i.e. 3 bombs). Update loop 0xB292 (all 19 slots), hit
  check vs enemy bullets 0xA1CA (18 slots), explosion pieces spawned at 0xA2FC into free slots from +$A0.
- **Discomen (medals):** the counter shown under the score is P1 `$106C3C` (copies `$106C3E`, `$106C62`;
  P2 `$106C40/$106C42/$106C82`), capped at 999. There are five pickup routines, one per discoman object kind
  (0x6CE70, 0x6D440, 0x6EA8E, 0x6EDCA, 0x6F3C6), each with a P1 and a P2 branch that bump the three counters, then
  build the value popup from the counter (0x778D0). `$10402A/$10402C` = per-player pickup tally.
- **Discoman pool:** `$10C5F2`, **50 slots** of 0x20 (cleared at 0xEEE, updated by the loop at 0x6CE08 with
  `move.w #$31,d7`). Spawn: 0x6CCDE searches for a free slot (starting at slot `$1051A0`), then initialises it at
  0x6D73C from a table at 0x6DB2A, copying the position from `$6(a6)` of the source object. Object format: word 0 =
  flags (0x8000 in use) | kind (low 3 bits); `$6/$8` position; `$1A/$1B` speed/direction (generic mover 0x788F2).
  Raising the 50 would mean moving the pool, because the RAM right after it (`$10CC32`) holds other objects.
- **Item list (not discomen):** `$10C372`, 20 slots, for other pickups (P power-ups etc.). Its spawn helpers
  (0x6E562/0x6E5C0) search only the first 18 slots. Kind dispatch is via the table at 0x6E640.
- **Bomb (button 2):** trigger at 0xAAAE. It needs the stock `$25(a6)` > 0 and no bomb already active; it
  decrements the stock, sets up the bomb object `$10D3B2` (type = ship type) and sets `$10E722` = 1 while the bomb
  runs. While active, 0x9D2A dispatches one of three blast routines (0x9D54 / 0x9DFC / 0x9EC0). Each walks the
  **enemy list `$1075F2`** (120 slots of 0x20, HP word `$18`, bit 5 of byte 0 = hittable), subtracts damage, and
  calls the enemy kill routine **0xA432** when HP goes negative (normal shots use the same routine, e.g. 0x9C6C).
  **Enemy bullets:** `$108572`, 70 slots of 0x40 (bit 15 of word 0 = in use, position `$6/$8`), spawned by the
  pattern routines from 0x7522C (hint `$10519C`). The bomb object's `$10` = owning player object (`$10D3C2` for
  the main bomb object). **The discoman setup at 0x6DA3C deletes any new discoman while a bomb is active**; Build 5
  turns that off.
- **Discoman counter start/reset:** the counter is set to its start value at 0x16D0/0x16D8, 0x395E (all six), 0x8294...
  (game/stage start) and 0x6D004... (when a discoman falls off the screen: the chain breaks). Stock start = 1;
  Build 5 = 0 (`DISCO_RESETS`). The big gold popup is the game's own and appears when the value is a multiple of 10.
- **Counter cap (999):** 20 sites, `cmpi.w #$3E8,ctr` + `move.w #$3E7,ctr`, two counters per player in each of the
  five pickup routines (0x6CE94 ... 0x6F478). At the cap the pickup takes a different path (`jsr $6DE4C`, sound).
- **Counter display (HUD, the red box):** P1 renderer at 0x63F88 reads `$106C3E` (P2: 0x64350, `$106C42`). It counts
  hundreds by subtracting 100 in a loop, then tens and ones. Each digit is one 16-byte sprite entry appended at
  `$101596` (tile `0x0B14`+digit, zoom words `0100 0100`, special blank tile `0x0B1D` when hundreds = 0). There's
  no thousands digit; values >= 1000 would pick tiles past '9'.
- **Big popups:** list `$10DFA2` (15 x 0x20), created by 0x6FD30 (value in BCD at `$2`, style words `$4`/`$A`,
  position `$6/$8`) when the value is a multiple of 10, and drawn by 0x6FD90/0x6FE1A: '+' then BCD digit pairs
  (tiles 0x4F0C+, 0x4F16+), 4 digits max. Zoom is in d6 (from the pop-in table at 0x6FDBA, then 0x100 = 1.0).
  The sprite emitter 0x79E9A writes x, y, attr, tile, zoom long, size word, and re-centres by zoom. `$1C/$1E` of a
  popup object are unused by the game (Build 7 stores the spacing there).
- **Two counters per player:** `$106C3C/$106C40` = the value used for popups and score (reset to the start value
  when a discoman is missed); `$106C3E/$106C42` = what the HUD shows. The stage-end bonus multiplies the two.
- **Score (per stage):** P1 `$10ECEA` / P2 `$10ECEE` are pending-points buffers; each frame 0x637BC adds them into
  the live score P1 `$103DE8` / P2 `$103DEC` (BCD, capped 9999999) and clears them. The game scores **per stage**:
  each stage has a slot (P1 `$103FAE[stage]`, P2 `$103FCE[stage]`, stage index `$1052D8`); at stage start 0x63634
  loads the live score from the slot (0 for a new stage), and at stage end 0x63806 saves it back. The top-left box is
  drawn at 0x64948 (P1) / 0x64984 (P2) from `d7`. Stage start also clears RAM `$105A98`-`$10ED12` (0x2F42), which
  includes all object lists and the patch's own RAM at `$10B4xx`.
- **Popup value and score:** after a pickup, 0x6DE58/0x6DE7C convert the counter to BCD (0x778D0, 6 digits) and add
  it to the score at `$10ECEE` (P1) / `$10ECF2` (P2) with `abcd` (0x6336A). The popup sprite is built at 0x632FE
  (`d1` = 8 for the capped path). **Stage-end bonus** (0x1FC6) = `$106C3E` x `$106C3C`, capped at 999999.
- **Score digits:** renderer 0x649C2 (P1 start y 0x200, P2 0x3040; `d7` = BCD score). It picks a layout from the
  BCD high word: 5+ digits start 0x100 left; 7 digits take the path at 0x64BBE (stock: spacing 0x1C0, zoom
  0x00E0, top digit never drawn). Digit emitter 0x64C7C (tile 0x0258+digit).
- **Lives and extends:** lives P1 `$1052C4`, P2 `$1052C6` (words). Extra lives come only from a 1UP item (item
  kind 5 in the item list `$10C372`; pickup handler 0x6F150 adds the life). The item is dropped by 0x6100A when the
  1UP flag `$105112` == 1 (it waits while `$105188` is set). The flag is set by the pickup routine at 0x6D41C, which
  counts every discoman collected by either player in `$10510C` (not on stage index 6). Stock: once, at exactly
  2000. Build 11: every 1000 (the counter is reset each time).
- **Bomb item:** item kind 3 ("B"); its pickup at 0x6ECF4 adds 1 to the bomb stock (P1 `$105A3B`, P2 `$105A7B`,
  max 4). Items are spawned with 0x6E5C0 (d0 = kind, d2 = position long). Build 12 drops one every 250 pickups,
  from the same count as the 1UP.
- **Title screen text:** routine 0x650E draws a 0-terminated string (a0) with colour d1 at height d3 (larger =
  higher on the rotated screen) from start d4 (0x200 per character; strings are centred with leading spaces on a
  30-column line). Lines: PLEASE INSERT COIN 0x503C (stock height 0x2200), C BUTTON 0x1800 (only when the C button
  is enabled), RANK 0x1200, (c)1998 0x0C00, NOT FOR SALE 0x0780. With a credit, the animated PRESS START text is drawn
  by 0x644E from a 22-letter buffer at `$10CC32`, set up at 0x63A2 (height at 0x63B0). The wave only cycles colours.
- **"STAGE HIGH /" label:** one sprite, tile 0x0FE9 x 4 tiles (size 0x0104) at x 0x4D00, y 0x0EC0, drawn at
  0x644E4; `HIGH /` is in its last 2 tiles. The high-score number next to it is drawn separately.
- **Score box frame:** sprites drawn at 0x63D24 (P1) / 0x640E6 (P2 mirrored, growing the other way): middle
  0x099F (size 0x0201), left end 0x099B (0x0202), right end 0x09A1 (0x0201). The game moves the middle and right end
  out 0x200 when the score's digits 10^5/10^6 are non-zero. The digits themselves are drawn at 0x64948 onward
  (tiles 0x0258+digit, 0x200 apart). This is all sprites; layer 1 VRAM holds only background decoration.
- **RAM used by the patch:** `$10B400` (bomb pull timer, word), `$10B402` (bomb frame tick, byte), `$10B408`
  (score-box BCD work buffer, long), `$10B490/$10B491` (P1/P2 score box size level: 0 = up to 6 digits, 1 = 7, 2 = 8) and `$10B410`-`$10B487` (per-enemy "dropped a
  discoman" marks). Both are in `$109F72`-`$10C372`, which is always 0 in every dump and not referenced by code
  around there.
- **Free space:** 0x9E400-0xAFBFF is unused `0xFF`. Code hooks go at the start (0x9E400, ...), and
  `CHECKSUM_FILL` uses the end (0xAF000-0xAFBFF).

| File | Size | CRC32 | Role |
|---|---|---|---|
| cv01-u33.bin | 512 KB | e53a7db3 | program, odd bytes (patched) |
| cv01-u34.bin | 512 KB | be87f19d | program, even bytes (patched) |
| cv01-u19.bin | 4 MB | 5f5514da | sound |
| cv01-u25.bin / u26 | 4 MB each | a6f6a95d / 32edb62a | sprites |
| cv01-u50.bin / u49 | 2 MB each | 7a344417 / d21cdda7 | layer 0 / layer 1 |
| eeprom-dfeveron.bin | 128 B | c3174959 | EEPROM |

SHA-1s are in `FILES` in `patch.py`.

## Known addresses
| Address | What | Patch |
|---|---|---|
| 0x00622D | title screen line `   SALES BY NIHON SYSTEM INC. ` (30 chars) | `NOT FOR SALE`, centred |
| 0x009302 | notice: `NOTICE` heading | unchanged |
| 0x009315 | notice: `  THIS GAME IS FOR USE IN   ` (28 chars) | blanked |
| 0x009332 + 0x1D·n | notice: 7 region lines (KOREA ... JAPAN ONLY, drawn in red) | blanked |
| 0x0093FD + 0x1D·n | notice: 9 body lines, 28 chars each | the disclaimer, word-wrapped at 27 |
| 0x009502 | notice footer `              98/09/17 VER. ` (28 chars) | `<MRA date> BUILD <n>`, right-aligned |
| 0x0096C7 | a second notice text (`THIS GAME MAY NOT BE SOLD, ...`), not seen on the Japan set | unchanged |
| 0x008CAA / 0x008CAE | stored ROM-check sums (even / odd) | unchanged; sums kept via `CHECKSUM_FILL` |
| 0x00A9A2 | player move: `jsr $788F2` | `jsr $9E400` (slow-speed hook) |
| 0x00AE82 | BOMB launch free-slot search `moveq #2,d7` | `moveq #7,d7` (8 bombs) |
| 0x6CEEC ... (30 sites, `DISCO_ADDS`) | discoman counters `addq.w #1` | `addq.w #2` |
| 0x16D0 ... (22 sites, `DISCO_RESETS`) | counter start/reset `#1` | `#0` |
| 0x06CE08 | discoman loop `lea $10C5F2,a6` | `jsr FRAME_HOOK` (0x9E4C0) |
| 0x00A432 | enemy-kill entry | `jmp KILL_HOOK` (0x9E440) + 2 nops |
| 0x06DA42 | "no discomen during a bomb" `bpl` | `bra` |
| 0x9DE0 / 0x9E92 / 0x9F16 | blast routines: mark hit enemy (`move.w $24(a5),d4 / or.w d4,(a6)`) | `jsr HIT_HOOK` (0x9E5C0) |
| 0x6CEA6 ... (10 pairs, `VALUE_CAPS`) | value counter cap 999 | 9999 (HUD counter stays 999) |
| 0x6FE2C | big popup zoom setup | `jsr ZOOM_HOOK` (0x9E600) + 3 nops |
| 0x6FE62 / 0x6FEB6 / 0x6FEC8 / 0x6FF08 | big popup digit spacing `subi.w #n,d4` | `sub.w $1E/$1C(a2),d4` |
| 0x64948 / 0x64984 | score box `move.l $103DE8/$103DEC,d7` | `jsr SCORE_HOOK` (0x9E680 / 0x9E692): running total |
| 0x63D24 / 0x640E6 | score box frame size `move.l $103DE8/$103DEC,d0` | `jsr VAL` (total + size level 0/1/2) |
| 0x63DA8 / 0x64162 | frame: after middle piece | `jsr EXTRA` + nop (one extra middle piece per level) |
| 0x63E0A / 0x641BC | frame: right end offset | `jsr RIGHT` + nop (+0x200 per level) |
| 0x64BD4 ... (6) / 0x64C92 | 7-digit path spacing 0x1C0 / zoom 0x00E0 | 0x200 / 0x0100 |
| 0x64A04 / 0x64A10 / 0x64A16 | digit masks 0x0FFF / 0x0FF0 / 0x0F00 | 0xFFFF / 0xFFF0 / 0xFF00 (include 8th digit) |
| 0x64BBE | 7-digit path first digit | `jsr DIG8` + nop (draws the 8th digit first) |
| 0x649A6 | P2 digits: `move.l $103DEC,d0` | `jsr dstart` (running total, start 0x200 left per level) |
| 0x6D42C / 0x6D438 | 1UP threshold 2000 / set flag | 1000 / `jsr EXTEND_HOOK` (also resets the counter) |
| 0x6D426 | pickup count `addq.l #1,$10510C` | `jsr BOMB_ITEM_HOOK` (bomb item every 250) |
| 0x4FF2 / 0x60E8 | title: C-button check `btst #2,$10161D` | `jsr TITLE_HOOK` + nop (draws DISCO FEVER) |
| 0x503C / 0x63B0 | title: PLEASE INSERT COIN / PRESS START height 0x2200 | 0x1E00 (DISCO FEVER at 0x2400) |
| 0x644E4 / 0x644EC / 0x64502 | "STAGE HIGH /" sprite tile / y / size | tile +2, y +0x800, size 0x0102 ("HIGH /" only) |
| 0x09E400 | free space | `SLOW_HOOK_CODE`: while button 1 is held, `$1A -= $39 - slowest` |

## Repo layout
- `patch.py`: Python patcher (stdlib only). `python patch.py feversos.zip [-o out.zip]` writes a standalone
  `dfeveronfever.zip`: only the 8 dfeveron files, flat, with no feversos files and no `dfeveron/` folder. **Every file
  the patch changes gets `fever` appended** (`cv01-u33fever.bin`, `cv01-u34fever.bin`; see `OUT_NAMES`). It also
  rewrites the program-ROM names and CRCs in `mister/Dangun Feveron More Fever.mra`. Contents:
  - `BUILD`: the build number, the single source of truth.
  - `PATCHES`: list of `(address, old hex, new hex, description)`. The old bytes are checked before anything is
    written. `text_patch()` builds text replacements padded to the field width. `notice_patches()` word-wraps
    `NOTICE_TEXT` into the notice body.
  - `footer_patch()`: the notice footer is built at patch time from the date in the MRA `<name>` (`mra_date()`, a
    `YY/MM/DD` date) plus `BUILD`. **Changing the date in the MRA changes the footer** on the next build.
  - `apply_patches()`: interleave, apply, keep the ROM-check sums, split.
- `index.html`: web patcher (GitHub Pages), adapted from the owner's Ibara "Show Time" patcher template. It does the
  same thing in the browser, with the same functions (`mraDate`, `footerPatch`, `applyPatches`). It has exactly two
  downloads: `dfeveronfever.zip` and `Dangun Feveron More Fever.mra` (the repo MRA, embedded as `MRA_TEMPLATE`, with
  the patched names and CRCs filled in). Its footer date comes from that embedded MRA.
- `mister/Dangun Feveron More Fever.mra`: the project's MiSTer MRA (Cave core), maintained by the owner. Setname
  `dfeveronfever`, zip `dfeveronfever.zip`, and the release date in `<name>`. Running `patch.py` keeps its
  program-ROM CRCs current and writes the build number into `<name>` after "Build"
  (`(26/11/21 Build 1)`, see `mra_with_build()`). The web page's MRA download does the same.
- `tools/`: test and research helpers (see below).
- `dev_notes/`: this file and `BUILDS.md`.

### Keeping the two patchers in sync
`patch.py` is the source of truth. `python patch.py --write-web` regenerates these generated lines in `index.html`:
`const BUILD`, `FOOTER`, `CHECKSUM_FILL`, the `const PATCHES = [...]` block, and `MRA_TEMPLATE`. Run it after any
change to `patch.py` or the MRA. The `FILES` / `OUT_NAMES` tables and the logic functions are duplicated by hand;
change both if they change.

## Making a new build
1. Bump `BUILD` in `patch.py` and make the changes.
2. Run `python patch.py roms/feversos.zip -o <tmp>/dfeveronfever.zip`. This also updates the MRA CRCs.
3. Run `python patch.py --write-web`, so the page gets the new build, patches and the MRA with its fresh CRCs.
4. Test in MAME: `python tools/mame_set.py <tmp>/dfeveronfever.zip <tmp>/mameset` makes a `dfeveron/` folder
   with the original names, then run MAME with `ROMPATH=<tmp>/mameset` (see below). Also load `roms/feversos.zip`
   in the web page; both patchers must give the same CRCs.
5. Add an entry to `dev_notes/BUILDS.md` with the build number, date, changes and output CRC32/SHA-1s.
6. Update this file if anything learned changes the picture.

## Test environment (MAME 0.289 in WSL)
- Lives at `~/mame` in WSL (user `brian`): `bin/cave` is the 68000 Cave driver build, `scripts/run.sh` runs a
  headless session, `lua/harness.lua` drives inputs. See `~/mame/README.md`.
- `~/mame/roms/feversos.zip` is the owner's dump. The repo's `roms/feversos.zip` was later removed by the owner;
  build with `python patch.py "$(wsl -e wslpath -w /home/brian/mame/roms/feversos.zip)" -o <tmp>/dfeveronfever.zip`
  (PowerShell: `$z=(wsl -e wslpath -w /home/brian/mame/roms/feversos.zip)`). For the web check, the
  `patcher-test` entry in `.claude/launch.json` serves a scratch folder holding a copy of `index.html` and
  `roms/feversos.zip`. Don't copy ROMs into the project.
  `bin/cave -verifyroms dfeveron -rompath roms` reports it as good.
- Run a patched set:
  `wsl -e bash -lc "cd ~/mame && GAME=dfeveron ROMPATH=<abs path>/mameset BT_SNAP=100 scripts/run.sh 2300"`.
  Use absolute paths; `$PWD` gets mangled through PowerShell. MAME warns that the two program ROMs have the wrong
  CRC; that's expected.
- `tools/run_play.sh <sched> <outdir> [frames] [snap_every]` runs the stock set with an input schedule and copies
  the PNG snapshots out. Call it as `wsl -e sh /mnt/d/GitHub/Dangun_Feveron/tools/run_play.sh ...`.
  Write schedule files with an editor; quoting through PowerShell and `wsl bash -lc` mangles inline `printf`.
- Schedule tokens: `U D L R`, `A B C` = buttons 1-3, `K` coin, `S` 1P start, `-` = release all.
- Boot timeline (frames, warm nvram): black until ~600, notice screen ~600-1000, ranking ~1000, fighter-select
  demo, gameplay demo, **title screen ~2000-2500**.
- Research tools:
  - `tools/find_text.py <zip> "TEXT"`: find ASCII text in the interleaved program.
  - `tools/vdump.lua`: dump 0x300000-0x9FFFFF at frame `VD_FRAME` (default 2200) to `work/vdump.bin`.
  - `tools/tap_sprite.lua`: log the PC and registers for writes to a sprite RAM range (`TAP_LO`/`TAP_HI`, frames
    `TAP_FROM`-`TAP_TO`) to `work/tap.log`. Use this instead of debugger watchpoints: `-debugscript` with
    `logerror` gave no output here.
  - `tools/ports.lua`: list input ports. dfeveron uses `:IN0` (P1, Coin 1, Service Mode, 1P Start) and `:IN1`
    (P2, Coin 2, Service 1, 2P Start), all active-low.
  - `tools/find_rel.py`, `tools/find_pattern.py`: search for text in unknown encodings (they weren't needed once
    the byte order was fixed).
- **Coin and start work** (the earlier "coin doesn't register" was a misread of the snapshots). A working
  sequence (frames, warm nvram): `1300 K` coin, `1400 S` start, then three menus at `1600 A` (fighter), `1700 A`
  (powerful shot) and `1800 A` (speed; `U`/`D` before it moves the cursor from row 2). Gameplay runs from about 1900.
  See `tools/speed1.txt`, `tools/speed4.txt`, `tools/slow_test.txt`.
- More helpers:
  - `tools/disasm.py <zip|prog.bin> <start> <len>`: 68000 disassembly with capstone (`pip install capstone`).
  - `tools/run_dump.sh <sched> <tag> <frame>`: dump RAM at a frame to `work/ram_<tag>.bin` (`tools/sched_dump.lua`).
    Diffing two runs that differ in one choice is a quick way to find a variable.
  - `tools/run_tap.sh <sched> <lo> <hi> <from> <to> [r|w]`: log every unique PC that reads/writes a range
    (`tools/tap_read_range.lua`).
  - `tools/pos_log.lua`: print P1 position and speed bytes each frame (`PL_FROM`/`PL_TO`). Used to measure speed.
  - `tools/bomb_count.lua`: count P1 shot-list slots flying/exploding each frame (`BC_FROM`/`BC_TO`), and print the
    max. Use with `tools/bomb_hold.txt` (BOMB type, hold button 1 from frame 2000).
  - `tools/ramdiff.py a.bin b.bin [max]`: diff two RAM dumps and show the P1 object.
  - `tools/bomb_monitor.lua`: each N frames print bomb active, pull timer, bullet count, discoman count and P1
    counter (`MN_FROM/MN_TO/MN_EVERY`). The **attract demo bombs at frames ~3375 and ~3847**, so it's a ready-made
    bomb test.
  - `tools/disco_pos.lua`: P1 position plus every active discoman's word0/position/state, each N frames.
  - `tools/snap_at.lua`: snapshots at the frames listed in `SN_FRAMES`.
  - `tools/popup_test.lua`: test-only helper that sets P1's value counter at chosen frames and snapshots when it
    reaches given values (`PT_*`). Used to see `+100` / `+1000` popups without playing to them.
  - `tools/stage_sim.lua`: test-only; writes P1's stage-1 slot and stage index 1 to preview the score box as if
    stage 2 had started. `tools/watch_longs.lua`: print changes of several RAM longs.
  - `tools/sprite_dump.lua` (sprite RAM at a frame) and `tools/vram_dump.lua` (layer 1 VRAM): find which sprites
    or tiles draw something on screen.
  - `tools/extend_test.lua`: test-only; sets the pickup counter at chosen frames (`ET_SETS=frame:value,...`) and
    prints the counter, 1UP flag, lives, bomb stocks and 1UP / bomb items.
  - `tools/count_pc.lua`: count how often code runs (reads of `CP_ADDR` at `CP_PC`). Note that the PC the tap
    reports is the next instruction's address.
  - Free ROM used so far (in 0x9E400-0xAEFFF): 0x9E400 slow hook, 0x9E440 kill hook, 0x9E4C0 frame hook (to
    0x9E580), 0x9E5C0 hit hook, 0x9E600 zoom hook (to 0x9E66A), 0x9E680 score hook (to 0x9E6D8), 0x9E6E0 / 0x9E7CA score box hooks, 0x9E8D6 8th-digit hook, 0x9E90C extend hook, 0x9E92C bomb item hook, 0x9E96A title hook + text (to 0x9E9A6). `patch.py` asserts the hooks don't overlap.
  - `tools/find_lists.py`, `tools/find_refs.py`: find object arrays in a RAM dump, and code references to a RAM range.
  - Hand-written 68000 code goes through `asm()` in `patch.py` (labels and short branches). Always disassemble the
    result with capstone to check it.
  - `tools/find_value.py d1.bin=5 d2.bin=16 ...`: find a RAM variable from values read off the screen (binary/BCD).
  - `tools/watch_word.lua`: print every change of a RAM word (`WW_ADDR`, `WW_FROM`, `WW_TO`).
  - **The attract demo is a free test run:** it plays the game and collects plenty of discomen (frames ~2700-5600
    without inputs; `tools/empty.txt`). Scripted play tends to die quickly, so use the demo for anything that
    needs real pickups.
  - Videos the owner sends: ffmpeg comes with the `imageio-ffmpeg` pip package (`python -c "import imageio_ffmpeg;
    print(imageio_ffmpeg.get_ffmpeg_exe())"`). Make contact sheets with `-vf "fps=4,scale=-1:400,tile=6x2"`. The
    owner's reference videos are of a newer Dangun Feveron release (with a "CYBORG COUNTER" side panel), used to
    show the behaviour wanted.
  - All of these accept `ROMPATH=` to run a patched set made by `tools/mame_set.py`.

## Credits / attribution
Project and testing: IAmTheChuckster. Reverse engineering and patcher code: Claude.
