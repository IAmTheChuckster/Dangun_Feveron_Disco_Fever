-- Log the PCs that read the input ports (0xB00000-0xB00003), frames 1290-1320, with a coin at 1300.
local cpu = manager.machine.devices[":maincpu"]
local sp = cpu.spaces["program"]
local p = manager.machine.ioport.ports[":IN0"]
local coin
for name, f in pairs(p.fields) do if name == "Coin 1" then coin = f end end
local frame, seen = 0, {}
tap = sp:install_read_tap(0xA00000, 0xBFFFFF, "r", function(off, data, mask)
  if frame >= 1290 then
    local k = string.format("%06x@%06x", off, cpu.state["PC"].value)
    if not seen[k] then seen[k] = true; print(frame, k, string.format("%04x", data)) end
  end
end)
emu.register_frame_done(function()
  frame = frame + 1
  if frame == 1300 then coin:set_value(1) end
  if frame == 1302 then coin:set_value(0) end
  if frame == 1320 then manager.machine:exit() end
end)
