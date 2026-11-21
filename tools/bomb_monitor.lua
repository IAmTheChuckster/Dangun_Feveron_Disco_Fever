-- Harness + every MN_EVERY frames between MN_FROM and MN_TO print: bomb active ($10E722), pull timer ($10B400),
-- active enemy bullets ($108572, 70 x 0x40), active discomen ($10C5F2, 50 x 0x20), P1 counter ($106C3C).
dofile("lua/harness.lua")
local sp = manager.machine.devices[":maincpu"].spaces["program"]
local from, to = tonumber(os.getenv("MN_FROM")), tonumber(os.getenv("MN_TO"))
local every = tonumber(os.getenv("MN_EVERY") or "5")
local frame = 0
local function count(base, n, stride)
  local c = 0
  for i = 0, n - 1 do if sp:read_u16(base + i * stride) >= 0x8000 then c = c + 1 end end
  return c
end
emu.register_frame_done(function()
  frame = frame + 1
  if frame >= from and frame <= to and (frame - from) % every == 0 then
    print(string.format("f=%d bomb=%d pull=%d bullets=%d disco=%d counter=%d", frame, sp:read_u8(0x10e722),
      sp:read_u16(0x10b400), count(0x108572, 70, 0x40), count(0x10c5f2, 50, 0x20), sp:read_u16(0x106c3c)))
  end
end)
