from k0dasm.disassemble import disassemble
from processor import Processor

proc = Processor()
proc.write_memory(0x0000, [
    0x9a, 0xcd, 0xab,  # call 0xabcd
])
proc.write_memory(0xabcd, [
    0x00, # nop
    0x00, # nop
    0xaf, # ret
])
proc.pc = 0

for i in range(11):
    print("%04x: %s" % (proc.pc, disassemble(proc.memory, proc.pc)))
    proc.step()
