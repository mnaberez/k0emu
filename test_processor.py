import unittest
import sys
from processor import Processor, Registers, Flags

class ProcessorTests(unittest.TestCase):

    # register banks

    def test_rb0_accesses_fef8_feff(self):
        proc = Processor()
        proc.rb = 0
        proc.memory[0xFEF8] = 0
        proc.write_gp_reg(0, 0xAA) # 0=X register
        self.assertEqual(proc.memory[0xFEF8], 0xAA)
        self.assertEqual(proc.read_gp_reg(0), 0xAA)
        proc.memory[0xFEFF] = 0
        proc.write_gp_reg(7, 0x55) # 7=H register
        self.assertEqual(proc.memory[0xFEFF], 0x55)
        self.assertEqual(proc.read_gp_reg(7), 0x55)

    def test_rb1_accesses_fef0_fef7(self):
        proc = Processor()
        proc.rb = 1
        proc.memory[0xFEF0] = 0
        proc.write_gp_reg(0, 0xAA) # 0=X register
        self.assertEqual(proc.memory[0xFEF0], 0xAA)
        self.assertEqual(proc.read_gp_reg(0), 0xAA)
        proc.memory[0xFEF7] = 0
        proc.write_gp_reg(7, 0x55) # 7=H register
        self.assertEqual(proc.memory[0xFEF7], 0x55)
        self.assertEqual(proc.read_gp_reg(7), 0x55)

    def test_rb2_accesses_fee8_feef(self):
        proc = Processor()
        proc.rb = 2
        proc.memory[0xFEE8] = 0
        proc.write_gp_reg(0, 0xAA) # 0=X register
        self.assertEqual(proc.memory[0xFEE8], 0xAA)
        self.assertEqual(proc.read_gp_reg(0), 0xAA)
        proc.memory[0xFEEF] = 0
        proc.write_gp_reg(7, 0x55) # 7=H register
        self.assertEqual(proc.memory[0xFEEF], 0x55)
        self.assertEqual(proc.read_gp_reg(7), 0x55)

    def test_rb3_accesses_fee0_fee7(self):
        proc = Processor()
        proc.rb = 3
        proc.memory[0xFEE0] = 0
        proc.write_gp_reg(0, 0xAA) # 0=X register
        self.assertEqual(proc.memory[0xFEE0], 0xAA)
        self.assertEqual(proc.read_gp_reg(0), 0xAA)
        proc.memory[0xFEE7] = 0
        proc.write_gp_reg(7, 0x55) # 7=H register
        self.assertEqual(proc.memory[0xFEE7], 0x55)
        self.assertEqual(proc.read_gp_reg(7), 0x55)

    # instructions

    # nop
    def test_00_nop(self):
        proc = Processor()
        code = [0x00] # nop
        proc.write_memory(0x0000, code)
        proc.step()
        self.assertEqual(proc.pc, len(code))

    # not1 cy
    def test_01_not1_cy_0_to_1(self):
        proc = Processor()
        code = [0x01] # not1 cy
        proc.write_memory(0x0000, code)
        proc.psw = 0
        proc.step()
        self.assertEqual(proc.psw, Flags.CY)
        self.assertEqual(proc.pc, len(code))

    # not1 cy
    def test_01_not1_cy_1_to_0(self):
        proc = Processor()
        code = [0x01] # not1 cy
        proc.write_memory(0x0000, code)
        proc.psw = 0xFF
        proc.step()
        self.assertEqual(proc.psw, 0xFF & ~Flags.CY)
        self.assertEqual(proc.pc, len(code))

    # set1 cy
    def test_20_set1_cy(self):
        proc = Processor()
        code = [0x20] # set1 cy
        proc.write_memory(0x0000, code)
        proc.psw = 0
        proc.step()
        self.assertEqual(proc.psw, 0 | Flags.CY)
        self.assertEqual(proc.pc, len(code))

    # clr1 cy
    def test_21_clr1_cy(self):
        proc = Processor()
        code = [0x21] # clr1 cy
        proc.write_memory(0x0000, code)
        proc.psw = 0xFF
        proc.step()
        self.assertEqual(proc.psw, 0xFF & ~Flags.CY)
        self.assertEqual(proc.pc, len(code))

    # xch a,x                     ;30
    def test_30_xch_a_x(self):
        proc = Processor()
        code = [0x30] # xch a,x
        proc.write_memory(0x0000, code)
        proc.write_gp_reg(Registers.A, 0x55)
        proc.write_gp_reg(Registers.X, 0xAA)
        proc.psw = 0xA5
        proc.step()
        self.assertEqual(proc.psw, 0xA5) # unchanged
        self.assertEqual(proc.read_gp_reg(Registers.A), 0xAA)
        self.assertEqual(proc.read_gp_reg(Registers.X), 0x55)
        self.assertEqual(proc.pc, len(code))

    # xch a,c                     ;32
    def test_32_xch_a_c(self):
        proc = Processor()
        code = [0x32] # xch a,c
        proc.write_memory(0x0000, code)
        proc.write_gp_reg(Registers.A, 0x55)
        proc.write_gp_reg(Registers.C, 0xAA)
        proc.psw = 0xA5
        proc.step()
        self.assertEqual(proc.psw, 0xA5) # unchanged
        self.assertEqual(proc.read_gp_reg(Registers.A), 0xAA)
        self.assertEqual(proc.read_gp_reg(Registers.C), 0x55)
        self.assertEqual(proc.pc, len(code))

    #   xch a,b                     ;33
    def test_32_xch_a_b(self):
        proc = Processor()
        code = [0x33] # xch a,c
        proc.write_memory(0x0000, code)
        proc.write_gp_reg(Registers.A, 0x55)
        proc.write_gp_reg(Registers.B, 0xAA)
        proc.psw = 0xA5
        proc.step()
        self.assertEqual(proc.psw, 0xA5) # unchanged
        self.assertEqual(proc.read_gp_reg(Registers.A), 0xAA)
        self.assertEqual(proc.read_gp_reg(Registers.B), 0x55)
        self.assertEqual(proc.pc, len(code))

    # xch a,e                     ;34
    def test_32_xch_a_e(self):
        proc = Processor()
        code = [0x34] # xch a,c
        proc.write_memory(0x0000, code)
        proc.write_gp_reg(Registers.A, 0x55)
        proc.write_gp_reg(Registers.E, 0xAA)
        proc.psw = 0xA5
        proc.step()
        self.assertEqual(proc.psw, 0xA5) # unchanged
        self.assertEqual(proc.read_gp_reg(Registers.A), 0xAA)
        self.assertEqual(proc.read_gp_reg(Registers.E), 0x55)
        self.assertEqual(proc.pc, len(code))

    # xch a,d                     ;35
    def test_35_xch_a_e(self):
        proc = Processor()
        code = [0x35] # xch a,c
        proc.write_memory(0x0000, code)
        proc.write_gp_reg(Registers.A, 0x55)
        proc.write_gp_reg(Registers.D, 0xAA)
        proc.psw = 0xA5
        proc.step()
        self.assertEqual(proc.psw, 0xA5) # unchanged
        self.assertEqual(proc.read_gp_reg(Registers.A), 0xAA)
        self.assertEqual(proc.read_gp_reg(Registers.D), 0x55)
        self.assertEqual(proc.pc, len(code))

    # xch a,l                     ;36
    def test_35_xch_a_l(self):
        proc = Processor()
        code = [0x36] # xch a,l
        proc.write_memory(0x0000, code)
        proc.write_gp_reg(Registers.A, 0x55)
        proc.write_gp_reg(Registers.L, 0xAA)
        proc.psw = 0xA5
        proc.step()
        self.assertEqual(proc.psw, 0xA5) # unchanged
        self.assertEqual(proc.read_gp_reg(Registers.A), 0xAA)
        self.assertEqual(proc.read_gp_reg(Registers.L), 0x55)
        self.assertEqual(proc.pc, len(code))

    # xch a,h                     ;37
    def test_37_xch_a_h(self):
        proc = Processor()
        code = [0x37] # xch a,h
        proc.write_memory(0x0000, code)
        proc.write_gp_reg(Registers.A, 0x55)
        proc.write_gp_reg(Registers.H, 0xAA)
        proc.psw = 0xA5
        proc.step()
        self.assertEqual(proc.psw, 0xA5) # unchanged
        self.assertEqual(proc.read_gp_reg(Registers.A), 0xAA)
        self.assertEqual(proc.read_gp_reg(Registers.H), 0x55)
        self.assertEqual(proc.pc, len(code))

    # xch a,!0abcdh               ;ce cd ab
    def test_ce_xch_a_abs(self):
        proc = Processor()
        code = [0xce, 0xcd, 0xab] # xch a,!0abcdh
        proc.write_memory(0x0000, code)
        proc.write_gp_reg(Registers.A, 0x55)
        proc.memory[0xabcd] = 0xAA
        proc.psw = 0xA5
        proc.step()
        self.assertEqual(proc.psw, 0xA5) # unchanged
        self.assertEqual(proc.read_gp_reg(Registers.A), 0xAA)
        self.assertEqual(proc.memory[0xabcd], 0x55)
        self.assertEqual(proc.pc, len(code))

    # xch a,0fe20h                ;83 20          saddr
    def test_83_xch_a_saddr(self):
        proc = Processor()
        code = [0x83, 0x20] # xch a,0fe20h
        proc.write_memory(0x0000, code)
        proc.write_gp_reg(Registers.A, 0x55)
        proc.memory[0xfe20] = 0xAA
        proc.psw = 0xA5
        proc.step()
        self.assertEqual(proc.psw, 0xA5) # unchanged
        self.assertEqual(proc.read_gp_reg(Registers.A), 0xAA)
        self.assertEqual(proc.memory[0xfe20], 0x55)
        self.assertEqual(proc.pc, len(code))

    # xch a,0fffeh                ;93 fe          sfr
    def test_93_xch_a_sfr(self):
        proc = Processor()
        code = [0x93, 0xfe] # xch a,0fffeh
        proc.write_memory(0x0000, code)
        proc.write_gp_reg(Registers.A, 0x55)
        proc.memory[0xfffe] = 0xAA
        proc.psw = 0xA5
        proc.step()
        self.assertEqual(proc.psw, 0xA5) # unchanged
        self.assertEqual(proc.read_gp_reg(Registers.A), 0xAA)
        self.assertEqual(proc.memory[0xfffe], 0x55)
        self.assertEqual(proc.pc, len(code))

    # mov r,#byte
    def test_a0_mov_x_imm_byte(self):
        proc = Processor()
        code = [0xA0, 0x42] # mov x, #42
        proc.write_memory(0x0000, code)
        proc.step()
        self.assertEqual(proc.read_gp_reg(Registers.X), 0x42)
        self.assertEqual(proc.pc, len(code))

    # mov r,#byte
    def test_a7_mov_l_imm_byte(self):
        proc = Processor()
        code = [0xA7, 0x42] # mov h, #42
        proc.write_memory(0x0000, code)
        proc.step()
        self.assertEqual(proc.read_gp_reg(Registers.H), 0x42)
        self.assertEqual(proc.pc, len(code))

    # br !0abcdh                  ;9b cd ab
    def test_9b_br_addr16(self):
        proc = Processor()
        code = [0x9B, 0xCD, 0xAB] # br !0abcdh
        proc.write_memory(0x0000, code)
        proc.step()
        self.assertEqual(proc.pc, 0xABCD)

    # sel rb0                     ;61 d0
    def test_61_d0_sel_rb0(self):
        proc = Processor()
        code = [0x61, 0xD0] # sel rb0
        proc.write_memory(0x0000, code)
        proc.rb = 1
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.rb, 0)

    # sel rb1                     ;61 d8
    def test_61_d8_sel_rb1(self):
        proc = Processor()
        code = [0x61, 0xD8] # sel rb1
        proc.write_memory(0x0000, code)
        self.assertEqual(proc.rb, 0)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.rb, 1)

    # sel rb2                     ;61 f0
    def test_61_f0_sel_rb2(self):
        proc = Processor()
        code = [0x61, 0xF0] # sel rb2
        proc.write_memory(0x0000, code)
        self.assertEqual(proc.rb, 0)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.rb, 2)

    # sel rb3                     ;61 f8
    def test_61_f8_sel_rb3(self):
        proc = Processor()
        code = [0x61, 0xF8] # sel rb3
        proc.write_memory(0x0000, code)
        self.assertEqual(proc.rb, 0)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.rb, 3)


def test_suite():
    return unittest.findTestCases(sys.modules[__name__])

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
