-- Test helper (not part of the patch): harness + hold a HUD slide word (HS_ADDR hex, default $10518C) at HS_VAL (hex) from frame
-- HS_FROM, snapshot at SN_FRAMES, exit after the last one.
dofile("lua/harness.lua")
local sp = manager.machine.devices[":maincpu"].spaces["program"]
local from, val = tonumber(os.getenv("HS_FROM")), tonumber(os.getenv("HS_VAL"), 16)
local addr = tonumber(os.getenv("HS_ADDR") or "10518c", 16)
local want, last = {}, 0
for f in string.gmatch(os.getenv("SN_FRAMES") or "", "%d+") do want[tonumber(f)] = true; last = math.max(last, tonumber(f)) end
local frame = 0
emu.register_frame_done(function()
  frame = frame + 1
  if frame >= from then sp:write_u16(addr, val) end
  if want[frame] then manager.machine.video:snapshot() end
  if frame >= last then manager.machine:exit() end
end)
