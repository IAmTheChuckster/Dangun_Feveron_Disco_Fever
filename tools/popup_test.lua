-- Test helper (not part of the patch): harness + set the P1 value counter $106C3C to PT_SET1 at frame PT_F1 and to
-- PT_SET2 at frame PT_F2, then snapshot PT_DELAY frames after the counter first reaches each value in PT_WATCH
-- (comma-separated). Prints the frames.
dofile("lua/harness.lua")
local sp = manager.machine.devices[":maincpu"].spaces["program"]
local f1, s1 = tonumber(os.getenv("PT_F1")), tonumber(os.getenv("PT_SET1"))
local f2, s2 = tonumber(os.getenv("PT_F2")), tonumber(os.getenv("PT_SET2"))
local delay = tonumber(os.getenv("PT_DELAY") or "10")
local watch, pending = {}, {}
for v in string.gmatch(os.getenv("PT_WATCH") or "", "%d+") do watch[tonumber(v)] = true end
local frame = 0
emu.register_frame_done(function()
  frame = frame + 1
  if frame == f1 then sp:write_u16(0x106c3c, s1) end
  if frame == f2 then sp:write_u16(0x106c3c, s2) end
  local v = sp:read_u16(0x106c3c)
  if watch[v] then watch[v] = nil; pending[frame + delay] = v; print(string.format("reached %d at frame %d", v, frame)) end
  if pending[frame] then manager.machine.video:snapshot(); print(string.format("snap for %d at frame %d", pending[frame], frame)) end
end)
