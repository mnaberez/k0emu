import sys
from k0emu.debug import make_debugger_from_argv

def test(debug, outfile):
    for psw in (0, 1):
        for a in range(256):
            for x in range(256):
                code = [
                    0x11, 0x1e, psw,    # mov psw,#<psw>
                    0xa1, a,            # mov a,#<a>
                    0xa0, x,            # mov x,#<x>
                    0x61, 0x08,         # add a,x
                    0x9e, 0x06, 0xfe,   # mov 0xfe06,a
                    0xf0, 0x1e,         # mov a,psw
                    0x9e, 0x07, 0xfe,   # mov 0xfe07,a
                    0xaf                # ret
                ]
                debug.write(0xf000, code)
                debug.call(0xf000)
                a_out, psw_out = debug.read(0xfe06, length=2)

                fmt = "A(IN)=%02x, X(IN)=%02x, PSW(IN)=%02x -> A(OUT)=%02x, PSW(OUT)=%02x\n"
                outfile.write(fmt % (a, x, psw, a_out, psw_out))
                outfile.flush()

def main():
    debug = make_debugger_from_argv()
    test(debug, sys.stdout)

if __name__ == '__main__':
    main()
