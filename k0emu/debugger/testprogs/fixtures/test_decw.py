import itertools
import sys
from k0emu.debug import make_debugger_from_argv

def test(debug, outfile):
    low  = lambda word: word & 0xff
    high = lambda word: word >> 8

    psw_iterator = itertools.cycle((0x00, 0x01, 0x10, 0x40, 0x51))
    for ax in range(0xFFFF, -1, -1):
        psw = next(psw_iterator)
        code = [
            0x11, 0x1e, psw,            # mov psw,#<psw>
            0x10, low(ax), high(ax),    # movw ax,#<ax>
            0x90,                       # decw ax
            0x03, 0x06, 0xfe,           # movw 0xfe06,ax
            0xf0, 0x1e,                 # mov a,psw
            0x9e, 0x08, 0xfe,           # mov 0xfe08,a
            0xaf                        # ret
        ]
        debug.write(0xf000, code)
        debug.branch(0xf000)
        x_out, a_out, psw_out = debug.read(0xfe06, length=3)
        ax_out = (a_out << 8) + x_out

        fmt = "AX(IN)=%04x, PSW(IN)=%02x -> AX(OUT)=%04x, PSW(OUT)=%02x\n"
        outfile.write(fmt % (ax, psw, ax_out, psw_out))
        outfile.flush()

def main():
    debug = make_debugger_from_argv()
    test(debug, sys.stdout)

if __name__ == '__main__':
    main()
