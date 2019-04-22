import os
import sys
import importlib.util
from k0emu.debug import make_debugger_from_argv

def main(debug):
    here = os.path.abspath(os.path.join(os.path.dirname(__file__), 'fixtures'))
    for filename in sorted(os.listdir(here)):
        if not filename.startswith('test_') or not filename.endswith('.py'):
            continue
        fullname = os.path.join(here, filename)

        basename = os.path.basename(filename).split('.')[0] + '.txt'
        if 'emulator' in sys.argv:
            what = 'emulator'
        else:
            what = 'serial'
        outfilename = os.path.abspath(os.path.join(here, '..', 'results', what, basename))

        if os.path.exists(outfilename):
            print("Skipping %s on %s (report exists)" % (basename, what))
        else:
            print("Running %s on %s" % (basename, what))
            with open(outfilename, 'w') as outfile:
                spec = importlib.util.spec_from_file_location("module.name", fullname)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                mod.test(debug, outfile)

if __name__ == '__main__':
    debug = make_debugger_from_argv()
    main(debug)
