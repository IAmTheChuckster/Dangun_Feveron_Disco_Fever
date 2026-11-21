-- Harness + at frame VR_FRAME print the non-zero 32-bit entries of 0x600000-0x601FFF (layer 1 VRAM) with
-- their index, then exit.
dofile("lua/harness.lua")
local sp = manager.machine.devices[":maincpu"].spaces["program"]
local target = tonumber(os.getenv("VR_FRAME") or "3002")
local frame = 0
emu.register_frame_done(function()
  frame = frame + 1
  if frame == target then
    for a = 0x600000, 0x601FFC, 4 do
      local v = sp:read_u32(a)
      if v ~= 0 then print(string.format("%06x %08x", a, v)) end
    end
    manager.machine:exit()
  end
end)
