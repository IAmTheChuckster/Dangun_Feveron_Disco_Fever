-- Harness + count reads of address CP_ADDR (hex) made at PC CP_PC (hex) between frames CP_FROM and CP_TO.
-- Used to count how often a hook runs (it reads a known variable at a known PC).
dofile("lua/harness.lua")
local cpu = manager.machine.devices[":maincpu"]
local sp = cpu.spaces["program"]
local addr, pc = tonumber(os.getenv("CP_ADDR"), 16), tonumber(os.getenv("CP_PC"), 16)
local from, to = tonumber(os.getenv("CP_FROM")), tonumber(os.getenv("CP_TO"))
local frame, n, frames = 0, 0, {}
tap3 = sp:install_read_tap(addr, addr + 1, "cp", function(off, data, mask)
  if frame >= from and frame <= to and cpu.state["PC"].value == pc then
    n = n + 1; frames[frame] = (frames[frame] or 0) + 1
  end
end)
emu.register_frame_done(function()
  frame = frame + 1
  if frame == to then
    local hits = 0
    for _ in pairs(frames) do hits = hits + 1 end
    print(string.format("calls=%d on %d frames", n, hits))
  end
end)
