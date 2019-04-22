from k0emu.debugger import make_debugger_from_argv

def test(debug):
    for a in range(256):
        for x in range(256):
            code = [
                0xa1, 0,            # mov a,#0
                0xf2, 0x1e,         # mov psw,a
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
            print("CMP A,X with A=%02x, X=%02x: PSW=%02x" % (a, x, psw))

def main():
    debug = make_debugger_from_argv()
    test(debug)

if __name__ == '__main__':
    main()
