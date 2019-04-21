import debugger

def test(debug):
    code = [
        # f000 A1 01         [ 4]   31     mov a, #0
        0xa1, 0,
        # f002 A0 02         [ 4]   32     mov x, #0
        0xa0, 0,
        # f004 61 48         [ 4]   33     cmp a, x
        0x61, 0x48,
        # f006 F0 1E         [ 5]   34     mov a ,psw
        0xf0, 0x1e,
        # f008 9E 07 FE      [ 9]   35     mov 0xfe07, a
        0x9e, 0x07, 0xfe,
        # ret
        0xaf
    ]
    for address, value in enumerate(code, 0xf000):
        debug.write_memory(address, value)

    for a in range(256):
        for x in range(256):
            debug.write_memory(0xf001, a) # mov a,#<a>
            debug.write_memory(0xf003, x) # mov x,#<x>
            debug.branch(0xf000)
            psw = debug.read_memory(0xfe07)
            print("CMP A,X with A=%02x, X=%02x: PSW=%02x" % (a, x, psw))

def main():
    debug = debugger.make_debugger()
    test(debug)

if __name__ == '__main__':
    main()
