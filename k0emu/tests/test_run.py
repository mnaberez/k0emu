import io
import unittest
from k0emu.devices import MemoryDevice
from k0emu.processor import Processor
from k0emu.run import Runner


def _make_runner(code):
    proc = Processor()
    mem = MemoryDevice("test_memory", size=0x10000)
    proc.bus.add_device([(0x0000, 0xFFFF)], mem)
    for i, byte in enumerate(code):
        mem.write(i, byte)
    output = io.StringIO()
    return Runner(proc, output=output)


class FormatTraceTests(unittest.TestCase):

    def test_initial_state(self):
        runner = _make_runner([0x00])
        runner.proc.step()
        trace = runner.format_trace()
        self.assertIn("AX=0000", trace)
        self.assertIn("SP=0000", trace)
        self.assertIn("T=2", trace)

    def test_shows_register_values(self):
        runner = _make_runner([0xa1, 0x42])  # mov a,#42h
        runner.proc.step()
        trace = runner.format_trace()
        self.assertIn("AX=4200", trace)


class FormatStepTests(unittest.TestCase):

    def test_nop_returns_trace_line(self):
        runner = _make_runner([0x00])
        line, error = runner.format_step()
        self.assertFalse(error)
        self.assertIn("0000:", line)
        self.assertIn("nop", line)
        self.assertIn("T=2", line)

    def test_unimplemented_returns_error(self):
        runner = _make_runner([0x06])  # undefined opcode
        line, error = runner.format_step()
        self.assertTrue(error)
        self.assertIn("NOT IMPLEMENTED", line)


class RunTests(unittest.TestCase):

    def test_run_outputs_trace_lines(self):
        runner = _make_runner([0x00, 0x00, 0x06])  # nop, nop, undefined
        runner.run()
        lines = runner.output.getvalue().strip().split("\n")
        self.assertEqual(len(lines), 3)
        self.assertIn("nop", lines[0])
        self.assertIn("nop", lines[1])
        self.assertIn("NOT IMPLEMENTED", lines[2])

    def test_run_stops_on_unimplemented(self):
        runner = _make_runner([0x06])  # undefined opcode
        runner.run()
        lines = runner.output.getvalue().strip().split("\n")
        self.assertEqual(len(lines), 1)
        self.assertIn("NOT IMPLEMENTED", lines[0])
