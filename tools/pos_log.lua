-- Harness + print player 1 position ($6/$8 of the object at $105A16) and speed bytes each frame PL_FROM..PL_TO.
dofile("lua/harness.lua")
local sp = manager.machine.devices[":maincpu"].spaces["program"]
local from, to = tonumber(os.getenv("PL_FROM")), tonumber(os.getenv("PL_TO"))
local frame = 0
emu.register_frame_done(function()
  frame = frame + 1
  if frame >= from and frame <= to then
    print(string.format("f=%d x=%04x y=%04x spd1a=%02x base39=%02x idx=%d btn=%02x", frame, sp:read_u16(0x105a1c),
      sp:read_u16(0x105a1e), sp:read_u8(0x105a30), sp:read_u8(0x105a4f), sp:read_u8(0x105a37), sp:read_u8(0x101615)))
  end
end)
