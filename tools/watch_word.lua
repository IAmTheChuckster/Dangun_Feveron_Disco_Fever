-- Harness + print every change of the word at WW_ADDR (hex) between frames WW_FROM and WW_TO.
dofile("lua/harness.lua")
local sp = manager.machine.devices[":maincpu"].spaces["program"]
local addr = tonumber(os.getenv("WW_ADDR"), 16)
local from, to = tonumber(os.getenv("WW_FROM")), tonumber(os.getenv("WW_TO"))
local frame, last = 0, nil
emu.register_frame_done(function()
  frame = frame + 1
  if frame >= from and frame <= to then
    local v = sp:read_u16(addr)
    if v ~= last then print(string.format("f=%d %06x=%d", frame, addr, v)); last = v end
  end
end)
