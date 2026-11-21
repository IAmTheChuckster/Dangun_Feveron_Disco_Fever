-- Harness + take a snapshot at each frame listed in SN_FRAMES (comma-separated), then exit after the last one.
dofile("lua/harness.lua")
local want, last = {}, 0
for f in string.gmatch(os.getenv("SN_FRAMES") or "", "%d+") do want[tonumber(f)] = true; last = math.max(last, tonumber(f)) end
local frame = 0
emu.register_frame_done(function()
  frame = frame + 1
  if want[frame] then manager.machine.video:snapshot() end
end)
