import sys
from k0emu.debug import make_debugger_from_argv

def test(debug, outfile):
    for a in range(256):
        for x in range(256):
            code = [
                0x11, 0x1e, 0,      # mov psw,#0
                0xa1, a,            # mov a,#<a>
                0xa0, x,            # mov x,#<x>
                0x61, 0x48,         # cmp a,x
                0xf0, 0x1e,         # mov a,psw
                0x9e, 0x07, 0xfe,   # mov 0xfe07,a
                0xaf                # ret
            ]
            debug.write(0xf000, code)
            debug.branch(0xf000)
            psw = debug.read(0xfe07, length=1)[0]

            fmt = "A(IN)=%02x, X(IN)=%02x -> PSW(OUT)=%02x\n"
            outfile.write(fmt % (a, x, psw))
            outfile.flush()

def main():
    debug = make_debugger_from_argv()
    test(debug, sys.stdout)

if __name__ == '__main__':
    main()
