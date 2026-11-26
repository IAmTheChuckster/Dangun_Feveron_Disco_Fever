-- Test helper (not part of the patch): harness + at frame SS_FRAME pretend stage 2 has started for the score box:
-- write P1's stage-1 slot $103FAE = SS_SLOT (hex BCD) and the stage index $1052D8 = 1, then snapshot SS_AFTER
-- frames later and print the live score.
dofile("lua/harness.lua")
local sp = manager.machine.devices[":maincpu"].spaces["program"]
local f, slot = tonumber(os.getenv("SS_FRAME")), tonumber(os.getenv("SS_SLOT"), 16)
local after = tonumber(os.getenv("SS_AFTER") or "2")
local frame = 0
emu.register_frame_done(function()
  frame = frame + 1
  if frame == f then
    sp:write_u32(0x103fae, slot); sp:write_u16(0x1052d8, 1)
    -- optional SS_HIGH (hex BCD): stage high entry for stage index 1 ($103FEA + 4)
    local hi = os.getenv("SS_HIGH")
    if hi then sp:write_u32(0x103fee, tonumber(hi, 16)) end
  end
  if frame == f + after then
    manager.machine.video:snapshot()
    print(string.format("live score $103DE8 = %08x", sp:read_u32(0x103de8)))
  end
end)
