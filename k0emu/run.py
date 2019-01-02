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
    else:
        sys.stderr.write(__doc__)
        sys.exit(1)

    while True:
        dasm = disassemble(proc.memory, proc.pc)
        hex = ' '.join(["%02x" % x for x in dasm.all_bytes]).ljust(12)
        line = ("%04x: %s %s" % (proc.pc, hex, dasm)).ljust(36)
        try:
            proc.step()
        except NotImplementedError:
            line += "!!! NOT IMPLEMENTED !!!"
            print(line)
            sys.exit(1)
        line += str(proc)
        print(line)

if __name__ == "__main__":
    main()
