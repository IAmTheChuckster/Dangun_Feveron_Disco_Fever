-- Harness + print a line whenever any of the longs at WL_ADDRS (comma-separated hex) changes, frames WL_FROM..WL_TO.
dofile("lua/harness.lua")
local sp = manager.machine.devices[":maincpu"].spaces["program"]
local addrs = {}
for a in string.gmatch(os.getenv("WL_ADDRS") or "", "%x+") do addrs[#addrs + 1] = tonumber(a, 16) end
local from, to = tonumber(os.getenv("WL_FROM")), tonumber(os.getenv("WL_TO"))
local frame, last = 0, ""
emu.register_frame_done(function()
  frame = frame + 1
  if frame >= from and frame <= to then
    local t = {}
    for _, a in ipairs(addrs) do t[#t + 1] = string.format("%06x=%08x", a, sp:read_u32(a)) end
    local s = table.concat(t, " ")
    if s ~= last then print("f=" .. frame .. " " .. s); last = s end
  end
end)
