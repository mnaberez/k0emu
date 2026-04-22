'''
Usage: k0emu <rom.bin>
       k0emu --watch <rom.bin>
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
        disp = bytes(proc.bus.read(0xF19A + i) for i in range(11))
        text = ''.join(chr(b) if 0x20 <= b <= 0x7E else '.' for b in disp)
        led = not bool(proc.bus.read(0xFF03) & 0x08)  # P3.3 active low
        parts.append("[%s] %s" % (text, "(ALM)" if led else "(   )"))
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

    def _press_power(self):
        """Simulate a POWER key press and release (INTP4 on P0.4)."""
        proc = self.proc
        intc = proc.bus.device("intc")
        # Press: P0.4 low + INTP4 falling edge
        p0 = proc.bus.read(0xFF00)
        proc.bus.write(0xFF00, p0 & ~0x10)
        intc.write(intc.IF0L, intc.read(intc.IF0L) | 0x20)
        # Hold for ~500ms (2095000 cycles at 4.19MHz)
        hold_until = proc.total_cycles + 2095000
        while proc.total_cycles < hold_until:
            proc.step()
        # Release: P0.4 high + INTP4 rising edge
        p0 = proc.bus.read(0xFF00)
        proc.bus.write(0xFF00, p0 | 0x10)
        intc.write(intc.IF0L, intc.read(intc.IF0L) | 0x20)

    def watch(self):
        """Run the processor, printing only when display or LED changes.
        Stops on unimplemented opcode or KeyboardInterrupt."""
        proc = self.proc
        last_disp = None
        last_led = None
        scontact_on = False
        while True:
            try:
                proc.step()
                # Turn S-Contact on after 8 seconds (simulate key turn)
                if not scontact_on and proc.total_cycles > 8 * 4190000:
                    self.output.write("--- S-CONTACT ON ---\n")
                    self.output.flush()
                    scontact_on = True
                    # Force P9.0 high from now on
                    proc.bus.device("ports")._FORCE_HIGH[9] = 0x01
                disp = bytes(proc.bus.read(0xF19A + i) for i in range(11))
                led = not bool(proc.bus.read(0xFF03) & 0x08)
                if disp != last_disp or led != last_led:
                        text = ''.join(chr(b) if 0x20 <= b <= 0x7E else '.' for b in disp)
                        sim = proc.total_cycles / 4190000
                        t30 = proc.bus.read(0xF18D) * 0.1
                        self.output.write("%.3fs [%s] %s %.1fV\n" % (
                            sim, text, "(ALM)" if led else "(   )", t30))
                        self.output.flush()
                        last_disp = disp
                        last_led = led
            except NotImplementedError:
                self.output.write("Unimplemented opcode at %04X\n" % (proc.pc - 1))
                break
            except KeyboardInterrupt:
                break


def print_memory_map(output=None):
    if output is None:
        output = sys.stdout
    proc = make_processor()
    for start, end, device in proc.bus.memory_map():
        size = end - start + 1
        output.write("  %04X-%04X  %5d  %-20s  %s\n" % (start, end, size, device.name, type(device).__name__))


def main():
    if len(sys.argv) < 2:
        sys.stderr.write(__doc__)
        sys.exit(1)

    if sys.argv[1] == '--map':
        print_memory_map()
        sys.exit(0)

    if sys.argv[1] == '--watch':
        if len(sys.argv) < 3:
            sys.stderr.write(__doc__)
            sys.exit(1)
        runner = Runner()
        with open(sys.argv[2], 'rb') as f:
            runner.load(f.read())
        runner.watch()
        sys.exit(0)

    runner = Runner()
    with open(sys.argv[1], 'rb') as f:
        runner.load(f.read())
    runner.run()

if __name__ == "__main__":
    main()
