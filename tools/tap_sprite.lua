-- Log the PC and registers of every write to a sprite RAM range, from frame TAP_FROM to TAP_TO.
local cpu = manager.machine.devices[":maincpu"]
local sp = cpu.spaces["program"]
local lo = tonumber(os.getenv("TAP_LO") or "400230", 16)
local hi = tonumber(os.getenv("TAP_HI") or "40026f", 16)
local from = tonumber(os.getenv("TAP_FROM") or "2150")
local to = tonumber(os.getenv("TAP_TO") or "2200")
local out = io.open("work/tap.log", "w")
local frame = 0
local function r(n) return cpu.state[n].value end
tap = sp:install_write_tap(lo, hi, "t", function(off, data, mask)
  if frame >= from and frame <= to then
    out:write(string.format("f=%d pc=%06x a=%06x d=%04x A0=%08x A1=%08x A2=%08x A3=%08x D0=%08x D1=%08x\n",
      frame, r("PC"), off, data, r("A0"), r("A1"), r("A2"), r("A3"), r("D0"), r("D1")))
  end
end)
emu.register_frame_done(function()
  frame = frame + 1
  if frame > to then out:close(); manager.machine:exit() end
end)
