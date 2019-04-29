import sys
from k0emu.debug import make_debugger_from_argv

def test(debug, outfile):
    # bank 0 is the working bank so it is not tested
    for bank, opc in enumerate((0xD8, 0xF0, 0xF8), 1):
        code = [
            0x61, opc,          # sel rb<bank>
            0x10, 0x88, 0x99,   # movw ax,#0x8899
            0x12, 0xaa, 0xbb,   # movw bc,#0xAABB
            0x14, 0xcc, 0xdd,   # movw de,#0xCCDD
            0x16, 0xee, 0xff,   # movw hl,#0xEEFF
            0x61, 0xd0,         # sel rb0
            0xaf,               # ret
        ]
        debug.write(0xf000, code)
        debug.write(0xfee0, [0]*24)
        debug.call(0xf000)
        registers = debug.read(0xfee0, length=24)
        dump = ', '.join([ '%02x' % r for r in registers])
        outfile.write('SEL RB%d FEE0: %s\n' % (bank, dump))
        outfile.flush()

def main():
    debug = make_debugger_from_argv()
    test(debug, sys.stdout)

if __name__ == '__main__':
    main()
