import os
import sys

def main():
    serial_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'results/serial'))
    emulator_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'results/emulator'))

    serial_filenames = [ f for f in sorted(os.listdir(serial_dir)) if f.endswith('.txt') ]
    exitcode = 0
    for basename in serial_filenames:
        s_filename = os.path.join(serial_dir, basename)
        e_filename = os.path.join(emulator_dir, basename)

        if os.path.exists(e_filename):
            with open(s_filename) as f:
                s_contents = f.read()
            with open(e_filename) as f:
                e_contents = f.read()

            if s_contents == e_contents:
                result = 'ok'
            else:
                exitcode = 1
                result = 'DIFFERENT'

        else:
            exitcode = 1
            result = 'MISSING'

        print("%s: %s" % (basename, result))
    sys.exit(exitcode)

if __name__ == '__main__':
    assert sys.version_info[0] >= 3
    main()
