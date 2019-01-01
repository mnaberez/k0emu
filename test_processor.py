import unittest
import sys
from processor import Processor, Registers, Flags

class ProcessorTests(unittest.TestCase):

    # register banks

    def test_rb0_accesses_fef8_feff(self):
        proc = Processor()
        proc.write_rb(0)
        self.assertEqual(proc.read_rb(), 0)
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
        proc.write_rb(1)
        self.assertEqual(proc.read_rb(), 1)
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
        proc.write_rb(2)
        self.assertEqual(proc.read_rb(), 2)
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
        proc.write_rb(3)
        self.assertEqual(proc.read_rb(), 3)
        proc.memory[0xFEE0] = 0
        proc.write_gp_reg(0, 0xAA) # 0=X register
        self.assertEqual(proc.memory[0xFEE0], 0xAA)
        self.assertEqual(proc.read_gp_reg(0), 0xAA)
        proc.memory[0xFEE7] = 0
        proc.write_gp_reg(7, 0x55) # 7=H register
        self.assertEqual(proc.memory[0xFEE7], 0x55)
        self.assertEqual(proc.read_gp_reg(7), 0x55)

    def test_write_rb_preserves_other_psw_bits(self):
        proc = Processor()
        proc.write_psw(0b11111111)
        proc.write_rb(0)
        self.assertEqual(proc.read_psw(), 0b11010111)
        proc.write_psw(0b00000000)
        proc.write_rb(3)
        self.assertEqual(proc.read_psw(), 0b00101000)

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
        proc.write_psw(proc.read_psw() & ~Flags.CY)
        proc.step()
        self.assertEqual(proc.read_psw(), Flags.CY)
        self.assertEqual(proc.pc, len(code))

    # not1 cy
    def test_01_not1_cy_1_to_0(self):
        proc = Processor()
        code = [0x01] # not1 cy
        proc.write_memory(0x0000, code)
        proc.write_psw(proc.read_psw() | Flags.CY)
        proc.step()
        self.assertEqual(proc.read_psw() & Flags.CY, 0)
        self.assertEqual(proc.pc, len(code))

    # set1 cy
    def test_20_set1_cy(self):
        proc = Processor()
        code = [0x20] # set1 cy
        proc.write_memory(0x0000, code)
        proc.write_psw(proc.read_psw() & ~Flags.CY)
        proc.step()
        self.assertEqual(proc.read_psw() & Flags.CY, Flags.CY)
        self.assertEqual(proc.pc, len(code))

    # clr1 cy
    def test_21_clr1_cy(self):
        proc = Processor()
        code = [0x21] # clr1 cy
        proc.write_memory(0x0000, code)
        proc.write_psw(proc.read_psw() | Flags.CY)
        proc.step()
        self.assertEqual(proc.read_psw() & Flags.CY, 0)
        self.assertEqual(proc.pc, len(code))

    # xch a,x                     ;30
    def test_30_xch_a_x(self):
        proc = Processor()
        code = [0x30] # xch a,x
        proc.write_memory(0x0000, code)
        proc.write_gp_reg(Registers.A, 0x55)
        proc.write_gp_reg(Registers.X, 0xAA)
        proc.step()
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
        proc.step()
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
        proc.step()
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
        proc.step()
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
        proc.step()
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
        proc.step()
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
        proc.step()
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
        proc.step()
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
        proc.step()
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
        proc.step()
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
        # TODO FLAGS

    # mov r,#byte
    def test_a7_mov_l_imm_byte(self):
        proc = Processor()
        code = [0xA7, 0x42] # mov h, #42
        proc.write_memory(0x0000, code)
        proc.step()
        self.assertEqual(proc.read_gp_reg(Registers.H), 0x42)
        self.assertEqual(proc.pc, len(code))
        # TODO FLAGS

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
        proc.write_rb(1)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_rb(), 0)

    # sel rb1                     ;61 d8
    def test_61_d8_sel_rb1(self):
        proc = Processor()
        code = [0x61, 0xD8] # sel rb1
        proc.write_memory(0x0000, code)
        self.assertEqual(proc.read_rb(), 0)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_rb(), 1)

    # sel rb2                     ;61 f0
    def test_61_f0_sel_rb2(self):
        proc = Processor()
        code = [0x61, 0xF0] # sel rb2
        proc.write_memory(0x0000, code)
        self.assertEqual(proc.read_rb(), 0)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_rb(), 2)

    # sel rb3                     ;61 f8
    def test_61_f8_sel_rb3(self):
        proc = Processor()
        code = [0x61, 0xF8] # sel rb3
        proc.write_memory(0x0000, code)
        self.assertEqual(proc.read_rb(), 0)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_rb(), 3)

    # mov a,x                   ;60
    def test_60_mov_a_x(self):
        proc = Processor()
        code = [0x60] # mov a,x
        proc.write_memory(0x0000, code)
        self.assertEqual(proc.read_gp_reg(Registers.A), 0)
        proc.write_gp_reg(Registers.X, 0x42)
        proc.step()
        self.assertEqual(proc.read_gp_reg(Registers.A), 0x42)

    # mov a,c                   ;62
    def test_62_mov_a_c(self):
        proc = Processor()
        code = [0x62] # mov a,c
        proc.write_memory(0x0000, code)
        self.assertEqual(proc.read_gp_reg(Registers.A), 0)
        proc.write_gp_reg(Registers.C, 0x42)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0x42)

    # mov a,b                   ;63
    def test_62_mov_a_b(self):
        proc = Processor()
        code = [0x63] # mov a,b
        proc.write_memory(0x0000, code)
        self.assertEqual(proc.read_gp_reg(Registers.A), 0)
        proc.write_gp_reg(Registers.B, 0x42)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0x42)

    # mov a,e                   ;64
    def test_62_mov_a_e(self):
        proc = Processor()
        code = [0x64] # mov a,e
        proc.write_memory(0x0000, code)
        self.assertEqual(proc.read_gp_reg(Registers.A), 0)
        proc.write_gp_reg(Registers.E, 0x42)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0x42)

    # mov a,d                   ;65
    def test_65_mov_a_d(self):
        proc = Processor()
        code = [0x65] # mov a,d
        proc.write_memory(0x0000, code)
        self.assertEqual(proc.read_gp_reg(Registers.A), 0)
        proc.write_gp_reg(Registers.D, 0x42)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0x42)

    # mov a,l                   ;66
    def test_66_mov_a_l(self):
        proc = Processor()
        code = [0x66] # mov a,l
        proc.write_memory(0x0000, code)
        self.assertEqual(proc.read_gp_reg(Registers.A), 0)
        proc.write_gp_reg(Registers.L, 0x42)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0x42)

    # mov a,h                   ;67
    def test_67_mov_a_h(self):
        proc = Processor()
        code = [0x67] # mov a,h
        proc.write_memory(0x0000, code)
        self.assertEqual(proc.read_gp_reg(Registers.A), 0)
        proc.write_gp_reg(Registers.H, 0x42)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0x42)

    # mov x,a                   ;70
    def test_70_mov_x_a(self):
        proc = Processor()
        code = [0x70] # mov a,x
        proc.write_memory(0x0000, code)
        self.assertEqual(proc.read_gp_reg(Registers.X), 0)
        proc.write_gp_reg(Registers.A, 0x42)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.X), 0x42)

    # mov c,a                   ;72
    def test_72_mov_a_c(self):
        proc = Processor()
        code = [0x72] # mov c,a
        proc.write_memory(0x0000, code)
        self.assertEqual(proc.read_gp_reg(Registers.C), 0)
        proc.write_gp_reg(Registers.A, 0x42)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.C), 0x42)

    # mov b,a                   ;73
    def test_73_mov_b_a(self):
        proc = Processor()
        code = [0x73] # mov b,a
        proc.write_memory(0x0000, code)
        self.assertEqual(proc.read_gp_reg(Registers.B), 0)
        proc.write_gp_reg(Registers.A, 0x42)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.B), 0x42)

    # mov e,a                   ;74
    def test_74_mov_e_a(self):
        proc = Processor()
        code = [0x74] # mov e,a
        proc.write_memory(0x0000, code)
        self.assertEqual(proc.read_gp_reg(Registers.E), 0)
        proc.write_gp_reg(Registers.A, 0x42)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.E), 0x42)

    # mov d,a                   ;75
    def test_75_mov_d_a(self):
        proc = Processor()
        code = [0x75] # mov d,a
        proc.write_memory(0x0000, code)
        self.assertEqual(proc.read_gp_reg(Registers.D), 0)
        proc.write_gp_reg(Registers.A, 0x42)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.D), 0x42)

    # mov l,a                   ;76
    def test_76_mov_l_a(self):
        proc = Processor()
        code = [0x76] # mov l,a
        proc.write_memory(0x0000, code)
        self.assertEqual(proc.read_gp_reg(Registers.L), 0)
        proc.write_gp_reg(Registers.A, 0x42)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.L), 0x42)

    # mov h,a                   ;77
    def test_67_mov_a_l(self):
        proc = Processor()
        code = [0x77] # mov h,a
        proc.write_memory(0x0000, code)
        self.assertEqual(proc.read_gp_reg(Registers.H), 0)
        proc.write_gp_reg(Registers.A, 0x42)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.H), 0x42)

    # mov a,!0abcdh               ;8e cd ab
    def test_8e_mov_a_addr16(self):
        proc = Processor()
        code = [0x8e, 0xcd, 0xab]
        proc.write_memory(0x0000, code)
        proc.memory[0xabcd] = 0x42
        self.assertEqual(proc.read_gp_reg(Registers.A), 0)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0x42)

    # mov !addr16,a               ;9e cd ab
    def test_9e_mov_addr16_a(self):
        proc = Processor()
        code = [0x9e, 0xcd, 0xab]
        proc.write_memory(0x0000, code)
        self.assertEqual(proc.memory[0xabcd], 0)
        proc.write_gp_reg(Registers.A, 0x42)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xabcd], 0x42)

    # mov a,0fe20h                ;F0 20          saddr
    def test_f0_mov_a_saddr(self):
        proc = Processor()
        code = [0xf0, 0x20]
        proc.write_memory(0x0000, code)
        proc.memory[0xfe20] = 0x42
        self.assertEqual(proc.read_gp_reg(Registers.A), 0)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0x42)

    # mov a,psw                   ;f0 1e
    def test_f0_mov_a_psw(self):
        proc = Processor()
        code = [0xf0, 0x1e]
        proc.write_memory(0x0000, code)
        proc.write_psw(0x42)
        self.assertEqual(proc.read_gp_reg(Registers.A), 0)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0x42)

    # mov 0fe20h,a                ;f2 20          saddr
    def test_f2_mov_saddr_a(self):
        proc = Processor()
        code = [0xf2, 0x20]
        proc.write_memory(0x0000, code)
        proc.write_gp_reg(Registers.A, 0x42)
        self.assertEqual(proc.memory[0xfe20], 0)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xfe20], 0x42)

    # mov psw,a                   ;f2 1e
    def test_f2_mov_psw_a(self):
        proc = Processor()
        code = [0xf2, 0x1e]
        proc.write_memory(0x0000, code)
        proc.write_gp_reg(Registers.A, 0x42)
        proc.write_psw(0)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0x42)

    # mov a,0fffeh                ;f4 fe          sfr
    def test_f4_mov_a_sfr(self):
        proc = Processor()
        code = [0xf4, 0xfe]
        proc.write_memory(0x0000, code)
        proc.memory[0xfffe] = 0x42
        self.assertEqual(proc.read_gp_reg(Registers.A), 0)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0x42)

    # mov 0fffeh,a                ;f6 fe          sfr
    def test_f6_mov_sfr_a(self):
        proc = Processor()
        code = [0xf6, 0xfe]
        proc.write_memory(0x0000, code)
        proc.write_gp_reg(Registers.A, 0x42)
        self.assertEqual(proc.memory[0xfffe], 0)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xfffe], 0x42)

    # mov 0fe20h,#0abh            ;11 20 ab       saddr
    def test_11_mov_saddr_imm(self):
        proc = Processor()
        code = [0x11, 0x20, 0xab]
        proc.write_memory(0x0000, code)
        proc.memory[0xfe20] = 0
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xfe20], 0xab)

    # mov psw,#0abh               ;11 1e ab
    def test_11_mov_psw_imm(self):
        proc = Processor()
        code = [0x11, 0x1e, 0x42]
        proc.write_memory(0x0000, code)
        proc.write_psw(0)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0x42)

    # mov 0fffeh, #0abh           ;13 fe ab       sfr
    def test_13_mov_sfr_imm(self):
        proc = Processor()
        code = [0x13, 0xfe, 0xab]
        proc.write_memory(0x0000, code)
        proc.memory[0xfffe] = 0
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xfffe], 0xab)

    # or a,#0aah                  ;6d aa
    def test_6d_or_a_imm_result_nonzero(self):
        proc = Processor()
        code = [0x6d, 0xaa]
        proc.write_memory(0x0000, code)
        proc.write_gp_reg(Registers.A, 0x55)
        proc.write_psw(proc.read_psw() | Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0xFF)
        self.assertEqual(proc.read_psw() & Flags.Z, 0)

    # or a,#000h                  ;6d 00
    def test_6d_or_a_imm_result_zero(self):
        proc = Processor()
        code = [0x6d, 0x00]
        proc.write_memory(0x0000, code)
        proc.write_gp_reg(Registers.A, 0)
        proc.write_psw(proc.read_psw() & ~Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0)
        self.assertEqual(proc.read_psw() & Flags.Z, Flags.Z)

    # or a,0fe20h                 ;6e 20          saddr
    def test_6e_or_a_saddr(self):
        proc = Processor()
        code = [0x6e, 0x20]
        proc.write_memory(0x0000, code)
        proc.memory[0xfe20] = 0xAA
        proc.write_gp_reg(Registers.A, 0x55)
        proc.write_psw(proc.read_psw() | Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0xFF)
        self.assertEqual(proc.read_psw() & Flags.Z, 0)

    # or a,x                      ;61 68
    def test_61_68_or_a_x(self):
        proc = Processor()
        code = [0x61, 0x68]
        proc.write_memory(0x0000, code)
        proc.write_gp_reg(Registers.A, 0xAA)
        proc.write_gp_reg(Registers.X, 0x55)
        proc.write_psw(proc.read_psw() | Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0xFF)
        self.assertEqual(proc.read_psw() & Flags.Z, 0)

    # or a,c                      ;61 6a
    def test_61_6a_or_a_c(self):
        proc = Processor()
        code = [0x61, 0x6a]
        proc.write_memory(0x0000, code)
        proc.write_gp_reg(Registers.A, 0xAA)
        proc.write_gp_reg(Registers.C, 0x55)
        proc.write_psw(proc.read_psw() | Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0xFF)
        self.assertEqual(proc.read_psw() & Flags.Z, 0)

    # or a,b                      ;61 6b
    def test_61_6b_or_a_b(self):
        proc = Processor()
        code = [0x61, 0x6b]
        proc.write_memory(0x0000, code)
        proc.write_gp_reg(Registers.A, 0xAA)
        proc.write_gp_reg(Registers.B, 0x55)
        proc.write_psw(proc.read_psw() | Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0xFF)
        self.assertEqual(proc.read_psw() & Flags.Z, 0)

    # or a,e                      ;61 6c
    def test_61_6e_or_a_e(self):
        proc = Processor()
        code = [0x61, 0x6c]
        proc.write_memory(0x0000, code)
        proc.write_gp_reg(Registers.A, 0xAA)
        proc.write_gp_reg(Registers.E, 0x55)
        proc.write_psw(proc.read_psw() | Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0xFF)
        self.assertEqual(proc.read_psw() & Flags.Z, 0)

    # or a,d                      ;61 6d
    def test_61_6d_or_a_d(self):
        proc = Processor()
        code = [0x61, 0x6d]
        proc.write_memory(0x0000, code)
        proc.write_gp_reg(Registers.A, 0xAA)
        proc.write_gp_reg(Registers.D, 0x55)
        proc.write_psw(proc.read_psw() | Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0xFF)
        self.assertEqual(proc.read_psw() & Flags.Z, 0)

    # or a,l                      ;61 6e
    def test_61_6e_or_a_l(self):
        proc = Processor()
        code = [0x61, 0x6e]
        proc.write_memory(0x0000, code)
        proc.write_gp_reg(Registers.A, 0xAA)
        proc.write_gp_reg(Registers.L, 0x55)
        proc.write_psw(proc.read_psw() | Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0xFF)
        self.assertEqual(proc.read_psw() & Flags.Z, 0)

    # or a,h                      ;61 6f
    def test_61_6f_or_a_h(self):
        proc = Processor()
        code = [0x61, 0x6f]
        proc.write_memory(0x0000, code)
        proc.write_gp_reg(Registers.A, 0xAA)
        proc.write_gp_reg(Registers.H, 0x55)
        proc.write_psw(proc.read_psw() | Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0xFF)
        self.assertEqual(proc.read_psw() & Flags.Z, 0)

    # or x,a                      ;61 60
    def test_61_60_or_x_a(self):
        proc = Processor()
        code = [0x61, 0x60]
        proc.write_memory(0x0000, code)
        proc.write_gp_reg(Registers.X, 0x55)
        proc.write_gp_reg(Registers.A, 0xAA)
        proc.write_psw(proc.read_psw() | Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.X), 0xFF)
        self.assertEqual(proc.read_psw() & Flags.Z, 0)

    # or a,a                      ;61 61
    def test_61_61_or_a_a(self):
        proc = Processor()
        code = [0x61, 0x61]
        proc.write_memory(0x0000, code)
        proc.write_gp_reg(Registers.A, 0xff)
        proc.write_psw(proc.read_psw() | Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0xFF)
        self.assertEqual(proc.read_psw() & Flags.Z, 0)

    # or c,a                      ;61 62
    def test_61_62_or_c_a(self):
        proc = Processor()
        code = [0x61, 0x62]
        proc.write_memory(0x0000, code)
        proc.write_gp_reg(Registers.C, 0x55)
        proc.write_gp_reg(Registers.A, 0xAA)
        proc.write_psw(proc.read_psw() | Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.C), 0xFF)
        self.assertEqual(proc.read_psw() & Flags.Z, 0)

    # or b,a                      ;61 63
    def test_61_63_or_b_a(self):
        proc = Processor()
        code = [0x61, 0x63]
        proc.write_memory(0x0000, code)
        proc.write_gp_reg(Registers.B, 0x55)
        proc.write_gp_reg(Registers.A, 0xAA)
        proc.write_psw(proc.read_psw() | Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.B), 0xFF)
        self.assertEqual(proc.read_psw() & Flags.Z, 0)

    # or d,a                      ;61 65
    def test_61_65_or_d_a(self):
        proc = Processor()
        code = [0x61, 0x65]
        proc.write_memory(0x0000, code)
        proc.write_gp_reg(Registers.D, 0x55)
        proc.write_gp_reg(Registers.A, 0xAA)
        proc.write_psw(proc.read_psw() | Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.D), 0xFF)
        self.assertEqual(proc.read_psw() & Flags.Z, 0)

    # or l,a                      ;61 66
    def test_61_66_or_l_a(self):
        proc = Processor()
        code = [0x61, 0x66]
        proc.write_memory(0x0000, code)
        proc.write_gp_reg(Registers.L, 0x55)
        proc.write_gp_reg(Registers.A, 0xAA)
        proc.write_psw(proc.read_psw() | Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.L), 0xFF)
        self.assertEqual(proc.read_psw() & Flags.Z, 0)

    # or h,a                      ;61 67
    def test_61_67_or_h_a(self):
        proc = Processor()
        code = [0x61, 0x67]
        proc.write_memory(0x0000, code)
        proc.write_gp_reg(Registers.H, 0x55)
        proc.write_gp_reg(Registers.A, 0xAA)
        proc.write_psw(proc.read_psw() | Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.H), 0xFF)
        self.assertEqual(proc.read_psw() & Flags.Z, 0)

    # or 0fe20h,#0abh             ;e8 20 ab      saddr
    def test_e8_or_saddr_imm(self):
        proc = Processor()
        code = [0xe8, 0x20, 0x55]
        proc.write_memory(0x0000, code)
        proc.memory[0xfe20] = 0xAA
        proc.write_psw(proc.read_psw() | Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xfe20], 0xFF)
        self.assertEqual(proc.read_psw() & Flags.Z, 0)

    # or a,!0abcdh                ;68 cd ab
    def test_68_or_a_addr16(self):
        proc = Processor()
        code = [0x68, 0xcd, 0xab]
        proc.write_memory(0x0000, code)
        proc.write_gp_reg(Registers.A, 0x55)
        proc.memory[0xabcd] = 0xAA
        proc.write_psw(proc.read_psw() | Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0xFF)
        self.assertEqual(proc.read_psw() & Flags.Z, 0)

    # and a,#0abh                 ;5d ab
    def test_5d_and_a_imm_result_zero(self):
        proc = Processor()
        code = [0x5d, 0xff]
        proc.write_memory(0x0000, code)
        proc.write_gp_reg(Registers.A, 0x00)
        proc.write_psw(proc.read_psw() & ~Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0)
        self.assertEqual(proc.read_psw() & Flags.Z, Flags.Z)

    # and a,#0abh                 ;5d ab
    def test_5d_and_a_imm_result_nonzero(self):
        proc = Processor()
        code = [0x5d, 0xff]
        proc.write_memory(0x0000, code)
        proc.write_gp_reg(Registers.A, 0xf0)
        proc.write_psw(proc.read_psw() & ~Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0xf0)
        self.assertEqual(proc.read_psw() & Flags.Z, 0)

    # and a,0fe20h                ;5e 20          saddr
    def test_5e_and_a_saddr(self):
        proc = Processor()
        code = [0x5e, 0x20]
        proc.write_memory(0x0000, code)
        proc.memory[0xfe20] = 0xff
        proc.write_gp_reg(Registers.A, 0xf0)
        proc.write_psw(proc.read_psw() | Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0xf0)
        self.assertEqual(proc.read_psw() & Flags.Z, 0)

    # and a,!0abcdh               ;58 cd ab
    def test_58_and_a_addr16(self):
        proc = Processor()
        code = [0x58, 0xcd, 0xab]
        proc.write_memory(0x0000, code)
        proc.memory[0xabcd] = 0xff
        proc.write_gp_reg(Registers.A, 0xf0)
        proc.write_psw(proc.read_psw() | Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0xf0)
        self.assertEqual(proc.read_psw() & Flags.Z, 0)

    # and 0fe20h,#0abh            ;d8 20 ab       saddr
    def test_d8_and_saddr_imm(self):
        proc = Processor()
        code = [0xd8, 0x20, 0xf0]
        proc.write_memory(0x0000, code)
        proc.memory[0xfe20] = 0xff
        proc.write_psw(proc.read_psw() | Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xfe20], 0xf0)
        self.assertEqual(proc.read_psw() & Flags.Z, 0)

    # and a,x                     ;61 58
    def test_61_58_and_a_x(self):
        proc = Processor()
        code = [0x61, 0x58]
        proc.write_memory(0x0000, code)
        proc.write_gp_reg(Registers.A, 0xff)
        proc.write_gp_reg(Registers.X, 0xf0)
        proc.write_psw(proc.read_psw() | Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0xf0)
        self.assertEqual(proc.read_psw() & Flags.Z, 0)

    # and a,c                     ;61 5a
    def test_61_5a_and_a_c(self):
        proc = Processor()
        code = [0x61, 0x5a]
        proc.write_memory(0x0000, code)
        proc.write_gp_reg(Registers.A, 0xff)
        proc.write_gp_reg(Registers.C, 0xf0)
        proc.write_psw(proc.read_psw() | Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0xf0)
        self.assertEqual(proc.read_psw() & Flags.Z, 0)

    # and a,b                     ;61 5b
    def test_61_5b_and_a_b(self):
        proc = Processor()
        code = [0x61, 0x5b]
        proc.write_memory(0x0000, code)
        proc.write_gp_reg(Registers.A, 0xff)
        proc.write_gp_reg(Registers.B, 0xf0)
        proc.write_psw(proc.read_psw() | Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0xf0)
        self.assertEqual(proc.read_psw() & Flags.Z, 0)

    # and a,e                     ;61 5c
    def test_61_5c_and_a_e(self):
        proc = Processor()
        code = [0x61, 0x5c]
        proc.write_memory(0x0000, code)
        proc.write_gp_reg(Registers.A, 0xff)
        proc.write_gp_reg(Registers.E, 0xf0)
        proc.write_psw(proc.read_psw() | Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0xf0)
        self.assertEqual(proc.read_psw() & Flags.Z, 0)

    # and a,d                     ;61 5d
    def test_61_5d_and_a_d(self):
        proc = Processor()
        code = [0x61, 0x5d]
        proc.write_memory(0x0000, code)
        proc.write_gp_reg(Registers.A, 0xff)
        proc.write_gp_reg(Registers.D, 0xf0)
        proc.write_psw(proc.read_psw() | Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0xf0)
        self.assertEqual(proc.read_psw() & Flags.Z, 0)

    # and a,l                     ;61 5e
    def test_61_5e_and_a_l(self):
        proc = Processor()
        code = [0x61, 0x5e]
        proc.write_memory(0x0000, code)
        proc.write_gp_reg(Registers.A, 0xff)
        proc.write_gp_reg(Registers.L, 0xf0)
        proc.write_psw(proc.read_psw() | Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0xf0)
        self.assertEqual(proc.read_psw() & Flags.Z, 0)

    # and a,h                     ;61 5f
    def test_61_5f_and_a_h(self):
        proc = Processor()
        code = [0x61, 0x5f]
        proc.write_memory(0x0000, code)
        proc.write_gp_reg(Registers.A, 0xff)
        proc.write_gp_reg(Registers.H, 0xf0)
        proc.write_psw(proc.read_psw() | Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0xf0)
        self.assertEqual(proc.read_psw() & Flags.Z, 0)

    # and x,a                     ;61 50
    def test_61_50_and_x_a(self):
        proc = Processor()
        code = [0x61, 0x50]
        proc.write_memory(0x0000, code)
        proc.write_gp_reg(Registers.X, 0xff)
        proc.write_gp_reg(Registers.A, 0xf0)
        proc.write_psw(proc.read_psw() | Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.X), 0xf0)
        self.assertEqual(proc.read_psw() & Flags.Z, 0)

    # and a,a                     ;61 51
    def test_61_51_and_a_a(self):
        proc = Processor()
        code = [0x61, 0x51]
        proc.write_memory(0x0000, code)
        proc.write_gp_reg(Registers.A, 0xff)
        proc.write_psw(proc.read_psw() | Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0xff)
        self.assertEqual(proc.read_psw() & Flags.Z, 0)

    # and c,a                     ;61 52
    def test_61_52_and_c_a(self):
        proc = Processor()
        code = [0x61, 0x52]
        proc.write_memory(0x0000, code)
        proc.write_gp_reg(Registers.C, 0xff)
        proc.write_gp_reg(Registers.A, 0xf0)
        proc.write_psw(proc.read_psw() | Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.C), 0xf0)
        self.assertEqual(proc.read_psw() & Flags.Z, 0)

    # and b,a                     ;61 53
    def test_61_53_and_b_a(self):
        proc = Processor()
        code = [0x61, 0x53]
        proc.write_memory(0x0000, code)
        proc.write_gp_reg(Registers.B, 0xff)
        proc.write_gp_reg(Registers.A, 0xf0)
        proc.write_psw(proc.read_psw() | Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.B), 0xf0)
        self.assertEqual(proc.read_psw() & Flags.Z, 0)

    # and e,a                     ;61 54
    def test_61_54_and_e_a(self):
        proc = Processor()
        code = [0x61, 0x54]
        proc.write_memory(0x0000, code)
        proc.write_gp_reg(Registers.E, 0xff)
        proc.write_gp_reg(Registers.A, 0xf0)
        proc.write_psw(proc.read_psw() | Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.E), 0xf0)
        self.assertEqual(proc.read_psw() & Flags.Z, 0)

    # and d,a                     ;61 55
    def test_61_55_and_e_a(self):
        proc = Processor()
        code = [0x61, 0x55]
        proc.write_memory(0x0000, code)
        proc.write_gp_reg(Registers.D, 0xff)
        proc.write_gp_reg(Registers.A, 0xf0)
        proc.write_psw(proc.read_psw() | Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.D), 0xf0)
        self.assertEqual(proc.read_psw() & Flags.Z, 0)

    # and l,a                     ;61 56
    def test_61_56_and_e_a(self):
        proc = Processor()
        code = [0x61, 0x56]
        proc.write_memory(0x0000, code)
        proc.write_gp_reg(Registers.L, 0xff)
        proc.write_gp_reg(Registers.A, 0xf0)
        proc.write_psw(proc.read_psw() | Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.L), 0xf0)
        self.assertEqual(proc.read_psw() & Flags.Z, 0)

    # and h,a                     ;61 57
    def test_61_57_and_h_a(self):
        proc = Processor()
        code = [0x61, 0x57]
        proc.write_memory(0x0000, code)
        proc.write_gp_reg(Registers.H, 0xff)
        proc.write_gp_reg(Registers.A, 0xf0)
        proc.write_psw(proc.read_psw() | Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.H), 0xf0)
        self.assertEqual(proc.read_psw() & Flags.Z, 0)

    # call !0abcdh                ;9a cd ab
    def test_9a_call(self):
        proc = Processor()
        code = [0x9a, 0xcd, 0xab]
        proc.write_memory(0x0123, code)
        proc.pc = 0x0123
        return_address = proc.pc + len(code)
        proc.sp = 0xFE1F
        proc.step()
        self.assertEqual(proc.sp, 0xFE1d)
        self.assertEqual(proc.memory[0xFE1d], (return_address & 0xFF))
        self.assertEqual(proc.memory[0xFE1e], (return_address >> 8))
        self.assertEqual(proc.pc, 0xabcd)

    # ret                         ;af
    def test_af_ret(self):
        proc = Processor()
        code = [0xaf]
        proc.write_memory(0x0000, code)
        proc.sp = 0xfe1d
        proc.memory[0xfe1d] = 0xcd # stack: return address low
        proc.memory[0xfe1e] = 0xab # stack: return address high
        proc.step()
        self.assertEqual(proc.sp, 0xfe1f)
        self.assertEqual(proc.pc, 0xabcd)

    # push psw                    ;22
    def test_22_push_psw(self):
        proc = Processor()
        code = [0x22]
        proc.write_memory(0x0000, code)
        proc.sp = 0xFE1F
        proc.write_psw(0x42)
        proc.step()
        self.assertEqual(proc.sp, 0xfe1e)
        self.assertEqual(proc.memory[0xfe1e], 0x42)
        self.assertEqual(proc.pc, len(code))

    # pop psw                     ;23
    def test_23_pop_psw(self):
        proc = Processor()
        code = [0x23]
        proc.write_memory(0x0000, code)
        proc.sp = 0xFE1E
        proc.memory[0xFE1E] = 0x42 # stack: psw
        proc.write_psw(0)
        proc.step()
        self.assertEqual(proc.sp, 0xfe1F)
        self.assertEqual(proc.read_psw(), 0x42)
        self.assertEqual(proc.pc, len(code))

    # xor a,x                     ;61 78
    def test_61_78_and_xor_a_x_result_nonzero(self):
        proc = Processor()
        code = [0x61, 0x78]
        proc.write_memory(0x0000, code)
        proc.write_gp_reg(Registers.A, 0x55)
        proc.write_gp_reg(Registers.X, 0xFF)
        proc.write_psw(proc.read_psw() | Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0xAA)
        self.assertEqual(proc.read_psw() & Flags.Z, 0)

    # xor a,x                     ;61 78
    def test_61_78_and_xor_a_x_result_zero(self):
        proc = Processor()
        code = [0x61, 0x78]
        proc.write_memory(0x0000, code)
        proc.write_gp_reg(Registers.A, 0xFF)
        proc.write_gp_reg(Registers.X, 0xFF)
        proc.write_psw(proc.read_psw() | Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0)
        self.assertEqual(proc.read_psw() & Flags.Z, Flags.Z)

    # xor a,c                     ;61 7a
    def test_61_7a_and_xor_a_c(self):
        proc = Processor()
        code = [0x61, 0x7a]
        proc.write_memory(0x0000, code)
        proc.write_gp_reg(Registers.A, 0x55)
        proc.write_gp_reg(Registers.C, 0xFF)
        proc.write_psw(proc.read_psw() | Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0xAA)
        self.assertEqual(proc.read_psw() & Flags.Z, 0)

    # xor a,b                     ;61 7b
    def test_61_7b_and_xor_a_b(self):
        proc = Processor()
        code = [0x61, 0x7b]
        proc.write_memory(0x0000, code)
        proc.write_gp_reg(Registers.A, 0x55)
        proc.write_gp_reg(Registers.B, 0xFF)
        proc.write_psw(proc.read_psw() | Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0xAA)
        self.assertEqual(proc.read_psw() & Flags.Z, 0)

    # xor a,e                     ;61 7c
    def test_61_7c_and_xor_a_e(self):
        proc = Processor()
        code = [0x61, 0x7c]
        proc.write_memory(0x0000, code)
        proc.write_gp_reg(Registers.A, 0x55)
        proc.write_gp_reg(Registers.E, 0xFF)
        proc.write_psw(proc.read_psw() | Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0xAA)
        self.assertEqual(proc.read_psw() & Flags.Z, 0)

    # xor a,d                     ;61 7d
    def test_61_7d_and_xor_a_d(self):
        proc = Processor()
        code = [0x61, 0x7d]
        proc.write_memory(0x0000, code)
        proc.write_gp_reg(Registers.A, 0x55)
        proc.write_gp_reg(Registers.D, 0xFF)
        proc.write_psw(proc.read_psw() | Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0xAA)
        self.assertEqual(proc.read_psw() & Flags.Z, 0)

    # xor a,l                     ;61 7e
    def test_61_7e_and_xor_a_l(self):
        proc = Processor()
        code = [0x61, 0x7e]
        proc.write_memory(0x0000, code)
        proc.write_gp_reg(Registers.A, 0x55)
        proc.write_gp_reg(Registers.L, 0xFF)
        proc.write_psw(proc.read_psw() | Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0xAA)
        self.assertEqual(proc.read_psw() & Flags.Z, 0)

    # xor a,h                     ;61 7f
    def test_61_7f_and_xor_a_h(self):
        proc = Processor()
        code = [0x61, 0x7f]
        proc.write_memory(0x0000, code)
        proc.write_gp_reg(Registers.A, 0x55)
        proc.write_gp_reg(Registers.H, 0xFF)
        proc.write_psw(proc.read_psw() | Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0xAA)
        self.assertEqual(proc.read_psw() & Flags.Z, 0)

    # xor x,a                     ;61 70
    def test_61_70_and_xor_x_a(self):
        proc = Processor()
        code = [0x61, 0x70]
        proc.write_memory(0x0000, code)
        proc.write_gp_reg(Registers.A, 0x55)
        proc.write_gp_reg(Registers.X, 0xFF)
        proc.write_psw(proc.read_psw() | Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.X), 0xAA)
        self.assertEqual(proc.read_psw() & Flags.Z, 0)

    # xor a,a                     ;61 71
    def test_61_71_and_xor_a_a(self):
        proc = Processor()
        code = [0x61, 0x71]
        proc.write_memory(0x0000, code)
        proc.write_gp_reg(Registers.A, 0xFF)
        proc.write_psw(proc.read_psw() | Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0)
        self.assertEqual(proc.read_psw() & Flags.Z, Flags.Z)

    # xor c,a                     ;61 72
    def test_61_72_and_xor_c_a(self):
        proc = Processor()
        code = [0x61, 0x72]
        proc.write_memory(0x0000, code)
        proc.write_gp_reg(Registers.A, 0x55)
        proc.write_gp_reg(Registers.C, 0xFF)
        proc.write_psw(proc.read_psw() | Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.C), 0xAA)
        self.assertEqual(proc.read_psw() & Flags.Z, 0)

    # xor b,a                     ;61 73
    def test_61_73_and_xor_b_a(self):
        proc = Processor()
        code = [0x61, 0x73]
        proc.write_memory(0x0000, code)
        proc.write_gp_reg(Registers.A, 0x55)
        proc.write_gp_reg(Registers.B, 0xFF)
        proc.write_psw(proc.read_psw() | Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.B), 0xAA)
        self.assertEqual(proc.read_psw() & Flags.Z, 0)

    # xor e,a                     ;61 74
    def test_61_74_and_xor_e_a(self):
        proc = Processor()
        code = [0x61, 0x74]
        proc.write_memory(0x0000, code)
        proc.write_gp_reg(Registers.A, 0x55)
        proc.write_gp_reg(Registers.E, 0xFF)
        proc.write_psw(proc.read_psw() | Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.E), 0xAA)
        self.assertEqual(proc.read_psw() & Flags.Z, 0)

    # xor d,a                     ;61 75
    def test_61_75_and_xor_d_a(self):
        proc = Processor()
        code = [0x61, 0x75]
        proc.write_memory(0x0000, code)
        proc.write_gp_reg(Registers.A, 0x55)
        proc.write_gp_reg(Registers.D, 0xFF)
        proc.write_psw(proc.read_psw() | Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.D), 0xAA)
        self.assertEqual(proc.read_psw() & Flags.Z, 0)

    # xor l,a                     ;61 76
    def test_61_76_and_xor_l_a(self):
        proc = Processor()
        code = [0x61, 0x76]
        proc.write_memory(0x0000, code)
        proc.write_gp_reg(Registers.A, 0x55)
        proc.write_gp_reg(Registers.L, 0xFF)
        proc.write_psw(proc.read_psw() | Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.L), 0xAA)
        self.assertEqual(proc.read_psw() & Flags.Z, 0)

    # xor h,a                     ;61 77
    def test_61_77_and_xor_h_a(self):
        proc = Processor()
        code = [0x61, 0x77]
        proc.write_memory(0x0000, code)
        proc.write_gp_reg(Registers.A, 0x55)
        proc.write_gp_reg(Registers.H, 0xFF)
        proc.write_psw(proc.read_psw() | Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.H), 0xAA)
        self.assertEqual(proc.read_psw() & Flags.Z, 0)

    # xor a,!0abcdh               ;78 cd ab
    def test_78_xor_a_addr16(self):
        proc = Processor()
        code = [0x78, 0xcd, 0xab]
        proc.write_memory(0x0000, code)
        proc.write_gp_reg(Registers.A, 0x55)
        proc.memory[0xabcd] = 0xFF
        proc.write_psw(proc.read_psw() | Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0xAA)
        self.assertEqual(proc.read_psw() & Flags.Z, 0)

    # xor a,#0abh                 ;7d ab
    def test_7d_xor_a_imm(self):
        proc = Processor()
        code = [0x7d, 0xff]
        proc.write_memory(0x0000, code)
        proc.write_gp_reg(Registers.A, 0x55)
        proc.memory[0xabcd] = 0xFF
        proc.write_psw(proc.read_psw() | Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0xAA)
        self.assertEqual(proc.read_psw() & Flags.Z, 0)

    # xor a,0fe20h                ;7e 20          saddr
    def test_7e_xor_a_saddr(self):
        proc = Processor()
        code = [0x7e, 0x20]
        proc.write_memory(0x0000, code)
        proc.write_gp_reg(Registers.A, 0x55)
        proc.memory[0xfe20] = 0xFF
        proc.write_psw(proc.read_psw() | Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0xAA)
        self.assertEqual(proc.read_psw() & Flags.Z, 0)

    # xor 0fe20h,#0abh            ;f8 20 ab       saddr
    def test_f8_xor_saddr_imm(self):
        proc = Processor()
        code = [0xf8, 0x20, 0xff]
        proc.write_memory(0x0000, code)
        proc.memory[0xfe20] = 0x55
        proc.write_psw(proc.read_psw() | Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xfe20], 0xAA)
        self.assertEqual(proc.read_psw() & Flags.Z, 0)


def test_suite():
    return unittest.findTestCases(sys.modules[__name__])

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
