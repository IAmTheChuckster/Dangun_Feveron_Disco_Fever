-- Coin at frame 1300; print RAM words that differ between frame 1299 and 1330, plus $101620 and $1050e8.
local sp = manager.machine.devices[":maincpu"].spaces["program"]
local p = manager.machine.ioport.ports[":IN0"]
local coin
for name, f in pairs(p.fields) do if name == "Coin 1" then coin = f end end
local frame, before = 0, {}
emu.register_frame_done(function()
  frame = frame + 1
  if frame == 1299 then for a = 0x100000, 0x10FFFE, 2 do before[a] = sp:read_u16(a) end end
  if frame == 1300 then coin:set_value(1) end
  if frame == 1303 then coin:set_value(0) end
  if frame == 1330 then
    print(string.format("101620=%04x 1050e8=%04x 10172e=%04x", sp:read_u16(0x101620), sp:read_u16(0x1050e8), sp:read_u16(0x10172e)))
    local n = 0
    for a = 0x100000, 0x10FFFE, 2 do
      local v = sp:read_u16(a)
      if v ~= before[a] and n < 60 then print(string.format("%06x %04x -> %04x", a, before[a], v)); n = n + 1 end
    end
    manager.machine:exit()
  end
end)
