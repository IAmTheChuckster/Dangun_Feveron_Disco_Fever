#!/bin/sh
# Run dfeveron headless in ~/mame with a schedule file; copy snapshots to $2.
# Usage: tools/run_play.sh <sched> <outdir> [frames] [snap_every]
set -e
SCHED=$(realpath "$1"); OUT=$2; FR=${3:-2000}; SN=${4:-200}
cd ~/mame
export GAME=dfeveron ROMPATH=$PWD/roms
rm -rf work/snap/dfeveron
BT_SCHED=$SCHED BT_SNAP=$SN scripts/run.sh "$FR" >/dev/null 2>&1
mkdir -p "$OUT"; cp work/snap/dfeveron/*.png "$OUT"/
ls "$OUT"
