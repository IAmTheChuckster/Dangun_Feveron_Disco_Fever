#!/bin/sh
# Usage: tools/run_tap.sh <sched> <lo hex> <hi hex> <from> <to> [r|w]   -> ~/mame/work/tap_read.log
set -e
SCHED=$(realpath "$1")
cd ~/mame
GAME=dfeveron ROMPATH=${ROMPATH:-/home/brian/mame/roms} BT_SCHED=$SCHED BT_SNAP=0 TR_LO=$2 TR_HI=$3 TR_FROM=$4 TR_TO=$5 TR_MODE=${6:-r} \
  HARNESS=/mnt/d/GitHub/Dangun_Feveron/tools/tap_read_range.lua scripts/run.sh $(($5 + 2)) >/dev/null 2>&1
wc -l work/tap_read.log
