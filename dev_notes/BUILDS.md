# Builds

One entry per build, newest first. The build number is `BUILD` in `patch.py` (copied to `index.html`).

## Build 15 (2026-11-21)
- **Bomb item every 100 discomen collected** (was 250, Build 12): `BOMB_ITEM_EVERY = 100`. Drops at 100 / 200 /
  ... of each 1000; at 1000 a bomb item and a 1UP both drop.
- The TLB "even if you died" change (see CLAUDE.md) is in `patch.py` but **switched off** (`TLB_ANY_DEATHS = False`):
  a test game with deaths still didn't reach the TLB, so it isn't proven yet.
- Measured in MAME (attract demo; test-only helper set the pickup count to 96 and later 196): bomb items appeared
  at 100 and at 200; P2 collected one and their bomb stock went 3 -> 4.
- Footer `26/11/21 BUILD 15`; MRA name `(26/11/21 Build 15)`.
- Output (from `feversos.zip`):
  - `cv01-u33fever.bin`: CRC32 `9d271333`, SHA-1 `c9effc9d90ddf0f3a12bd56350dbf76439165b64`
  - `cv01-u34fever.bin`: CRC32 `db6810e7`, SHA-1 `dbb5809bdce22b9d1d7d0ba055c87405e83ad04c`
- Tested: MAME 0.289; the web page gives the same CRCs. Not tested on MiSTer or by hand.

## Build 14 (2026-11-21)
- **Title lines moved up**, from the owner's mock-up taken with the C BUTTON line showing (in Build 13 the start
  line sat right on top of it). DISCO FEVER 0x2200 -> 0x2400 (further into the purple stripes); PLEASE INSERT COIN /
  PRESS START 0x1C00 -> 0x1E00. That gives even 0x600 gaps: DISCO FEVER, start line, C BUTTON (0x1800).
- Measured in MAME: title screenshots with and without a credit show DISCO FEVER over the stripes, a gap, then the
  start line, with room before RANK for the C BUTTON line (that line is off on this test setup's settings).
- Footer `26/11/21 BUILD 14`; MRA name `(26/11/21 Build 14)`.
- Output (from `feversos.zip`):
  - `cv01-u33fever.bin`: CRC32 `8e15045f`, SHA-1 `1fe1438e8341b4d4c2fe1ca6835c4aeade7e842a`
  - `cv01-u34fever.bin`: CRC32 `91204cf8`, SHA-1 `933a521cd7d55b53ce6472d2a61e845622e29345`
- Tested: MAME 0.289; the web page gives the same CRCs. Not tested on MiSTer or by hand.

## Build 13 (2026-11-21)
- **"DISCO FEVER" on the title screen**, in the C BUTTON gold (`0x3A30`), centred at height 0x2200 (the line
  PLEASE INSERT COIN used to have), over the bottom of the purple Japanese characters' stripes, as in the owner's
  mock-up. Drawn with the game's title text routine 0x650E by `TITLE_HOOK` (0x9E96A; the text is stored right after
  the code). The hook replaces the C-button check `btst #2,$10161D` at 0x4FF2 (no credit) and 0x60E8 (credit), and
  repeats it, so the line shows in both title states.
- **PLEASE INSERT COIN and the animated PRESS START moved down** from height 0x2200 to 0x1C00 (0x503C and the
  letter setup at 0x63B0), leaving a gap under DISCO FEVER and 0x400 to the C BUTTON line at 0x1800.
- Layout history: first 0x2200 / 0x1D00; then 0x2000 / 0x1C00 to clear the stripes; the owner then asked for DISCO
  FEVER higher with a gap below, giving 0x2200 / 0x1C00.
- Measured in MAME: screenshots of the title with no credit (`DISCO FEVER` / gap / `PLEASE INSERT COIN`) and after
  a coin (`DISCO FEVER` / gap / `PRESS 1P OR 2P START BUTTON`). The C BUTTON line isn't shown on this test setup's
  settings, so its spacing wasn't seen.
- Footer `26/11/21 BUILD 13`; MRA name `(26/11/21 Build 13)`.
- Output (from `feversos.zip`):
  - `cv01-u33fever.bin`: CRC32 `8e15045f`, SHA-1 `1fe1438e8341b4d4c2fe1ca6835c4aeade7e842a`
  - `cv01-u34fever.bin`: CRC32 `89f2cc87`, SHA-1 `a1b43190e0442846d8c2fdd90a3ce0fa38abec71`
- Tested: MAME 0.289; the web page gives the same CRCs (served from a scratch copy, because `roms/feversos.zip` is
  no longer in the project). Not tested on MiSTer or by hand.

## Build 12 (2026-11-21)
- **A bomb item (the "B" pickup) every 250 discomen collected.** Same pickup count as the 1UP (`$10510C`, both
  players, not on the final stage). Its increment at 0x6D426 now calls `BOMB_ITEM_HOOK` (0x9E92C), which does the
  increment and, when the count divides by 250, spawns item kind 3 through the item spawner 0x6E5C0 at
  (`$5400`, `$2400`), next to the 1UP drop point. The pickup handler (0x6ECF4) adds 1 bomb, max 4. The count resets
  every 1000 (Build 11), so drops come at 250 / 500 / 750 / 1000 of each 1000; at 1000 a bomb item and a 1UP both
  drop.
- Measured in MAME (attract demo; a test-only Lua helper set the count to 246 and later 996): a bomb item appeared
  at 250; P2 collected it and their bomb stock went 3 -> 4; at 1000 a 1UP and another bomb item appeared.
- Footer `26/11/21 BUILD 12`; MRA name `(26/11/21 Build 12)`.
- Output (from `feversos.zip`):
  - `cv01-u33fever.bin`: CRC32 `9b55d4ca`, SHA-1 `8b5d7e01909dbb356725a042b2c8dcd23447bc2a`
  - `cv01-u34fever.bin`: CRC32 `d2f3eaae`, SHA-1 `ae1992602d97ee9d25eeb05868527e50bd8dcb0b`
- Tested: MAME 0.289; the web page gives the same CRCs. Not tested on MiSTer or by hand.

## Build 11 (2026-11-21)
- **An extra life every 1000 discomen collected** (stock: once per game, at 2000). The pickup routine at 0x6D41C
  counts every discoman collected by either player in `$10510C` (not on the final stage, stage index 6). Stock set
  the 1UP flag (`$105112` bit 0) when it equalled 2000 and never reset it; 0x6100A then drops a 1UP item (item kind
  5), whose pickup (0x6F150) adds a life (`$1052C4` P1 / `$1052C6` P2).
  - The threshold at 0x6D42C is now 1000 (`EXTEND_EVERY`).
  - Setting the flag (0x6D438) calls `EXTEND_HOOK` (0x9E90C), which also resets the counter, so it repeats.
- Measured in MAME (attract demo; a test-only Lua helper set the counter to 996 at frames 2900 and 3150):
  - At 1000 the flag is set, the counter goes to 0 and a 1UP item appears the next frame, both times.
  - P1 collected one and lives went 1 -> 2.
- Footer `26/11/21 BUILD 11`; MRA name `(26/11/21 Build 11)`.
- Output (from `feversos.zip`):
  - `cv01-u33fever.bin`: CRC32 `e3804967`, SHA-1 `13bb02d980265699727522e4f158e8dd61ca6df7`
  - `cv01-u34fever.bin`: CRC32 `57adac43`, SHA-1 `621d98f1b2aa51f03569ae85db9e5282386dd9d8`
- Tested: MAME 0.289; the web page gives the same CRCs. Not tested on MiSTer or by hand.

## Build 10 (2026-11-21)
- **The first digit of a 7-digit score is no longer cut off.** The digit renderer (0x649C2) sent 7-digit scores
  down a separate path (0x64BBE) that squeezed them (spacing 0x1C0, zoom 0x00E0) and started them half a digit to
  the left, under the frame's left end. With the wider frame that isn't needed: that path now uses normal spacing
  0x200 (6 sites) and zoom 1.0 (0x64C92).
- **8-digit scores are covered.** The renderer masked out the top digit; the masks at 0x64A04/0x64A10/0x64A16 now
  include it, and DIG8 (hook at 0x64BBE) draws the 8th digit first. The frame has size levels (0 = up to 6 digits,
  1 = 7, 2 = 8; `$10B490`/`$10B491`): one extra middle piece and +0x200 on the right end per level. P2's digits
  start 0x200 further left per level (0x649A6). Hooks: P1 0x9E6E0, P2 0x9E7CA, DIG8 0x9E8D6.
- **"STAGE" removed from "STAGE HIGH /".** The label is one 4-tile sprite (tile 0x0FE9, size 0x0104, drawn at
  0x644E4). Only its last 2 tiles are drawn now (tile 0x0FEB, size 0x0102), moved along by 0x800 so `HIGH /` stays
  in place.
- Measured in MAME (simulated stage 2 via `tools/stage_sim.lua`): `123456`, `1399905` and `12345678` all sit
  fully inside the frame. `HIGH /600000` is shown without "STAGE", with a clear gap after an 8-digit box.
- Footer `26/11/21 BUILD 10`; MRA name `(26/11/21 Build 10)`.
- Output (from `feversos.zip`):
  - `cv01-u33fever.bin`: CRC32 `1e3605fe`, SHA-1 `fab6032f01a2a0168c3d1c46ab98b3e4dad82404`
  - `cv01-u34fever.bin`: CRC32 `c3b89db7`, SHA-1 `e50f9676680d832e3765321dda4b40d47870d888`
- Tested: MAME 0.289; the web page gives the same CRCs. P2's box at 7/8 digits wasn't seen (the test only set P1).
  Not tested on MiSTer or by hand.

## Build 9 (2026-11-21)
- **The score box frame grows to fit a 7-digit running total.** The frame is three sprites drawn at 0x63D24 (P1)
  / 0x640E6 (P2, mirrored): middle 0x099F, left end 0x099B, right end 0x09A1. The game already moved the middle
  and right end out by 0x200 for 6+ digits, but it tested the stage score and had no 7-digit step. Now:
  - The score read calls BOXVAL, which returns the running total (Build 8) and sets a 7-digit flag (`$10B490` P1,
    `$10B491` P2).
  - EXTRA draws a second middle piece 0x200 further out when the flag is set (0x63DA8 / 0x64162).
  - The right end moves out another 0x200 (0x63E0A / 0x641BC).
  - Hooks at 0x9E6E0 (P1) and 0x9E780 (P2).
- Measured in MAME (simulated stage 2 via `tools/stage_sim.lua`): a total of `1234567` fits inside the widened
  frame with its end cap after the last digit; `123456` gives the original 6-digit frame.
- Footer `26/11/21 BUILD 9`; MRA name `(26/11/21 Build 9)`.
- Output (from `feversos.zip`):
  - `cv01-u33fever.bin`: CRC32 `afef3021`, SHA-1 `965cbaf726bc7d66f699900a35b7131b1de6bc5d`
  - `cv01-u34fever.bin`: CRC32 `0267e201`, SHA-1 `b4494bc8123c85072c4523b6790cfcc09567858f`
- Tested: MAME 0.289; the web page gives the same CRCs. P2's mirrored frame wasn't seen with 7 digits (the test
  only set P1). Not tested on MiSTer or by hand.

## Build 8 (2026-11-21)
- **The top-left score box shows the running total** instead of restarting at 0 each stage. Display only: the
  game keeps a score per stage (P1 `$103FAE[stage]`, P2 `$103FCE[stage]`; the live score `$103DE8`/`$103DEC` is
  loaded from the current stage's slot at stage start (0x63634) and saved back at stage end (0x63806)). The box's
  loads `move.l $103DE8,d7` (0x64948) and `move.l $103DEC,d7` (0x64984) now call `SCORE_HOOK` (0x9E680, P2 entry
  0x9E692), which returns the BCD sum of the earlier stages' slots plus the live score. Scoring, stage records,
  STAGE HIGH and the ranking are unchanged.
- Measured in MAME (attract demo plus a test-only Lua step that set P1's stage-1 slot and the stage index to 1, as
  if stage 2 had started):
  - Slot 12345 + live 0 -> the box shows `12345`; P2's box still shows its own score.
  - Slot 1234567 -> the box shows `1234567` (7 digits fit; an 8th digit would run past the frame).
  - A real stage change wasn't played through (scripted play doesn't survive stage 1).
- Footer `26/11/21 BUILD 8`; MRA name `(26/11/21 Build 8)`.
- Output (from `feversos.zip`):
  - `cv01-u33fever.bin`: CRC32 `77e89111`, SHA-1 `d80dd8fe9c77912ecdca31886b6462f29635eec6`
  - `cv01-u34fever.bin`: CRC32 `a91c8a5c`, SHA-1 `7fff47867de58e35688ecacaf9d7dee2ac13df22`
- Tested: MAME 0.289 (simulated stage 2); the web page gives the same CRCs. Not tested on MiSTer or by hand.

## Build 7 (2026-11-21)
- **Popup/score values go past 999:** the value counter (P1 `$106C3C`, P2 `$106C40`) is capped at 9999 instead of
  999 (10 sites, `VALUE_CAPS`: `cmpi.w #1000` -> `#10000`, `move.w #999` -> `#9999`). The HUD counter (`$106C3E` /
  `$106C42`, the red box) keeps its 999 cap, as the owner asked.
- **Bigger big popups:** a multiple of 100 is drawn 1.5x, a multiple of 1000 2x (same gold style). Hook at 0x6FE2C
  (`jsr ZOOM_HOOK`, 0x9E600) builds the zoom as stock, then scales both zoom words by the popup's BCD value. It
  stores the digit spacing in the popup object's unused `$1C` (0x180 / 0x240 / 0x300) and `$1E` (0x200 / 0x300 /
  0x400). The four `subi.w #n,d4` spacing steps (0x6FE62, 0x6FEB6, 0x6FEC8, 0x6FF08) are now
  `sub.w $1C/$1E(a2),d4`.
- Measured in MAME (attract demo; a test-only Lua helper set P1's value counter to 94 and later 994):
  - The counter went 1000 -> 1002, past the old cap.
  - Screenshots: `+100` drawn 1.5x, `1000` drawn 2x with wider spacing; normal big popups (e.g. `+40`) unchanged.
- Footer `26/11/21 BUILD 7`; MRA name `(26/11/21 Build 7)`.
- Output (from `feversos.zip`):
  - `cv01-u33fever.bin`: CRC32 `f485e756`, SHA-1 `040a0ff92cbfa5a58c81795da067d2e475fff344`
  - `cv01-u34fever.bin`: CRC32 `03532e47`, SHA-1 `c2110a14d8292d6f02228691c7ff9904ee2cc70b`
- Tested: MAME 0.289; the web page gives the same CRCs. **Not tested on MiSTer: zoom above 1.0 is used here for the
  first time, and the MiSTer Cave core's support for it isn't verified.** Not tested by hand.

## Build 6 (2026-11-21)
- **Every bomb hit drops discomen, not just kills.** The three blast routines mark each enemy they hit every frame
  with `move.w $24(a5),d4 / or.w d4,(a6)` (0x9DE0, 0x9E92, 0x9F16). That pair is now `jsr HIT_HOOK` (0x9E5C0), which
  does the same marking and, on every 4th frame of the bomb (`HIT_EVERY`, frame tick `$10B402` counted by the
  per-frame hook), spawns a discoman at the enemy. Kill drops and bullet conversion (Build 5) are unchanged.
- Expected: up to ~30 extra discomen per enemy that stays in the blast for a whole bomb (~120 frames), e.g. bosses
  and tough enemies.
- Measured in MAME (attract demo, 1st bomb): the hook runs 12 times on 8 frames. The bomb only damages enemies
  within a fixed area around the blast, and the demo's small enemies die in a frame or two, so it adds ~3 discomen
  there (P1 counter at frame 3470: 66 vs 63 in Build 5). Not yet tested against a boss or tough enemy.
- Footer `26/11/21 BUILD 6`; MRA name `(26/11/21 Build 6)`.
- Output (from `feversos.zip`):
  - `cv01-u33fever.bin`: CRC32 `a7a6b890`, SHA-1 `2f0bbf0610335b0ad868f7ca55c46a12dab3b86d`
  - `cv01-u34fever.bin`: CRC32 `f39886a7`, SHA-1 `3170d42c7cfd1a02f700c51c99a4cc9ad438047e`
- Tested: MAME 0.289; the web page gives the same CRCs. Not tested on MiSTer or by hand.

## Build 5 (2026-11-21)
- **Discoman counter starts at 0** (was 1). Every reset to 1 is now 0: 21 `move.w #1` writes (game/stage start,
  and the reset when a discoman falls off the screen) plus the `moveq #1` at 0x395E. With Build 4's +2, the first
  pickup is `+2` and the values are even (2, 4 ... 160). The HUD starts at `000`.
- **Big gold popup every 10 is back:** the original game shows the big number when the value is a multiple of 10.
  With odd values (Build 4) that never happened; with even values it does. MAME screenshot: a big `+20` when the
  counter reaches 20. No extra code was needed.
- **Bomb turns bullets and hits into discomen that fly to you:**
  - Per-frame hook at 0x6CE08 (`jsr FRAME_HOOK` at 0x9E4C0). While a bomb is active (`$10E722`), every enemy
    bullet (`$108572`, 70 x 0x40) is removed and a discoman is spawned at its position (spawner 0x6CD0E). A pull
    timer (`$10B400`) is held at 90 frames. While it runs, every uncollected discoman moves up to 0x400 per axis
    per frame toward the bomb's owner (`$10D3C2`), and the game's normal pickup collects it on contact.
  - Enemy-kill hook at 0xA432 (`jmp KILL_HOOK` at 0x9E440). When called by the bomb (a5 = `$10D3B2`), each enemy
    spawns one discoman (spawner 0x6CCDE). A byte per enemy slot (`$10B410`, 120 bytes) stops repeats, because the
    bomb calls the kill routine every frame while the enemy's HP is negative. The bytes are cleared when no bomb is
    active.
  - The game deleted any new discoman while a bomb was active (check at 0x6DA3C). That check is skipped
    (`bpl` -> `bra` at 0x6DA42).
- Measured in MAME (attract demo, which bombs at frames ~3375 and ~3847):
  - 2nd bomb: 4 bullets on screen -> 0, discomen 2 -> 6 the same frame, then collected (counter 84 -> 88 -> 92).
  - 1st bomb: enemies destroyed by the bomb drop discomen that are pulled in. P1 counter 40 -> 44 -> 46 -> 54 ->
    58 during the bomb (stock: no pickups at all during a bomb).
  - Screenshots show the discomen streaming to the ship and big `+40` / `+60` popups.
- Footer `26/11/21 BUILD 5`; MRA name `(26/11/21 Build 5)`.
- Output (from `feversos.zip`):
  - `cv01-u33fever.bin`: CRC32 `20362b2d`, SHA-1 `0e200254a9e1c90e269ca32efc25d57fb9673128`
  - `cv01-u34fever.bin`: CRC32 `08493d7b`, SHA-1 `4b608a8675bb96a127217b71b15d34f389ed7e14`
- Tested: MAME 0.289 (attract demo); the web page gives the same CRCs. Not tested on MiSTer, and not tried by hand.
  The discoman pool cap of 50 wasn't reached in these tests.

## Build 4 (2026-11-21)
- **Discomen count +2 instead of +1** (all discoman kinds). There are five pickup routines (0x6CE70, 0x6D440,
  0x6EA8E, 0x6EDCA, 0x6F3C6). Each adds 1 to three counters per player (P1 `$106C62/$106C3E/$106C3C`, P2
  `$106C82/$106C42/$106C40`); all 30 `addq.w #1` are now `addq.w #2`. The value popup and points are read from
  the counter, so they step by 2 (`+21`, `+23` ...). The 999 caps still apply. The pickup tally
  `$10402A/$10402C` still counts 1 per pickup.
- Measured in MAME (attract demo): the counter changes only by 2s (1, 3, 7, 9, 19, 21 ...), and the HUD climbs about
  twice as fast as stock (frame 3500: 043 vs 021; score 1203 vs 613). A screenshot shows popups `+21` and `+23`.
- Footer `26/11/21 BUILD 4`; MRA name `(26/11/21 Build 4)`.
- Output (from `feversos.zip`):
  - `cv01-u33fever.bin`: CRC32 `1081a306`, SHA-1 `0e565afbbd0fc40471aeac46d72b046d84cc07b0` (same as Build 3:
    all of this build's changes are in even bytes)
  - `cv01-u34fever.bin`: CRC32 `5530cce8`, SHA-1 `4812c01d6f8a2569a1fc6164eeac0d476ef933e6`
- Tested: MAME 0.289; the web page gives the same CRCs. Not tested on MiSTer.

## Build 3 (2026-11-21)
- **BOMB-type powerful shot: up to 8 bombs in flight (was 3).** One byte at 0xAE82: the launch code's free-slot
  search `moveq #2,d7` -> `moveq #7,d7`. Bombs now use shot-list slots +$20..+$100. Explosion pieces share the
  slots from +$A0, which the game already handles, since all 19 slots are processed alike by state.
- Measured in MAME holding button 1 with BOMB type: stock tops out at 3 flying; Build 3 climbs to 8 and stays
  capped at 8, with explosions still spawning alongside. A screenshot shows 8 bombs drawn normally.
- Footer `26/11/21 BUILD 3`; MRA name `(26/11/21 Build 3)`.
- Output (from `feversos.zip`):
  - `cv01-u33fever.bin`: CRC32 `1081a306`, SHA-1 `0e565afbbd0fc40471aeac46d72b046d84cc07b0`
  - `cv01-u34fever.bin`: CRC32 `2fba93ad`, SHA-1 `1f1c3dc93c1f654612c1a2eaecbe8a11c5dba01b`
- Tested: MAME 0.289; the web page gives the same CRCs. Not tested on MiSTer. A long session with heavy bomb use
  (many explosions at once) hasn't been played.

## Build 2 (2026-11-21)
- **Hold button 1 = slowest speed.** While button 1 is held, the ship moves at the slowest of the four speeds.
  Releasing it returns to the selected speed on the next frame. Works for P1 and P2.
  - Hook at 0x9E400 (free space). The player move code's `jsr $788F2` at 0xA9A2 now calls the hook. The hook
    lowers this frame's speed `$1A(a6)` by (selected speed `$39(a6)` - slowest speed, table entry 0 at 0xBFCC).
  - Measured in MAME on speed row 4: 0x168 per frame normally, 0xD0 while held (= the row 1 speed), back to
    0x168 on the frame of release.
- Footer now `26/11/21 BUILD 2`; MRA name `(26/11/21 Build 2)`.
- Output (from `feversos.zip`):
  - `cv01-u33fever.bin`: CRC32 `cb4894be`, SHA-1 `8ab9063d1aac04d06161061b4de269a4a2fa7086`
  - `cv01-u34fever.bin`: CRC32 `c9ebddba`, SHA-1 `dfbcc1be5099b4b8eecc36b7d3fd90d314cb7b6f`
- Tested: MAME 0.289 (boots, movement measured as above). The web page gives the same CRCs. Not tested on MiSTer.

## Build 1 (2026-11-21)
- Title screen: `SALES BY NIHON SYSTEM INC.` -> `NOT FOR SALE` (centred).
- Notice screen: the old warning is replaced by "THIS PROJECT IS UNOFFICIAL AND IS NOT AFFILIATED WITH, ENDORSED
  BY, OR AUTHORIZED BY CAVE. ALL RIGHTS TO THE ORIGINAL GAME AND ITS ASSOCIATED INTELLECTUAL PROPERTY REMAIN WITH
  THEIR RESPECTIVE RIGHTS HOLDERS." The "THIS GAME IS FOR USE IN" and red region lines are blanked.
- Notice footer: `98/09/17 VER.` -> `26/11/21 BUILD 1`. The date comes from the MRA `<name>`.
- The boot ROM-check sums are kept by compensating bytes in unused space (0xAF000-0xAFBFF), so the game boots
  without the MRA's CRC-skip patch.
- Fixed the program byte order in both patchers: u34 = even bytes, u33 = odd bytes. The output CRCs didn't change
  for Build 0, because nothing was patched there.
- Output (from `feversos.zip`):
  - `cv01-u33fever.bin`: CRC32 `12895d17`, SHA-1 `d52f525102226dabc8b2b0d53df91e2b2b1015f8`
  - `cv01-u34fever.bin`: CRC32 `365900ce`, SHA-1 `f598540bd34f7ed16977e373a317d7dd3fc80989`
- Tested: MAME 0.289 boots it, and the notice and title screens show the new text. The web page gives the same CRCs
  as `patch.py`. `mister/Dangun Feveron More Fever.mra` is updated with these CRCs. Not yet tested on MiSTer.
- Web fix (same build, ROM output unchanged): the "Download complete romset" button did nothing. The click handler
  read `ev.currentTarget` after an `await`, when it's already `null`. It now reads the button first. Checked: the
  download gives `dfeveronfever.zip` with the 8 files and the CRCs above.

## Build 0 (2026-11-21)
- Baseline: the Python patcher (`patch.py`) and the web patcher (`index.html`, adapted from the Show Time template).
- No changes (`PATCHES` is empty), so the program data is identical to the original.
- Output is a standalone `dfeveronfever.zip` holding only the 8 dfeveron files, flat. No feversos files and no
  `dfeveron/` folder. Changed files get `fever` appended to the name.
- The web page offers two downloads: the complete romset and `Dangun Feveron More Fever.mra`.
- Output: `cv01-u33fever.bin` CRC32 `e53a7db3`, `cv01-u34fever.bin` CRC32 `be87f19d` (same as the originals).
