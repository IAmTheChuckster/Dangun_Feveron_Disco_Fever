-- Test helper (not part of the patch): harness + final_stage.lua features, and print the TLB conditions every time
-- the stage index changes: $10E816, $103FA4, $103FA8, $10529C, $10529E (0xF94 tests them when the final stage
-- starts), plus how often the TLB flag store at 0xFD6 runs (counted via reads of $10529E at the test before it).
dofile("/mnt/d/GitHub/Dangun_Feveron/tools/final_stage.lua")
local cpu = manager.machine.devices[":maincpu"]
local sp2 = cpu.spaces["program"]
local reached = 0
tlb_tap = sp2:install_read_tap(0x10529e, 0x10529f, "tlb", function(off, data, mask)
  local pc = cpu.state["PC"].value
  if pc >= 0xfcc and pc <= 0xfd8 then reached = reached + 1 end
end)
local last = -1
emu.register_frame_done(function()
  local st = sp2:read_u16(0x1052d8)
  if st ~= last then
    print(string.format("STAGE %d: e816=%04x fa4=%04x fa8=%04x 529c=%04x 529e=%04x lives=%d deathcheck_reached=%d",
      st, sp2:read_u16(0x10e816), sp2:read_u16(0x103fa4), sp2:read_u16(0x103fa8), sp2:read_u16(0x10529c),
      sp2:read_u16(0x10529e), sp2:read_u16(0x1052c4), reached))
    last = st
  end
end)
