import sys
from k0emu.debug import make_debugger_from_argv

def test(debug, outfile):
    for a in range(256):
        for mem in range(256):
            code = [
                0x16, 0x00, 0xfe,   # movw hl,#0xfe00
                0xa1, mem,          # mov a,#<mem>
                0x97,               # mov [hl],a
                0xa1, a,            # mov a,#<a>
                0x31, 0x80,         # rol4 [hl]
                0x9e, 0x01, 0xfe,   # mov 0xfe01,a
                0xaf                # ret
            ]
            debug.write(0xf000, code)
            debug.call(0xf000)
            mem_out, a_out = debug.read(0xfe00, length=2)

            fmt = "A(IN)=%02x, MEM(IN)=%02x -> A(OUT)=%02x, MEM(OUT)=%02x\n"
            outfile.write(fmt % (a, mem, a_out, mem_out))
            outfile.flush()

def main():
    debug = make_debugger_from_argv()
    test(debug, sys.stdout)

if __name__ == '__main__':
    main()
