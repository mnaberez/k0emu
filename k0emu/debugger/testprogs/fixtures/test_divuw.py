import sys
from k0emu.debug import make_debugger_from_argv

def test(debug, outfile):
    for a in range(256):
        for x in range(256):
            for c in range(256):
                code = [
                    0xa1, 0,            # mov a,#0
                    0xf2, 0x1e,         # mov psw,a
                    0xa1, a,            # mov a,#<a>
                    0xa0, x,            # mov x,#<x>
                    0xa2, c,            # mov c,#<c>
                    0x31, 0x82,         # divuw c
                    0x9e, 0x06, 0xfe,   # mov 0xfe06,a
                    0x60,               # mov a,x
                    0x9e, 0x07, 0xfe,   # mov 0xfe07,a
                    0x62,               # mov a,c
                    0x9e, 0x08, 0xfe,   # mov 0xfe08,a
                    0xf0, 0x1e,         # mov a,psw
                    0x9e, 0x08, 0xfe,   # mov 0xfe09,a
                    0xaf                # ret
                ]
                debug.write(0xf000, code)
                debug.branch(0xf000)
                a_out, x_out, c_out, psw_out = debug.read(0xfe06, length=4)

                fmt = "A(IN)=%02x, X(IN)=%02x, C(IN)=%02x -> " \
                      "A(OUT)=%02x, X(OUT)=%02x, C(OUT)=%02x, PSW(OUT)=%02x\n"
                outfile.write(fmt % (a, x, c, a_out, x_out, c_out, psw_out))
                outfile.flush()

def main():
    debug = make_debugger_from_argv()
    test(debug, sys.stdout)

if __name__ == '__main__':
    main()