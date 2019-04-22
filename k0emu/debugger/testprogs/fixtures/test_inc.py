import sys
from k0emu.debug import make_debugger_from_argv

def test(debug, outfile):
    for a in range(256):
        code = [
           0xA1, 0x00,          # mov a,#0
           0xF2, 0x1E,          # mov psw,a
           0xA1, a,             # mov a,#<a>
           0x41,                # inc a
           0x9E, 0x00, 0xFE,    # mov 0xfe00,a
           0xF0, 0x1E,          # mov a,psw
           0x9E, 0x01, 0xFE,    # mov 0xfe01,a
        ]
        debug.write(0xf000, code)
        debug.branch(0xf000)
        a_out, psw = debug.read(0xfe00, length=2)

        fmt = "A(IN)=%02x -> A(OUT)=%02x, PSW(OUT)=%02x\n"
        outfile.write(fmt % (a, a_out, psw))
        outfile.flush()

def main():
    debug = make_debugger_from_argv()
    test(debug, sys.stdout)

if __name__ == '__main__':
    main()
