import sys
from k0emu.debug import make_debugger_from_argv

def test(debug, outfile):
    for psw in (0, 1):
        for a in range(256):
            code = [
                0x11, 0x1e, psw,     # mov psw,#<psw
                0xA1, a,             # mov a,#<a>
                0x25,                # rorc a,1
                0x9E, 0x00, 0xFE,    # mov 0xfe00,a
                0xF0, 0x1E,          # mov a,psw
                0x9E, 0x01, 0xFE,    # mov 0xfe01,a
                0xAF,                # ret
            ]
            debug.write(0xf000, code)
            debug.branch(0xf000)
            a_out, psw_out = debug.read(0xfe00, length=2)

            fmt = "A(IN)=%02x, PSW(IN)=%02x -> A(OUT)=%02x, PSW(OUT)=%02x\n"
            outfile.write(fmt % (a, psw, a_out, psw_out))
            outfile.flush()

def main():
    debug = make_debugger_from_argv()
    test(debug, sys.stdout)

if __name__ == '__main__':
    main()
