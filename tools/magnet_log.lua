-- Test helper (not part of the patch): harness + every frame ML_FROM..ML_TO print P1 position and every active
-- discoman's word0, position and distance (dx, dy) to P1, marking ones within ML_RANGE (hex, default 0x600).
dofile("lua/harness.lua")
local sp = manager.machine.devices[":maincpu"].spaces["program"]
local from, to = tonumber(os.getenv("ML_FROM")), tonumber(os.getenv("ML_TO"))
local range = tonumber(os.getenv("ML_RANGE") or "600", 16)
local frame = 0
local function s16(v) if v >= 0x8000 then return v - 0x10000 end return v end
emu.register_frame_done(function()
  frame = frame + 1
  if frame < from or frame > to then return end
  local px, py = sp:read_u16(0x105a1c), sp:read_u16(0x105a1e)
  local out = {}
  for i = 0, 49 do
    local a = 0x10c5f2 + i * 0x20
    local w = sp:read_u16(a)
    if w >= 0x8000 then
      local dx, dy = s16((px - sp:read_u16(a + 6)) & 0xffff), s16((py - sp:read_u16(a + 8)) & 0xffff)
      local near = (math.abs(dx) <= range and math.abs(dy) <= range) and "*" or ""
      out[#out + 1] = string.format("[%d %04x d=%d,%d%s]", i, w, dx, dy, near)
    end
  end
  if #out > 0 then print(string.format("f=%d P1=%04x,%04x w0=%04x %s", frame, px, py, sp:read_u16(0x105a16), table.concat(out, " "))) end
end)
