-- Harness + each frame BC_FROM..BC_TO: count P1 shot-list slots ($10673A+$20.., 19 x 0x20) that are in use,
-- split into flying (state $2 == 0) and exploding. Prints the maximum seen and a line every 10 frames.
dofile("lua/harness.lua")
local sp = manager.machine.devices[":maincpu"].spaces["program"]
local from, to = tonumber(os.getenv("BC_FROM")), tonumber(os.getenv("BC_TO"))
local frame, maxfly = 0, 0
emu.register_frame_done(function()
  frame = frame + 1
  if frame >= from and frame <= to then
    local fly, boom = 0, 0
    for i = 1, 19 do
      local a = 0x10673a + i * 0x20
      if sp:read_u16(a) >= 0x8000 then
        if sp:read_u16(a + 2) == 0 then fly = fly + 1 else boom = boom + 1 end
      end
    end
    if fly > maxfly then maxfly = fly end
    if frame % 10 == 0 then print(string.format("f=%d flying=%d exploding=%d", frame, fly, boom)) end
    if frame == to then print("MAX flying = " .. maxfly) end
  end
end)
