-- Test helper (not part of the patch): harness + jump to a stage and keep P1 alive.
--  FS_STAGE  stage index to force (written to $1052D8 every frame from FS_SETFROM to FS_SETTO, before the stage loads)
--  FS_GOD    1 = P1 invincible ($3E of the player object = 0xFF every frame; the collision code skips 0xFF)
--  FS_DIEAT  optional frame at which invincibility is dropped for FS_DIEFOR frames (to record a death)
--  FS_EVERY  print stage / lives / boss-ish state every N frames
dofile("lua/harness.lua")
local sp = manager.machine.devices[":maincpu"].spaces["program"]
local stage = tonumber(os.getenv("FS_STAGE") or "6")
local setfrom, setto = tonumber(os.getenv("FS_SETFROM") or "1820"), tonumber(os.getenv("FS_SETTO") or "1880")
local god = os.getenv("FS_GOD") == "1"
local dieat, diefor = tonumber(os.getenv("FS_DIEAT") or "0"), tonumber(os.getenv("FS_DIEFOR") or "200")
local every = tonumber(os.getenv("FS_EVERY") or "300")
local godfrom = tonumber(os.getenv("FS_GODFROM") or "1900")   -- 0 when starting from a save state
local watch = tonumber(os.getenv("FS_WATCH") or "0")          -- print player state changes up to this frame
if watch == 0 then watch = nil end
local lastw = ""
local lives_keep = tonumber(os.getenv("FS_LIVES") or "0")
if lives_keep == 0 then lives_keep = nil end
local frame = 0
-- FS_NOHIT=1: strip bit 8 (the "hit" bit, bit 0 of the high byte) from every write to P1's state word $105A16,
-- so P1 can never start dying (the player code at 0xA898 tests it). A write tap's return value replaces the data.
if os.getenv("FS_NOHIT") == "1" then
  nohit_tap = sp:install_write_tap(0x105a16, 0x105a17, "nohit", function(off, data, mask)
    if frame >= godfrom and off == 0x105a16 then return data & ~0x0100 end
  end)
end
emu.register_frame_done(function()
  frame = frame + 1
  if frame >= setfrom and frame <= setto then sp:write_u16(0x1052d8, stage) end
  local dying = dieat > 0 and frame >= dieat and frame < dieat + diefor
  -- only once the game is running: writing RAM during the power-on RAM test makes the boot hang
  if god and not dying and frame >= godfrom then sp:write_u8(0x105a54, 0xff) end
  -- FS_LIVES=n: keep P1's lives topped up to n (deaths still happen and are recorded, but the game never ends)
  if lives_keep and frame >= godfrom and sp:read_u16(0x1052c4) > 0 and sp:read_u16(0x1052c4) < lives_keep then
    sp:write_u16(0x1052c4, lives_keep)
  end
  if watch and frame <= watch then
    local s = string.format("w0=%04x st=%04x 3e=%02x lives=%d e8=%04x", sp:read_u16(0x105a16), sp:read_u16(0x105a18),
      sp:read_u8(0x105a54), sp:read_u16(0x1052c4), sp:read_u16(0x1050e8))
    if s ~= lastw then print("f=" .. frame .. " " .. s); lastw = s end
  end
  if frame % every == 0 then
    print(string.format("f=%d stage=%d lives=%d score=%08x rank=%08x e722=%d", frame, sp:read_u16(0x1052d8),
      sp:read_u16(0x1052c4), sp:read_u32(0x103de8), sp:read_u32(0x105118), sp:read_u8(0x10e722)))
  end
end)
