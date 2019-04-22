from k0emu.debugger import make_debugger_from_argv

def test(debug):
    for a in range(0x80):
        code = [
            0xa1, a,            # mov a,#<a>
            0xf2, 0x1e,         # mov psw,a
            0xf0, 0x1e,         # mov a,psw
            0x9e, 0x00, 0xfe,   # mov 0xfe00,a
            0xf0, 0x1e,         # mov a,0xff1e
            0x9e, 0x01, 0xfe,   # mov 0xfe01,a
            0xaf,               # ret
        ]
        debug.write(0xf000, code)
        debug.branch(0xf000)
        psw, ff1e = debug.read(0xfe00, length=2)
        extra = ''
        if psw != a:
            extra = ' PSW %02x NOT EQUAL TO VALUE SET %02x' % (psw, a)
        print("PSW=%02x (%s), FF1E=%02x (%s) %s" % (psw, binary(psw), ff1e, binary(ff1e), extra))

def binary(b):
    return bin(b)[2:].rjust(8,'0')

def main():
    debug = make_debugger_from_argv()
    test(debug)

if __name__ == '__main__':
    main()
