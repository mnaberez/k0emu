import sys
from k0emu.debug import make_debugger_from_argv

def test(debug, outfile):
    for psw in (0x00, 0x01, 0x40, 0x41):
        for a in range(256):
            code = [
                0xa1, psw,          # mov a,#<psw>
                0xf2, 0x1e,         # mov psw,a
                0xa1, a,            # mov a,#<a>
                0x61, 0x90,         # adjbs
                0x9e, 0x06, 0xfe,   # mov 0xfe06,a
                0xf0, 0x1e,         # mov a,psw
                0x9e, 0x07, 0xfe,   # mov 0xfe07,a
                0xaf                # ret
            ]
            debug.write(0xf000, code)
            debug.branch(0xf000)
            a_out, psw_out = debug.read(0xfe06, length=2)

            fmt = "PSW(IN)=%02x, A(IN)=%02x -> PSW(OUT)=%02x, A(OUT)=%02x\n"
            outfile.write(fmt % (psw, a, psw_out, a_out))
            outfile.flush()

def main():
    debug = make_debugger_from_argv()
    test(debug, sys.stdout)

if __name__ == '__main__':
    main()
