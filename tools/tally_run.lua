-- Test helper (not part of the patch): final_stage.lua (lives top-up etc.) plus snapshots at SN_FRAMES.
dofile("/mnt/d/GitHub/Dangun_Feveron/tools/final_stage.lua")
local want = {}
for f in string.gmatch(os.getenv("SN_FRAMES") or "", "%d+") do want[tonumber(f)] = true end
local n = 0
emu.register_frame_done(function()
  n = n + 1
  if want[n] then manager.machine.video:snapshot() end
end)
