import sys
from k0emu.debug import make_debugger_from_argv

def test(debug, outfile):
    low  = lambda word: word & 0xff
    high = lambda word: word >> 8

    for ax in range(0x10000):
        for imm in range(0x10000):
            code = [
                0x11, 0x1e, 0,              # mov psw,#0
                0x10, low(ax), high(ax),    # movw ax,#<ax>
                0xca, low(imm), high(imm),  # addw ax,#<imm>
                0x03, 0x06, 0xfe,           # movw 0xfe06,ax
                0xf0, 0x1e,                 # mov a,psw
                0x9e, 0x08, 0xfe,           # mov 0xfe08,a
                0xaf                        # ret
            ]
            debug.write(0xf000, code)
            debug.branch(0xf000)
            x_out, a_out, psw_out = debug.read(0xfe06, length=3)
            ax_out = (a_out << 8) + x_out

            fmt = "AX(IN)=%04x, IMM(IN)=%04x -> AX(OUT)=%04x, PSW(OUT)=%02x\n"
            outfile.write(fmt % (ax, imm, ax_out, psw_out))
            outfile.flush()

def main():
    debug = make_debugger_from_argv()
    test(debug, sys.stdout)

if __name__ == '__main__':
    main()
