-- Harness + log unique PCs that READ a range (TR_LO..TR_HI) between frames TR_FROM and TR_TO, with A0-A6.
dofile("lua/harness.lua")
local cpu = manager.machine.devices[":maincpu"]
local sp = cpu.spaces["program"]
local lo, hi = tonumber(os.getenv("TR_LO"), 16), tonumber(os.getenv("TR_HI"), 16)
local from, to = tonumber(os.getenv("TR_FROM")), tonumber(os.getenv("TR_TO"))
local mode = os.getenv("TR_MODE") or "r"
local frame, seen = 0, {}
local out = io.open("work/tap_read.log", "w")
local function cb(off, data, mask)
  if frame >= from and frame <= to then
    local pc = cpu.state["PC"].value
    local k = string.format("%06x@%06x", off, pc)
    if not seen[k] then
      seen[k] = true
      local r = {}
      for _, n in ipairs({"A0", "A1", "A2", "A3", "A4", "A5", "A6", "D0", "D1"}) do r[#r + 1] = string.format("%s=%08x", n, cpu.state[n].value) end
      out:write(string.format("f=%d %s d=%04x %s\n", frame, k, data, table.concat(r, " ")))
    end
  end
end
if mode == "w" then tap2 = sp:install_write_tap(lo, hi, "tw", cb) else tap2 = sp:install_read_tap(lo, hi, "tr", cb) end
emu.register_frame_done(function()
  frame = frame + 1
  if frame == to + 1 then out:close() end
end)
