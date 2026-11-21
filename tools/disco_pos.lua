-- Harness + every DP_EVERY frames in DP_FROM..DP_TO: P1 position and word0, then each active discoman's word0/pos.
dofile("lua/harness.lua")
local sp = manager.machine.devices[":maincpu"].spaces["program"]
local from, to = tonumber(os.getenv("DP_FROM")), tonumber(os.getenv("DP_TO"))
local every = tonumber(os.getenv("DP_EVERY") or "3")
local frame = 0
emu.register_frame_done(function()
  frame = frame + 1
  if frame >= from and frame <= to and (frame - from) % every == 0 then
    local s = string.format("f=%d bomb=%d P1 w0=%04x pos=%04x,%04x |", frame, sp:read_u8(0x10e722),
      sp:read_u16(0x105a16), sp:read_u16(0x105a1c), sp:read_u16(0x105a1e))
    for i = 0, 49 do
      local a = 0x10c5f2 + i * 0x20
      local w = sp:read_u16(a)
      if w >= 0x8000 then
        s = s .. string.format(" [%d %04x %04x,%04x st%04x]", i, w, sp:read_u16(a + 6), sp:read_u16(a + 8), sp:read_u16(a + 2))
      end
    end
    print(s)
  end
end)
