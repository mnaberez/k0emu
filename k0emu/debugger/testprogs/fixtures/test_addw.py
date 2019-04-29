import sys
from k0emu.debug import make_debugger_from_argv

def test(debug, outfile):
    low  = lambda word: word & 0xff
    high = lambda word: word >> 8

    # due to latency of the usb-serial adapter, sending one code
    # payload per addw test takes far too long.  we batch multiple
    # multiple addw tests into one code payload to speed it up.
    batch_size = 8

    for ax in range(0, 0x10000):
        for imm_start in range(0, 0x10000, batch_size):
            # generate test code for <batch_size> additions
            code = []
            for i in range(batch_size):
                imm = imm_start + i    # immediate number to add
                res = 0xfe00 + (i * 3) # results address
                code.extend([
                    0x11, 0x1e, 0,                  # mov psw,#0
                    0x10, low(ax), high(ax),        # movw ax,#<ax>
                    0xca, low(imm), high(imm),      # addw ax,#<imm>
                    0x9e, low(res+1), high(res+1),  # mov <res+1>,a
                    0x60,                           # mov a,x
                    0x9e, low(res+0), high(res+0),  # mov <res+0>,a
                    0xf0, 0x1e,                     # mov a,psw
                    0x9e, low(res+2), high(res+2),  # mov <res+2>,a
                ])
            code.append(0xaf) # ret

            # run test code, collect results of 3 bytes each * <batch_size>
            debug.write(0xf000, code)
            debug.call(0xf000)
            results = debug.read(0xfe00, length=batch_size * 3)

            # parse results and print them
            res_offset = 0
            for i in range(batch_size):
                imm = imm_start + i
                x_out, a_out, psw_out = (results[res_offset],
                                         results[res_offset+1],
                                         results[res_offset+2])
                ax_out = (a_out << 8) + x_out
                fmt = "AX(IN)=%04x, IMM(IN)=%04x -> AX(OUT)=%04x, PSW(OUT)=%02x\n"
                outfile.write(fmt % (ax, imm, ax_out, psw_out))
                res_offset += 3

            outfile.flush()

def main():
    debug = make_debugger_from_argv()
    test(debug, sys.stdout)

if __name__ == '__main__':
    main()
