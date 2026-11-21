-- Hold Coin 1 for frames 1300-1310 and print IN0 as MAME and as the CPU sees it.
local p = manager.machine.ioport.ports[":IN0"]
local coin
for name, f in pairs(p.fields) do if name == "Coin 1" then coin = f end end
local frame = 0
emu.register_frame_done(function()
  frame = frame + 1
  if frame == 1300 then coin:set_value(1) end
  if frame == 1310 then coin:set_value(0) end
  if frame >= 1298 and frame <= 1312 then print(frame, string.format("IN0=%04x", p:read())) end
  if frame == 1320 then manager.machine:exit() end
end)
