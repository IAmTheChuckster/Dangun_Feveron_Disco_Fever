#!/bin/sh
# Run dfeveron (stock set, or ROMPATH) with a schedule and dump RAM at a frame.
# Usage: tools/run_dump.sh <sched> <tag> <frame> [snap_every]   -> ~/mame/work/ram_<tag>.bin, snaps in work/snap/dfeveron
set -e
SCHED=$(realpath "$1")
cd ~/mame
rm -rf work/snap/dfeveron
GAME=dfeveron ROMPATH=${ROMPATH:-/home/brian/mame/roms} BT_SCHED=$SCHED BT_SNAP=${4:-0} RD_TAG=$2 RD_FRAME=$3 \
  HARNESS=/mnt/d/GitHub/Dangun_Feveron/tools/sched_dump.lua scripts/run.sh $(($3 + 1)) >/dev/null 2>&1
ls -la work/ram_$2.bin
