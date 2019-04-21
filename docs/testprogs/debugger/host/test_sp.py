'''
Check that the stack pointer really is stored in location
0xFF1C as the instruction set encoding implies.

Result = yes, it is.
'''

import debugger

def test_cmp(debug):
    code = [
        # f000 89 1C         movw ax,sp
        0x89, 0x1c,
        # f002 03 00 FE      movw 0xfe00,ax
        0x03, 0x00, 0xfe,
        # f005 89 1C         movw ax,0xff1c
        0x89, 0x1c,
        # f007 03 02 FE      movw 0xfe02,ax
        0x03, 0x02, 0xfe,
        # f00a af            ret
        0xaf
    ]
    for address, value in enumerate(code, 0xf000):
        debug.write_memory(address, value)
    debug.branch(0xf000)

    sp_low = debug.read_memory(0xfe00)
    sp_high = debug.read_memory(0xfe01)
    sp = (sp_high << 8) + sp_low

    ff1c_low = debug.read_memory(0xfe02)
    ff1c_high = debug.read_memory(0xfe03)
    ff1c = (ff1c_high << 8) + ff1c_low

    print("SP=%04x, FF1C=%04x" % (sp, ff1c))

def main():
    debug = debugger.make_debugger()
    test_cmp(debug)

if __name__ == '__main__':
    main()
