-- Test helper (not part of the patch): harness + set the pickup counter $10510C at chosen frames, and print the
-- counter, the 1UP flag $105112, lives ($1052C4/$1052C6), bomb stocks ($105A3B/$105A7B) and how many 1UP (kind 5)
-- and bomb (kind 3) items exist in the item list ($10C372, 20 x 0x20), whenever any of them changes.
-- ET_SETS = "frame:value,frame:value,..."   ET_TO = last frame to print.
dofile("lua/harness.lua")
local sp = manager.machine.devices[":maincpu"].spaces["program"]
local at = {}
for f, v in string.gmatch(os.getenv("ET_SETS") or "", "(%d+):(%d+)") do at[tonumber(f)] = tonumber(v) end
local to = tonumber(os.getenv("ET_TO") or "3600")
local frame, last = 0, ""
emu.register_frame_done(function()
  frame = frame + 1
  if at[frame] then sp:write_u32(0x10510c, at[frame]) end
  if frame <= to then
    local oneup, bomb = 0, 0
    for i = 0, 19 do
      local w = sp:read_u16(0x10c372 + i * 0x20)
      if w >= 0x8000 and (w & 7) == 5 then oneup = oneup + 1 end
      if w >= 0x8000 and (w & 7) == 3 then bomb = bomb + 1 end
    end
    local s = string.format("count=%d flag=%04x lives=%d/%d bombs=%d/%d 1UP_items=%d bomb_items=%d",
      sp:read_u32(0x10510c), sp:read_u16(0x105112), sp:read_u16(0x1052c4), sp:read_u16(0x1052c6),
      sp:read_u8(0x105a3b), sp:read_u8(0x105a7b), oneup, bomb)
    if s ~= last then print("f=" .. frame .. " " .. s); last = s end
  end
end)
