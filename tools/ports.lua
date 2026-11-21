-- Print every input port and field name, then exit.
for tag, p in pairs(manager.machine.ioport.ports) do
  for name, f in pairs(p.fields) do print(tag, name, string.format("mask=%x def=%x", f.mask, f.defvalue)) end
end
manager.machine:exit()
