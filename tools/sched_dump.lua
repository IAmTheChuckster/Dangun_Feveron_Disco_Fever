-- Run the normal harness (BT_SCHED etc.) and also dump 68000 RAM 0x100000-0x10FFFF at frame RD_FRAME
-- to work/ram_<RD_TAG>.bin.
dofile("lua/harness.lua")
local sp = manager.machine.devices[":maincpu"].spaces["program"]
local target = tonumber(os.getenv("RD_FRAME") or "2400")
local tag = os.getenv("RD_TAG") or "x"
local frame = 0
emu.register_frame_done(function()
  frame = frame + 1
  if frame == target then
    local t = {}
    for a = 0x100000, 0x10FFFE, 2 do local v = sp:read_u16(a); t[#t + 1] = string.char(v >> 8, v & 255) end
    local f = io.open("work/ram_" .. tag .. ".bin", "wb"); f:write(table.concat(t)); f:close()
  end
end)
