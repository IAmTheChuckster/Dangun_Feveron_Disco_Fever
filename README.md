# Dangun Feveron Disco Fever

A gameplay patch for `Dangun Feveron (Japan, 98/09/17 VER.)`<br>
This repository holds only source, tools and notes. **No ROM data is included**; you patch your own legally owned dump.
   
## About
Why did I make this? Because it's fun and for my own personal research to see the capabilities of Claude.<br>
While Claude was used I put effort in making sure there are balanced gameplay.<br>
I did all the testing and planning.

## Change Notes
- Title screen reads `NOT FOR SALE` instead of `SALES BY NIHON SYSTEM INC.`, and shows `DISCO FEVER` above `PLEASE INSERT COIN`.
- The notice screen shows an unofficial-project disclaimer, with the release date and build number in the footer.
- The score shown at the top left is your running total for the whole game; it no longer restarts at 0 each stage, and the score box widens to fit up to 8 digits. The word STAGE is removed from STAGE HIGH to make room.
- Extra life: a 1UP drops every 1000 discomen collected (originally once, at 2000).
- A bomb item drops every 100 discomen collected.
- Hold button 1 to move at the slowest speed; let go to return to your selected speed.
- BOMB-type powerful shot: up to 8 bombs in flight instead of 3.
- Each discoman adds 2 to the counter instead of 1, and the counter starts at 0, so pickups go +2, +4, +6 ... and every multiple of 10 shows the big gold number (1.5x size at every 100, 2x at every 1000). The counter box still stops at 999, but the popup values and score keep growing up to 9999.
- Bomb: enemy bullets on screen turn into discomen, enemies drop discomen while the bomb hits them (and when it destroys them), and they all fly to you and are collected.

## Patching the game

### Web Patcher
Open the **[Web Patcher](https://iamthechuckster.github.io/Dangun_Feveron_Disco_Fever/)** (`index.html`) and drop in your `feversos.zip` (or `dfeveron.zip`). It checks the file names and CRCs, builds the patched files automatically, and lets you download the complete `dfeveronfever.zip` romset and the MiSTer `Dangun Feveron More Fever.mra`. Everything runs in your browser; nothing is uploaded.

### With Python
Needs Python 3 (no extra packages):
```
python patch.py feversos.zip
```
This writes a standalone patched `dfeveronfever.zip` next to `patch.py` and updates the CRCs in `mister/Dangun Feveron More Fever.mra` (use `-o` to choose another path). `dfeveron.zip` or a folder with the loose files works too.

## Testing
This patch was tested with MAME 0.289<br>
It may even work on a PCB but do so on your own risk.

## Credits

- [IAmTheChuckster](https://github.com/IAmTheChuckster)  project, testing
- [Claude](https://claude.ai) (Anthropic)  reverse engineering and patcher code
- Tested on the MiSTer FPGA

## Disclaimer

This repository contains a fan-made patch for research and technical analysis. The repository does not intentionally distribute the original game ROM, executable, or game assets. Users must obtain their own copy of the original game. This project is unofficial and is not affiliated with, endorsed by, or authorized by CAVE. All rights to the original game and its associated intellectual property remain with their respective rights holders. No license to third-party copyrighted material is granted by this repository.
