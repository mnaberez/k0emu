import unittest
import sys
from processor import Processor, Registers, Flags

class ProcessorTests(unittest.TestCase):
    # nop
    def test_nop(self):
        proc = Processor()
        code = [0x00] # nop
        proc.write_memory(0x0000, code)
        proc.step()
        self.assertEqual(proc.pc, len(code))

    # not1 cy
    def test_not1_cy_0_to_1(self):
        proc = Processor()
        code = [0x01] # not1 cy
        proc.write_memory(0x0000, code)
        proc.psw = 0
        proc.step()
        self.assertEqual(proc.psw, Flags.CY)
        self.assertEqual(proc.pc, len(code))

    # not1 cy
    def test_not1_cy_1_to_0(self):
        proc = Processor()
        code = [0x01] # not1 cy
        proc.write_memory(0x0000, code)
        proc.psw = 0xFF
        proc.step()
        self.assertEqual(proc.psw, 0xFF & ~Flags.CY)
        self.assertEqual(proc.pc, len(code))

    # mov r,#byte
    def test_mov_x_imm_byte(self):
        proc = Processor()
        code = [0xA0, 0x42] # mov x, #42
        proc.write_memory(0x0000, code)
        proc.step()
        self.assertEqual(proc.read_gp_reg(Registers.X), 0x42)
        self.assertEqual(proc.pc, len(code))

    # mov r,#byte
    def test_mov_l_imm_byte(self):
        proc = Processor()
        code = [0xA7, 0x42] # mov h, #42
        proc.write_memory(0x0000, code)
        proc.step()
        self.assertEqual(proc.read_gp_reg(Registers.H), 0x42)
        self.assertEqual(proc.pc, len(code))


def test_suite():
    return unittest.findTestCases(sys.modules[__name__])

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
