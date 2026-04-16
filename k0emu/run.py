'''
Usage: k0emu <rom.bin>
       k0emu --map

'''
import sys

from k0dasm.disassemble import disassemble
from k0emu.processor import RegisterPairs, Flags
from k0emu.system import make_processor


class Runner(object):
    def __init__(self, proc=None, output=None):
        self.proc = proc or make_processor()
        self.output = output or sys.stdout

    def load(self, rom_data):
        self.proc.bus.device("rom").load(0, rom_data)
        self.proc.bus.reset()

    def format_trace(self):
        proc = self.proc
        parts = []
        for name, reg in (('AX', RegisterPairs.AX), ('BC', RegisterPairs.BC),
                          ('DE', RegisterPairs.DE), ('HL', RegisterPairs.HL)):
            parts.append("%s=%04X" % (name, proc.read_gp_regpair(reg)))
        parts.append("SP=%04X" % proc.read_sp())
        psw = proc.read_psw()
        parts.append("[IE:%d RB:%d ISP:%d Z:%d AC:%d CY:%d]" % (
            int(bool(psw & Flags.IE)),
            proc.read_rb(),
            int(bool(psw & Flags.ISP)),
            int(bool(psw & Flags.Z)),
            int(bool(psw & Flags.AC)),
            int(bool(psw & Flags.CY)),
        ))
        parts.append("T=%d" % proc.total_cycles)
        return ' '.join(parts)

    def format_step(self):
        """Disassemble the instruction at PC, step, return the trace line.
        Returns (line, error) where error is True if the opcode was not implemented."""
        proc = self.proc
        try:
            dasm = disassemble(proc.bus, proc.pc)
            hex_str = ' '.join(["%02x" % x for x in dasm.all_bytes]).ljust(12)
            line = ("%04x: %s %s" % (proc.pc, hex_str, dasm)).ljust(42)
        except Exception:
            line = ("%04x: %02x           ???" % (proc.pc, proc.bus[proc.pc])).ljust(42)
        try:
            proc.step()
        except NotImplementedError:
            line += "!!! NOT IMPLEMENTED !!!"
            return line, True
        line += self.format_trace()
        return line, False

    def run(self):
        """Run the processor, printing trace lines.
        Stops on unimplemented opcode or KeyboardInterrupt."""
        while True:
            try:
                line, error = self.format_step()
                self.output.write(line + "\n")
                if error:
                    break
            except KeyboardInterrupt:
                break


def print_memory_map(output=None):
    if output is None:
        output = sys.stdout
    proc = make_processor()
    for start, end, device in proc.bus.memory_map():
        size = end - start + 1
        output.write("  %04X-%04X  %5d  %s\n" % (start, end, size, device.name))


def main():
    if len(sys.argv) < 2:
        sys.stderr.write(__doc__)
        sys.exit(1)

    if sys.argv[1] == '--map':
        print_memory_map()
        sys.exit(0)

    runner = Runner()
    with open(sys.argv[1], 'rb') as f:
        runner.load(f.read())
    runner.run()

if __name__ == "__main__":
    main()
