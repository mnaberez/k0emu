'''
Usage: k0emu <rom.bin>

'''
import os
import sys

from k0dasm.disassemble import disassemble
from k0emu.processor import Processor

def write_dumpfile(proc): # XXX hack
    home = os.environ['HOME']
    filename = os.path.join(home, 'Desktop/memory.bin')
    with open(filename, 'wb') as f:
        f.write(proc.memory)
    print("\nDump written to: %s" % filename)

def main():
    proc = Processor()

    if len(sys.argv) > 1:
        filename = sys.argv[1]
        with open(filename, 'rb') as f:
            rom = bytearray(f.read())
        proc.write_memory_bytes(0, rom)
        proc.reset()
        for address in range(0xfb00, 0x10000):
            proc.memory[address] = 0
    else:
        sys.stderr.write(__doc__)
        sys.exit(1)

    while True:
        try:
            dasm = disassemble(proc.memory, proc.pc)
            hex = ' '.join(["%02x" % x for x in dasm.all_bytes]).ljust(12)
            line = ("%04x: %s %s" % (proc.pc, hex, dasm)).ljust(42)
            try:
                proc.step()
            except NotImplementedError:
                line += "!!! NOT IMPLEMENTED !!!"
                print(line)
                break
            line += str(proc)

            # interrupt masks
            binary = lambda x: bin(x)[2:].rjust(8, '0')
            for address in range(0xffe4, 0xffe8): # interrupt masks
                line += " %04x=%s" % (address, binary(proc.memory[address]))
            print(line)

            # crash if out of range on software 23
            if proc.pc < 0x135:
                print("CRASH PC")
                break
            if proc.read_sp() > 0xfe1f:
                print("CRASH SP")
                break

        except KeyboardInterrupt:
            break

    write_dumpfile(proc)

if __name__ == "__main__":
    main()
