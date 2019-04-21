import debugger

def test(debug):
    code = [
        0xa1, 0x7f,         # mov a,#0x7f
        0xf2, 0x1e,         # mov psw,a
        0xf0, 0x1e,         # mov a,psw
        0x9e, 0x00, 0xfe,   # mov 0xfe00,a
        0xf0, 0x1e,         # mov a,0xff1e
        0x9e, 0x01, 0xfe,   # mov 0xfe01,a
        0xaf,               # ret
    ]
    for address, value in enumerate(code, 0xf000):
        debug.write_memory(address, value)

    for a in range(0x80):
        debug.write_memory(0xf001, a)
        debug.branch(0xf000)

        psw = debug.read_memory(0xfe00)
        ff1e = debug.read_memory(0xfe01)
        extra = ''
        if psw != a:
            extra = ' PSW %02x NOT EQUAL TO VALUE SET %02x' % (psw, a)
        print("PSW=%02x (%s), FF1E=%02x (%s) %s" % (psw, binary(psw), ff1e, binary(ff1e), extra))

def binary(b):
    return bin(b)[2:].rjust(8,'0')

def main():
    debug = debugger.make_debugger()
    test(debug)

if __name__ == '__main__':
    main()
