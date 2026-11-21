-- Harness + at frame SD_FRAME print every sprite RAM entry (0x400000, 16 bytes each) as 8 words, then exit.
dofile("lua/harness.lua")
local sp = manager.machine.devices[":maincpu"].spaces["program"]
local target = tonumber(os.getenv("SD_FRAME") or "3002")
local frame = 0
emu.register_frame_done(function()
  frame = frame + 1
  if frame == target then
    for i = 0, 0x3FF do
      local a = 0x400000 + i * 16
      local w = {}
      for k = 0, 7 do w[#w + 1] = string.format("%04x", sp:read_u16(a + k * 2)) end
      if w[1] ~= "0000" or w[2] ~= "0000" then print(string.format("%03d %s", i, table.concat(w, " "))) end
    end
    manager.machine:exit()
  end
end)
