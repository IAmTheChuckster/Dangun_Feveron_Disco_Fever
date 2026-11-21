-- At frame VD_FRAME (default 2200) dump 68000 space 0x300000-0x9FFFFF to work/vdump.bin, then exit.
local target = tonumber(os.getenv("VD_FRAME") or "2200")
local sp = manager.machine.devices[":maincpu"].spaces["program"]
local frame = 0
emu.register_frame_done(function()
  frame = frame + 1
  if frame == target then
    local f = io.open("work/vdump.bin", "wb")
    for base = 0x300000, 0x9FFFFF, 0x10000 do
      local t = {}
      for a = base, base + 0xFFFF, 2 do local v = sp:read_u16(a); t[#t+1] = string.char(v >> 8, v & 255) end
      f:write(table.concat(t))
    end
    f:close()
    manager.machine.video:snapshot()
    manager.machine:exit()
  end
end)
