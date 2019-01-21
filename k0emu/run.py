'''
Usage: k0dasm <rom.bin>

'''
import sys

from k0dasm.disassemble import disassemble
from k0emu.processor import Processor

def main():
    proc = Processor()

    if len(sys.argv) > 1:
        filename = sys.argv[1]
        with open(filename, 'rb') as f:
            rom = bytearray(f.read())
        proc.write_memory(0, rom)
        proc.reset()
        for address in range(0xfb00, 0x10000):
            proc.memory[address] = 0x17
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
            print(line)
        except KeyboardInterrupt:
            break

    filename = "/Users/mnaberez/Desktop/memory.bin"
    with open(filename, 'wb') as f:
        f.write(proc.memory)
    print("\nDump written to: %s" % filename)

if __name__ == "__main__":
    main()
