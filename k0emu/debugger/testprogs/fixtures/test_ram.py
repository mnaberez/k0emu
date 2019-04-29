import sys
from k0emu.debug import make_debugger_from_argv

def test(debug, outfile):
    address_ranges = (
        # F000-F7FF Internal expansion RAM area (2KB)
        range(0xf000, 0xf800),

        # F800-FAFF Reserved
        range(0xf800, 0xfb00),

        # FB00-FEFF Internal high-speed RAM (1K)
        #   Avoid 0xFE1F and below (stack)
        #   Avoid 0xFEE0 and above (registers)
        range(0xfb00, 0xfe00),
        range(0xfe20, 0xfee0),
    )

    for address_range in address_ranges:
        for pat in (0x55, 0xAA):
            for address in address_range:
                debug.write(address, [pat])
                pat_out = debug.read(address, length=1)[0]

                if pat_out == pat:
                    msg = 'OK'
                else:
                    msg = "DIFFERENT"

                fmt = "%04x: IN=%02x -> OUT=%02x (%s)\n"
                outfile.write(fmt % (address, pat, pat_out, msg))
                outfile.flush()

def main():
    debug = make_debugger_from_argv()
    test(debug, sys.stdout)

if __name__ == '__main__':
    main()
