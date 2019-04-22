'''
Check that the stack pointer really is stored in location
0xFF1C as the instruction set encoding implies.

Result = yes, it is.
'''

import sys
from k0emu.debug import make_debugger_from_argv

def test(debug, outfile):
    code = [
        0x89, 0x1c,         # movw ax,sp
        0x03, 0x00, 0xfe,   # movw 0xfe00,ax
        0x89, 0x1c,         # movw ax,0xff1c
        0x03, 0x02, 0xfe,   # movw 0xfe02,ax
        0xaf                # ret
    ]
    debug.write(0xf000, code)
    debug.branch(0xf000)

    sp_low, sp_high, ff1c_low, ff1c_high = debug.read(0xfe00, length=4)
    sp = (sp_high << 8) + sp_low
    ff1c = (ff1c_high << 8) + ff1c_low

    outfile.write("SP=%04x, FF1C=%04x\n" % (sp, ff1c))
    outfile.flush()

def main():
    debug = make_debugger_from_argv()
    test(debug, sys.stdout)

if __name__ == '__main__':
    main()
