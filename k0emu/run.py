'''
Usage: k0emu <rom.bin>

'''
import sys

from k0dasm.disassemble import disassemble
from k0emu.system import make_processor


def main():
    proc = make_processor()

    if len(sys.argv) > 1:
        filename = sys.argv[1]
        with open(filename, 'rb') as f:
            rom_data = f.read()
        proc.bus.device("rom").load(0, rom_data)
        proc.bus.reset()
    else:
        sys.stderr.write(__doc__)
        sys.exit(1)

    while True:
        try:
            dasm = disassemble(proc.bus, proc.pc)
            hex_str = ' '.join(["%02x" % x for x in dasm.all_bytes]).ljust(12)
            line = ("%04x: %s %s" % (proc.pc, hex_str, dasm)).ljust(42)
            try:
                proc.step()
            except NotImplementedError:
                line += "!!! NOT IMPLEMENTED !!!"
                print(line)
                break
            line += str(proc)
            line += " T=%d" % proc.total_cycles
            print(line)

        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    main()
