import unittest
import sys
from k0emu.processor import Processor, Registers, RegisterPairs, Flags

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
        proc.write_memory(0, code)
        proc.step()
        self.assertEqual(proc.pc, len(code))

    # not1 cy
    def test_01_not1_cy_0_to_1(self):
        proc = Processor()
        code = [0x01] # not1 cy
        proc.write_memory(0, code)
        proc.write_psw(proc.read_psw() & ~Flags.CY)
        proc.step()
        self.assertEqual(proc.read_psw(), Flags.CY)
        self.assertEqual(proc.pc, len(code))

    # not1 cy
    def test_01_not1_cy_1_to_0(self):
        proc = Processor()
        code = [0x01] # not1 cy
        proc.write_memory(0, code)
        proc.write_psw(proc.read_psw() | Flags.CY)
        proc.step()
        self.assertEqual(proc.read_psw() & Flags.CY, 0)
        self.assertEqual(proc.pc, len(code))

    # set1 cy
    def test_20_set1_cy(self):
        proc = Processor()
        code = [0x20] # set1 cy
        proc.write_memory(0, code)
        proc.write_psw(proc.read_psw() & ~Flags.CY)
        proc.step()
        self.assertEqual(proc.read_psw() & Flags.CY, Flags.CY)
        self.assertEqual(proc.pc, len(code))

    # clr1 cy
    def test_21_clr1_cy(self):
        proc = Processor()
        code = [0x21] # clr1 cy
        proc.write_memory(0, code)
        proc.write_psw(proc.read_psw() | Flags.CY)
        proc.step()
        self.assertEqual(proc.read_psw() & Flags.CY, 0)
        self.assertEqual(proc.pc, len(code))

    # xch a,x                     ;30
    def test_30_xch_a_x(self):
        proc = Processor()
        code = [0x30] # xch a,x
        proc.write_memory(0, code)
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
        proc.write_memory(0, code)
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
        proc.write_memory(0, code)
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
        proc.write_memory(0, code)
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
        proc.write_memory(0, code)
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
        proc.write_memory(0, code)
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
        proc.write_memory(0, code)
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
        proc.write_memory(0, code)
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
        proc.write_memory(0, code)
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
        proc.write_memory(0, code)
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
        proc.write_memory(0, code)
        proc.step()
        self.assertEqual(proc.read_gp_reg(Registers.X), 0x42)
        self.assertEqual(proc.pc, len(code))
        # TODO FLAGS

    # mov r,#byte
    def test_a7_mov_l_imm_byte(self):
        proc = Processor()
        code = [0xA7, 0x42] # mov h, #42
        proc.write_memory(0, code)
        proc.step()
        self.assertEqual(proc.read_gp_reg(Registers.H), 0x42)
        self.assertEqual(proc.pc, len(code))
        # TODO FLAGS

    # br !0abcdh                  ;9b cd ab
    def test_9b_br_addr16(self):
        proc = Processor()
        code = [0x9B, 0xCD, 0xAB] # br !0abcdh
        proc.write_memory(0, code)
        proc.step()
        self.assertEqual(proc.pc, 0xABCD)

    # br ax                       ;31 98
    def test_31_98_br_ax(self):
        proc = Processor()
        code = [0x31, 0x98]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.AX, 0xabcd)
        proc.step()
        self.assertEqual(proc.pc, 0xabcd)

    # sel rb0                     ;61 d0
    def test_61_d0_sel_rb0(self):
        proc = Processor()
        code = [0x61, 0xD0] # sel rb0
        proc.write_memory(0, code)
        proc.write_rb(1)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_rb(), 0)

    # sel rb1                     ;61 d8
    def test_61_d8_sel_rb1(self):
        proc = Processor()
        code = [0x61, 0xD8] # sel rb1
        proc.write_memory(0, code)
        self.assertEqual(proc.read_rb(), 0)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_rb(), 1)

    # sel rb2                     ;61 f0
    def test_61_f0_sel_rb2(self):
        proc = Processor()
        code = [0x61, 0xF0] # sel rb2
        proc.write_memory(0, code)
        self.assertEqual(proc.read_rb(), 0)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_rb(), 2)

    # sel rb3                     ;61 f8
    def test_61_f8_sel_rb3(self):
        proc = Processor()
        code = [0x61, 0xF8] # sel rb3
        proc.write_memory(0, code)
        self.assertEqual(proc.read_rb(), 0)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_rb(), 3)

    # mov a,x                   ;60
    def test_60_mov_a_x(self):
        proc = Processor()
        code = [0x60] # mov a,x
        proc.write_memory(0, code)
        self.assertEqual(proc.read_gp_reg(Registers.A), 0)
        proc.write_gp_reg(Registers.X, 0x42)
        proc.step()
        self.assertEqual(proc.read_gp_reg(Registers.A), 0x42)

    # mov a,c                   ;62
    def test_62_mov_a_c(self):
        proc = Processor()
        code = [0x62] # mov a,c
        proc.write_memory(0, code)
        self.assertEqual(proc.read_gp_reg(Registers.A), 0)
        proc.write_gp_reg(Registers.C, 0x42)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0x42)

    # mov a,b                   ;63
    def test_62_mov_a_b(self):
        proc = Processor()
        code = [0x63] # mov a,b
        proc.write_memory(0, code)
        self.assertEqual(proc.read_gp_reg(Registers.A), 0)
        proc.write_gp_reg(Registers.B, 0x42)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0x42)

    # mov a,e                   ;64
    def test_62_mov_a_e(self):
        proc = Processor()
        code = [0x64] # mov a,e
        proc.write_memory(0, code)
        self.assertEqual(proc.read_gp_reg(Registers.A), 0)
        proc.write_gp_reg(Registers.E, 0x42)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0x42)

    # mov a,d                   ;65
    def test_65_mov_a_d(self):
        proc = Processor()
        code = [0x65] # mov a,d
        proc.write_memory(0, code)
        self.assertEqual(proc.read_gp_reg(Registers.A), 0)
        proc.write_gp_reg(Registers.D, 0x42)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0x42)

    # mov a,l                   ;66
    def test_66_mov_a_l(self):
        proc = Processor()
        code = [0x66] # mov a,l
        proc.write_memory(0, code)
        self.assertEqual(proc.read_gp_reg(Registers.A), 0)
        proc.write_gp_reg(Registers.L, 0x42)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0x42)

    # mov a,h                   ;67
    def test_67_mov_a_h(self):
        proc = Processor()
        code = [0x67] # mov a,h
        proc.write_memory(0, code)
        self.assertEqual(proc.read_gp_reg(Registers.A), 0)
        proc.write_gp_reg(Registers.H, 0x42)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0x42)

    # mov x,a                   ;70
    def test_70_mov_x_a(self):
        proc = Processor()
        code = [0x70] # mov a,x
        proc.write_memory(0, code)
        self.assertEqual(proc.read_gp_reg(Registers.X), 0)
        proc.write_gp_reg(Registers.A, 0x42)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.X), 0x42)

    # mov c,a                   ;72
    def test_72_mov_a_c(self):
        proc = Processor()
        code = [0x72] # mov c,a
        proc.write_memory(0, code)
        self.assertEqual(proc.read_gp_reg(Registers.C), 0)
        proc.write_gp_reg(Registers.A, 0x42)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.C), 0x42)

    # mov b,a                   ;73
    def test_73_mov_b_a(self):
        proc = Processor()
        code = [0x73] # mov b,a
        proc.write_memory(0, code)
        self.assertEqual(proc.read_gp_reg(Registers.B), 0)
        proc.write_gp_reg(Registers.A, 0x42)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.B), 0x42)

    # mov e,a                   ;74
    def test_74_mov_e_a(self):
        proc = Processor()
        code = [0x74] # mov e,a
        proc.write_memory(0, code)
        self.assertEqual(proc.read_gp_reg(Registers.E), 0)
        proc.write_gp_reg(Registers.A, 0x42)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.E), 0x42)

    # mov d,a                   ;75
    def test_75_mov_d_a(self):
        proc = Processor()
        code = [0x75] # mov d,a
        proc.write_memory(0, code)
        self.assertEqual(proc.read_gp_reg(Registers.D), 0)
        proc.write_gp_reg(Registers.A, 0x42)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.D), 0x42)

    # mov l,a                   ;76
    def test_76_mov_l_a(self):
        proc = Processor()
        code = [0x76] # mov l,a
        proc.write_memory(0, code)
        self.assertEqual(proc.read_gp_reg(Registers.L), 0)
        proc.write_gp_reg(Registers.A, 0x42)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.L), 0x42)

    # mov h,a                   ;77
    def test_67_mov_a_l(self):
        proc = Processor()
        code = [0x77] # mov h,a
        proc.write_memory(0, code)
        self.assertEqual(proc.read_gp_reg(Registers.H), 0)
        proc.write_gp_reg(Registers.A, 0x42)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.H), 0x42)

    # mov a,!0abcdh               ;8e cd ab
    def test_8e_mov_a_addr16(self):
        proc = Processor()
        code = [0x8e, 0xcd, 0xab]
        proc.write_memory(0, code)
        proc.memory[0xabcd] = 0x42
        self.assertEqual(proc.read_gp_reg(Registers.A), 0)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0x42)

    # mov !addr16,a               ;9e cd ab
    def test_9e_mov_addr16_a(self):
        proc = Processor()
        code = [0x9e, 0xcd, 0xab]
        proc.write_memory(0, code)
        self.assertEqual(proc.memory[0xabcd], 0)
        proc.write_gp_reg(Registers.A, 0x42)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xabcd], 0x42)

    # mov a,0fe20h                ;F0 20          saddr
    def test_f0_mov_a_saddr(self):
        proc = Processor()
        code = [0xf0, 0x20]
        proc.write_memory(0, code)
        proc.memory[0xfe20] = 0x42
        self.assertEqual(proc.read_gp_reg(Registers.A), 0)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0x42)

    # mov a,psw                   ;f0 1e
    def test_f0_mov_a_psw(self):
        proc = Processor()
        code = [0xf0, 0x1e]
        proc.write_memory(0, code)
        proc.write_psw(0x42)
        self.assertEqual(proc.read_gp_reg(Registers.A), 0)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0x42)

    # mov 0fe20h,a                ;f2 20          saddr
    def test_f2_mov_saddr_a(self):
        proc = Processor()
        code = [0xf2, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0x42)
        self.assertEqual(proc.memory[0xfe20], 0)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xfe20], 0x42)

    # mov psw,a                   ;f2 1e
    def test_f2_mov_psw_a(self):
        proc = Processor()
        code = [0xf2, 0x1e]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0x42)
        proc.write_psw(0)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0x42)

    # mov a,0fffeh                ;f4 fe          sfr
    def test_f4_mov_a_sfr(self):
        proc = Processor()
        code = [0xf4, 0xfe]
        proc.write_memory(0, code)
        proc.memory[0xfffe] = 0x42
        self.assertEqual(proc.read_gp_reg(Registers.A), 0)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0x42)

    # mov 0fffeh,a                ;f6 fe          sfr
    def test_f6_mov_sfr_a(self):
        proc = Processor()
        code = [0xf6, 0xfe]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0x42)
        self.assertEqual(proc.memory[0xfffe], 0)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xfffe], 0x42)

    # mov 0fe20h,#0abh            ;11 20 ab       saddr
    def test_11_mov_saddr_imm(self):
        proc = Processor()
        code = [0x11, 0x20, 0xab]
        proc.write_memory(0, code)
        proc.memory[0xfe20] = 0
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xfe20], 0xab)

    # mov psw,#0abh               ;11 1e ab
    def test_11_mov_psw_imm(self):
        proc = Processor()
        code = [0x11, 0x1e, 0x42]
        proc.write_memory(0, code)
        proc.write_psw(0)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0x42)

    # mov 0fffeh, #0abh           ;13 fe ab       sfr
    def test_13_mov_sfr_imm(self):
        proc = Processor()
        code = [0x13, 0xfe, 0xab]
        proc.write_memory(0, code)
        proc.memory[0xfffe] = 0
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xfffe], 0xab)

    # or a,#0aah                  ;6d aa
    def test_6d_or_a_imm_result_nonzero(self):
        proc = Processor()
        code = [0x6d, 0xaa]
        proc.write_memory(0, code)
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
        proc.write_memory(0, code)
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
        proc.write_memory(0, code)
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
        proc.write_memory(0, code)
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
        proc.write_memory(0, code)
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
        proc.write_memory(0, code)
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
        proc.write_memory(0, code)
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
        proc.write_memory(0, code)
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
        proc.write_memory(0, code)
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
        proc.write_memory(0, code)
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
        proc.write_memory(0, code)
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
        proc.write_memory(0, code)
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
        proc.write_memory(0, code)
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
        proc.write_memory(0, code)
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
        proc.write_memory(0, code)
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
        proc.write_memory(0, code)
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
        proc.write_memory(0, code)
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
        proc.write_memory(0, code)
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
        proc.write_memory(0, code)
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
        proc.write_memory(0, code)
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
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0xf0)
        proc.write_psw(proc.read_psw() & ~Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0xf0)
        self.assertEqual(proc.read_psw() & Flags.Z, 0)

    # and a,[hl+0abh]             ;59 ab
    def test_59_and_a_based_hl_imm(self):
        proc = Processor()
        code = [0x59, 0xcd]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xab00)
        proc.memory[0xabcd] = 0xff
        proc.write_gp_reg(Registers.A, 0xf0)
        proc.write_psw(proc.read_psw() | Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0xf0)
        self.assertEqual(proc.read_psw() & Flags.Z, 0)

    # and a,0fe20h                ;5e 20          saddr
    def test_5e_and_a_saddr(self):
        proc = Processor()
        code = [0x5e, 0x20]
        proc.write_memory(0, code)
        proc.memory[0xfe20] = 0xff
        proc.write_gp_reg(Registers.A, 0xf0)
        proc.write_psw(proc.read_psw() | Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0xf0)
        self.assertEqual(proc.read_psw() & Flags.Z, 0)

    # and a,[hl]                  ;5f
    def test_5f_and_a_hl(self):
        proc = Processor()
        code = [0x5f]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0xff
        proc.write_gp_reg(Registers.A, 0xf0)
        proc.write_psw(proc.read_psw() | Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0xf0)
        self.assertEqual(proc.read_psw() & Flags.Z, 0)

    # and a,[hl+c]                ;31 5a
    def test_31_5a_and_a_based_hl_c(self):
        proc = Processor()
        code = [0x31, 0x5a]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xab00)
        proc.write_gp_reg(Registers.C, 0xcd)
        proc.memory[0xabcd] = 0xff
        proc.write_gp_reg(Registers.A, 0xf0)
        proc.write_psw(proc.read_psw() | Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0xf0)
        self.assertEqual(proc.read_psw() & Flags.Z, 0)

    # and a,[hl+b]                ;31 5b
    def test_31_5b_and_a_based_hl_b(self):
        proc = Processor()
        code = [0x31, 0x5b]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xab00)
        proc.write_gp_reg(Registers.B, 0xcd)
        proc.memory[0xabcd] = 0xff
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
        proc.write_memory(0, code)
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
        proc.write_memory(0, code)
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
        proc.write_memory(0, code)
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
        proc.write_memory(0, code)
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
        proc.write_memory(0, code)
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
        proc.write_memory(0, code)
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
        proc.write_memory(0, code)
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
        proc.write_memory(0, code)
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
        proc.write_memory(0, code)
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
        proc.write_memory(0, code)
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
        proc.write_memory(0, code)
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
        proc.write_memory(0, code)
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
        proc.write_memory(0, code)
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
        proc.write_memory(0, code)
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
        proc.write_memory(0, code)
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
        proc.write_memory(0, code)
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
        proc.write_memory(0, code)
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
        proc.write_memory(0, code)
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
        proc.write_memory(0, code)
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
        proc.write_memory(0, code)
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
        proc.write_memory(0, code)
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
        proc.write_memory(0, code)
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
        proc.write_memory(0, code)
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
        proc.write_memory(0, code)
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
        proc.write_memory(0, code)
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
        proc.write_memory(0, code)
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
        proc.write_memory(0, code)
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
        proc.write_memory(0, code)
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
        proc.write_memory(0, code)
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
        proc.write_memory(0, code)
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
        proc.write_memory(0, code)
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
        proc.write_memory(0, code)
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
        proc.write_memory(0, code)
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
        proc.write_memory(0, code)
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
        proc.write_memory(0, code)
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
        proc.write_memory(0, code)
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
        proc.write_memory(0, code)
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
        proc.write_memory(0, code)
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
        proc.write_memory(0, code)
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
        proc.write_memory(0, code)
        proc.memory[0xfe20] = 0x55
        proc.write_psw(proc.read_psw() | Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xfe20], 0xAA)
        self.assertEqual(proc.read_psw() & Flags.Z, 0)

    # set1 0fe20h.0               ;0a 20          saddr
    def test_0a_set1_saddr_bit0(self):
        proc = Processor()
        code = [0x0a, 0x20]
        proc.write_memory(0, code)
        proc.memory[0xfe20] = 0b11111110
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xfe20], 0xff)

    # set1 psw.0                  ;0a 1e
    def test_0a_set1_psw_bit0(self):
        proc = Processor()
        code = [0x0a, 0x1e]
        proc.write_memory(0, code)
        proc.write_psw(0b11111110)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0xff)

    # set1 0fe20h.1               ;1a 20          saddr
    def test_1a_set1_saddr_bit1(self):
        proc = Processor()
        code = [0x1a, 0x20]
        proc.write_memory(0, code)
        proc.memory[0xfe20] = 0b11111101
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xfe20], 0xff)

    # set1 psw.1                  ;1a 1e
    def test_1a_set1_psw_bit1(self):
        proc = Processor()
        code = [0x1a, 0x1e]
        proc.write_memory(0, code)
        proc.write_psw(0b11111101)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0xff)

    # set1 0fe20h.2               ;2a 20          saddr
    def test_2a_set1_saddr_bit2(self):
        proc = Processor()
        code = [0x2a, 0x20]
        proc.write_memory(0, code)
        proc.memory[0xfe20] = 0b11111011
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xfe20], 0xff)

    # set1 psw.2                  ;2a 1e
    def test_2a_set1_psw_bit2(self):
        proc = Processor()
        code = [0x2a, 0x1e]
        proc.write_memory(0, code)
        proc.write_psw(0b11111011)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0xff)

    # set1 0fe20h.3               ;3a 20          saddr
    def test_3a_set1_saddr_bit3(self):
        proc = Processor()
        code = [0x3a, 0x20]
        proc.write_memory(0, code)
        proc.memory[0xfe20] = 0b11110111
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xfe20], 0xff)

    # set1 psw.3                  ;3a 1e
    def test_3a_set1_psw_bit3(self):
        proc = Processor()
        code = [0x3a, 0x1e]
        proc.write_memory(0, code)
        proc.write_psw(0b11110111)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0xff)

    # set1 0fe20h.4               ;4a 20          saddr
    def test_4a_set1_saddr_bit4(self):
        proc = Processor()
        code = [0x4a, 0x20]
        proc.write_memory(0, code)
        proc.memory[0xfe20] = 0b11101111
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xfe20], 0xff)

    # set1 psw.4                  ;4a 1e
    def test_4a_set1_psw_bit4(self):
        proc = Processor()
        code = [0x4a, 0x1e]
        proc.write_memory(0, code)
        proc.write_psw(0b11101111)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0xff)

    # set1 0fe20h.5               ;5a 20          saddr
    def test_5a_set1_saddr_bit5(self):
        proc = Processor()
        code = [0x5a, 0x20]
        proc.write_memory(0, code)
        proc.memory[0xfe20] = 0b11011111
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xfe20], 0xff)

    # set1 psw.5                  ;5a 1e
    def test_5a_set1_psw_bit5(self):
        proc = Processor()
        code = [0x5a, 0x1e]
        proc.write_memory(0, code)
        proc.write_psw(0b11011111)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0xff)

    # set1 0fe20h.6               ;6a 20          saddr
    def test_6a_set1_saddr_bit6(self):
        proc = Processor()
        code = [0x6a, 0x20]
        proc.write_memory(0, code)
        proc.memory[0xfe20] = 0b10111111
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xfe20], 0xff)

    # set1 psw.6                  ;6a 1e
    def test_6a_set1_psw_bit6(self):
        proc = Processor()
        code = [0x6a, 0x1e]
        proc.write_memory(0, code)
        proc.write_psw(0b10111111)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0xff)

    # set1 0fe20h.7               ;7a 20          saddr
    def test_7a_set1_saddr_bit7(self):
        proc = Processor()
        code = [0x7a, 0x20]
        proc.write_memory(0, code)
        proc.memory[0xfe20] = 0b01111111
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xfe20], 0xff)

    # set1 psw.7                  ;7a 1e
    # ei                          ;7a 1e          alias for set1 psw.7
    def test_7a_set1_psw_bit7(self):
        proc = Processor()
        code = [0x7a, 0x1e]
        proc.write_memory(0, code)
        proc.write_psw(0b01111111)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0xff)

    # set1 a.0                    ;61 8a
    def test_61_8a_set1_a_bit0(self):
        proc = Processor()
        code = [0x61, 0x8a]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0b11111110)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0xff)

    # set1 a.1                    ;61 9a
    def test_61_9a_set1_a_bit1(self):
        proc = Processor()
        code = [0x61, 0x9a]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0b11111101)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0xff)

    # set1 a.2                    ;61 aa
    def test_61_aa_set1_a_bit2(self):
        proc = Processor()
        code = [0x61, 0xaa]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0b11111011)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0xff)

    # set1 a.3                    ;61 ba
    def test_61_ba_set1_a_bit3(self):
        proc = Processor()
        code = [0x61, 0xba]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0b11110111)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0xff)

    # set1 a.4                    ;61 ca
    def test_61_ca_set1_a_bit4(self):
        proc = Processor()
        code = [0x61, 0xca]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0b11101111)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0xff)

    # set1 a.5                    ;61 da
    def test_61_da_set1_a_bit5(self):
        proc = Processor()
        code = [0x61, 0xda]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0b11011111)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0xff)

    # set1 a.6                    ;61 ea
    def test_61_ea_set1_a_bit6(self):
        proc = Processor()
        code = [0x61, 0xea]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0b10111111)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0xff)

    # set1 a.7                    ;61 fa
    def test_61_fa_set1_a_bit7(self):
        proc = Processor()
        code = [0x61, 0xfa]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0b01111111)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0xff)

    # set1 0fffeh.0               ;71 0a fe       sfr
    def test_71_0a_set1_sfr_bit0(self):
        proc = Processor()
        code = [0x71, 0x0a, 0xfe]
        proc.write_memory(0, code)
        proc.memory[0xfffe] = 0b11111110
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xfffe], 0xff)

    # set1 0fffeh.1               ;71 1a fe       sfr
    def test_71_1a_set1_sfr_bit1(self):
        proc = Processor()
        code = [0x71, 0x1a, 0xfe]
        proc.write_memory(0, code)
        proc.memory[0xfffe] = 0b11111101
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xfffe], 0xff)

    # set1 0fffeh.2               ;71 2a fe       sfr
    def test_71_2a_set1_sfr_bit2(self):
        proc = Processor()
        code = [0x71, 0x2a, 0xfe]
        proc.write_memory(0, code)
        proc.memory[0xfffe] = 0b11111011
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xfffe], 0xff)

    # set1 0fffeh.3               ;71 3a fe       sfr
    def test_71_3a_set1_sfr_bit3(self):
        proc = Processor()
        code = [0x71, 0x3a, 0xfe]
        proc.write_memory(0, code)
        proc.memory[0xfffe] = 0b11110111
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xfffe], 0xff)

    # set1 0fffeh.4               ;71 4a fe       sfr
    def test_71_4a_set1_sfr_bit4(self):
        proc = Processor()
        code = [0x71, 0x4a, 0xfe]
        proc.write_memory(0, code)
        proc.memory[0xfffe] = 0b11101111
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xfffe], 0xff)

    # set1 0fffeh.5               ;71 5a fe       sfr
    def test_71_5a_set1_sfr_bit5(self):
        proc = Processor()
        code = [0x71, 0x5a, 0xfe]
        proc.write_memory(0, code)
        proc.memory[0xfffe] = 0b11011111
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xfffe], 0xff)

    # set1 0fffeh.6               ;71 6a fe       sfr
    def test_71_6a_set1_sfr_bit6(self):
        proc = Processor()
        code = [0x71, 0x6a, 0xfe]
        proc.write_memory(0, code)
        proc.memory[0xfffe] = 0b10111111
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xfffe], 0xff)

    # set1 0fffeh.7               ;71 7a fe       sfr
    def test_71_7a_set1_sfr_bit7(self):
        proc = Processor()
        code = [0x71, 0x7a, 0xfe]
        proc.write_memory(0, code)
        proc.memory[0xfffe] = 0b01111111
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xfffe], 0xff)

    # br $label7                  ;fa 14
    def test_fa_br(self):
        proc = Processor()
        code = [0xfa, 0x14]
        proc.write_memory(0x1000, code)
        proc.pc = 0x1000
        proc.step()
        self.assertEqual(proc.pc, 0x1016)

    # bc $label3                  ;8d fe
    def test_8d_bc_branches_if_carry_set(self):
        proc = Processor()
        code = [0x8d, 0x34]
        proc.write_memory(0x1000, code)
        proc.pc = 0x1000
        proc.write_psw(Flags.CY)
        proc.step()
        self.assertEqual(proc.pc, 0x1036)

    # bc $label3                  ;8d fe
    def test_8d_bc_continues_if_carry_clear(self):
        proc = Processor()
        code = [0x8d, 0x14]
        proc.write_memory(0x1000, code)
        proc.pc = 0x1000
        proc.write_psw(0)
        proc.step()
        self.assertEqual(proc.pc, 0x1000 + len(code))

    # bnc $label3                  ;9d fe
    def test_9d_bc_branches_if_carry_set(self):
        proc = Processor()
        code = [0x9d, 0x34]
        proc.write_memory(0x1000, code)
        proc.pc = 0x1000
        proc.write_psw(0)
        proc.step()
        self.assertEqual(proc.pc, 0x1036)

    # bnc $label3                  ;9d fe
    def test_9d_bc_continues_if_carry_clear(self):
        proc = Processor()
        code = [0x9d, 0x34]
        proc.write_memory(0x1000, code)
        proc.pc = 0x1000
        proc.write_psw(Flags.CY)
        proc.step()
        self.assertEqual(proc.pc, 0x1000 + len(code))

    # bz $label5                  ;ad fe
    def test_ad_bz_branches_if_zero_set(self):
        proc = Processor()
        code = [0xad, 0x34]
        proc.write_memory(0x1000, code)
        proc.pc = 0x1000
        proc.write_psw(Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, 0x1036)

    # bz $label5                  ;ad fe
    def test_ad_bz_continues_if_zero_clear(self):
        proc = Processor()
        code = [0xad, 0x34]
        proc.write_memory(0x1000, code)
        proc.pc = 0x1000
        proc.write_psw(0)
        proc.step()
        self.assertEqual(proc.pc, 0x1000 + len(code))

    # bnz $label5                 ;bd fe
    def test_bd_bz_branches_if_zero_clear(self):
        proc = Processor()
        code = [0xbd, 0x34]
        proc.write_memory(0x1000, code)
        proc.pc = 0x1000
        proc.write_psw(0)
        proc.step()
        self.assertEqual(proc.pc, 0x1036)

    # bnz $label5                 ;bd fe
    def test_bd_bz_continues_if_zero_set(self):
        proc = Processor()
        code = [0xbd, 0x34]
        proc.write_memory(0x1000, code)
        proc.pc = 0x1000
        proc.write_psw(Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, 0x1000 + len(code))

    # clr1 a.0                    ;61 8b
    def test_61_8b_clr1_a_bit0(self):
        proc = Processor()
        code = [0x61, 0x8b]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0b11111111)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0b11111110)

    # clr1 a.1                    ;61 9b
    def test_61_9b_clr1_a_bit1(self):
        proc = Processor()
        code = [0x61, 0x9b]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0b11111111)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0b11111101)

    # clr1 a.2                    ;61 ab
    def test_61_ab_clr1_a_bit2(self):
        proc = Processor()
        code = [0x61, 0xab]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0b11111111)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0b11111011)

    # clr1 a.3                    ;61 bb
    def test_61_bb_clr1_a_bit3(self):
        proc = Processor()
        code = [0x61, 0xbb]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0b11111111)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0b11110111)

    # clr1 a.4                    ;61 cb
    def test_61_cb_clr1_a_bit4(self):
        proc = Processor()
        code = [0x61, 0xcb]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0b11111111)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0b11101111)

    # clr1 a.5                    ;61 db
    def test_61_db_clr1_a_bit5(self):
        proc = Processor()
        code = [0x61, 0xdb]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0b11111111)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0b11011111)

    # clr1 a.6                    ;61 eb
    def test_61_eb_clr1_a_bit6(self):
        proc = Processor()
        code = [0x61, 0xeb]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0b11111111)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0b10111111)

    # clr1 a.7                    ;61 fb
    def test_61_fb_clr1_a_bit7(self):
        proc = Processor()
        code = [0x61, 0xfb]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0b11111111)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0b01111111)

    # clr1 0fffeh.0               ;71 0b fe       sfr
    def test_71_0b_clr1_sfr_bit0(self):
        proc = Processor()
        code = [0x71, 0x0b, 0xfe]
        proc.write_memory(0, code)
        proc.memory[0xfffe] = 0b11111111
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xfffe], 0b11111110)

    # clr1 0fffeh.1               ;71 1b fe       sfr
    def test_71_1b_clr1_sfr_bit1(self):
        proc = Processor()
        code = [0x71, 0x1b, 0xfe]
        proc.write_memory(0, code)
        proc.memory[0xfffe] = 0b11111111
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xfffe], 0b11111101)

    # clr1 0fffeh.2               ;71 2b fe       sfr
    def test_71_2b_clr1_sfr_bit2(self):
        proc = Processor()
        code = [0x71, 0x2b, 0xfe]
        proc.write_memory(0, code)
        proc.memory[0xfffe] = 0b11111111
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xfffe], 0b11111011)

    # clr1 0fffeh.3               ;71 3b fe       sfr
    def test_71_3b_clr1_sfr_bit3(self):
        proc = Processor()
        code = [0x71, 0x3b, 0xfe]
        proc.write_memory(0, code)
        proc.memory[0xfffe] = 0b11111111
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xfffe], 0b11110111)

    # clr1 0fffeh.4               ;71 4b fe       sfr
    def test_71_4b_clr1_sfr_bit4(self):
        proc = Processor()
        code = [0x71, 0x4b, 0xfe]
        proc.write_memory(0, code)
        proc.memory[0xfffe] = 0b11111111
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xfffe], 0b11101111)

    # clr1 0fffeh.5               ;71 5b fe       sfr
    def test_71_5b_clr1_sfr_bit5(self):
        proc = Processor()
        code = [0x71, 0x5b, 0xfe]
        proc.write_memory(0, code)
        proc.memory[0xfffe] = 0b11111111
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xfffe], 0b11011111)

    # clr1 0fffeh.6               ;71 6b fe       sfr
    def test_71_6b_clr1_sfr_bit6(self):
        proc = Processor()
        code = [0x71, 0x6b, 0xfe]
        proc.write_memory(0, code)
        proc.memory[0xfffe] = 0b11111111
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xfffe], 0b10111111)

    # clr1 0fffeh.7               ;71 7b fe       sfr
    def test_71_7b_clr1_sfr_bit7(self):
        proc = Processor()
        code = [0x71, 0x7b, 0xfe]
        proc.write_memory(0, code)
        proc.memory[0xfffe] = 0b11111111
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xfffe], 0b01111111)

    # clr1 0fe20h.0               ;0b 20          saddr
    def test_0b_clr1_saddr_bit0(self):
        proc = Processor()
        code = [0x0b, 0x20]
        proc.write_memory(0, code)
        proc.memory[0xfe20] = 0b11111111
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xfe20], 0b11111110)

    # clr1 psw.0                  ;0b 1e
    def test_0b_clr1_psw_bit0(self):
        proc = Processor()
        code = [0x0b, 0x1e]
        proc.write_memory(0, code)
        proc.write_psw(0b11111111)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0b11111110)

    # clr1 0fe20h.1               ;1b 20          saddr
    def test_1b_clr1_saddr_bit1(self):
        proc = Processor()
        code = [0x1b, 0x20]
        proc.write_memory(0, code)
        proc.memory[0xfe20] = 0b11111111
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xfe20], 0b11111101)

    # clr1 psw.1                  ;1b 1e
    def test_1b_clr1_psw_bit1(self):
        proc = Processor()
        code = [0x1b, 0x1e]
        proc.write_memory(0, code)
        proc.write_psw(0b11111111)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0b11111101)

    # clr1 0fe20h.2               ;2b 20          saddr
    def test_2b_clr1_saddr_bit2(self):
        proc = Processor()
        code = [0x2b, 0x20]
        proc.write_memory(0, code)
        proc.memory[0xfe20] = 0b11111111
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xfe20], 0b11111011)

    # clr1 psw.2                  ;2b 1e
    def test_2b_clr1_psw_bit2(self):
        proc = Processor()
        code = [0x2b, 0x1e]
        proc.write_memory(0, code)
        proc.write_psw(0b11111111)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0b11111011)

    # clr1 0fe20h.3               ;3b 20          saddr
    def test_3b_clr1_saddr_bit3(self):
        proc = Processor()
        code = [0x3b, 0x20]
        proc.write_memory(0, code)
        proc.memory[0xfe20] = 0b11111111
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xfe20], 0b11110111)

    # clr1 psw.3                  ;3b 1e
    def test_3b_clr1_psw_bit3(self):
        proc = Processor()
        code = [0x3b, 0x1e]
        proc.write_memory(0, code)
        proc.write_psw(0b11111111)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0b11110111)

    # clr1 0fe20h.4               ;4b 20          saddr
    def test_4b_clr1_saddr_bit4(self):
        proc = Processor()
        code = [0x4b, 0x20]
        proc.write_memory(0, code)
        proc.memory[0xfe20] = 0b11111111
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xfe20], 0b11101111)

    # clr1 psw.4                  ;4b 1e
    def test_4b_clr1_psw_bit4(self):
        proc = Processor()
        code = [0x4b, 0x1e]
        proc.write_memory(0, code)
        proc.write_psw(0b11111111)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0b11101111)

    # clr1 0fe20h.5               ;5b 20          saddr
    def test_5b_clr1_saddr_bit5(self):
        proc = Processor()
        code = [0x5b, 0x20]
        proc.write_memory(0, code)
        proc.memory[0xfe20] = 0b11111111
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xfe20], 0b11011111)

    # clr1 psw.5                  ;5b 1e
    def test_5b_clr1_psw_bit5(self):
        proc = Processor()
        code = [0x5b, 0x1e]
        proc.write_memory(0, code)
        proc.write_psw(0b11111111)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0b11011111)

    # clr1 0fe20h.6               ;6b 20          saddr
    def test_6b_clr1_saddr_bit6(self):
        proc = Processor()
        code = [0x6b, 0x20]
        proc.write_memory(0, code)
        proc.memory[0xfe20] = 0b11111111
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xfe20], 0b10111111)

    # clr1 psw.6                  ;6b 1e
    def test_6b_clr1_psw_bit6(self):
        proc = Processor()
        code = [0x6b, 0x1e]
        proc.write_memory(0, code)
        proc.write_psw(0b11111111)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0b10111111)

    # clr1 0fe20h.7               ;7b 20          saddr
    def test_7b_clr1_saddr_bit6(self):
        proc = Processor()
        code = [0x7b, 0x20]
        proc.write_memory(0, code)
        proc.memory[0xfe20] = 0b11111111
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xfe20], 0b01111111)

    # clr1 psw.7                  ;7b 1e
    # di                          ;7b 1e          alias for clr1 psw.7
    def test_7b_clr1_psw_bit7(self):
        proc = Processor()
        code = [0x7b, 0x1e]
        proc.write_memory(0, code)
        proc.write_psw(0b11111111)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0b01111111)

    # movw sp,#0abcdh             ;ee 1c cd ab  (SP=0xFF1C)
    def test_ee_movw_sp_imm16(self):
        proc = Processor()
        code = [0xee, 0x1c, 0xcd, 0xab]
        proc.write_memory(0, code)
        proc.sp = 0
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.sp, 0xabcd)

    # mov1 cy,a.0                 ;61 8c
    def test_61_8c_mov1_cy_a_bit0_set(self):
        proc = Processor()
        code = [0x61, 0x8c]
        proc.write_memory(0, code)
        proc.write_psw(0b11111110)
        proc.write_gp_reg(Registers.A, 0b01010101) # bit 0 = 1
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0b11111111)# bit 0 = 1

    # mov1 cy,a.0                 ;61 8c
    def test_61_8c_mov1_cy_a_bit0_clear(self):
        proc = Processor()
        code = [0x61, 0x8c]
        proc.write_memory(0, code)
        proc.write_psw(0b11111111)
        proc.write_gp_reg(Registers.A, 0b10101010) # bit 0 = 0
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0b11111110) # CY = 0

    # mov1 cy,a.1                 ;61 9c
    def test_61_9c_mov1_cy_a_bit1(self):
        proc = Processor()
        code = [0x61, 0x9c]
        proc.write_memory(0, code)
        proc.write_psw(0b11111111)
        proc.write_gp_reg(Registers.A, 0b11111101) # bit 1 = 0
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0b11111110) # CY = 0

    # mov1 cy,a.2                 ;61 ac
    def test_61_ac_mov1_cy_a_bit2(self):
        proc = Processor()
        code = [0x61, 0xac]
        proc.write_memory(0, code)
        proc.write_psw(0b11111111)
        proc.write_gp_reg(Registers.A, 0b11111011) # bit 2 = 0
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0b11111110) # CY = 0

    # mov1 cy,a.3                 ;61 bc
    def test_61_bc_mov1_cy_a_bit3(self):
        proc = Processor()
        code = [0x61, 0xbc]
        proc.write_memory(0, code)
        proc.write_psw(0b11111111)
        proc.write_gp_reg(Registers.A, 0b11110111) # bit 3 = 0
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0b11111110) # CY = 0

    # mov1 cy,a.4                 ;61 cc
    def test_61_cc_mov1_cy_a_bit3(self):
        proc = Processor()
        code = [0x61, 0xcc]
        proc.write_memory(0, code)
        proc.write_psw(0b11111111)
        proc.write_gp_reg(Registers.A, 0b11101111) # bit 4 = 0
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0b11111110) # CY = 0

    # mov1 cy,a.5                 ;61 dc
    def test_61_dc_mov1_cy_a_bit4(self):
        proc = Processor()
        code = [0x61, 0xdc]
        proc.write_memory(0, code)
        proc.write_psw(0b11111111)
        proc.write_gp_reg(Registers.A, 0b11011111) # bit 5 = 0
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0b11111110) # CY = 0

    # mov1 cy,a.6                 ;61 ec
    def test_61_ec_mov1_cy_a_bit5(self):
        proc = Processor()
        code = [0x61, 0xec]
        proc.write_memory(0, code)
        proc.write_psw(0b11111111)
        proc.write_gp_reg(Registers.A, 0b10111111) # bit 6 = 0
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0b11111110) # CY = 0

    # mov1 cy,a.7                 ;61 fc
    def test_61_fc_mov1_cy_a_bit7(self):
        proc = Processor()
        code = [0x61, 0xfc]
        proc.write_memory(0, code)
        proc.write_psw(0b11111111)
        proc.write_gp_reg(Registers.A, 0b01111111) # bit 7 = 0
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0b11111110) # CY = 0

    # mov1 a.0,cy                 ;61 89
    def test_61_89_mov1_a_bit0_cy(self):
        proc = Processor()
        code = [0x61, 0x89]
        proc.write_memory(0, code)
        proc.write_psw(Flags.CY)
        proc.write_gp_reg(Registers.A, 0)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0b00000001) # bit 0 = 1

    # mov1 a.1,cy                 ;61 99
    def test_61_99_mov1_a_bit1_cy(self):
        proc = Processor()
        code = [0x61, 0x99]
        proc.write_memory(0, code)
        proc.write_psw(Flags.CY)
        proc.write_gp_reg(Registers.A, 0)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0b00000010) # bit 1 = 1

    # mov1 a.2,cy                 ;61 a9
    def test_61_a9_mov1_a_bit2_cy(self):
        proc = Processor()
        code = [0x61, 0xa9]
        proc.write_memory(0, code)
        proc.write_psw(Flags.CY)
        proc.write_gp_reg(Registers.A, 0)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0b00000100) # bit 2 = 1

    # mov1 a.3,cy                 ;61 b9
    def test_61_b9_mov1_a_bit3_cy(self):
        proc = Processor()
        code = [0x61, 0xb9]
        proc.write_memory(0, code)
        proc.write_psw(Flags.CY)
        proc.write_gp_reg(Registers.A, 0)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0b00001000) # bit 3 = 1

    # mov1 a.4,cy                 ;61 c9
    def test_61_c9_mov1_a_bit4_cy(self):
        proc = Processor()
        code = [0x61, 0xc9]
        proc.write_memory(0, code)
        proc.write_psw(Flags.CY)
        proc.write_gp_reg(Registers.A, 0)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0b00010000) # bit 4 = 1

    # mov1 a.5,cy                 ;61 d9
    def test_61_d9_mov1_a_bit5_cy(self):
        proc = Processor()
        code = [0x61, 0xd9]
        proc.write_memory(0, code)
        proc.write_psw(Flags.CY)
        proc.write_gp_reg(Registers.A, 0)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0b00100000) # bit 5 = 1

    # mov1 a.6,cy                 ;61 e9
    def test_61_e9_mov1_a_bit6_cy(self):
        proc = Processor()
        code = [0x61, 0xe9]
        proc.write_memory(0, code)
        proc.write_psw(Flags.CY)
        proc.write_gp_reg(Registers.A, 0)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0b01000000) # bit 6 = 1

    # mov1 a.7,cy                 ;61 f9
    def test_61_f9_mov1_a_bit7_cy(self):
        proc = Processor()
        code = [0x61, 0xf9]
        proc.write_memory(0, code)
        proc.write_psw(Flags.CY)
        proc.write_gp_reg(Registers.A, 0)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0b10000000) # bit 7 = 1

    # mov1 cy,0fffeh.0            ;71 0c fe       sfr
    def test_71_0c_mov1_cy_sfr_bit0(self):
        proc = Processor()
        code = [0x71, 0x0c, 0xfe]
        proc.write_memory(0, code)
        proc.memory[0xfffe] = 0b00000001
        proc.write_psw(0)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), Flags.CY)

    # mov1 cy,0fffeh.1            ;71 1c fe       sfr
    def test_71_1c_mov1_cy_sfr_bit1(self):
        proc = Processor()
        code = [0x71, 0x1c, 0xfe]
        proc.write_memory(0, code)
        proc.memory[0xfffe] = 0b00000010
        proc.write_psw(0)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), Flags.CY)

    # mov1 cy,0fffeh.2            ;71 2c fe       sfr
    def test_71_2c_mov1_cy_sfr_bit2(self):
        proc = Processor()
        code = [0x71, 0x2c, 0xfe]
        proc.write_memory(0, code)
        proc.memory[0xfffe] = 0b00000100
        proc.write_psw(0)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), Flags.CY)

    # mov1 cy,0fffeh.3            ;71 3c fe       sfr
    def test_71_3c_mov1_cy_sfr_bit3(self):
        proc = Processor()
        code = [0x71, 0x3c, 0xfe]
        proc.write_memory(0, code)
        proc.memory[0xfffe] = 0b00001000
        proc.write_psw(0)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), Flags.CY)

    # mov1 cy,0fffeh.4            ;71 4c fe       sfr
    def test_71_4c_mov1_cy_sfr_bit4(self):
        proc = Processor()
        code = [0x71, 0x4c, 0xfe]
        proc.write_memory(0, code)
        proc.memory[0xfffe] = 0b00010000
        proc.write_psw(0)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), Flags.CY)

    # mov1 cy,0fffeh.5            ;71 5c fe       sfr
    def test_71_5c_mov1_cy_sfr_bit5(self):
        proc = Processor()
        code = [0x71, 0x5c, 0xfe]
        proc.write_memory(0, code)
        proc.memory[0xfffe] = 0b00100000
        proc.write_psw(0)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), Flags.CY)

    # mov1 cy,0fffeh.6            ;71 6c fe       sfr
    def test_71_6c_mov1_cy_sfr_bit6(self):
        proc = Processor()
        code = [0x71, 0x6c, 0xfe]
        proc.write_memory(0, code)
        proc.memory[0xfffe] = 0b01000000
        proc.write_psw(0)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), Flags.CY)

    # mov1 cy,0fffeh.7            ;71 7c fe       sfr
    def test_71_7c_mov1_cy_sfr_bit7(self):
        proc = Processor()
        code = [0x71, 0x7c, 0xfe]
        proc.write_memory(0, code)
        proc.memory[0xfffe] = 0b10000000
        proc.write_psw(0)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), Flags.CY)

    # mov1 0fffeh.0,cy            ;71 09 fe       sfr
    def test_71_09_mov1_sfr_bit_0_cy(self):
        proc = Processor()
        code = [0x71, 0x09, 0xfe]
        proc.write_memory(0, code)
        proc.memory[0xfffe] = 0
        proc.write_psw(Flags.CY)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xfffe], 0b00000001)

    # mov1 0fffeh.1,cy            ;71 19 fe       sfr
    def test_71_19_mov1_sfr_bit_1_cy(self):
        proc = Processor()
        code = [0x71, 0x19, 0xfe]
        proc.write_memory(0, code)
        proc.memory[0xfffe] = 0
        proc.write_psw(Flags.CY)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xfffe], 0b00000010)

    # mov1 0fffeh.2,cy            ;71 29 fe       sfr
    def test_71_29_mov1_sfr_bit_2_cy(self):
        proc = Processor()
        code = [0x71, 0x29, 0xfe]
        proc.write_memory(0, code)
        proc.memory[0xfffe] = 0
        proc.write_psw(Flags.CY)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xfffe], 0b00000100)

    # mov1 0fffeh.3,cy            ;71 39 fe       sfr
    def test_71_39_mov1_sfr_bit_3_cy(self):
        proc = Processor()
        code = [0x71, 0x39, 0xfe]
        proc.write_memory(0, code)
        proc.memory[0xfffe] = 0
        proc.write_psw(Flags.CY)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xfffe], 0b00001000)

    # mov1 0fffeh.4,cy            ;71 49 fe       sfr
    def test_71_49_mov1_sfr_bit_4_cy(self):
        proc = Processor()
        code = [0x71, 0x49, 0xfe]
        proc.write_memory(0, code)
        proc.memory[0xfffe] = 0
        proc.write_psw(Flags.CY)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xfffe], 0b00010000)

    # mov1 0fffeh.5,cy            ;71 59 fe       sfr
    def test_71_59_mov1_sfr_bit_5_cy(self):
        proc = Processor()
        code = [0x71, 0x59, 0xfe]
        proc.write_memory(0, code)
        proc.memory[0xfffe] = 0
        proc.write_psw(Flags.CY)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xfffe], 0b00100000)

    # mov1 0fffeh.6,cy            ;71 69 fe       sfr
    def test_71_69_mov1_sfr_bit_6_cy(self):
        proc = Processor()
        code = [0x71, 0x69, 0xfe]
        proc.write_memory(0, code)
        proc.memory[0xfffe] = 0
        proc.write_psw(Flags.CY)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xfffe], 0b01000000)

    # mov1 0fffeh.7,cy            ;71 79 fe       sfr
    def test_71_79_mov1_sfr_bit_7_cy(self):
        proc = Processor()
        code = [0x71, 0x79, 0xfe]
        proc.write_memory(0, code)
        proc.memory[0xfffe] = 0
        proc.write_psw(Flags.CY)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xfffe], 0b10000000)

    # mov1 0fe20h.0,cy            ;71 01 20       saddr
    def test_71_01_mov1_saddr_bit0_cy(self):
        proc = Processor()
        code = [0x71, 0x01, 0x20]
        proc.write_memory(0, code)
        proc.memory[0xfe20] = 0
        proc.write_psw(Flags.CY)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xfe20], 0b00000001)

    # mov1 0fe20h.1,cy            ;71 11 20       saddr
    def test_71_11_mov1_saddr_bit1_cy(self):
        proc = Processor()
        code = [0x71, 0x11, 0x20]
        proc.write_memory(0, code)
        proc.memory[0xfe20] = 0
        proc.write_psw(Flags.CY)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xfe20], 0b00000010)

    # mov1 0fe20h.2,cy            ;71 21 20       saddr
    def test_71_21_mov1_saddr_bit2_cy(self):
        proc = Processor()
        code = [0x71, 0x21, 0x20]
        proc.write_memory(0, code)
        proc.memory[0xfe20] = 0
        proc.write_psw(Flags.CY)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xfe20], 0b00000100)

    # mov1 0fe20h.3,cy            ;71 31 20       saddr
    def test_71_31_mov1_saddr_bit3_cy(self):
        proc = Processor()
        code = [0x71, 0x31, 0x20]
        proc.write_memory(0, code)
        proc.memory[0xfe20] = 0
        proc.write_psw(Flags.CY)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xfe20], 0b00001000)

    # mov1 0fe20h.4,cy            ;71 41 20       saddr
    def test_71_41_mov1_saddr_bit4_cy(self):
        proc = Processor()
        code = [0x71, 0x41, 0x20]
        proc.write_memory(0, code)
        proc.memory[0xfe20] = 0
        proc.write_psw(Flags.CY)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xfe20], 0b00010000)

    # mov1 0fe20h.5,cy            ;71 51 20       saddr
    def test_71_51_mov1_saddr_bit5_cy(self):
        proc = Processor()
        code = [0x71, 0x51, 0x20]
        proc.write_memory(0, code)
        proc.memory[0xfe20] = 0
        proc.write_psw(Flags.CY)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xfe20], 0b00100000)

    # mov1 0fe20h.6,cy            ;71 61 20       saddr
    def test_71_61_mov1_saddr_bit6_cy(self):
        proc = Processor()
        code = [0x71, 0x61, 0x20]
        proc.write_memory(0, code)
        proc.memory[0xfe20] = 0
        proc.write_psw(Flags.CY)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xfe20], 0b01000000)

    # mov1 0fe20h.7,cy            ;71 71 20       saddr
    def test_71_71_mov1_saddr_bit7_cy(self):
        proc = Processor()
        code = [0x71, 0x71, 0x20]
        proc.write_memory(0, code)
        proc.memory[0xfe20] = 0
        proc.write_psw(Flags.CY)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xfe20], 0b10000000)

    # mov1 psw.0,cy               ;71 01 1e
    def test_71_01_mov1_psw_bit0_cy(self):
        proc = Processor()
        code = [0x71, 0x01, 0x1e]
        proc.write_memory(0, code)
        proc.write_psw(Flags.CY)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0b00000001)

    # mov1 psw.1,cy               ;71 11 1e
    def test_71_11_mov1_psw_bit1_cy(self):
        proc = Processor()
        code = [0x71, 0x11, 0x1e]
        proc.write_memory(0, code)
        proc.write_psw(Flags.CY)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0b00000011)

    # mov1 psw.2,cy               ;71 21 1e
    def test_71_21_mov1_psw_bit2_cy(self):
        proc = Processor()
        code = [0x71, 0x21, 0x1e]
        proc.write_memory(0, code)
        proc.write_psw(Flags.CY)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0b00000101)

    # mov1 psw.3,cy               ;71 31 1e
    def test_71_31_mov1_psw_bit3_cy(self):
        proc = Processor()
        code = [0x71, 0x31, 0x1e]
        proc.write_memory(0, code)
        proc.write_psw(Flags.CY)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0b00001001)

    # mov1 psw.4,cy               ;71 41 1e
    def test_71_41_mov1_psw_bit4_cy(self):
        proc = Processor()
        code = [0x71, 0x41, 0x1e]
        proc.write_memory(0, code)
        proc.write_psw(Flags.CY)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0b00010001)

    # mov1 psw.5,cy               ;71 51 1e
    def test_71_51_mov1_psw_bit5_cy(self):
        proc = Processor()
        code = [0x71, 0x51, 0x1e]
        proc.write_memory(0, code)
        proc.write_psw(Flags.CY)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0b00100001)

    # mov1 psw.6,cy               ;71 61 1e
    def test_71_61_mov1_psw_bit6_cy(self):
        proc = Processor()
        code = [0x71, 0x61, 0x1e]
        proc.write_memory(0, code)
        proc.write_psw(Flags.CY)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0b01000001)

    # mov1 psw.7,cy               ;71 71 1e
    def test_71_71_mov1_psw_bit7_cy(self):
        proc = Processor()
        code = [0x71, 0x71, 0x1e]
        proc.write_memory(0, code)
        proc.write_psw(Flags.CY)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0b10000001)

    # mov1 cy,0fe20h.0            ;71 04 20       saddr
    def test_71_04_mov1_cy_saddr_bit0(self):
        proc = Processor()
        code = [0x71, 0x04, 0x20]
        proc.write_memory(0, code)
        proc.memory[0xfe20] = 0b00000001
        proc.write_psw(0)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0b00000001)

    # mov1 cy,0fe20h.1            ;71 14 20       saddr
    def test_71_14_mov1_cy_saddr_bit1(self):
        proc = Processor()
        code = [0x71, 0x14, 0x20]
        proc.write_memory(0, code)
        proc.memory[0xfe20] = 0b00000010
        proc.write_psw(0)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0b00000001)

    # mov1 cy,0fe20h.2            ;71 24 20       saddr
    def test_71_24_mov1_cy_saddr_bit2(self):
        proc = Processor()
        code = [0x71, 0x24, 0x20]
        proc.write_memory(0, code)
        proc.memory[0xfe20] = 0b00000100
        proc.write_psw(0)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0b00000001)

    # mov1 cy,0fe20h.3            ;71 34 20       saddr
    def test_71_34_mov1_cy_saddr_bit3(self):
        proc = Processor()
        code = [0x71, 0x34, 0x20]
        proc.write_memory(0, code)
        proc.memory[0xfe20] = 0b00001000
        proc.write_psw(0)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0b00000001)

    # mov1 cy,0fe20h.4            ;71 44 20       saddr
    def test_71_44_mov1_cy_saddr_bit4(self):
        proc = Processor()
        code = [0x71, 0x44, 0x20]
        proc.write_memory(0, code)
        proc.memory[0xfe20] = 0b00010000
        proc.write_psw(0)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0b00000001)

    # mov1 cy,0fe20h.5            ;71 54 20       saddr
    def test_71_54_mov1_cy_saddr_bit5(self):
        proc = Processor()
        code = [0x71, 0x54, 0x20]
        proc.write_memory(0, code)
        proc.memory[0xfe20] = 0b00100000
        proc.write_psw(0)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0b00000001)

    # mov1 cy,0fe20h.6            ;71 64 20       saddr
    def test_71_64_mov1_cy_saddr_bit6(self):
        proc = Processor()
        code = [0x71, 0x64, 0x20]
        proc.write_memory(0, code)
        proc.memory[0xfe20] = 0b01000000
        proc.write_psw(0)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0b00000001)

    # mov1 cy,0fe20h.7            ;71 74 20       saddr
    def test_71_74_mov1_cy_saddr_bit7(self):
        proc = Processor()
        code = [0x71, 0x74, 0x20]
        proc.write_memory(0, code)
        proc.memory[0xfe20] = 0b10000000
        proc.write_psw(0)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0b00000001)

    # mov1 cy,psw.0               ;71 04 1e
    def test_71_04_mov1_cy_psw_bit0(self):
        proc = Processor()
        code = [0x71, 0x04, 0x1e]
        proc.write_memory(0, code)
        proc.write_psw(0b00000001)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0b00000001)

    # mov1 cy,psw.1               ;71 14 1e
    def test_71_14_mov1_cy_psw_bit1(self):
        proc = Processor()
        code = [0x71, 0x14, 0x1e]
        proc.write_memory(0, code)
        proc.write_psw(0b00000010)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0b00000011)

    # mov1 cy,psw.2               ;71 24 1e
    def test_71_24_mov1_cy_psw_bit2(self):
        proc = Processor()
        code = [0x71, 0x24, 0x1e]
        proc.write_memory(0, code)
        proc.write_psw(0b00000100)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0b00000101)

    # mov1 cy,psw.3               ;71 34 1e
    def test_71_34_mov1_cy_psw_bit3(self):
        proc = Processor()
        code = [0x71, 0x34, 0x1e]
        proc.write_memory(0, code)
        proc.write_psw(0b00001000)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0b00001001)

    # mov1 cy,psw.4               ;71 44 1e
    def test_71_44_mov1_cy_psw_bit4(self):
        proc = Processor()
        code = [0x71, 0x44, 0x1e]
        proc.write_memory(0, code)
        proc.write_psw(0b00010000)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0b00010001)

    # mov1 cy,psw.5               ;71 54 1e
    def test_71_54_mov1_cy_psw_bit5(self):
        proc = Processor()
        code = [0x71, 0x54, 0x1e]
        proc.write_memory(0, code)
        proc.write_psw(0b00100000)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0b00100001)

    # mov1 cy,psw.6               ;71 64 1e
    def test_71_64_mov1_cy_psw_bit6(self):
        proc = Processor()
        code = [0x71, 0x64, 0x1e]
        proc.write_memory(0, code)
        proc.write_psw(0b01000000)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0b01000001)

    # mov1 cy,psw.7               ;71 74 1e
    def test_71_74_mov1_cy_psw_bit7(self):
        proc = Processor()
        code = [0x71, 0x74, 0x1e]
        proc.write_memory(0, code)
        proc.write_psw(0b10000000)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0b10000001)

    #    inc x                       ;40
    def test_40_inc_x_result_0_to_1_clears_z_ac(self):
        proc = Processor()
        code = [0x40]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.X, 0)
        proc.write_psw(Flags.Z | Flags.AC)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0)
        self.assertEqual(proc.read_gp_reg(Registers.X), 1)

    #    inc x                       ;40
    def test_40_inc_x_result_ff_to_0_wraps_and_sets_z(self):
        proc = Processor()
        code = [0x40]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.X, 0xFF)
        proc.write_psw(Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), Flags.Z)
        self.assertEqual(proc.read_gp_reg(Registers.X), 0)

    #    inc x                       ;40
    def test_40_inc_x_result_0f_to_10_sets_ac(self):
        proc = Processor()
        code = [0x40]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.X, 0b00001111)
        proc.write_psw(Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), Flags.AC)
        self.assertEqual(proc.read_gp_reg(Registers.X), 0b00010000)

    #    inc a                       ;41
    def test_41_inc_a(self):
        proc = Processor()
        code = [0x41]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0)
        proc.write_psw(Flags.Z | Flags.AC)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0)
        self.assertEqual(proc.read_gp_reg(Registers.A), 1)

    #    inc c                       ;42
    def test_42_inc_c(self):
        proc = Processor()
        code = [0x42]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.C, 0)
        proc.write_psw(Flags.Z | Flags.AC)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0)
        self.assertEqual(proc.read_gp_reg(Registers.C), 1)

    #    inc b                       ;43
    def test_43_inc_b(self):
        proc = Processor()
        code = [0x43]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.B, 0)
        proc.write_psw(Flags.Z | Flags.AC)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0)
        self.assertEqual(proc.read_gp_reg(Registers.B), 1)

    #    inc e                       ;44
    def test_44_inc_e(self):
        proc = Processor()
        code = [0x44]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.E, 0)
        proc.write_psw(Flags.Z | Flags.AC)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0)
        self.assertEqual(proc.read_gp_reg(Registers.E), 1)

    #    inc d                       ;45
    def test_45_inc_d(self):
        proc = Processor()
        code = [0x45]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.D, 0)
        proc.write_psw(Flags.Z | Flags.AC)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0)
        self.assertEqual(proc.read_gp_reg(Registers.D), 1)

    #    inc l                       ;46
    def test_46_inc_l(self):
        proc = Processor()
        code = [0x46]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.L, 0)
        proc.write_psw(Flags.Z | Flags.AC)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0)
        self.assertEqual(proc.read_gp_reg(Registers.L), 1)

    #    inc h                       ;47
    def test_47_inc_h(self):
        proc = Processor()
        code = [0x47]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.H, 0)
        proc.write_psw(Flags.Z | Flags.AC)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0)
        self.assertEqual(proc.read_gp_reg(Registers.H), 1)

    # inc 0fe20h                  ;81 20          saddr
    def test_81_inc_saddr(self):
        proc = Processor()
        code = [0x81, 0x20]
        proc.write_memory(0, code)
        proc.memory[0xfe20] = 0
        proc.write_psw(Flags.Z | Flags.AC)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0)
        self.assertEqual(proc.memory[0xfe20], 1)

    # callf !0842h                ;0c 42
    def test_0c_callf_addr11(self):
        proc = Processor()
        code = [0x0c, 0x42]
        proc.write_memory(0x0123, code)
        proc.pc = 0x0123
        return_address = proc.pc + len(code)
        proc.sp = 0xFE1F
        proc.step()
        self.assertEqual(proc.sp, 0xFE1d)
        self.assertEqual(proc.memory[0xFE1d], (return_address & 0xFF))
        self.assertEqual(proc.memory[0xFE1e], (return_address >> 8))
        self.assertEqual(proc.pc, 0x0842)

    # callf !0942h                ;1c 42
    def test_1c_callf_addr11(self):
        proc = Processor()
        code = [0x1c, 0x42]
        proc.write_memory(0x0123, code)
        proc.pc = 0x0123
        return_address = proc.pc + len(code)
        proc.sp = 0xFE1F
        proc.step()
        self.assertEqual(proc.sp, 0xFE1d)
        self.assertEqual(proc.memory[0xFE1d], (return_address & 0xFF))
        self.assertEqual(proc.memory[0xFE1e], (return_address >> 8))
        self.assertEqual(proc.pc, 0x0942)

    # callf !0a42h                ;2c 42
    def test_2c_callf_addr11(self):
        proc = Processor()
        code = [0x2c, 0x42]
        proc.write_memory(0x0123, code)
        proc.pc = 0x0123
        return_address = proc.pc + len(code)
        proc.sp = 0xFE1F
        proc.step()
        self.assertEqual(proc.sp, 0xFE1d)
        self.assertEqual(proc.memory[0xFE1d], (return_address & 0xFF))
        self.assertEqual(proc.memory[0xFE1e], (return_address >> 8))
        self.assertEqual(proc.pc, 0x0a42)

    # callf !0b42h                ;3c 42
    def test_3c_callf_addr11(self):
        proc = Processor()
        code = [0x3c, 0x42]
        proc.write_memory(0x0123, code)
        proc.pc = 0x0123
        return_address = proc.pc + len(code)
        proc.sp = 0xFE1F
        proc.step()
        self.assertEqual(proc.sp, 0xFE1d)
        self.assertEqual(proc.memory[0xFE1d], (return_address & 0xFF))
        self.assertEqual(proc.memory[0xFE1e], (return_address >> 8))
        self.assertEqual(proc.pc, 0x0b42)

    # callf !0c42h                ;4c 42
    def test_4c_callf_addr11(self):
        proc = Processor()
        code = [0x4c, 0x42]
        proc.write_memory(0x0123, code)
        proc.pc = 0x0123
        return_address = proc.pc + len(code)
        proc.sp = 0xFE1F
        proc.step()
        self.assertEqual(proc.sp, 0xFE1d)
        self.assertEqual(proc.memory[0xFE1d], (return_address & 0xFF))
        self.assertEqual(proc.memory[0xFE1e], (return_address >> 8))
        self.assertEqual(proc.pc, 0x0c42)

    # callf !0d42h                ;5c 42
    def test_5c_callf_addr11(self):
        proc = Processor()
        code = [0x5c, 0x42]
        proc.write_memory(0x0123, code)
        proc.pc = 0x0123
        return_address = proc.pc + len(code)
        proc.sp = 0xFE1F
        proc.step()
        self.assertEqual(proc.sp, 0xFE1d)
        self.assertEqual(proc.memory[0xFE1d], (return_address & 0xFF))
        self.assertEqual(proc.memory[0xFE1e], (return_address >> 8))
        self.assertEqual(proc.pc, 0x0d42)

    # callf !0e42h                ;6c 42
    def test_6c_callf_addr11(self):
        proc = Processor()
        code = [0x6c, 0x42]
        proc.write_memory(0x0123, code)
        proc.pc = 0x0123
        return_address = proc.pc + len(code)
        proc.sp = 0xFE1F
        proc.step()
        self.assertEqual(proc.sp, 0xFE1d)
        self.assertEqual(proc.memory[0xFE1d], (return_address & 0xFF))
        self.assertEqual(proc.memory[0xFE1e], (return_address >> 8))
        self.assertEqual(proc.pc, 0x0e42)

    # callf !0f42h                ;7c 42
    def test_7c_callf_addr11(self):
        proc = Processor()
        code = [0x7c, 0x42]
        proc.write_memory(0x0123, code)
        proc.pc = 0x0123
        return_address = proc.pc + len(code)
        proc.sp = 0xFE1F
        proc.step()
        self.assertEqual(proc.sp, 0xFE1d)
        self.assertEqual(proc.memory[0xFE1d], (return_address & 0xFF))
        self.assertEqual(proc.memory[0xFE1e], (return_address >> 8))
        self.assertEqual(proc.pc, 0x0f42)

    def test_c1_to_ff_callt(self):
        vectors_by_opcode = {0xC1: 0x0040, 0xC3: 0x0042, 0xC5: 0x0044, 0xC7: 0x0046,
                             0xC9: 0x0048, 0xCB: 0x004a, 0xCD: 0x004c, 0xCF: 0x004e,
                             0xD1: 0x0050, 0xD3: 0x0052, 0xD5: 0x0054, 0xD7: 0x0056,
                             0xD9: 0x0058, 0xDB: 0x005A, 0xDD: 0x005C, 0xDF: 0x005e,
                             0xE1: 0x0060, 0xE3: 0x0062, 0xE5: 0x0064, 0xE7: 0x0066,
                             0xE9: 0x0068, 0xEB: 0x006a, 0xED: 0x006c, 0xEF: 0x006e,
                             0xF1: 0x0070, 0xF3: 0x0072, 0xF5: 0x0074, 0xF7: 0x0076,
                             0xF9: 0x0078, 0xFB: 0x007a, 0xFD: 0x007c, 0xFF: 0x007e,
                            }
        for opcode, vector in vectors_by_opcode.items():
            proc = Processor()
            subroutine_address = 0xabcd
            proc.memory[vector] = subroutine_address & 0xFF
            proc.memory[vector+1] = subroutine_address >> 8

            code = [opcode]
            proc.write_memory(0x1000, code)
            proc.pc = 0x1000
            return_address = proc.pc + len(code)

            proc.sp = 0xFE1F
            proc.step()
            self.assertEqual(proc.sp, 0xFE1d)
            self.assertEqual(proc.memory[0xFE1d], (return_address & 0xFF))
            self.assertEqual(proc.memory[0xFE1e], (return_address >> 8))
            self.assertEqual(proc.pc, 0xabcd)

    # rolc a,1                    ;27
    def test_27_rolc_a(self):
        tests = ((0,         0b00000000, 0,        0b00000000),
                 (Flags.CY,  0b00000000, 0,        0b00000001),
                 (0,         0b10000000, Flags.CY, 0b00000000),
                 (Flags.CY,  0b11111111, Flags.CY, 0b11111111),
                 (Flags.CY,  0b11000001, Flags.CY, 0b10000011))
        for original_psw, original_a, rotated_psw, rotated_a in tests:
            proc = Processor()
            code = [0x27]
            proc.write_memory(0, code)
            proc.write_psw(original_psw)
            proc.write_gp_reg(Registers.A, original_a)
            proc.step()
            self.assertEqual(proc.pc, len(code))
            self.assertEqual(proc.read_gp_reg(Registers.A), rotated_a)
            self.assertEqual(proc.read_psw(), rotated_psw)

    # rorc a,1                    ;25
    def test_25_rorc_a(self):
        tests = ((0,         0b00000000, 0,        0b00000000),
                 (Flags.CY,  0b00000000, 0,        0b10000000),
                 (0,         0b00000001, Flags.CY, 0b00000000),
                 (Flags.CY,  0b11111111, Flags.CY, 0b11111111),
                 (Flags.CY,  0b11000001, Flags.CY, 0b11100000))
        for original_psw, original_a, rotated_psw, rotated_a in tests:
            proc = Processor()
            code = [0x25]
            proc.write_memory(0, code)
            proc.write_psw(original_psw)
            proc.write_gp_reg(Registers.A, original_a)
            proc.step()
            self.assertEqual(proc.pc, len(code))
            self.assertEqual(proc.read_gp_reg(Registers.A), rotated_a)
            self.assertEqual(proc.read_psw(), rotated_psw)

    # rol a,1                    ;26
    def test_26_rol_a(self):
        tests = ((0,         0b00000000, 0,        0b00000000),
                 (Flags.CY,  0b01000010, 0,        0b10000100),
                 (0,         0b10010000, Flags.CY, 0b00100001),
                 (0,         0b11111111, Flags.CY, 0b11111111),
                 (Flags.CY,  0b10000000, Flags.CY, 0b00000001),)
        for original_psw, original_a, rotated_psw, rotated_a in tests:
            proc = Processor()
            code = [0x26]
            proc.write_memory(0, code)
            proc.write_psw(original_psw)
            proc.write_gp_reg(Registers.A, original_a)
            proc.step()
            self.assertEqual(proc.pc, len(code))
            self.assertEqual(proc.read_gp_reg(Registers.A), rotated_a)
            self.assertEqual(proc.read_psw(), rotated_psw)

    # ror a,1                     ;24
    def test_24_ror_a(self):
        tests = ((0,         0b00000000, 0,        0b00000000),
                 (Flags.CY,  0b00000000, 0,        0b00000000),
                 (0,         0b11111111, Flags.CY, 0b11111111),
                 (0,         0b00000101, Flags.CY, 0b10000010),
                 (Flags.CY,  0b00000001, Flags.CY, 0b10000000),)
        for original_psw, original_a, rotated_psw, rotated_a in tests:
            proc = Processor()
            code = [0x24]
            proc.write_memory(0, code)
            proc.write_psw(original_psw)
            proc.write_gp_reg(Registers.A, original_a)
            proc.step()
            self.assertEqual(proc.pc, len(code))
            self.assertEqual(proc.read_gp_reg(Registers.A), rotated_a)
            self.assertEqual(proc.read_psw(), rotated_psw)

    # dec x                       ;50
    def test_50_dec_x_0_to_ff_wraps_clears_z_ac(self):
        proc = Processor()
        code = [0x50]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.X, 0)
        proc.write_psw(Flags.Z | Flags.AC)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0)
        self.assertEqual(proc.read_gp_reg(Registers.X), 0xFF)

    # dec x                       ;50
    def test_50_dec_x_1_to_0_sets_z_clears_ac(self):
        proc = Processor()
        code = [0x50]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.X, 1)
        proc.write_psw(Flags.AC)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), Flags.Z)
        self.assertEqual(proc.read_gp_reg(Registers.X), 0)

    # dec x                       ;50
    def test_dec_x_10_to_0f_clears_z_sets_ac(self):
        proc = Processor()
        code = [0x50]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.X, 0x10)
        proc.write_psw(Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), Flags.AC)
        self.assertEqual(proc.read_gp_reg(Registers.X), 0x0f)

    # dec x                       ;50
    def test_dec_x_ff_to_fe_clears_z_clears_ac(self):
        proc = Processor()
        code = [0x50]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.X, 0xff)
        proc.write_psw(Flags.Z | Flags.AC)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0)
        self.assertEqual(proc.read_gp_reg(Registers.X), 0xfe)

    # dec a                       ;51
    def test_51_dec_a(self):
        proc = Processor()
        code = [0x51]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 1)
        proc.write_psw(Flags.AC)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), Flags.Z)
        self.assertEqual(proc.read_gp_reg(Registers.A), 0)

    # dec c                       ;52
    def test_52_dec_c(self):
        proc = Processor()
        code = [0x52]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.C, 1)
        proc.write_psw(Flags.AC)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), Flags.Z)
        self.assertEqual(proc.read_gp_reg(Registers.C), 0)

    # dec b                       ;53
    def test_53_dec_b(self):
        proc = Processor()
        code = [0x53]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.B, 1)
        proc.write_psw(Flags.AC)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), Flags.Z)
        self.assertEqual(proc.read_gp_reg(Registers.B), 0)

    # dec e                       ;54
    def test_54_dec_e(self):
        proc = Processor()
        code = [0x54]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.E, 1)
        proc.write_psw(Flags.AC)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), Flags.Z)
        self.assertEqual(proc.read_gp_reg(Registers.E), 0)

    # dec d                       ;55
    def test_55_dec_d(self):
        proc = Processor()
        code = [0x55]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.D, 1)
        proc.write_psw(Flags.AC)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), Flags.Z)
        self.assertEqual(proc.read_gp_reg(Registers.D), 0)

    # dec l                       ;56
    def test_56_dec_d(self):
        proc = Processor()
        code = [0x56]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.L, 1)
        proc.write_psw(Flags.AC)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), Flags.Z)
        self.assertEqual(proc.read_gp_reg(Registers.L), 0)

    # dec h                       ;57
    def test_57_dec_h(self):
        proc = Processor()
        code = [0x57]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.H, 1)
        proc.write_psw(Flags.AC)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), Flags.Z)
        self.assertEqual(proc.read_gp_reg(Registers.H), 0)

    # dec 0fe20h                  ;91 20          saddr
    def test_91_dec_saddr(self):
        proc = Processor()
        code = [0x91, 0x20]
        proc.write_memory(0, code)
        proc.memory[0xfe20] = 1
        proc.write_psw(Flags.AC)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), Flags.Z)
        self.assertEqual(proc.memory[0xfe20], 0)

    # dbnz c,$label1              ;8a fe
    def test_8a_dbnz_c_0_to_ff_branches(self):
        proc = Processor()
        code = [0x8a, 0xf0]
        proc.write_memory(0x1000, code)
        proc.pc = 0x1000
        proc.write_gp_reg(Registers.C, 0)
        proc.write_psw(Flags.AC | Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, 0x0ff2) # branch taken
        self.assertEqual(proc.read_psw(), Flags.AC | Flags.Z) # unchanged
        self.assertEqual(proc.read_gp_reg(Registers.C), 0xFF) # decremented

    # dbnz c,$label1              ;8a fe
    def test_8a_dbnz_c_3_to_2_branches(self):
        proc = Processor()
        code = [0x8a, 0xf0]
        proc.write_memory(0x1000, code)
        proc.pc = 0x1000
        proc.write_gp_reg(Registers.C, 3)
        proc.write_psw(Flags.AC | Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, 0x0ff2) # branch taken
        self.assertEqual(proc.read_psw(), Flags.AC | Flags.Z) # unchanged
        self.assertEqual(proc.read_gp_reg(Registers.C), 2) # decremented

    # dbnz c,$label1              ;8a fe
    def test_8a_dbnz_c_1_to_0_doesnt_branch(self):
        proc = Processor()
        code = [0x8a, 0xf0]
        proc.write_memory(0x1000, code)
        proc.pc = 0x1000
        proc.write_gp_reg(Registers.C, 1)
        proc.write_psw(Flags.AC)
        proc.step()
        self.assertEqual(proc.pc, 0x1000+len(code)) # branch not taken
        self.assertEqual(proc.read_psw(), Flags.AC) # unchanged
        self.assertEqual(proc.read_gp_reg(Registers.C), 0) # decremented

    # dbnz b,$label2              ;8b fe
    def test_8b_dbnz_b_0_to_ff_branches(self):
        proc = Processor()
        code = [0x8b, 0xf0]
        proc.write_memory(0x1000, code)
        proc.pc = 0x1000
        proc.write_gp_reg(Registers.B, 0)
        proc.write_psw(Flags.AC | Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, 0x0ff2) # branch taken
        self.assertEqual(proc.read_psw(), Flags.AC | Flags.Z) # unchanged
        self.assertEqual(proc.read_gp_reg(Registers.B), 0xFF) # decremented

    # dbnz b,$label1              ;8b fe
    def test_8b_dbnz_b_3_to_2_branches(self):
        proc = Processor()
        code = [0x8b, 0xf0]
        proc.write_memory(0x1000, code)
        proc.pc = 0x1000
        proc.write_gp_reg(Registers.B, 3)
        proc.write_psw(Flags.AC | Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, 0x0ff2) # branch taken
        self.assertEqual(proc.read_psw(), Flags.AC | Flags.Z) # unchanged
        self.assertEqual(proc.read_gp_reg(Registers.B), 2) # decremented

    # dbnz b,$label1              ;8b fe
    def test_8b_dbnz_b_1_to_0_doesnt_branch(self):
        proc = Processor()
        code = [0x8b, 0xf0]
        proc.write_memory(0x1000, code)
        proc.pc = 0x1000
        proc.write_gp_reg(Registers.B, 1)
        proc.write_psw(Flags.AC)
        proc.step()
        self.assertEqual(proc.pc, 0x1000+len(code)) # branch not taken
        self.assertEqual(proc.read_psw(), Flags.AC) # unchanged
        self.assertEqual(proc.read_gp_reg(Registers.B), 0) # decremented

    # dbnz 0fe20h,$label0         ;04 20 fd       saddr
    def test_04_dbnz_saddr_0_to_ff_branches(self):
        proc = Processor()
        code = [0x04, 0x20, 0xf0]
        proc.write_memory(0x1000, code)
        proc.pc = 0x1000
        proc.memory[0xfe20] = 0
        proc.write_psw(Flags.AC | Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, 0x0ff3) # branch taken
        self.assertEqual(proc.read_psw(), Flags.AC | Flags.Z) # unchanged
        self.assertEqual(proc.memory[0xfe20], 0xFF) # decremented

    # dbnz 0fe20h,$label0         ;04 20 fd       saddr
    def test_04_dbnz_saddr_3_to_2_branches(self):
        proc = Processor()
        code = [0x04, 0x20, 0xf0]
        proc.write_memory(0x1000, code)
        proc.pc = 0x1000
        proc.memory[0xfe20] = 3
        proc.write_psw(Flags.AC | Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, 0x0ff3) # branch taken
        self.assertEqual(proc.read_psw(), Flags.AC | Flags.Z) # unchanged
        self.assertEqual(proc.memory[0xfe20], 2) # decremented

    # dbnz 0fe20h,$label0         ;04 20 fd       saddr
    def test_04_dbnz_saddr_1_to_0_doesnt_branch(self):
        proc = Processor()
        code = [0x04, 0x20, 0xf0]
        proc.write_memory(0x1000, code)
        proc.pc = 0x1000
        proc.memory[0xfe20] = 1
        proc.write_psw(Flags.AC | Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, 0x1000+len(code)) # branch not taken
        self.assertEqual(proc.read_psw(), Flags.AC | Flags.Z) # unchanged
        self.assertEqual(proc.memory[0xfe20], 0) # decremented

    # bt [hl].0,$label40          ;31 86 fd
    def test_31_86_bt_hl_bit0_doesnt_branch_if_clear(self):
        proc = Processor()
        code = [0x31, 0x86, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0b11111110
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bt [hl].0,$label40          ;31 86 fd
    def test_31_86_bt_hl_bit0_branches_if_set(self):
        proc = Processor()
        code = [0x31, 0x86, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0b00000001
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x23) # branch taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bt [hl].1,$label41          ;31 96 fd
    def test_31_96_bt_hl_bit1_doesnt_branch_if_clear(self):
        proc = Processor()
        code = [0x31, 0x96, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0b11111101
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bt [hl].1,$label41          ;31 96 fd
    def test_31_96_bt_hl_bit1_branches_if_set(self):
        proc = Processor()
        code = [0x31, 0x96, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0b00000010
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x23) # branch taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bt [hl].2,$label42          ;31 a6 fd
    def test_31_a6_bt_hl_bit2_doesnt_branch_if_clear(self):
        proc = Processor()
        code = [0x31, 0xa6, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0b11111011
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bt [hl].2,$label42          ;31 a6 fd
    def test_31_a6_bt_hl_bit2_branches_if_set(self):
        proc = Processor()
        code = [0x31, 0xa6, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0b00000100
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x23) # branch taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bt [hl].3,$label43          ;31 b6 fd
    def test_31_b6_bt_hl_bit3_doesnt_branch_if_clear(self):
        proc = Processor()
        code = [0x31, 0xb6, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0b11110111
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bt [hl].3,$label43          ;31 b6 fd
    def test_31_b6_bt_hl_bit3_branches_if_set(self):
        proc = Processor()
        code = [0x31, 0xb6, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0b00001000
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x23) # branch taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bt [hl].4,$label44          ;31 c6 fd
    def test_31_c6_bt_hl_bit4_doesnt_branch_if_clear(self):
        proc = Processor()
        code = [0x31, 0xc6, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0b11101111
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bt [hl].4,$label44          ;31 c6 fd
    def test_31_c6_bt_hl_bit4_branches_if_set(self):
        proc = Processor()
        code = [0x31, 0xc6, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0b00010000
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x23) # branch taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bt [hl].5,$label45          ;31 d6 fd
    def test_31_d6_bt_hl_bit5_doesnt_branch_if_clear(self):
        proc = Processor()
        code = [0x31, 0xd6, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0b11011111
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bt [hl].5,$label45          ;31 d6 fd
    def test_31_d6_bt_hl_bit5_branches_if_set(self):
        proc = Processor()
        code = [0x31, 0xd6, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0b00100000
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x23) # branch taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bt [hl].6,$label46          ;31 e6 fd
    def test_31_e6_bt_hl_bit6_doesnt_branch_if_clear(self):
        proc = Processor()
        code = [0x31, 0xe6, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0b10111111
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bt [hl].6,$label46          ;31 e6 fd
    def test_31_e6_bt_hl_bit6_branches_if_set(self):
        proc = Processor()
        code = [0x31, 0xe6, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0b01000000
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x23) # branch taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bt [hl].7,$label47          ;31 f6 fd
    def test_31_f6_bt_hl_bit7_doesnt_branch_if_clear(self):
        proc = Processor()
        code = [0x31, 0xf6, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0b01111111
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bt [hl].7,$label47          ;31 f6 fd
    def test_31_f6_bt_hl_bit7_branches_if_set(self):
        proc = Processor()
        code = [0x31, 0xf6, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0b10000000
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x23) # branch taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr a.0,$label104         ;31 0d fd
    def test_31_0d_btclr_a_bit0_branches_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0x0d, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0b00000001)
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x23) # branch taken
        self.assertEqual(proc.read_gp_reg(Registers.A), 0b00000000) # bit cleared
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr a.0,$label104         ;31 0d fd
    def test_31_0d_btclr_a_bit0_clears_bit_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0x0d, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0b11111111)
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x23) # branch taken
        self.assertEqual(proc.read_gp_reg(Registers.A), 0b11111110) # bit cleared
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr a.0,$label104         ;31 0d fd
    def test_31_0d_btclr_a_bit0_doesnt_branch_if_clear(self):
        proc = Processor()
        code = [0x31, 0x0d, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0)
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr a.1,$label105         ;31 1d fd
    def test_31_1d_btclr_a_bit1_branches_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0x1d, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0b00000010)
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x23) # branch taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr a.1,$label105         ;31 1d fd
    def test_31_1d_btclr_a_bit1_clears_bit_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0x1d, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0b11111111)
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x23) # branch taken
        self.assertEqual(proc.read_gp_reg(Registers.A), 0b11111101) # bit cleared
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr a.1,$label105         ;31 1d fd
    def test_31_1d_btclr_a_bit0_doesnt_branch_if_clear(self):
        proc = Processor()
        code = [0x31, 0x1d, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0)
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr a.2,$label106         ;31 2d fd
    def test_31_2d_btclr_a_bit2_branches_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0x2d, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0b00000100)
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x23) # branch taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr a.2,$label106         ;31 2d fd
    def test_31_2d_btclr_a_bit2_clears_bit_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0x2d, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0b11111111)
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x23) # branch taken
        self.assertEqual(proc.read_gp_reg(Registers.A), 0b11111011) # bit cleared
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr a.2,$label106         ;31 2d fd
    def test_31_2d_btclr_a_bit2_doesnt_branch_if_clear(self):
        proc = Processor()
        code = [0x31, 0x2d, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0)
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr a.3,$label107         ;31 3d fd
    def test_31_3d_btclr_a_bit3_branches_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0x3d, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0b00001000)
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x23) # branch taken
        self.assertEqual(proc.read_gp_reg(Registers.A), 0b00000000) # bit cleared
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr a.3,$label107         ;31 3d fd
    def test_31_3d_btclr_a_bit3_clears_bit_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0x3d, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0b11111111)
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x23) # branch taken
        self.assertEqual(proc.read_gp_reg(Registers.A), 0b11110111) # bit cleared
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr a.3,$label107         ;31 3d fd
    def test_31_3d_btclr_a_bit3_doesnt_branch_if_clear(self):
        proc = Processor()
        code = [0x31, 0x3d, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0)
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr a.4,$label108         ;31 4d fd
    def test_31_4d_btclr_a_bit4_branches_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0x4d, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0b00010000)
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x23) # branch taken
        self.assertEqual(proc.read_gp_reg(Registers.A), 0b00000000) # bit cleared
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr a.4,$label108         ;31 4d fd
    def test_31_4d_btclr_a_bit4_clears_bit_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0x4d, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0b11111111)
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x23) # branch taken
        self.assertEqual(proc.read_gp_reg(Registers.A), 0b11101111) # bit cleared
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr a.4,$label108         ;31 4d fd
    def test_31_4d_btclr_a_bit3_doesnt_branch_if_clear(self):
        proc = Processor()
        code = [0x31, 0x4d, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0)
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr a.5,$label109         ;31 5d fd
    def test_31_5d_btclr_a_bit5_branches_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0x5d, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0b00100000)
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x23) # branch taken
        self.assertEqual(proc.read_gp_reg(Registers.A), 0b00000000) # bit cleared
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr a.5,$label109         ;31 5d fd
    def test_31_5d_btclr_a_bit5_clears_bit_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0x5d, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0b11111111)
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x23) # branch taken
        self.assertEqual(proc.read_gp_reg(Registers.A), 0b11011111) # bit cleared
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr a.5,$label109         ;31 5d fd
    def test_31_5d_btclr_a_bit5_doesnt_branch_if_clear(self):
        proc = Processor()
        code = [0x31, 0x5d, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0)
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr a.6,$label110         ;31 6d fd
    def test_31_6d_btclr_a_bit6_branches_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0x6d, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0b01000000)
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x23) # branch taken
        self.assertEqual(proc.read_gp_reg(Registers.A), 0b00000000) # bit cleared
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr a.6,$label110         ;31 6d fd
    def test_31_6d_btclr_a_bit6_clears_bit_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0x6d, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0b11111111)
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x23) # branch taken
        self.assertEqual(proc.read_gp_reg(Registers.A), 0b10111111) # bit cleared
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr a.6,$label110         ;31 6d fd
    def test_31_6d_btclr_a_bit6_doesnt_branch_if_clear(self):
        proc = Processor()
        code = [0x31, 0x6d, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0)
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr a.7,$label111         ;31 7d fd
    def test_31_7d_btclr_a_bit7_branches_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0x7d, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0b10000000)
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x23) # branch taken
        self.assertEqual(proc.read_gp_reg(Registers.A), 0b00000000) # bit cleared
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr a.7,$label111         ;31 7d fd
    def test_31_7d_btclr_a_bit7_clears_bit_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0x7d, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0b11111111)
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x23) # branch taken
        self.assertEqual(proc.read_gp_reg(Registers.A), 0b01111111) # bit cleared
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr a.7,$label111         ;31 7d fd
    def test_31_7d_btclr_a_bit7_doesnt_branch_if_clear(self):
        proc = Processor()
        code = [0x31, 0x7d, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0)
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bf a.0,$label32             ;31 0f fd
    def test_31_0f_bf_a_bit0_branches_if_clear(self):
        proc = Processor()
        code = [0x31, 0x0f, 0x20]
        proc.write_memory(0, code)
        proc.write_psw(0x55)
        proc.write_gp_reg(Registers.A, 0b11111110)
        proc.step()
        self.assertEqual(proc.pc, 0x23) # branch taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bf a.0,$label32             ;31 0f fd
    def test_31_0f_bf_a_bit0_doesnt_branch_if_set(self):
        proc = Processor()
        code = [0x31, 0x0f, 0x20]
        proc.write_memory(0, code)
        proc.write_psw(0x55)
        proc.write_gp_reg(Registers.A, 0b00000001)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bf a.1,$label32             ;31 1f fd
    def test_31_1f_bf_a_bit1_branches_if_clear(self):
        proc = Processor()
        code = [0x31, 0x1f, 0x20]
        proc.write_memory(0, code)
        proc.write_psw(0x55)
        proc.write_gp_reg(Registers.A, 0b11111101)
        proc.step()
        self.assertEqual(proc.pc, 0x23) # branch taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bf a.1,$label32             ;31 1f fd
    def test_31_1f_bf_a_bit1_doesnt_branch_if_set(self):
        proc = Processor()
        code = [0x31, 0x1f, 0x20]
        proc.write_memory(0, code)
        proc.write_psw(0x55)
        proc.write_gp_reg(Registers.A, 0b00000010)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bf a.2,$label32             ;31 2f fd
    def test_31_2f_bf_a_bit2_branches_if_clear(self):
        proc = Processor()
        code = [0x31, 0x2f, 0x20]
        proc.write_memory(0, code)
        proc.write_psw(0x55)
        proc.write_gp_reg(Registers.A, 0b11111011)
        proc.step()
        self.assertEqual(proc.pc, 0x23) # branch taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bf a.2,$label32             ;31 2f fd
    def test_31_2f_bf_a_bit2_doesnt_branch_if_set(self):
        proc = Processor()
        code = [0x31, 0x2f, 0x20]
        proc.write_memory(0, code)
        proc.write_psw(0x55)
        proc.write_gp_reg(Registers.A, 0b00000100)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bf a.3,$label32             ;31 3f fd
    def test_31_3f_bf_a_bit3_branches_if_clear(self):
        proc = Processor()
        code = [0x31, 0x3f, 0x20]
        proc.write_memory(0, code)
        proc.write_psw(0x55)
        proc.write_gp_reg(Registers.A, 0b11110111)
        proc.step()
        self.assertEqual(proc.pc, 0x23) # branch taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bf a.3,$label32             ;31 3f fd
    def test_31_3f_bf_a_bit3_doesnt_branch_if_set(self):
        proc = Processor()
        code = [0x31, 0x3f, 0x20]
        proc.write_memory(0, code)
        proc.write_psw(0x55)
        proc.write_gp_reg(Registers.A, 0b00001000)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bf a.4,$label32             ;31 4f fd
    def test_31_4f_bf_a_bit4_branches_if_clear(self):
        proc = Processor()
        code = [0x31, 0x4f, 0x20]
        proc.write_memory(0, code)
        proc.write_psw(0x55)
        proc.write_gp_reg(Registers.A, 0b11101111)
        proc.step()
        self.assertEqual(proc.pc, 0x23) # branch taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bf a.4,$label32             ;31 4f fd
    def test_31_4f_bf_a_bit4_doesnt_branch_if_set(self):
        proc = Processor()
        code = [0x31, 0x4f, 0x20]
        proc.write_memory(0, code)
        proc.write_psw(0x55)
        proc.write_gp_reg(Registers.A, 0b00010000)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bf a.5,$label32             ;31 5f fd
    def test_31_5f_bf_a_bit5_branches_if_clear(self):
        proc = Processor()
        code = [0x31, 0x5f, 0x20]
        proc.write_memory(0, code)
        proc.write_psw(0x55)
        proc.write_gp_reg(Registers.A, 0b11011111)
        proc.step()
        self.assertEqual(proc.pc, 0x23) # branch taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bf a.5,$label32             ;31 5f fd
    def test_31_5f_bf_a_bit5_doesnt_branch_if_set(self):
        proc = Processor()
        code = [0x31, 0x5f, 0x20]
        proc.write_memory(0, code)
        proc.write_psw(0x55)
        proc.write_gp_reg(Registers.A, 0b00100000)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bf a.6,$label32             ;31 6f fd
    def test_31_6f_bf_a_bit6_branches_if_clear(self):
        proc = Processor()
        code = [0x31, 0x6f, 0x20]
        proc.write_memory(0, code)
        proc.write_psw(0x55)
        proc.write_gp_reg(Registers.A, 0b10111111)
        proc.step()
        self.assertEqual(proc.pc, 0x23) # branch taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bf a.6,$label32             ;31 6f fd
    def test_31_6f_bf_a_bit6_doesnt_branch_if_set(self):
        proc = Processor()
        code = [0x31, 0x6f, 0x20]
        proc.write_memory(0, code)
        proc.write_psw(0x55)
        proc.write_gp_reg(Registers.A, 0b01000000)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bf a.7,$label32             ;31 7f fd
    def test_31_7f_bf_a_bit7_branches_if_clear(self):
        proc = Processor()
        code = [0x31, 0x7f, 0x20]
        proc.write_memory(0, code)
        proc.write_psw(0x55)
        proc.write_gp_reg(Registers.A, 0b01111111)
        proc.step()
        self.assertEqual(proc.pc, 0x23) # branch taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bf a.7,$label32             ;31 7f fd
    def test_31_7f_bf_a_bit7_doesnt_branch_if_set(self):
        proc = Processor()
        code = [0x31, 0x7f, 0x20]
        proc.write_memory(0, code)
        proc.write_psw(0x55)
        proc.write_gp_reg(Registers.A, 0b10000000)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bt a.0,$label32             ;31 0e fd
    def test_31_0e_bt_a_bit0_branches_if_set(self):
        proc = Processor()
        code = [0x31, 0x0e, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0b00000001)
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x23) # branch taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bt a.0,$label32             ;31 0e fd
    def test_31_0e_bt_a_bit0_doesnt_branch_if_clear(self):
        proc = Processor()
        code = [0x31, 0x0e, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0)
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bt a.1,$label33             ;31 1e fd
    def test_31_1e_bt_a_bit1_branches_if_set(self):
        proc = Processor()
        code = [0x31, 0x1e, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0b00000010)
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x23) # branch taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bt a.1,$label33             ;31 1e fd
    def test_31_1e_bt_a_bit1_doesnt_branch_if_clear(self):
        proc = Processor()
        code = [0x31, 0x1e, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0)
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bt a.2,$label34             ;31 2e fd
    def test_31_2e_bt_a_bit2_branches_if_set(self):
        proc = Processor()
        code = [0x31, 0x2e, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0b00000100)
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x23) # branch taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bt a.2,$label34             ;31 2e fd
    def test_31_2e_bt_a_bit2_doesnt_branch_if_clear(self):
        proc = Processor()
        code = [0x31, 0x2e, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0)
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bt a.3,$label35             ;31 3e fd
    def test_31_3e_bt_a_bit3_branches_if_set(self):
        proc = Processor()
        code = [0x31, 0x3e, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0b00001000)
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x23) # branch taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bt a.3,$label35             ;31 3e fd
    def test_31_3e_bt_a_bit3_doesnt_branch_if_clear(self):
        proc = Processor()
        code = [0x31, 0x3e, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0)
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bt a.4,$label36             ;31 4e fd
    def test_31_4e_bt_a_bit4_branches_if_set(self):
        proc = Processor()
        code = [0x31, 0x4e, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0b00010000)
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x23) # branch taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bt a.4,$label36             ;31 4e fd
    def test_31_4e_bt_a_bit4_doesnt_branch_if_clear(self):
        proc = Processor()
        code = [0x31, 0x4e, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0)
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bt a.5,$label37             ;31 5e fd
    def test_31_5e_bt_a_bit5_branches_if_set(self):
        proc = Processor()
        code = [0x31, 0x5e, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0b00100000)
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x23) # branch taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bt a.5,$label37             ;31 5e fd
    def test_31_5e_bt_a_bit5_doesnt_branch_if_clear(self):
        proc = Processor()
        code = [0x31, 0x5e, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0)
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bt a.6,$label38             ;31 6e fd
    def test_31_6e_bt_a_bit6_branches_if_set(self):
        proc = Processor()
        code = [0x31, 0x6e, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0b01000000)
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x23) # branch taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bt a.6,$label38             ;31 6e fd
    def test_31_6e_bt_a_bit6_doesnt_branch_if_clear(self):
        proc = Processor()
        code = [0x31, 0x6e, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0)
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bt a.7,$label39             ;31 7e fd
    def test_31_7e_bt_a_bit7_branches_if_set(self):
        proc = Processor()
        code = [0x31, 0x7e, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0b10000000)
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x23) # branch taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bt a.7,$label39             ;31 7e fd
    def test_31_7e_bt_a_bit7_doesnt_branch_if_clear(self):
        proc = Processor()
        code = [0x31, 0x7e, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0)
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr [hl].0,$label120      ;31 85 fd
    def test_31_05_btclr_hl_bit0_branches_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0x85, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0b00000001
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x23) # branch taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr [hl].0,$label120      ;31 85 fd
    def test_31_85_btclr_hl_bit0_clears_bit_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0x85, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0b11111111
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x23) # branch taken
        self.assertEqual(proc.memory[0xabcd], 0b11111110) # bit cleared
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr [hl].0,$label120      ;31 85 fd
    def test_31_05_btclr_hl_bit0_doesnt_branch_if_clear(self):
        proc = Processor()
        code = [0x31, 0x85, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr [hl].1,$label120      ;31 95 fd
    def test_31_95_btclr_hl_bit1_branches_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0x95, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0b00000010
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x23) # branch taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr [hl].1,$label120      ;31 95 fd
    def test_31_95_btclr_hl_bit1_clears_bit_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0x95, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0b11111111
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x23) # branch taken
        self.assertEqual(proc.memory[0xabcd], 0b11111101) # bit cleared
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr [hl].1,$label120      ;31 95 fd
    def test_31_95_btclr_hl_bit1_doesnt_branch_if_clear(self):
        proc = Processor()
        code = [0x31, 0x95, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr [hl].2,$label120      ;31 a5 fd
    def test_31_a5_btclr_hl_bit2_branches_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0xa5, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0b00000100
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x23) # branch taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr [hl].2,$label120      ;31 a5 fd
    def test_31_a5_btclr_hl_bit1_clears_bit_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0xa5, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0b11111111
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x23) # branch taken
        self.assertEqual(proc.memory[0xabcd], 0b11111011) # bit cleared
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr [hl].2,$label120      ;31 a5 fd
    def test_31_a5_btclr_hl_bit2_doesnt_branch_if_clear(self):
        proc = Processor()
        code = [0x31, 0xa5, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr [hl].3,$label120      ;31 b5 fd
    def test_31_b5_btclr_hl_bit3_branches_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0xb5, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0b00001000
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x23) # branch taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr [hl].3,$label120      ;31 b5 fd
    def test_31_b5_btclr_hl_bit3_clears_bit_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0xb5, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0b11111111
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x23) # branch taken
        self.assertEqual(proc.memory[0xabcd], 0b11110111) # bit cleared
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr [hl].3,$label120      ;31 b5 fd
    def test_31_a5_btclr_hl_bit3_doesnt_branch_if_clear(self):
        proc = Processor()
        code = [0x31, 0xb5, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr [hl].4,$label120      ;31 c5 fd
    def test_31_c5_btclr_hl_bit4_branches_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0xc5, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0b00010000
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x23) # branch taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr [hl].4,$label120      ;31 c5 fd
    def test_31_c5_btclr_hl_bit4_clears_bit_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0xc5, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0b11111111
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x23) # branch taken
        self.assertEqual(proc.memory[0xabcd], 0b11101111) # bit cleared
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr [hl].4,$label120      ;31 c5 fd
    def test_31_c5_btclr_hl_bit4_doesnt_branch_if_clear(self):
        proc = Processor()
        code = [0x31, 0xc5, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr [hl].5,$label120      ;31 d5 fd
    def test_31_d5_btclr_hl_bit5_branches_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0xd5, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0b00100000
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x23) # branch taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr [hl].5,$label120      ;31 d5 fd
    def test_31_d5_btclr_hl_bit5_clears_bit_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0xd5, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0b11111111
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x23) # branch taken
        self.assertEqual(proc.memory[0xabcd], 0b11011111) # bit cleared
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr [hl].5,$label120      ;31 d5 fd
    def test_31_d5_btclr_hl_bit5_doesnt_branch_if_clear(self):
        proc = Processor()
        code = [0x31, 0xd5, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr [hl].6,$label120      ;31 e5 fd
    def test_31_e5_btclr_hl_bit6_branches_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0xe5, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0b01000000
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x23) # branch taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr [hl].6,$label120      ;31 e5 fd
    def test_31_e5_btclr_hl_bit6_clears_bit_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0xe5, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0b11111111
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x23) # branch taken
        self.assertEqual(proc.memory[0xabcd], 0b10111111) # bit cleared
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr [hl].6,$label120      ;31 e5 fd
    def test_31_e5_btclr_hl_bit6_doesnt_branch_if_clear(self):
        proc = Processor()
        code = [0x31, 0xe5, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr [hl].7,$label120      ;31 f5 fd
    def test_31_f5_btclr_hl_bit7_branches_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0xf5, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0b10000000
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x23) # branch taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr [hl].7,$label120      ;31 f5 fd
    def test_31_f5_btclr_hl_bit7_clears_bit_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0xf5, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0b11111111
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x23) # branch taken
        self.assertEqual(proc.memory[0xabcd], 0b01111111) # bit cleared
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr [hl].7,$label120      ;31 f5 fd
    def test_31_f5_btclr_hl_bit7_doesnt_branch_if_clear(self):
        proc = Processor()
        code = [0x31, 0xf5, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr 0fe20h.0,$label88     ;31 01 20 fc    saddr
    def test_31_01_btclr_saddr_bit0_branches_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0x01, 0x20, 0x30]
        proc.write_memory(0, code)
        proc.memory[0x0fe20] = 0b00000001
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x34) # branch taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr 0fe20h.0,$label88     ;31 01 20 fc    saddr
    def test_31_01_btclr_saddr_bit0_clears_bit_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0x01, 0x20, 0x30]
        proc.write_memory(0, code)
        proc.memory[0x0fe20] = 0b11111111
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x34) # branch taken
        self.assertEqual(proc.memory[0x0fe20], 0b11111110) # bit cleared
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr 0fe20h.0,$label88     ;31 01 20 fc    saddr
    def test_31_01_btclr_saddr_bit0_doesnt_branch_if_clear(self):
        proc = Processor()
        code = [0x31, 0x01, 0x20, 0x30]
        proc.write_memory(0, code)
        proc.memory[0x0fe20] = 0
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr 0fe20h.1,$label89     ;31 11 20 fc    saddr
    def test_31_11_btclr_saddr_bit1_branches_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0x11, 0x20, 0x30]
        proc.write_memory(0, code)
        proc.memory[0x0fe20] = 0b00000010
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x34) # branch taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr 0fe20h.1,$label88     ;31 11 20 fc    saddr
    def test_31_11_btclr_saddr_bit1_clears_bit_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0x11, 0x20, 0x30]
        proc.write_memory(0, code)
        proc.memory[0x0fe20] = 0b11111111
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x34) # branch taken
        self.assertEqual(proc.memory[0x0fe20], 0b11111101) # bit cleared
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr 0fe20h.1,$label88     ;31 11 20 fc    saddr
    def test_31_11_btclr_saddr_bit1_doesnt_branch_if_clear(self):
        proc = Processor()
        code = [0x31, 0x11, 0x20, 0x30]
        proc.write_memory(0, code)
        proc.memory[0x0fe20] = 0
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr 0fe20h.2,$label90     ;31 21 20 fc    saddr
    def test_31_21_btclr_saddr_bit2_branches_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0x21, 0x20, 0x30]
        proc.write_memory(0, code)
        proc.memory[0x0fe20] = 0b00000100
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x34) # branch taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr 0fe20h.2,$label90     ;31 21 20 fc    saddr
    def test_31_21_btclr_saddr_bit2_clears_bit_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0x21, 0x20, 0x30]
        proc.write_memory(0, code)
        proc.memory[0x0fe20] = 0b11111111
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x34) # branch taken
        self.assertEqual(proc.memory[0x0fe20], 0b11111011) # bit cleared
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr 0fe20h.2,$label90     ;31 21 20 fc    saddr
    def test_31_21_btclr_saddr_bit2_doesnt_branch_if_clear(self):
        proc = Processor()
        code = [0x31, 0x21, 0x20, 0x30]
        proc.write_memory(0, code)
        proc.memory[0x0fe20] = 0
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr 0fe20h.3,$label91     ;31 31 20 fc    saddr
    def test_31_31_btclr_saddr_bit3_branches_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0x31, 0x20, 0x30]
        proc.write_memory(0, code)
        proc.memory[0x0fe20] = 0b00001000
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x34) # branch taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr 0fe20h.3,$label91     ;31 31 20 fc    saddr
    def test_31_31_btclr_saddr_bit3_clears_bit_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0x31, 0x20, 0x30]
        proc.write_memory(0, code)
        proc.memory[0x0fe20] = 0b11111111
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x34) # branch taken
        self.assertEqual(proc.memory[0x0fe20], 0b11110111) # bit cleared
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr 0fe20h.3,$label91     ;31 31 20 fc    saddr
    def test_31_31_btclr_saddr_bit3_doesnt_branch_if_clear(self):
        proc = Processor()
        code = [0x31, 0x31, 0x20, 0x30]
        proc.write_memory(0, code)
        proc.memory[0x0fe20] = 0
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr 0fe20h.4,$label91     ;41 31 20 fc    saddr
    def test_31_41_btclr_saddr_bit4_branches_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0x41, 0x20, 0x30]
        proc.write_memory(0, code)
        proc.memory[0x0fe20] = 0b00010000
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x34) # branch taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr 0fe20h.4,$label91     ;31 41 20 fc    saddr
    def test_31_41_btclr_saddr_bit4_clears_bit_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0x41, 0x20, 0x30]
        proc.write_memory(0, code)
        proc.memory[0x0fe20] = 0b11111111
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x34) # branch taken
        self.assertEqual(proc.memory[0x0fe20], 0b11101111) # bit cleared
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr 0fe20h.4,$label91     ;31 41 20 fc    saddr
    def test_31_41_btclr_saddr_bit3_doesnt_branch_if_clear(self):
        proc = Processor()
        code = [0x31, 0x41, 0x20, 0x30]
        proc.write_memory(0, code)
        proc.memory[0x0fe20] = 0
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr 0fe20h.5,$label91     ;41 51 20 fc    saddr
    def test_31_51_btclr_saddr_bit5_branches_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0x51, 0x20, 0x30]
        proc.write_memory(0, code)
        proc.memory[0x0fe20] = 0b00100000
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x34) # branch taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr 0fe20h.5,$label91     ;31 51 20 fc    saddr
    def test_31_51_btclr_saddr_bit5_clears_bit_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0x51, 0x20, 0x30]
        proc.write_memory(0, code)
        proc.memory[0x0fe20] = 0b11111111
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x34) # branch taken
        self.assertEqual(proc.memory[0x0fe20], 0b11011111) # bit cleared
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr 0fe20h.5,$label91     ;31 41 20 fc    saddr
    def test_31_51_btclr_saddr_bit5_doesnt_branch_if_clear(self):
        proc = Processor()
        code = [0x31, 0x51, 0x20, 0x30]
        proc.write_memory(0, code)
        proc.memory[0x0fe20] = 0
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr 0fe20h.6,$label91     ;41 61 20 fc    saddr
    def test_31_61_btclr_saddr_bit6_branches_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0x61, 0x20, 0x30]
        proc.write_memory(0, code)
        proc.memory[0x0fe20] = 0b01000000
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x34) # branch taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr 0fe20h.6,$label91     ;31 61 20 fc    saddr
    def test_31_61_btclr_saddr_bit6_clears_bit_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0x61, 0x20, 0x30]
        proc.write_memory(0, code)
        proc.memory[0x0fe20] = 0b11111111
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x34) # branch taken
        self.assertEqual(proc.memory[0x0fe20], 0b10111111) # bit cleared
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr 0fe20h.6,$label91     ;31 61 20 fc    saddr
    def test_31_61_btclr_saddr_bit6_doesnt_branch_if_clear(self):
        proc = Processor()
        code = [0x31, 0x61, 0x20, 0x30]
        proc.write_memory(0, code)
        proc.memory[0x0fe20] = 0
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr 0fe20h.7,$label91     ;41 71 20 fc    saddr
    def test_31_71_btclr_saddr_bit7_branches_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0x71, 0x20, 0x30]
        proc.write_memory(0, code)
        proc.memory[0x0fe20] = 0b10000000
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x34) # branch taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr psw.0,$label112       ;31 01 1e fc
    def test_31_01_btclr_psw_bit0_branches_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0x01, 0x1e, 0x30]
        proc.write_memory(0, code)
        proc.write_psw(0b00000001)
        proc.step()
        self.assertEqual(proc.pc, 0x34) # branch taken

    # btclr psw.0,$label112       ;31 01 1e fc
    def test_31_01_btclr_psw_bit0_clears_bit_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0x01, 0x1e, 0x30]
        proc.write_memory(0, code)
        proc.write_psw(0b11111111)
        proc.step()
        self.assertEqual(proc.pc, 0x34) # branch taken
        self.assertEqual(proc.read_psw(), 0b11111110) # bit cleared

    # btclr psw.0,$label112       ;31 01 1e fc
    def test_31_01_btclr_psw_bit0_doesnt_branch_if_clear(self):
        proc = Processor()
        code = [0x31, 0x01, 0x1e, 0x30]
        proc.write_memory(0, code)
        proc.write_psw(0)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken

    # btclr psw.1,$label112       ;31 11 1e fc
    def test_31_11_btclr_psw_bit1_branches_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0x11, 0x1e, 0x30]
        proc.write_memory(0, code)
        proc.write_psw(0b00000010)
        proc.step()
        self.assertEqual(proc.pc, 0x34) # branch taken

    # btclr psw.1,$label112       ;31 11 1e fc
    def test_31_11_btclr_psw_bit1_clears_bit_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0x11, 0x1e, 0x30]
        proc.write_memory(0, code)
        proc.write_psw(0b11111111)
        proc.step()
        self.assertEqual(proc.pc, 0x34) # branch taken
        self.assertEqual(proc.read_psw(), 0b11111101) # bit cleared

    # btclr psw.1,$label112       ;31 11 1e fc
    def test_31_11_btclr_psw_bit1_doesnt_branch_if_clear(self):
        proc = Processor()
        code = [0x31, 0x11, 0x1e, 0x30]
        proc.write_memory(0, code)
        proc.write_psw(0)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken

    # btclr psw.2,$label112       ;31 21 1e fc
    def test_31_21_btclr_psw_bit2_branches_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0x21, 0x1e, 0x30]
        proc.write_memory(0, code)
        proc.write_psw(0b00000100)
        proc.step()
        self.assertEqual(proc.pc, 0x34) # branch taken

    # btclr psw.2,$label112       ;31 21 1e fc
    def test_31_21_btclr_psw_bit1_clears_bit_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0x21, 0x1e, 0x30]
        proc.write_memory(0, code)
        proc.write_psw(0b11111111)
        proc.step()
        self.assertEqual(proc.pc, 0x34) # branch taken
        self.assertEqual(proc.read_psw(), 0b11111011) # bit cleared

    # btclr psw.2,$label112       ;31 21 1e fc
    def test_31_21_btclr_psw_bit2_doesnt_branch_if_clear(self):
        proc = Processor()
        code = [0x31, 0x21, 0x1e, 0x30]
        proc.write_memory(0, code)
        proc.write_psw(0)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken

    # btclr psw.3,$label112       ;31 31 1e fc
    def test_31_31_btclr_psw_bit3_branches_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0x31, 0x1e, 0x30]
        proc.write_memory(0, code)
        proc.write_psw(0b00001000)
        proc.step()
        self.assertEqual(proc.pc, 0x34) # branch taken

    # btclr psw.3,$label112       ;31 31 1e fc
    def test_31_31_btclr_psw_bit3_clears_bit_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0x31, 0x1e, 0x30]
        proc.write_memory(0, code)
        proc.write_psw(0b11111111)
        proc.step()
        self.assertEqual(proc.pc, 0x34) # branch taken
        self.assertEqual(proc.read_psw(), 0b11110111) # bit cleared

    # btclr psw.3,$label112       ;31 31 1e fc
    def test_31_31_btclr_psw_bit3_doesnt_branch_if_clear(self):
        proc = Processor()
        code = [0x31, 0x31, 0x1e, 0x30]
        proc.write_memory(0, code)
        proc.write_psw(0)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken

    # btclr psw.4,$label112       ;31 41 1e fc
    def test_31_41_btclr_psw_bit4_branches_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0x41, 0x1e, 0x30]
        proc.write_memory(0, code)
        proc.write_psw(0b00010000)
        proc.step()
        self.assertEqual(proc.pc, 0x34) # branch taken

    # btclr psw.4,$label112       ;31 41 1e fc
    def test_31_41_btclr_psw_bit4_clears_bit_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0x41, 0x1e, 0x30]
        proc.write_memory(0, code)
        proc.write_psw(0b11111111)
        proc.step()
        self.assertEqual(proc.pc, 0x34) # branch taken
        self.assertEqual(proc.read_psw(), 0b11101111) # bit cleared

    # btclr psw.4,$label112       ;31 41 1e fc
    def test_31_41_btclr_psw_bit4_doesnt_branch_if_clear(self):
        proc = Processor()
        code = [0x31, 0x41, 0x1e, 0x30]
        proc.write_memory(0, code)
        proc.write_psw(0)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken

    # btclr psw.5,$label112       ;31 51 1e fc
    def test_31_51_btclr_psw_bit5_branches_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0x51, 0x1e, 0x30]
        proc.write_memory(0, code)
        proc.write_psw(0b00100000)
        proc.step()
        self.assertEqual(proc.pc, 0x34) # branch taken

    # btclr psw.5,$label112       ;31 51 1e fc
    def test_31_51_btclr_psw_bit5_clears_bit_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0x51, 0x1e, 0x30]
        proc.write_memory(0, code)
        proc.write_psw(0b11111111)
        proc.step()
        self.assertEqual(proc.pc, 0x34) # branch taken
        self.assertEqual(proc.read_psw(), 0b11011111) # bit cleared

    # btclr psw.5,$label112       ;31 51 1e fc
    def test_31_51_btclr_psw_bit5_doesnt_branch_if_clear(self):
        proc = Processor()
        code = [0x31, 0x51, 0x1e, 0x30]
        proc.write_memory(0, code)
        proc.write_psw(0)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken

    # btclr psw.6,$label112       ;31 61 1e fc
    def test_31_61_btclr_psw_bit6_branches_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0x61, 0x1e, 0x30]
        proc.write_memory(0, code)
        proc.write_psw(0b01000000)
        proc.step()
        self.assertEqual(proc.pc, 0x34) # branch taken

    # btclr psw.6,$label112       ;31 61 1e fc
    def test_31_61_btclr_psw_bit6_clears_bit_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0x61, 0x1e, 0x30]
        proc.write_memory(0, code)
        proc.write_psw(0b11111111)
        proc.step()
        self.assertEqual(proc.pc, 0x34) # branch taken
        self.assertEqual(proc.read_psw(), 0b10111111) # bit cleared

    # btclr psw.6,$label112       ;31 61 1e fc
    def test_31_61_btclr_psw_bit6_doesnt_branch_if_clear(self):
        proc = Processor()
        code = [0x31, 0x61, 0x1e, 0x30]
        proc.write_memory(0, code)
        proc.write_psw(0)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken

    # btclr psw.7,$label112       ;31 71 1e fc
    def test_31_71_btclr_psw_bit7_branches_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0x71, 0x1e, 0x30]
        proc.write_memory(0, code)
        proc.write_psw(0b10000000)
        proc.step()
        self.assertEqual(proc.pc, 0x34) # branch taken

    # btclr psw.7,$label112       ;31 71 1e fc
    def test_31_71_btclr_psw_bit7_clears_bit_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0x71, 0x1e, 0x30]
        proc.write_memory(0, code)
        proc.write_psw(0b11111111)
        proc.step()
        self.assertEqual(proc.pc, 0x34) # branch taken
        self.assertEqual(proc.read_psw(), 0b01111111) # bit cleared

    # btclr psw.7,$label112       ;31 71 1e fc
    def test_31_71_btclr_psw_bit7_doesnt_branch_if_clear(self):
        proc = Processor()
        code = [0x31, 0x71, 0x1e, 0x30]
        proc.write_memory(0, code)
        proc.write_psw(0)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken

    # btclr 0fe20h.7,$label91     ;31 71 20 fc    saddr
    def test_31_71_btclr_saddr_bit7_clears_bit_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0x71, 0x20, 0x30]
        proc.write_memory(0, code)
        proc.memory[0x0fe20] = 0b11111111
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x34) # branch taken
        self.assertEqual(proc.memory[0x0fe20], 0b01111111) # bit cleared
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr 0fe20h.7,$label91     ;31 71 20 fc    saddr
    def test_31_71_btclr_saddr_bit7_doesnt_branch_if_clear(self):
        proc = Processor()
        code = [0x31, 0x71, 0x20, 0x30]
        proc.write_memory(0, code)
        proc.memory[0x0fe20] = 0
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr 0fffeh.0,$label96     ;31 05 fe fc    sfr
    def test_31_05_btclr_sfr_bit0_branches_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0x05, 0xfe, 0x20]
        proc.write_memory(0, code)
        proc.memory[0x0fffe] = 0b00000001
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x24) # branch taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr 0fffeh.0,$label96     ;31 05 fe fc    sfr
    def test_31_05_btclr_sfr_bit0_clears_bit_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0x05, 0xfe, 0x20]
        proc.write_memory(0, code)
        proc.memory[0x0fffe] = 0b11111111
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x24) # branch taken
        self.assertEqual(proc.memory[0x0fffe], 0b11111110) # bit cleared
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr 0fffeh.0,$label96     ;31 05 fe fc    sfr
    def test_31_05_btclr_sfr_bit0_doesnt_branch_if_clear(self):
        proc = Processor()
        code = [0x31, 0x05, 0xfe, 0x20]
        proc.write_memory(0, code)
        proc.memory[0x0fffe] = 0
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr 0fffeh.1,$label97     ;31 15 fe fc    sfr
    def test_31_15_btclr_sfr_bit1_branches_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0x15, 0xfe, 0x20]
        proc.write_memory(0, code)
        proc.memory[0x0fffe] = 0b00000010
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x24) # branch taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr 0fffeh.1,$label97     ;31 15 fe fc    sfr
    def test_31_15_btclr_sfr_bit1_clears_bit_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0x15, 0xfe, 0x20]
        proc.write_memory(0, code)
        proc.memory[0x0fffe] = 0b11111111
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x24) # branch taken
        self.assertEqual(proc.memory[0x0fffe], 0b11111101) # bit cleared
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr 0fffeh.1,$label96     ;31 15 fe fc    sfr
    def test_31_15_btclr_sfr_bit1_doesnt_branch_if_clear(self):
        proc = Processor()
        code = [0x31, 0x05, 0xfe, 0x20]
        proc.write_memory(0, code)
        proc.memory[0x0fffe] = 0
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr 0fffeh.2,$label98     ;31 25 fe fc    sfr
    def test_31_25_btclr_sfr_bit2_branches_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0x25, 0xfe, 0x20]
        proc.write_memory(0, code)
        proc.memory[0x0fffe] = 0b00000100
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x24) # branch taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr 0fffeh.2,$label98     ;31 25 fe fc    sfr
    def test_31_25_btclr_sfr_bit2_clears_bit_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0x25, 0xfe, 0x20]
        proc.write_memory(0, code)
        proc.memory[0x0fffe] = 0b11111111
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x24) # branch taken
        self.assertEqual(proc.memory[0x0fffe], 0b11111011) # bit cleared
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr 0fffeh.2,$label96     ;31 25 fe fc    sfr
    def test_31_25_btclr_sfr_bit2_doesnt_branch_if_clear(self):
        proc = Processor()
        code = [0x31, 0x25, 0xfe, 0x20]
        proc.write_memory(0, code)
        proc.memory[0x0fffe] = 0
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr 0fffeh.3,$label99     ;31 35 fe fc    sfr
    def test_31_35_btclr_sfr_bit3_branches_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0x35, 0xfe, 0x20]
        proc.write_memory(0, code)
        proc.memory[0x0fffe] = 0b00001000
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x24) # branch taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr 0fffeh.3,$label98     ;31 35 fe fc    sfr
    def test_31_35_btclr_sfr_bit3_clears_bit_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0x35, 0xfe, 0x20]
        proc.write_memory(0, code)
        proc.memory[0x0fffe] = 0b11111111
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x24) # branch taken
        self.assertEqual(proc.memory[0x0fffe], 0b11110111) # bit cleared
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr 0fffeh.3,$label96     ;31 35 fe fc    sfr
    def test_31_35_btclr_sfr_bit3_doesnt_branch_if_clear(self):
        proc = Processor()
        code = [0x31, 0x35, 0xfe, 0x20]
        proc.write_memory(0, code)
        proc.memory[0x0fffe] = 0
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr 0fffeh.4,$label100    ;31 45 fe fc    sfr
    def test_31_45_btclr_sfr_bit4_branches_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0x45, 0xfe, 0x20]
        proc.write_memory(0, code)
        proc.memory[0x0fffe] = 0b00010000
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x24) # branch taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr 0fffeh.4,$label98     ;31 45 fe fc    sfr
    def test_31_45_btclr_sfr_bit4_clears_bit_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0x45, 0xfe, 0x20]
        proc.write_memory(0, code)
        proc.memory[0x0fffe] = 0b11111111
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x24) # branch taken
        self.assertEqual(proc.memory[0x0fffe], 0b11101111) # bit cleared
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr 0fffeh.4,$label96     ;31 45 fe fc    sfr
    def test_31_45_btclr_sfr_bit4_doesnt_branch_if_clear(self):
        proc = Processor()
        code = [0x31, 0x45, 0xfe, 0x20]
        proc.write_memory(0, code)
        proc.memory[0x0fffe] = 0
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr 0fffeh.5,$label101    ;31 55 fe fc    sfr
    def test_31_55_btclr_sfr_bit5_branches_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0x55, 0xfe, 0x20]
        proc.write_memory(0, code)
        proc.memory[0x0fffe] = 0b00100000
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x24) # branch taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr 0fffeh.5,$label98     ;31 55 fe fc    sfr
    def test_31_55_btclr_sfr_bit5_clears_bit_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0x55, 0xfe, 0x20]
        proc.write_memory(0, code)
        proc.memory[0x0fffe] = 0b11111111
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x24) # branch taken
        self.assertEqual(proc.memory[0x0fffe], 0b11011111) # bit cleared
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr 0fffeh.5,$label96     ;31 55 fe fc    sfr
    def test_31_55_btclr_sfr_bit5_doesnt_branch_if_clear(self):
        proc = Processor()
        code = [0x31, 0x55, 0xfe, 0x20]
        proc.write_memory(0, code)
        proc.memory[0x0fffe] = 0
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr 0fffeh.6,$label102    ;31 65 fe fc    sfr
    def test_31_65_btclr_sfr_bit6_branches_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0x65, 0xfe, 0x20]
        proc.write_memory(0, code)
        proc.memory[0x0fffe] = 0b01000000
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x24) # branch taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr 0fffeh.6,$label98     ;31 65 fe fc    sfr
    def test_31_65_btclr_sfr_bit6_clears_bit_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0x65, 0xfe, 0x20]
        proc.write_memory(0, code)
        proc.memory[0x0fffe] = 0b11111111
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x24) # branch taken
        self.assertEqual(proc.memory[0x0fffe], 0b10111111) # bit cleared
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr 0fffeh.6,$label96     ;31 65 fe fc    sfr
    def test_31_65_btclr_sfr_bit6_doesnt_branch_if_clear(self):
        proc = Processor()
        code = [0x31, 0x65, 0xfe, 0x20]
        proc.write_memory(0, code)
        proc.memory[0x0fffe] = 0
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr 0fffeh.7,$label103    ;31 75 fe fc    sfr
    def test_31_75_btclr_sfr_bit7_branches_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0x75, 0xfe, 0x20]
        proc.write_memory(0, code)
        proc.memory[0x0fffe] = 0b10000000
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x24) # branch taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr 0fffeh.7,$label98     ;31 75 fe fc    sfr
    def test_31_75_btclr_sfr_bit7_clears_bit_if_bit_is_set(self):
        proc = Processor()
        code = [0x31, 0x75, 0xfe, 0x20]
        proc.write_memory(0, code)
        proc.memory[0x0fffe] = 0b11111111
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x24) # branch taken
        self.assertEqual(proc.memory[0x0fffe], 0b01111111) # bit cleared
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # btclr 0fffeh.7,$label96     ;31 75 fe fc    sfr
    def test_31_75_btclr_sfr_bit7_doesnt_branch_if_clear(self):
        proc = Processor()
        code = [0x31, 0x75, 0xfe, 0x20]
        proc.write_memory(0, code)
        proc.memory[0x0fffe] = 0
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bt 0fffeh.0,$label24        ;31 06 fe fc    sfr
    def test_31_06_bt_sfr_bit0_branches_if_set(self):
        proc = Processor()
        code = [0x31, 0x06, 0xfe, 0x20]
        proc.write_memory(0, code)
        proc.memory[0x0fffe] = 0b00000001
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x24) # branch taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bt 0fffeh.0,$label24        ;31 06 fe fc    sfr
    def test_31_06_bt_sfr_bit0_doesnt_branch_if_clear(self):
        proc = Processor()
        code = [0x31, 0x06, 0xfe, 0x20]
        proc.write_memory(0, code)
        proc.memory[0x0fffe] = 0
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bt 0fffeh.1,$label25        ;31 16 fe fc    sfr
    def test_31_16_bt_sfr_bit1_branches_if_set(self):
        proc = Processor()
        code = [0x31, 0x16, 0xfe, 0x20]
        proc.write_memory(0, code)
        proc.memory[0x0fffe] = 0b00000010
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x24) # branch taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bt 0fffeh.1,$label25        ;31 16 fe fc    sfr
    def test_31_16_bt_sfr_bit1_doesnt_branch_if_clear(self):
        proc = Processor()
        code = [0x31, 0x16, 0xfe, 0x20]
        proc.write_memory(0, code)
        proc.memory[0x0fffe] = 0
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bt 0fffeh.2,$label26        ;31 26 fe fc    sfr
    def test_31_26_bt_sfr_bit2_branches_if_set(self):
        proc = Processor()
        code = [0x31, 0x26, 0xfe, 0x20]
        proc.write_memory(0, code)
        proc.memory[0x0fffe] = 0b00000100
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x24) # branch taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bt 0fffeh.2,$label26        ;31 26 fe fc    sfr
    def test_31_26_bt_sfr_bit2_doesnt_branch_if_clear(self):
        proc = Processor()
        code = [0x31, 0x26, 0xfe, 0x20]
        proc.write_memory(0, code)
        proc.memory[0x0fffe] = 0
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bt 0fffeh.3,$label27        ;31 36 fe fc    sfr
    def test_31_36_bt_sfr_bit3_branches_if_set(self):
        proc = Processor()
        code = [0x31, 0x36, 0xfe, 0x20]
        proc.write_memory(0, code)
        proc.memory[0x0fffe] = 0b00001000
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x24) # branch taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bt 0fffeh.3,$label27        ;31 36 fe fc    sfr
    def test_31_36_bt_sfr_bit3_doesnt_branch_if_clear(self):
        proc = Processor()
        code = [0x31, 0x36, 0xfe, 0x20]
        proc.write_memory(0, code)
        proc.memory[0x0fffe] = 0
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bt 0fffeh.4,$label28        ;31 46 fe fc    sfr
    def test_31_46_bt_sfr_bit4_branches_if_set(self):
        proc = Processor()
        code = [0x31, 0x46, 0xfe, 0x20]
        proc.write_memory(0, code)
        proc.memory[0x0fffe] = 0b00010000
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x24) # branch taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bt 0fffeh.4,$label28        ;31 46 fe fc    sfr
    def test_31_46_bt_sfr_bit4_doesnt_branch_if_clear(self):
        proc = Processor()
        code = [0x31, 0x46, 0xfe, 0x20]
        proc.write_memory(0, code)
        proc.memory[0x0fffe] = 0
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bt 0fffeh.5,$label29        ;31 56 fe fc    sfr
    def test_31_56_bt_sfr_bit5_branches_if_set(self):
        proc = Processor()
        code = [0x31, 0x56, 0xfe, 0x20]
        proc.write_memory(0, code)
        proc.memory[0x0fffe] = 0b00100000
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x24) # branch taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bt 0fffeh.5,$label29        ;31 56 fe fc    sfr
    def test_31_56_bt_sfr_bit5_doesnt_branch_if_clear(self):
        proc = Processor()
        code = [0x31, 0x56, 0xfe, 0x20]
        proc.write_memory(0, code)
        proc.memory[0x0fffe] = 0
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bt 0fffeh.6,$label30        ;31 66 fe fc    sfr
    def test_31_66_bt_sfr_bit6_branches_if_set(self):
        proc = Processor()
        code = [0x31, 0x66, 0xfe, 0x20]
        proc.write_memory(0, code)
        proc.memory[0x0fffe] = 0b01000000
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x24) # branch taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bt 0fffeh.6,$label30        ;31 66 fe fc    sfr
    def test_31_66_bt_sfr_bit6_doesnt_branch_if_clear(self):
        proc = Processor()
        code = [0x31, 0x66, 0xfe, 0x20]
        proc.write_memory(0, code)
        proc.memory[0x0fffe] = 0
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bt 0fffeh.7,$label31        ;31 76 fe fc    sfr
    def test_31_76_bt_sfr_bit7_branches_if_set(self):
        proc = Processor()
        code = [0x31, 0x76, 0xfe, 0x20]
        proc.write_memory(0, code)
        proc.memory[0x0fffe] = 0b10000000
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x24) # branch taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bt 0fffeh.7,$label31        ;31 76 fe fc    sfr
    def test_31_76_bt_sfr_bit7_doesnt_branch_if_clear(self):
        proc = Processor()
        code = [0x31, 0x76, 0xfe, 0x20]
        proc.write_memory(0, code)
        proc.memory[0x0fffe] = 0
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bt psw.0,$label9            ;8c 1e fd
    def test_8c_bt_psw_bit0_branches_if_set(self):
        proc = Processor()
        code = [0x8c, 0x1e, 0x30]
        proc.write_memory(0, code)
        proc.memory[0xfe20] = 0b00000001
        proc.write_psw(0b00000001)
        proc.step()
        self.assertEqual(proc.pc, 0x33) # branch taken
        self.assertEqual(proc.read_psw(), 0b00000001) # unchanged

    # bt 0fe20h.0,$label8         ;8c 20 fd       saddr
    def test_8c_bt_saddr_bit0_branches_if_set(self):
        proc = Processor()
        code = [0x8c, 0x20, 0x30]
        proc.write_memory(0, code)
        proc.memory[0xfe20] = 0b00000001
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x33) # branch taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bt 0fe20h.0,$label8         ;8c 20 fd       saddr
    def test_8c_bt_saddr_bit0_doesnt_branch_if_clear(self):
        proc = Processor()
        code = [0x8c, 0x20, 0x30]
        proc.write_memory(0, code)
        proc.memory[0xfe20] = 0
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bt 0fe20h.1,$label10        ;9c 20 fd       saddr
    def test_9c_bt_saddr_bit1_branches_if_set(self):
        proc = Processor()
        code = [0x9c, 0x20, 0x30]
        proc.write_memory(0, code)
        proc.memory[0xfe20] = 0b00000010
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x33) # branch taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bt psw.1,$label11           ;9c 1e fd
    def test_9c_bt_psw_bit1_branches_if_set(self):
        proc = Processor()
        code = [0x9c, 0x1e, 0x30]
        proc.write_memory(0, code)
        proc.write_psw(0b00000010)
        proc.step()
        self.assertEqual(proc.pc, 0x33) # branch taken
        self.assertEqual(proc.read_psw(), 0b00000010) # unchanged

    # bt 0fe20h.1,$label10        ;9c 20 fd       saddr
    def test_9c_bt_saddr_bit1_doesnt_branch_if_clear(self):
        proc = Processor()
        code = [0x9c, 0x20, 0x30]
        proc.write_memory(0, code)
        proc.memory[0xfe20] = 0
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bt 0fe20h.2,$label12        ;ac 20 fd       saddr
    def test_ac_bt_saddr_bit2_branches_if_set(self):
        proc = Processor()
        code = [0xac, 0x20, 0x30]
        proc.write_memory(0, code)
        proc.memory[0xfe20] = 0b00000100
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x33) # branch taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bt psw.2,$label13           ;ac 1e fd
    def test_ac_bt_psw_bit2_branches_if_set(self):
        proc = Processor()
        code = [0xac, 0x1e, 0x30]
        proc.write_memory(0, code)
        proc.write_psw(0b00000100)
        proc.step()
        self.assertEqual(proc.pc, 0x33) # branch taken
        self.assertEqual(proc.read_psw(), 0b00000100) # unchanged

    # bt 0fe20h.2,$label12        ;ac 20 fd       saddr
    def test_ac_bt_saddr_bit2_doesnt_branch_if_clear(self):
        proc = Processor()
        code = [0xac, 0x20, 0x30]
        proc.write_memory(0, code)
        proc.memory[0xfe20] = 0
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bt 0fe20h.3,$label14        ;bc 20 fd       saddr
    def test_bc_bt_saddr_bit3_branches_if_set(self):
        proc = Processor()
        code = [0xbc, 0x20, 0x30]
        proc.write_memory(0, code)
        proc.memory[0xfe20] = 0b00001000
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x33) # branch taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bt psw.3,$label15           ;bc 1e fd
    def test_bc_bt_psw_bit3_branches_if_set(self):
        proc = Processor()
        code = [0xbc, 0x1e, 0x30]
        proc.write_memory(0, code)
        proc.write_psw(0b00001000)
        proc.step()
        self.assertEqual(proc.pc, 0x33) # branch taken
        self.assertEqual(proc.read_psw(), 0b00001000) # unchanged

    # bt 0fe20h.3,$label14        ;bc 20 fd       saddr
    def test_bc_bt_saddr_bit3_doesnt_branch_if_clear(self):
        proc = Processor()
        code = [0xbc, 0x20, 0x30]
        proc.write_memory(0, code)
        proc.memory[0xfe20] = 0
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bt 0fe20h.4,$label16        ;cc 20 fd       saddr
    def test_cc_bt_saddr_bit4_branches_if_set(self):
        proc = Processor()
        code = [0xcc, 0x20, 0x30]
        proc.write_memory(0, code)
        proc.memory[0xfe20] = 0b0010000
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x33) # branch taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bt psw.4,$label17           ;cc 1e fd
    def test_cc_bt_psw_bit4_branches_if_set(self):
        proc = Processor()
        code = [0xcc, 0x1e, 0x30]
        proc.write_memory(0, code)
        proc.write_psw(0b0010000)
        proc.step()
        self.assertEqual(proc.pc, 0x33) # branch taken
        self.assertEqual(proc.read_psw(), 0b0010000) # unchanged

    # bt 0fe20h.4,$label16        ;cc 20 fd       saddr
    def test_cc_bt_saddr_bit4_doesnt_branch_if_clear(self):
        proc = Processor()
        code = [0xcc, 0x20, 0x30]
        proc.write_memory(0, code)
        proc.memory[0xfe20] = 0
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bt 0fe20h.5,$label20        ;dc 20 fd       saddr
    def test_dc_bt_saddr_bit5_branches_if_set(self):
        proc = Processor()
        code = [0xdc, 0x20, 0x30]
        proc.write_memory(0, code)
        proc.memory[0xfe20] = 0b00100000
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x33) # branch taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bt psw.5,$label21           ;dc 1e fd
    def test_dc_bt_psw_bit5_branches_if_set(self):
        proc = Processor()
        code = [0xdc, 0x1e, 0x30]
        proc.write_memory(0, code)
        proc.write_psw(0b00100000)
        proc.step()
        self.assertEqual(proc.pc, 0x33) # branch taken
        self.assertEqual(proc.read_psw(), 0b00100000) # unchanged

    # bt 0fe20h.5,$label20        ;dc 20 fd       saddr
    def test_dc_bt_saddr_bit5_doesnt_branch_if_clear(self):
        proc = Processor()
        code = [0xdc, 0x20, 0x30]
        proc.write_memory(0, code)
        proc.memory[0xfe20] = 0
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bt 0fe20h.6,$label22        ;ec 20 fd       saddr
    def test_ec_bt_saddr_bit6_branches_if_set(self):
        proc = Processor()
        code = [0xec, 0x20, 0x30]
        proc.write_memory(0, code)
        proc.memory[0xfe20] = 0b01000000
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x33) # branch taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bt psw.6,$label23           ;ec 1e fd
    def test_ec_bt_psw_bit6_branches_if_set(self):
        proc = Processor()
        code = [0xec, 0x1e, 0x30]
        proc.write_memory(0, code)
        proc.write_psw(0b01000000)
        proc.step()
        self.assertEqual(proc.pc, 0x33) # branch taken
        self.assertEqual(proc.read_psw(), 0b01000000) # unchanged

    # bt 0fe20h.6,$label22        ;ec 20 fd       saddr
    def test_ec_bt_saddr_bit6_doesnt_branch_if_clear(self):
        proc = Processor()
        code = [0xec, 0x20, 0x30]
        proc.write_memory(0, code)
        proc.memory[0xfe20] = 0
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bt 0fe20h.7,$label18        ;fc 20 fd       saddr
    def test_fc_bt_saddr_bit7_branches_if_set(self):
        proc = Processor()
        code = [0xfc, 0x20, 0x30]
        proc.write_memory(0, code)
        proc.memory[0xfe20] = 0b10000000
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, 0x33) # branch taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # bt psw.7,$label19           ;fc 1e fd
    def test_fc_bt_psw_bit7_branches_if_set(self):
        proc = Processor()
        code = [0xfc, 0x1e, 0x30]
        proc.write_memory(0, code)
        proc.write_psw(0b10000000)
        proc.step()
        self.assertEqual(proc.pc, 0x33) # branch taken
        self.assertEqual(proc.read_psw(), 0b10000000) # unchanged

    # bt 0fe20h.7,$label18        ;fc 20 fd       saddr
    def test_fc_bt_saddr_bit7_doesnt_branch_if_clear(self):
        proc = Processor()
        code = [0xfc, 0x20, 0x30]
        proc.write_memory(0, code)
        proc.memory[0xfe20] = 0
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code)) # branch not taken
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # movw ax,#0abcdh             ;10 cd ab
    def test_10_movw_ax_imm16(self):
        proc = Processor()
        code = [0x10, 0xcd, 0xab]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.AX, 0)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_regpair(RegisterPairs.AX), 0xabcd)
        self.assertEqual(proc.read_gp_reg(Registers.X), 0xcd)
        self.assertEqual(proc.read_gp_reg(Registers.A), 0xab)

    # movw bc,#0abcdh             ;12 cd ab
    def test_12_movw_bc_imm16(self):
        proc = Processor()
        code = [0x12, 0xcd, 0xab]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.BC, 0)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_regpair(RegisterPairs.BC), 0xabcd)
        self.assertEqual(proc.read_gp_reg(Registers.C), 0xcd)
        self.assertEqual(proc.read_gp_reg(Registers.B), 0xab)

    # movw de,#0abcdh             ;14 cd ab
    def test_14_movw_de_imm16(self):
        proc = Processor()
        code = [0x14, 0xcd, 0xab]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.DE, 0)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_regpair(RegisterPairs.DE), 0xabcd)
        self.assertEqual(proc.read_gp_reg(Registers.E), 0xcd)
        self.assertEqual(proc.read_gp_reg(Registers.D), 0xab)

    # movw hl,#0abcdh             ;16 cd ab
    def test_16_movw_hl_imm16(self):
        proc = Processor()
        code = [0x16, 0xcd, 0xab]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_regpair(RegisterPairs.HL), 0xabcd)
        self.assertEqual(proc.read_gp_reg(Registers.L), 0xcd)
        self.assertEqual(proc.read_gp_reg(Registers.H), 0xab)

    # xchw ax,bc                  ;e2
    def test_e2_xchw_ax_bc(self):
        proc = Processor()
        code = [0xe2]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.AX, 0x12)
        proc.write_gp_regpair(RegisterPairs.BC, 0x34)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_regpair(RegisterPairs.AX), 0x34)
        self.assertEqual(proc.read_gp_regpair(RegisterPairs.BC), 0x12)

    # xchw ax,de                  ;e4
    def test_e4_xchw_ax_de(self):
        proc = Processor()
        code = [0xe4]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.AX, 0x12)
        proc.write_gp_regpair(RegisterPairs.DE, 0x34)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_regpair(RegisterPairs.AX), 0x34)
        self.assertEqual(proc.read_gp_regpair(RegisterPairs.DE), 0x12)

    # xchw ax,hl                  ;e6
    def test_e6_xchw_ax_hl(self):
        proc = Processor()
        code = [0xe6]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.AX, 0x12)
        proc.write_gp_regpair(RegisterPairs.HL, 0x34)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_regpair(RegisterPairs.AX), 0x34)
        self.assertEqual(proc.read_gp_regpair(RegisterPairs.HL), 0x12)

    # mov a,[de]                  ;85
    def test_85_mov_a_de(self):
        proc = Processor()
        code = [0x85]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0)
        proc.write_gp_regpair(RegisterPairs.DE, 0xabcd)
        proc.memory[0xabcd] = 0x42
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0x42)

    # mov [de],a                  ;95
    def test_95_mov_de_a(self):
        proc = Processor()
        code = [0x95]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0x42)
        proc.write_gp_regpair(RegisterPairs.DE, 0xabcd)
        proc.memory[0xabcd] = 0
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xabcd], 0x42)

    # mov a,[hl]                  ;87
    def test_87_mov_a_hl(self):
        proc = Processor()
        code = [0x87]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0x42
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0x42)

    # mov [hl],a                  ;97
    def test_97_mov_hl_a(self):
        proc = Processor()
        code = [0x97]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0x42)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xabcd], 0x42)

    # xch a,[de]                  ;05
    def test_05_xch_a_de(self):
        proc = Processor()
        code = [0x05]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0x12)
        proc.write_gp_regpair(RegisterPairs.DE, 0xabcd)
        proc.memory[0xabcd] = 0x34
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xabcd], 0x12)
        self.assertEqual(proc.read_gp_reg(Registers.A), 0x34)

    # xch a,[hl]                  ;07
    def test_07_xch_a_hl(self):
        proc = Processor()
        code = [0x07]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0x12)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0x34
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xabcd], 0x12)
        self.assertEqual(proc.read_gp_reg(Registers.A), 0x34)

    # push ax                     ;b1
    def test_b1_push_ax(self):
        proc = Processor()
        code = [0xb1]
        proc.write_memory(0, code)
        proc.sp = 0xfe12
        proc.write_gp_regpair(RegisterPairs.AX, 0xabcd)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.sp, 0xfe10)
        self.assertEqual(proc.memory[0xfe11], 0xab) # A
        self.assertEqual(proc.memory[0xfe10], 0xcd) # X

    # push bc                     ;b3
    def test_b3_push_bc(self):
        proc = Processor()
        code = [0xb3]
        proc.write_memory(0, code)
        proc.sp = 0xfe12
        proc.write_gp_regpair(RegisterPairs.BC, 0xabcd)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.sp, 0xfe10)
        self.assertEqual(proc.memory[0xfe11], 0xab) # B
        self.assertEqual(proc.memory[0xfe10], 0xcd) # C

    # push de                     ;b5
    def test_b5_push_de(self):
        proc = Processor()
        code = [0xb5]
        proc.write_memory(0, code)
        proc.sp = 0xfe12
        proc.write_gp_regpair(RegisterPairs.DE, 0xabcd)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.sp, 0xfe10)
        self.assertEqual(proc.memory[0xfe11], 0xab) # D
        self.assertEqual(proc.memory[0xfe10], 0xcd) # E

    # push hl                     ;b7
    def test_b7_push_de(self):
        proc = Processor()
        code = [0xb7]
        proc.write_memory(0, code)
        proc.sp = 0xfe12
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.sp, 0xfe10)
        self.assertEqual(proc.memory[0xfe11], 0xab) # H
        self.assertEqual(proc.memory[0xfe10], 0xcd) # L

    # pop ax                      ;b0
    def test_b0_pop_ax(self):
        proc = Processor()
        code = [0xb0]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.AX, 0)
        proc.sp = 0xfe10
        proc.memory[0xfe11] = 0xab # A
        proc.memory[0xfe10] = 0xcd # X
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.sp, 0xfe12)
        self.assertEqual(proc.read_gp_regpair(RegisterPairs.AX), 0xabcd)

    # pop bc                      ;b2
    def test_b2_pop_bc(self):
        proc = Processor()
        code = [0xb2]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.BC, 0)
        proc.sp = 0xfe10
        proc.memory[0xfe11] = 0xab # A
        proc.memory[0xfe10] = 0xcd # X
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.sp, 0xfe12)
        self.assertEqual(proc.read_gp_regpair(RegisterPairs.BC), 0xabcd)

    # pop de                      ;b4
    def test_b4_pop_de(self):
        proc = Processor()
        code = [0xb4]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.DE, 0)
        proc.sp = 0xfe10
        proc.memory[0xfe11] = 0xab # A
        proc.memory[0xfe10] = 0xcd # X
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.sp, 0xfe12)
        self.assertEqual(proc.read_gp_regpair(RegisterPairs.DE), 0xabcd)

    # pop hl                      ;b6
    def test_b4_pop_hl(self):
        proc = Processor()
        code = [0xb6]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0)
        proc.sp = 0xfe10
        proc.memory[0xfe11] = 0xab # A
        proc.memory[0xfe10] = 0xcd # X
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.sp, 0xfe12)
        self.assertEqual(proc.read_gp_regpair(RegisterPairs.HL), 0xabcd)

    # reti                        ;8f
    def test_8f_reti(self):
        proc = Processor()
        code = [0x8f]
        proc.write_memory(0, code)
        proc.sp = 0xfe10
        proc.memory[0xfe12] = 0x55 # psw
        proc.memory[0xfe11] = 0xab # pch
        proc.memory[0xfe10] = 0xcd # pcl
        proc.step()
        self.assertEqual(proc.pc, 0xabcd)
        self.assertEqual(proc.read_psw(), 0x55)
        self.assertEqual(proc.sp, 0xfe13)

    # set1 [hl].0                 ;71 82
    def test_71_82_set1_hl_bit_0(self):
        proc = Processor()
        code = [0x71, 0x82]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xabcd], 0b00000001)
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # set1 [hl].1                 ;71 92
    def test_71_92_set1_hl_bit_1(self):
        proc = Processor()
        code = [0x71, 0x92]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xabcd], 0b00000010)
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # set1 [hl].2                 ;71 a2
    def test_71_a2_set1_hl_bit_2(self):
        proc = Processor()
        code = [0x71, 0xa2]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xabcd], 0b00000100)
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # set1 [hl].3                 ;71 b2
    def test_71_b2_set1_hl_bit_3(self):
        proc = Processor()
        code = [0x71, 0xb2]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xabcd], 0b00001000)
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # set1 [hl].4                 ;71 c2
    def test_71_c2_set1_hl_bit_4(self):
        proc = Processor()
        code = [0x71, 0xc2]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xabcd], 0b00010000)
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # set1 [hl].5                 ;71 d2
    def test_71_d2_set1_hl_bit_5(self):
        proc = Processor()
        code = [0x71, 0xd2]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xabcd], 0b00100000)
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # set1 [hl].6                 ;71 e2
    def test_71_e2_set1_hl_bit_6(self):
        proc = Processor()
        code = [0x71, 0xe2]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xabcd], 0b01000000)
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # set1 [hl].7                 ;71 f2
    def test_71_f2_set1_hl_bit_7(self):
        proc = Processor()
        code = [0x71, 0xf2]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xabcd], 0b10000000)
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # clr1 [hl].0                 ;71 83
    def test_71_83_clr1_hl_bit_0(self):
        proc = Processor()
        code = [0x71, 0x83]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0b11111111
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xabcd], 0b11111110)
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # clr1 [hl].1                 ;71 93
    def test_71_93_clr1_hl_bit_1(self):
        proc = Processor()
        code = [0x71, 0x93]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0b11111111
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xabcd], 0b11111101)
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # clr1 [hl].2                 ;71 a3
    def test_71_a3_clr1_hl_bit_2(self):
        proc = Processor()
        code = [0x71, 0xa3]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0b11111111
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xabcd], 0b11111011)
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # clr1 [hl].3                 ;71 b3
    def test_71_b3_clr1_hl_bit_3(self):
        proc = Processor()
        code = [0x71, 0xb3]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0b11111111
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xabcd], 0b11110111)
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # clr1 [hl].4                 ;71 c3
    def test_71_c3_clr1_hl_bit_4(self):
        proc = Processor()
        code = [0x71, 0xc3]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0b11111111
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xabcd], 0b11101111)
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # clr1 [hl].5                 ;71 d3
    def test_71_d3_clr1_hl_bit_5(self):
        proc = Processor()
        code = [0x71, 0xd3]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0b11111111
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xabcd], 0b11011111)
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # clr1 [hl].6                 ;71 e3
    def test_71_e3_clr1_hl_bit_6(self):
        proc = Processor()
        code = [0x71, 0xe3]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0b11111111
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xabcd], 0b10111111)
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # clr1 [hl].7                 ;71 f3
    def test_71_f3_clr1_hl_bit_7(self):
        proc = Processor()
        code = [0x71, 0xf3]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0b11111111
        proc.write_psw(0x55)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xabcd], 0b01111111)
        self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # incw ax                     ;80
    def test_80_incw_ax(self):
        tests = ((0, 1), (0xff, 0x100), (0xffff, 0))
        for before, after in tests:
            proc = Processor()
            code = [0x80]
            proc.write_memory(0, code)
            proc.write_gp_regpair(RegisterPairs.AX, before)
            proc.write_psw(0x55)
            proc.step()
            self.assertEqual(proc.pc, len(code))
            self.assertEqual(proc.read_gp_regpair(RegisterPairs.AX), after)
            self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # incw bc                     ;82
    def test_82_incw_bc(self):
        tests = ((0, 1), (0xff, 0x100), (0xffff, 0))
        for before, after in tests:
            proc = Processor()
            code = [0x82]
            proc.write_memory(0, code)
            proc.write_gp_regpair(RegisterPairs.BC, before)
            proc.write_psw(0x55)
            proc.step()
            self.assertEqual(proc.pc, len(code))
            self.assertEqual(proc.read_gp_regpair(RegisterPairs.BC), after)
            self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # incw de                     ;84
    def test_84_incw_bc(self):
        tests = ((0, 1), (0xff, 0x100), (0xffff, 0))
        for before, after in tests:
            proc = Processor()
            code = [0x84]
            proc.write_memory(0, code)
            proc.write_gp_regpair(RegisterPairs.DE, before)
            proc.write_psw(0x55)
            proc.step()
            self.assertEqual(proc.pc, len(code))
            self.assertEqual(proc.read_gp_regpair(RegisterPairs.DE), after)
            self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # incw hl                     ;86
    def test_86_incw_bc(self):
        tests = ((0, 1), (0xff, 0x100), (0xffff, 0))
        for before, after in tests:
            proc = Processor()
            code = [0x86]
            proc.write_memory(0, code)
            proc.write_gp_regpair(RegisterPairs.HL, before)
            proc.write_psw(0x55)
            proc.step()
            self.assertEqual(proc.pc, len(code))
            self.assertEqual(proc.read_gp_regpair(RegisterPairs.HL), after)
            self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # decw ax                     ;90
    def test_90_decw_ax(self):
        tests = ((1, 0), (0x100, 0xff), (0, 0xffff))
        for before, after in tests:
            proc = Processor()
            code = [0x90]
            proc.write_memory(0, code)
            proc.write_gp_regpair(RegisterPairs.AX, before)
            proc.write_psw(0x55)
            proc.step()
            self.assertEqual(proc.pc, len(code))
            self.assertEqual(proc.read_gp_regpair(RegisterPairs.AX), after)
            self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # decw bc                     ;92
    def test_92_decw_bc(self):
        tests = ((1, 0), (0x100, 0xff), (0, 0xffff))
        for before, after in tests:
            proc = Processor()
            code = [0x92]
            proc.write_memory(0, code)
            proc.write_gp_regpair(RegisterPairs.BC, before)
            proc.write_psw(0x55)
            proc.step()
            self.assertEqual(proc.pc, len(code))
            self.assertEqual(proc.read_gp_regpair(RegisterPairs.BC), after)
            self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # decw de                     ;94
    def test_92_decw_de(self):
        tests = ((1, 0), (0x100, 0xff), (0, 0xffff))
        for before, after in tests:
            proc = Processor()
            code = [0x94]
            proc.write_memory(0, code)
            proc.write_gp_regpair(RegisterPairs.DE, before)
            proc.write_psw(0x55)
            proc.step()
            self.assertEqual(proc.pc, len(code))
            self.assertEqual(proc.read_gp_regpair(RegisterPairs.DE), after)
            self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # decw hl                     ;96
    def test_92_decw_hl(self):
        tests = ((1, 0), (0x100, 0xff), (0, 0xffff))
        for before, after in tests:
            proc = Processor()
            code = [0x96]
            proc.write_memory(0, code)
            proc.write_gp_regpair(RegisterPairs.HL, before)
            proc.write_psw(0x55)
            proc.step()
            self.assertEqual(proc.pc, len(code))
            self.assertEqual(proc.read_gp_regpair(RegisterPairs.HL), after)
            self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # mulu x                      ;31 88
    def test_31_88_mulu_x(self):
        tests = ((0, 0, 0), (2, 2, 4), (0xff, 0xff, 0xfe01))
        for a, x, expected in tests:
            proc = Processor()
            code = [0x31, 0x88]
            proc.write_memory(0, code)
            proc.write_gp_reg(Registers.A, a)
            proc.write_gp_reg(Registers.X, x)
            proc.write_psw(0x55)
            proc.step()
            self.assertEqual(proc.pc, len(code))
            self.assertEqual(proc.read_gp_regpair(RegisterPairs.AX), expected)
            self.assertEqual(proc.read_psw(), 0x55) # unchanged

    # mov a,[hl+0abh]             ;ae ab
    def test_ae_mov_a_hl_based_imm(self):
        proc = Processor()
        code = [0xae, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabad)
        proc.memory[0xabcd] = 0x42
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0x42)

    # mov a,[hl+0abh]             ;ae ab
    def test_ae_mov_a_hl_based_imm_wraps(self):
        proc = Processor()
        code = [0xae, 0x2]
        proc.write_memory(0x100, code)
        proc.pc = 0x100
        proc.write_gp_reg(Registers.A, 0)
        proc.write_gp_regpair(RegisterPairs.HL, 0xffff)
        proc.memory[0x0001] = 0x42
        proc.step()
        self.assertEqual(proc.pc, 0x100 + len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0x42)

    # mov [hl+c],a                ;ba
    def test_ba_mov_hl_based_c_a(self):
        proc = Processor()
        code = [0xba]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0x42)
        proc.write_gp_reg(Registers.C, 0xcd)
        proc.write_gp_regpair(RegisterPairs.HL, 0xab00)
        proc.memory[0xabcd] = 0
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xabcd], 0x42)

    # mov [hl+b],a                ;bb
    def test_bb_mov_hl_based_b_a(self):
        proc = Processor()
        code = [0xbb]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0x42)
        proc.write_gp_reg(Registers.B, 0xcd)
        proc.write_gp_regpair(RegisterPairs.HL, 0xab00)
        proc.memory[0xabcd] = 0
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xabcd], 0x42)

    # mov [hl+0abh],a             ;be ab
    def test_be_mov_hl_based_imm_a(self):
        proc = Processor()
        code = [0xbe, 0xcd]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0x42)
        proc.write_gp_regpair(RegisterPairs.HL, 0xab00)
        proc.memory[0xabcd] = 0
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xabcd], 0x42)

    # xch a,[hl+0abh]             ;de ab
    def test_de_xch_a_hl_based_imm_a(self):
        proc = Processor()
        code = [0xde, 0x20]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0x12)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabad)
        proc.memory[0xabcd] = 0x34
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xabcd], 0x12)
        self.assertEqual(proc.read_gp_reg(Registers.A), 0x34)

    # mov a,[hl+b]                ;ab
    def test_ab_mov_a_based_hl_b(self):
        proc = Processor()
        code = [0xab]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0)
        proc.write_gp_regpair(RegisterPairs.HL, 0xab00)
        proc.write_gp_reg(Registers.B, 0xcd)
        proc.memory[0xabcd] = 0x42
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0x42)

    # mov a,[hl+c]                ;aa
    def test_aa_mov_a_based_hl_c(self):
        proc = Processor()
        code = [0xaa]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0)
        proc.write_gp_regpair(RegisterPairs.HL, 0xab00)
        proc.write_gp_reg(Registers.C, 0xcd)
        proc.memory[0xabcd] = 0x42
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0x42)

    # xch a,[hl+c]                ;31 8a
    def test_31_8a_xch_a_based_hl_c(self):
        proc = Processor()
        code = [0x31, 0x8a]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0x55)
        proc.write_gp_regpair(RegisterPairs.HL, 0xAB00)
        proc.write_gp_reg(Registers.C, 0xCD)
        proc.memory[0xabcd] = 0xAA
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0xAA)
        self.assertEqual(proc.memory[0xABCD], 0x55)

    # xch a,[hl+b]                ;31 8b
    def test_31_8b_xch_a_based_hl_b(self):
        proc = Processor()
        code = [0x31, 0x8b]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0x55)
        proc.write_gp_regpair(RegisterPairs.HL, 0xAB00)
        proc.write_gp_reg(Registers.B, 0xCD)
        proc.memory[0xabcd] = 0xAA
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0xAA)
        self.assertEqual(proc.memory[0xABCD], 0x55)

    # movw ax,bc                  ;c2
    def test_c2_movw_ax_bc(self):
        proc = Processor()
        code = [0xc2]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.AX, 0)
        proc.write_gp_regpair(RegisterPairs.BC, 0x42)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_regpair(RegisterPairs.AX), 0x42)

    # movw ax,de                  ;c4
    def test_c4_movw_ax_de(self):
        proc = Processor()
        code = [0xc4]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.AX, 0)
        proc.write_gp_regpair(RegisterPairs.DE, 0x42)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_regpair(RegisterPairs.AX), 0x42)

    # movw ax,hl                  ;c6
    def test_c6_movw_ax_hl(self):
        proc = Processor()
        code = [0xc6]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.AX, 0)
        proc.write_gp_regpair(RegisterPairs.HL, 0x42)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_regpair(RegisterPairs.AX), 0x42)

    # movw bc,ax                  ;d2
    def test_d2_movw_bc_ax(self):
        proc = Processor()
        code = [0xd2]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.BC, 0)
        proc.write_gp_regpair(RegisterPairs.AX, 0x42)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_regpair(RegisterPairs.BC), 0x42)

    # movw de,ax                  ;d4
    def test_d4_movw_de_ax(self):
        proc = Processor()
        code = [0xd4]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.DE, 0)
        proc.write_gp_regpair(RegisterPairs.AX, 0x42)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_regpair(RegisterPairs.DE), 0x42)

    # movw hl,ax                  ;d6
    def test_d6_movw_hl_ax(self):
        proc = Processor()
        code = [0xd6]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0)
        proc.write_gp_regpair(RegisterPairs.AX, 0x42)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_regpair(RegisterPairs.HL), 0x42)

    # or a,[hl]                   ;6f
    def test_6f_or_a_hl(self):
        proc = Processor()
        code = [0x6f]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0x55)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0xAA
        proc.write_psw(proc.read_psw() | Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0xFF)
        self.assertEqual(proc.read_psw() & Flags.Z, 0)

    # or a,[hl+0abh]              ;69 ab
    def test_69_or_a_based_hl_imm(self):
        proc = Processor()
        code = [0x69, 0xcd]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0x55)
        proc.write_gp_regpair(RegisterPairs.HL, 0xab00)
        proc.memory[0xabcd] = 0xAA
        proc.write_psw(proc.read_psw() | Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0xFF)
        self.assertEqual(proc.read_psw() & Flags.Z, 0)

    # or a,[hl+c]                 ;31 6a
    def test_31_6a_or_a_based_hl_c(self):
        proc = Processor()
        code = [0x31, 0x6a]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0x55)
        proc.write_gp_regpair(RegisterPairs.HL, 0xab00)
        proc.write_gp_reg(Registers.C, 0xcd)
        proc.memory[0xabcd] = 0xAA
        proc.write_psw(proc.read_psw() | Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0xFF)
        self.assertEqual(proc.read_psw() & Flags.Z, 0)

    # or a,[hl+b]                 ;31 6b
    def test_31_6b_or_a_based_hl_b(self):
        proc = Processor()
        code = [0x31, 0x6b]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0x55)
        proc.write_gp_regpair(RegisterPairs.HL, 0xab00)
        proc.write_gp_reg(Registers.B, 0xcd)
        proc.memory[0xabcd] = 0xAA
        proc.write_psw(proc.read_psw() | Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0xFF)
        self.assertEqual(proc.read_psw() & Flags.Z, 0)

    # xor a,[hl]                  ;7f
    def test_7f_xor_a_hl(self):
        proc = Processor()
        code = [0x7f]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0x55)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0xFF
        proc.write_psw(proc.read_psw() | Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0xAA)
        self.assertEqual(proc.read_psw() & Flags.Z, 0)

    # xor a,[hl+0abh]             ;79 ab
    def test_79_xor_a_based_hl_imm(self):
        proc = Processor()
        code = [0x79, 0xcd]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0x55)
        proc.write_gp_regpair(RegisterPairs.HL, 0xab00)
        proc.memory[0xabcd] = 0xFF
        proc.write_psw(proc.read_psw() | Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0xAA)
        self.assertEqual(proc.read_psw() & Flags.Z, 0)

    # xor a,[hl+c]                ;31 7a
    def test_31_7a_xor_a_based_hl_c(self):
        proc = Processor()
        code = [0x31, 0x7a]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0x55)
        proc.write_gp_regpair(RegisterPairs.HL, 0xab00)
        proc.write_gp_reg(Registers.C, 0xcd)
        proc.memory[0xabcd] = 0xFF
        proc.write_psw(proc.read_psw() | Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0xAA)
        self.assertEqual(proc.read_psw() & Flags.Z, 0)

    # xor a,[hl+b]                ;31 7b
    def test_31_7b_xor_a_based_hl_b(self):
        proc = Processor()
        code = [0x31, 0x7b]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0x55)
        proc.write_gp_regpair(RegisterPairs.HL, 0xab00)
        proc.write_gp_reg(Registers.B, 0xcd)
        proc.memory[0xabcd] = 0xFF
        proc.write_psw(proc.read_psw() | Flags.Z)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0xAA)
        self.assertEqual(proc.read_psw() & Flags.Z, 0)

    # mov1 cy,[hl].0              ;71 84
    def test_71_84_mov1_cy_hl_bit0(self):
        proc = Processor()
        code = [0x71, 0x84]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0b00000001
        proc.write_psw(0)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), Flags.CY)

    # mov1 cy,[hl].1              ;71 94
    def test_71_94_mov1_cy_hl_bit1(self):
        proc = Processor()
        code = [0x71, 0x94]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0b00000010
        proc.write_psw(0)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), Flags.CY)

    # mov1 cy,[hl].2              ;71 a4
    def test_71_a4_mov1_cy_hl_bit2(self):
        proc = Processor()
        code = [0x71, 0xa4]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0b00000100
        proc.write_psw(0)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), Flags.CY)

    # mov1 cy,[hl].3              ;71 b4
    def test_71_b4_mov1_cy_hl_bit3(self):
        proc = Processor()
        code = [0x71, 0xb4]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0b00001000
        proc.write_psw(0)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), Flags.CY)

    # mov1 cy,[hl].4              ;71 c4
    def test_71_c4_mov1_cy_hl_bit4(self):
        proc = Processor()
        code = [0x71, 0xc4]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0b00010000
        proc.write_psw(0)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), Flags.CY)

    # mov1 cy,[hl].5              ;71 d4
    def test_71_d4_mov1_cy_hl_bit5(self):
        proc = Processor()
        code = [0x71, 0xd4]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0b00100000
        proc.write_psw(0)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), Flags.CY)

    # mov1 cy,[hl].6              ;71 e4
    def test_71_e4_mov1_cy_hl_bit6(self):
        proc = Processor()
        code = [0x71, 0xe4]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0b01000000
        proc.write_psw(0)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), Flags.CY)

    # mov1 cy,[hl].7              ;71 f4
    def test_71_f4_mov1_cy_hl_bit6(self):
        proc = Processor()
        code = [0x71, 0xf4]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0b10000000
        proc.write_psw(0)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), Flags.CY)

    # mov1 [hl].0,cy              ;71 81
    def test_71_81_mov1_hl_cy_bit0(self):
        proc = Processor()
        code = [0x71, 0x81]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0
        proc.write_psw(Flags.CY)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xabcd], 0b00000001)

    # mov1 [hl].1,cy              ;71 91
    def test_71_91_mov1_hl_cy_bit1(self):
        proc = Processor()
        code = [0x71, 0x91]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0
        proc.write_psw(Flags.CY)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xabcd], 0b00000010)

    # mov1 [hl].2,cy              ;71 a1
    def test_71_a1_mov1_hl_cy_bit2(self):
        proc = Processor()
        code = [0x71, 0xa1]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0
        proc.write_psw(Flags.CY)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xabcd], 0b00000100)

    # mov1 [hl].3,cy              ;71 b1
    def test_71_b1_mov1_hl_cy_bit3(self):
        proc = Processor()
        code = [0x71, 0xb1]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0
        proc.write_psw(Flags.CY)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xabcd], 0b00001000)

    # mov1 [hl].4,cy              ;71 c1
    def test_71_c1_mov1_hl_cy_bit4(self):
        proc = Processor()
        code = [0x71, 0xc1]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0
        proc.write_psw(Flags.CY)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xabcd], 0b00010000)

    # mov1 [hl].5,cy              ;71 d1
    def test_71_d1_mov1_hl_cy_bit5(self):
        proc = Processor()
        code = [0x71, 0xd1]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0
        proc.write_psw(Flags.CY)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xabcd], 0b00100000)

    # mov1 [hl].6,cy              ;71 e1
    def test_71_e1_mov1_hl_cy_bit6(self):
        proc = Processor()
        code = [0x71, 0xe1]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0
        proc.write_psw(Flags.CY)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xabcd], 0b01000000)

    # mov1 [hl].7,cy              ;71 f1
    def test_71_f1_mov1_hl_cy_bit7(self):
        proc = Processor()
        code = [0x71, 0xf1]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0
        proc.write_psw(Flags.CY)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.memory[0xabcd], 0b10000000)

    # and1 cy,a.0                 ;61 8d
    def test_61_8d_and1_cy_a_bit0_turns_cy_off(self):
        proc = Processor()
        code = [0x61, 0x8d]
        proc.write_memory(0, code)
        proc.write_psw(Flags.CY)
        proc.write_gp_reg(Registers.A, 0b11111110)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw() & Flags.CY, 0)

    # and1 cy,a.0                 ;61 8d
    def test_61_8d_and1_cy_a_bit0_leaves_cy_on(self):
        proc = Processor()
        code = [0x61, 0x8d]
        proc.write_memory(0, code)
        proc.write_psw(Flags.CY)
        proc.write_gp_reg(Registers.A, 0b00000001)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw() & Flags.CY, Flags.CY)

    # and1 cy,a.1                 ;61 9d
    def test_61_9d_and1_cy_a_bit1_turns_cy_off(self):
        proc = Processor()
        code = [0x61, 0x9d]
        proc.write_memory(0, code)
        proc.write_psw(Flags.CY)
        proc.write_gp_reg(Registers.A, 0b11111101)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw() & Flags.CY, 0)

    # and1 cy,a.1                 ;61 9d
    def test_61_8d_and1_cy_a_bit1_leaves_cy_on(self):
        proc = Processor()
        code = [0x61, 0x9d]
        proc.write_memory(0, code)
        proc.write_psw(Flags.CY)
        proc.write_gp_reg(Registers.A, 0b00000010)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw() & Flags.CY, Flags.CY)

    # and1 cy,a.2                 ;61 ad
    def test_61_ad_and1_cy_a_bit2_turns_cy_off(self):
        proc = Processor()
        code = [0x61, 0xad]
        proc.write_memory(0, code)
        proc.write_psw(Flags.CY)
        proc.write_gp_reg(Registers.A, 0b11111011)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw() & Flags.CY, 0)

    # and1 cy,a.2                 ;61 ad
    def test_61_ad_and1_cy_a_bit2_leaves_cy_on(self):
        proc = Processor()
        code = [0x61, 0xad]
        proc.write_memory(0, code)
        proc.write_psw(Flags.CY)
        proc.write_gp_reg(Registers.A, 0b00000100)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw() & Flags.CY, Flags.CY)

    # and1 cy,a.3                 ;61 bd
    def test_61_bd_and1_cy_a_bit3_turns_cy_off(self):
        proc = Processor()
        code = [0x61, 0xbd]
        proc.write_memory(0, code)
        proc.write_psw(Flags.CY)
        proc.write_gp_reg(Registers.A, 0b11110111)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw() & Flags.CY, 0)

    # and1 cy,a.3                 ;61 bd
    def test_61_bd_and1_cy_a_bit3_leaves_cy_on(self):
        proc = Processor()
        code = [0x61, 0xbd]
        proc.write_memory(0, code)
        proc.write_psw(Flags.CY)
        proc.write_gp_reg(Registers.A, 0b00001000)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw() & Flags.CY, Flags.CY)

    # and1 cy,a.4                 ;61 cd
    def test_61_cd_and1_cy_a_bit4_turns_cy_off(self):
        proc = Processor()
        code = [0x61, 0xcd]
        proc.write_memory(0, code)
        proc.write_psw(Flags.CY)
        proc.write_gp_reg(Registers.A, 0b11101111)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw() & Flags.CY, 0)

    # and1 cy,a.4                 ;61 cd
    def test_61_cd_and1_cy_a_bit4_leaves_cy_on(self):
        proc = Processor()
        code = [0x61, 0xcd]
        proc.write_memory(0, code)
        proc.write_psw(Flags.CY)
        proc.write_gp_reg(Registers.A, 0b00010000)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw() & Flags.CY, Flags.CY)

    # and1 cy,a.5                 ;61 dd
    def test_61_dd_and1_cy_a_bit5_turns_cy_off(self):
        proc = Processor()
        code = [0x61, 0xdd]
        proc.write_memory(0, code)
        proc.write_psw(Flags.CY)
        proc.write_gp_reg(Registers.A, 0b11011111)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw() & Flags.CY, 0)

    # and1 cy,a.4                 ;61 dd
    def test_61_dd_and1_cy_a_bit5_leaves_cy_on(self):
        proc = Processor()
        code = [0x61, 0xdd]
        proc.write_memory(0, code)
        proc.write_psw(Flags.CY)
        proc.write_gp_reg(Registers.A, 0b00100000)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw() & Flags.CY, Flags.CY)

    # and1 cy,a.6                 ;61 ed
    def test_61_ed_and1_cy_a_bit6_turns_cy_off(self):
        proc = Processor()
        code = [0x61, 0xed]
        proc.write_memory(0, code)
        proc.write_psw(0xFF)
        proc.write_gp_reg(Registers.A, 0b10111111)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw() & Flags.CY, 0)

    # and1 cy,a.6                 ;61 ed
    def test_61_ed_and1_cy_a_bit6_leaves_cy_on(self):
        proc = Processor()
        code = [0x61, 0xed]
        proc.write_memory(0, code)
        proc.write_psw(Flags.CY)
        proc.write_gp_reg(Registers.A, 0b01000000)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw() & Flags.CY, Flags.CY)

    # and1 cy,a.7                 ;61 fd
    def test_61_fd_and1_cy_a_bit7_turns_cy_off(self):
        proc = Processor()
        code = [0x61, 0xfd]
        proc.write_memory(0, code)
        proc.write_psw(Flags.CY)
        proc.write_gp_reg(Registers.A, 0b01111111)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw() & Flags.CY, 0)

    # and1 cy,a.7                 ;61 fd
    def test_61_fd_and1_cy_a_bit7_leaves_cy_on(self):
        proc = Processor()
        code = [0x61, 0xfd]
        proc.write_memory(0, code)
        proc.write_psw(Flags.CY)
        proc.write_gp_reg(Registers.A, 0b10000000)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw() & Flags.CY, Flags.CY)

    # and1 cy,[hl].0              ;71 85
    def test_71_85_and1_cy_hl_bit0_turns_cy_off(self):
        proc = Processor()
        code = [0x71, 0x85]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0b11111110
        proc.write_psw(Flags.CY)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw() & Flags.CY, 0)

    # and1 cy,[hl].0              ;71 85
    def test_71_85_and1_cy_hl_bit0_leaves_cy_on(self):
        proc = Processor()
        code = [0x71, 0x85]
        proc.write_memory(0, code)
        proc.write_psw(Flags.CY)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0b00000001
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw() & Flags.CY, Flags.CY)

    # and1 cy,[hl].1              ;71 95
    def test_71_95_and1_cy_hl_bit1_turns_cy_off(self):
        proc = Processor()
        code = [0x71, 0x95]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0b11111101
        proc.write_psw(Flags.CY)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw() & Flags.CY, 0)

    # and1 cy,[hl].1              ;71 95
    def test_71_95_and1_cy_hl_bit1_leaves_cy_on(self):
        proc = Processor()
        code = [0x71, 0x95]
        proc.write_memory(0, code)
        proc.write_psw(Flags.CY)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0b00000010
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw() & Flags.CY, Flags.CY)

    # and1 cy,[hl].2              ;71 a5
    def test_71_a5_and1_cy_hl_bit2_turns_cy_off(self):
        proc = Processor()
        code = [0x71, 0xa5]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0b11111011
        proc.write_psw(Flags.CY)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw() & Flags.CY, 0)

    # and1 cy,[hl].2              ;71 a5
    def test_71_a5_and1_cy_hl_bit2_leaves_cy_on(self):
        proc = Processor()
        code = [0x71, 0xa5]
        proc.write_memory(0, code)
        proc.write_psw(Flags.CY)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0b00000100
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw() & Flags.CY, Flags.CY)

    # and1 cy,[hl].3              ;71 b5
    def test_71_b5_and1_cy_hl_bit3_turns_cy_off(self):
        proc = Processor()
        code = [0x71, 0xb5]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0b11110111
        proc.write_psw(Flags.CY)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw() & Flags.CY, 0)

    # and1 cy,[hl].3              ;71 b5
    def test_71_b5_and1_cy_hl_bit3_leaves_cy_on(self):
        proc = Processor()
        code = [0x71, 0xb5]
        proc.write_memory(0, code)
        proc.write_psw(Flags.CY)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0b00001000
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw() & Flags.CY, Flags.CY)

    # and1 cy,[hl].4              ;71 c5
    def test_71_c5_and1_cy_hl_bit4_turns_cy_off(self):
        proc = Processor()
        code = [0x71, 0xc5]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0b11101111
        proc.write_psw(Flags.CY)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw() & Flags.CY, 0)

    # and1 cy,[hl].4              ;71 c5
    def test_71_c5_and1_cy_hl_bit4_leaves_cy_on(self):
        proc = Processor()
        code = [0x71, 0xc5]
        proc.write_memory(0, code)
        proc.write_psw(Flags.CY)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0b00010000
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw() & Flags.CY, Flags.CY)

    # and1 cy,[hl].5              ;71 d5
    def test_71_d5_and1_cy_hl_bit5_turns_cy_off(self):
        proc = Processor()
        code = [0x71, 0xd5]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0b11011111
        proc.write_psw(Flags.CY)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw() & Flags.CY, 0)

    # and1 cy,[hl].5              ;71 d5
    def test_71_d5_and1_cy_hl_bit5_leaves_cy_on(self):
        proc = Processor()
        code = [0x71, 0xd5]
        proc.write_memory(0, code)
        proc.write_psw(Flags.CY)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0b00100000
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw() & Flags.CY, Flags.CY)

    # and1 cy,[hl].6              ;71 e5
    def test_71_e5_and1_cy_hl_bit6_turns_cy_off(self):
        proc = Processor()
        code = [0x71, 0xe5]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0b10111111
        proc.write_psw(Flags.CY)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw() & Flags.CY, 0)

    # and1 cy,[hl].6              ;71 e5
    def test_71_e5_and1_cy_hl_bit6_leaves_cy_on(self):
        proc = Processor()
        code = [0x71, 0xe5]
        proc.write_memory(0, code)
        proc.write_psw(Flags.CY)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0b01000000
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw() & Flags.CY, Flags.CY)

    # and1 cy,[hl].7              ;71 f5
    def test_71_f5_and1_cy_hl_bit7_turns_cy_off(self):
        proc = Processor()
        code = [0x71, 0xf5]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0b01111111
        proc.write_psw(Flags.CY)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw() & Flags.CY, 0)

    # and1 cy,[hl].7              ;71 f5
    def test_71_f5_and1_cy_hl_bit7_leaves_cy_on(self):
        proc = Processor()
        code = [0x71, 0xf5]
        proc.write_memory(0, code)
        proc.write_psw(Flags.CY)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0b10000000
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw() & Flags.CY, Flags.CY)

    # and1 cy,0fffeh.0            ;71 0d fe       sfr
    def test_71_0d_and1_cy_sfr_bit0_turns_cy_off(self):
        proc = Processor()
        code = [0x71, 0x0d, 0xfe]
        proc.write_memory(0, code)
        proc.memory[0xfffe] = 0b11111110
        proc.write_psw(Flags.CY)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw() & Flags.CY, 0)

    # and1 cy,0fffeh.0            ;71 0d fe       sfr
    def test_71_0d_and1_cy_sfr_bit0_leaves_cy_on(self):
        proc = Processor()
        code = [0x71, 0x0d, 0xfe]
        proc.write_memory(0, code)
        proc.write_psw(Flags.CY)
        proc.memory[0xfffe] = 0b00000001
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw() & Flags.CY, Flags.CY)

    # and1 cy,0fffeh.1            ;71 1d fe       sfr
    def test_71_1d_and1_cy_sfr_bit1_turns_cy_off(self):
        proc = Processor()
        code = [0x71, 0x1d, 0xfe]
        proc.write_memory(0, code)
        proc.memory[0xfffe] = 0b11111101
        proc.write_psw(Flags.CY)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw() & Flags.CY, 0)

    # and1 cy,0fffeh.1            ;71 1d fe       sfr
    def test_71_1d_and1_cy_sfr_bit1_leaves_cy_on(self):
        proc = Processor()
        code = [0x71, 0x1d, 0xfe]
        proc.write_memory(0, code)
        proc.write_psw(Flags.CY)
        proc.memory[0xfffe] = 0b00000010
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw() & Flags.CY, Flags.CY)

    # and1 cy,0fffeh.2            ;71 2d fe       sfr
    def test_71_2d_and1_cy_sfr_bit2_turns_cy_off(self):
        proc = Processor()
        code = [0x71, 0x2d, 0xfe]
        proc.write_memory(0, code)
        proc.memory[0xfffe] = 0b11111011
        proc.write_psw(Flags.CY)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw() & Flags.CY, 0)

    # and1 cy,0fffeh.2            ;71 2d fe       sfr
    def test_71_2d_and1_cy_sfr_bit2_leaves_cy_on(self):
        proc = Processor()
        code = [0x71, 0x2d, 0xfe]
        proc.write_memory(0, code)
        proc.write_psw(Flags.CY)
        proc.memory[0xfffe] = 0b00000100
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw() & Flags.CY, Flags.CY)

    # and1 cy,0fffeh.3            ;71 3d fe       sfr
    def test_71_3d_and1_cy_sfr_bit3_turns_cy_off(self):
        proc = Processor()
        code = [0x71, 0x3d, 0xfe]
        proc.write_memory(0, code)
        proc.memory[0xfffe] = 0b11110111
        proc.write_psw(Flags.CY)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw() & Flags.CY, 0)

    # and1 cy,0fffeh.3            ;71 3d fe       sfr
    def test_71_3d_and1_cy_sfr_bit3_leaves_cy_on(self):
        proc = Processor()
        code = [0x71, 0x3d, 0xfe]
        proc.write_memory(0, code)
        proc.write_psw(Flags.CY)
        proc.memory[0xfffe] = 0b00001000
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw() & Flags.CY, Flags.CY)

    # and1 cy,0fffeh.4            ;71 4d fe       sfr
    def test_71_4d_and1_cy_sfr_bit4_turns_cy_off(self):
        proc = Processor()
        code = [0x71, 0x4d, 0xfe]
        proc.write_memory(0, code)
        proc.memory[0xfffe] = 0b11101111
        proc.write_psw(Flags.CY)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw() & Flags.CY, 0)

    # and1 cy,0fffeh.4            ;71 4d fe       sfr
    def test_71_4d_and1_cy_sfr_bit4_leaves_cy_on(self):
        proc = Processor()
        code = [0x71, 0x4d, 0xfe]
        proc.write_memory(0, code)
        proc.write_psw(Flags.CY)
        proc.memory[0xfffe] = 0b00010000
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw() & Flags.CY, Flags.CY)

    # and1 cy,0fffeh.5            ;71 5d fe       sfr
    def test_71_5d_and1_cy_sfr_bit5_turns_cy_off(self):
        proc = Processor()
        code = [0x71, 0x5d, 0xfe]
        proc.write_memory(0, code)
        proc.memory[0xfffe] = 0b11011111
        proc.write_psw(Flags.CY)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw() & Flags.CY, 0)

    # and1 cy,0fffeh.5            ;71 5d fe       sfr
    def test_71_5d_and1_cy_sfr_bit5_leaves_cy_on(self):
        proc = Processor()
        code = [0x71, 0x5d, 0xfe]
        proc.write_memory(0, code)
        proc.write_psw(Flags.CY)
        proc.memory[0xfffe] = 0b00100000
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw() & Flags.CY, Flags.CY)

    # and1 cy,0fffeh.6            ;71 6d fe       sfr
    def test_71_6d_and1_cy_sfr_bit6_turns_cy_off(self):
        proc = Processor()
        code = [0x71, 0x6d, 0xfe]
        proc.write_memory(0, code)
        proc.memory[0xfffe] = 0b10111111
        proc.write_psw(Flags.CY)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw() & Flags.CY, 0)

    # and1 cy,0fffeh.6            ;71 6d fe       sfr
    def test_71_6d_and1_cy_sfr_bit6_leaves_cy_on(self):
        proc = Processor()
        code = [0x71, 0x6d, 0xfe]
        proc.write_memory(0, code)
        proc.write_psw(Flags.CY)
        proc.memory[0xfffe] = 0b01000000
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw() & Flags.CY, Flags.CY)

    # and1 cy,0fffeh.7            ;71 7d fe       sfr
    def test_71_7d_and1_cy_sfr_bit7_turns_cy_off(self):
        proc = Processor()
        code = [0x71, 0x7d, 0xfe]
        proc.write_memory(0, code)
        proc.memory[0xfffe] = 0b01111111
        proc.write_psw(Flags.CY)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw() & Flags.CY, 0)

    # and1 cy,0fffeh.7            ;71 7d fe       sfr
    def test_71_7d_and1_cy_sfr_bit7_leaves_cy_on(self):
        proc = Processor()
        code = [0x71, 0x7d, 0xfe]
        proc.write_memory(0, code)
        proc.write_psw(Flags.CY)
        proc.memory[0xfffe] = 0b10000000
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw() & Flags.CY, Flags.CY)

    # and1 cy,0fe20h.0            ;71 05 20       saddr
    def test_71_05_and1_cy_saddr_bit0_turns_cy_off(self):
        proc = Processor()
        code = [0x71, 0x05, 0x20]
        proc.write_memory(0, code)
        proc.memory[0xfe20] = 0b11111110
        proc.write_psw(Flags.CY)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw() & Flags.CY, 0)

    # and1 cy,0fe20h.0            ;71 05 20       saddr
    def test_71_05_and1_cy_saddr_bit0_leaves_cy_on(self):
        proc = Processor()
        code = [0x71, 0x05, 0x20]
        proc.write_memory(0, code)
        proc.write_psw(Flags.CY)
        proc.memory[0xfe20] = 0b00000001
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw() & Flags.CY, Flags.CY)

    # and1 cy,0fe20h.1            ;71 15 20       saddr
    def test_71_15_and1_cy_saddr_bit1_turns_cy_off(self):
        proc = Processor()
        code = [0x71, 0x15, 0x20]
        proc.write_memory(0, code)
        proc.memory[0xfe20] = 0b11111101
        proc.write_psw(Flags.CY)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw() & Flags.CY, 0)

    # and1 cy,0fe20h.1            ;71 15 20       saddr
    def test_71_15_and1_cy_saddr_bit1_leaves_cy_on(self):
        proc = Processor()
        code = [0x71, 0x15, 0x20]
        proc.write_memory(0, code)
        proc.write_psw(Flags.CY)
        proc.memory[0xfe20] = 0b00000010
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw() & Flags.CY, Flags.CY)

    # and1 cy,0fe20h.2            ;71 25 20       saddr
    def test_71_25_and1_cy_saddr_bit2_turns_cy_off(self):
        proc = Processor()
        code = [0x71, 0x25, 0x20]
        proc.write_memory(0, code)
        proc.memory[0xfe20] = 0b11111011
        proc.write_psw(Flags.CY)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw() & Flags.CY, 0)

    # and1 cy,0fe20h.2            ;71 25 20       saddr
    def test_71_25_and1_cy_saddr_bit2_leaves_cy_on(self):
        proc = Processor()
        code = [0x71, 0x25, 0x20]
        proc.write_memory(0, code)
        proc.write_psw(Flags.CY)
        proc.memory[0xfe20] = 0b00000100
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw() & Flags.CY, Flags.CY)

    # and1 cy,0fe20h.3            ;71 35 20       saddr
    def test_71_35_and1_cy_saddr_bit3_turns_cy_off(self):
        proc = Processor()
        code = [0x71, 0x35, 0x20]
        proc.write_memory(0, code)
        proc.memory[0xfe20] = 0b11110111
        proc.write_psw(Flags.CY)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw() & Flags.CY, 0)

    # and1 cy,0fe20h.3            ;71 35 20       saddr
    def test_71_35_and1_cy_saddr_bit3_leaves_cy_on(self):
        proc = Processor()
        code = [0x71, 0x35, 0x20]
        proc.write_memory(0, code)
        proc.write_psw(Flags.CY)
        proc.memory[0xfe20] = 0b00001000
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw() & Flags.CY, Flags.CY)

    # and1 cy,0fe20h.4            ;71 45 20       saddr
    def test_71_45_and1_cy_saddr_bit4_turns_cy_off(self):
        proc = Processor()
        code = [0x71, 0x45, 0x20]
        proc.write_memory(0, code)
        proc.memory[0xfe20] = 0b11101111
        proc.write_psw(Flags.CY)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw() & Flags.CY, 0)

    # and1 cy,0fe20h.4            ;71 45 20       saddr
    def test_71_45_and1_cy_saddr_bit4_leaves_cy_on(self):
        proc = Processor()
        code = [0x71, 0x45, 0x20]
        proc.write_memory(0, code)
        proc.write_psw(Flags.CY)
        proc.memory[0xfe20] = 0b00010000
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw() & Flags.CY, Flags.CY)

    # and1 cy,0fe20h.5            ;71 55 20       saddr
    def test_71_55_and1_cy_saddr_bit5_turns_cy_off(self):
        proc = Processor()
        code = [0x71, 0x55, 0x20]
        proc.write_memory(0, code)
        proc.memory[0xfe20] = 0b11011111
        proc.write_psw(Flags.CY)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw() & Flags.CY, 0)

    # and1 cy,0fe20h.5            ;71 55 20       saddr
    def test_71_55_and1_cy_saddr_bit5_leaves_cy_on(self):
        proc = Processor()
        code = [0x71, 0x55, 0x20]
        proc.write_memory(0, code)
        proc.write_psw(Flags.CY)
        proc.memory[0xfe20] = 0b00100000
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw() & Flags.CY, Flags.CY)

    # and1 cy,0fe20h.6            ;71 65 20       saddr
    def test_71_65_and1_cy_saddr_bit6_turns_cy_off(self):
        proc = Processor()
        code = [0x71, 0x65, 0x20]
        proc.write_memory(0, code)
        proc.memory[0xfe20] = 0b10111111
        proc.write_psw(Flags.CY)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw() & Flags.CY, 0)

    # and1 cy,0fe20h.6            ;71 65 20       saddr
    def test_71_65_and1_cy_saddr_bit6_leaves_cy_on(self):
        proc = Processor()
        code = [0x71, 0x65, 0x20]
        proc.write_memory(0, code)
        proc.write_psw(Flags.CY)
        proc.memory[0xfe20] = 0b01000000
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw() & Flags.CY, Flags.CY)

    # and1 cy,0fe20h.7            ;71 75 20       saddr
    def test_71_75_and1_cy_saddr_bit7_turns_cy_off(self):
        proc = Processor()
        code = [0x71, 0x75, 0x20]
        proc.write_memory(0, code)
        proc.memory[0xfe20] = 0b01111111
        proc.write_psw(Flags.CY)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw() & Flags.CY, 0)

    # and1 cy,0fe20h.7            ;71 75 20       saddr
    def test_71_75_and1_cy_saddr_bit7_leaves_cy_on(self):
        proc = Processor()
        code = [0x71, 0x75, 0x20]
        proc.write_memory(0, code)
        proc.write_psw(Flags.CY)
        proc.memory[0xfe20] = 0b10000000
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw() & Flags.CY, Flags.CY)

    # and1 cy,psw.0               ;71 05 1e
    def test_71_05_and0_cy_psw_bit0_unchanged_since_cy_is_bit0(self):
        proc = Processor()
        code = [0x71, 0x05, 0x1e]
        proc.write_memory(0, code)
        proc.write_psw(Flags.CY)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), Flags.CY)

    # and1 cy,psw.0               ;71 05 1e
    def test_71_05_and1_cy_psw_bit0_unchanged_since_cy_is_bit0(self):
        proc = Processor()
        code = [0x71, 0x05, 0x1e]
        proc.write_memory(0, code)
        proc.write_psw(0)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0)

    # and1 cy,psw.1               ;71 15 1e
    def test_71_15_and1_cy_psw_bit1_turns_cy_off(self):
        proc = Processor()
        code = [0x71, 0x15, 0x1e]
        proc.write_memory(0, code)
        proc.write_psw(Flags.CY) # carry on, bit 1 off
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0)

    # and1 cy,psw.1               ;71 15 1e
    def test_71_15_and1_cy_psw_bit1_leaves_cy_on(self):
        proc = Processor()
        code = [0x71, 0x15, 0x1e]
        proc.write_memory(0, code)
        proc.write_psw(0b00000011) # carry on, bit 1 on
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0b00000011)

    # and1 cy,psw.2               ;71 25 1e
    def test_71_25_and1_cy_psw_bit2_turns_cy_off(self):
        proc = Processor()
        code = [0x71, 0x25, 0x1e]
        proc.write_memory(0, code)
        proc.write_psw(Flags.CY) # carry on, bit 2 off
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0)

    # and1 cy,psw.2               ;71 25 1e
    def test_71_25_and1_cy_psw_bit2_leaves_cy_on(self):
        proc = Processor()
        code = [0x71, 0x25, 0x1e]
        proc.write_memory(0, code)
        proc.write_psw(0b00000101) # carry on, bit 2 on
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0b00000101)

    # and1 cy,psw.3               ;71 35 1e
    def test_71_35_and1_cy_psw_bit3_turns_cy_off(self):
        proc = Processor()
        code = [0x71, 0x35, 0x1e]
        proc.write_memory(0, code)
        proc.write_psw(Flags.CY) # carry on, bit 3 off
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0)

    # and1 cy,psw.3               ;71 35 1e
    def test_71_35_and1_cy_psw_bit3_leaves_cy_on(self):
        proc = Processor()
        code = [0x71, 0x35, 0x1e]
        proc.write_memory(0, code)
        proc.write_psw(0b00001001) # carry on, bit 3 on
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0b00001001)

    # and1 cy,psw.4               ;71 45 1e
    def test_71_45_and1_cy_psw_bit4_turns_cy_off(self):
        proc = Processor()
        code = [0x71, 0x45, 0x1e]
        proc.write_memory(0, code)
        proc.write_psw(Flags.CY) # carry on, bit 4 off
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0)

    # and1 cy,psw.4               ;71 45 1e
    def test_71_45_and1_cy_psw_bit4_leaves_cy_on(self):
        proc = Processor()
        code = [0x71, 0x45, 0x1e]
        proc.write_memory(0, code)
        proc.write_psw(0b00010001) # carry on, bit 4 on
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0b00010001)

    # and1 cy,psw.5               ;71 55 1e
    def test_71_55_and1_cy_psw_bit5_turns_cy_off(self):
        proc = Processor()
        code = [0x71, 0x55, 0x1e]
        proc.write_memory(0, code)
        proc.write_psw(Flags.CY) # carry on, bit 5 off
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0)

    # and1 cy,psw.5               ;71 55 1e
    def test_71_55_and1_cy_psw_bit5_leaves_cy_on(self):
        proc = Processor()
        code = [0x71, 0x55, 0x1e]
        proc.write_memory(0, code)
        proc.write_psw(0b00100001) # carry on, bit 5 on
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0b00100001)

    # and1 cy,psw.6               ;71 65 1e
    def test_71_65_and1_cy_psw_bit6_turns_cy_off(self):
        proc = Processor()
        code = [0x71, 0x65, 0x1e]
        proc.write_memory(0, code)
        proc.write_psw(Flags.CY) # carry on, bit 6 off
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0)

    # and1 cy,psw.6               ;71 65 1e
    def test_71_65_and1_cy_psw_bit6_leaves_cy_on(self):
        proc = Processor()
        code = [0x71, 0x65, 0x1e]
        proc.write_memory(0, code)
        proc.write_psw(0b01000001) # carry on, bit 6 on
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0b01000001)

    # and1 cy,psw.7               ;71 75 1e
    def test_71_75_and1_cy_psw_bit7_turns_cy_off(self):
        proc = Processor()
        code = [0x71, 0x75, 0x1e]
        proc.write_memory(0, code)
        proc.write_psw(Flags.CY) # carry on, bit 7 off
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0)

    # and1 cy,psw.7               ;71 75 1e
    def test_71_75_and1_cy_psw_bit7_leaves_cy_on(self):
        proc = Processor()
        code = [0x71, 0x75, 0x1e]
        proc.write_memory(0, code)
        proc.write_psw(0b10000001) # carry on, bit 7 on
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0b10000001)

    # or1 cy,a.0                  ;61 8e
    def test_61_8e_or1_cy_a_bit0_leaves_cy_off(self):
        proc = Processor()
        code = [0x61, 0x8e]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0b00000000)
        proc.write_psw(0) # carry off
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0) # unchanged

    # or1 cy,a.0                  ;61 8e
    def test_61_8e_or1_cy_a_bit0_leaves_cy_on(self):
        proc = Processor()
        code = [0x61, 0x8e]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0b00000000)
        proc.write_psw(Flags.CY)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), Flags.CY) # unchanged

    # or1 cy,a.0                  ;61 8e
    def test_61_8e_or1_cy_a_bit0_turns_cy_on(self):
        proc = Processor()
        code = [0x61, 0x8e]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0b00000001)
        proc.write_psw(0) # carry off
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), Flags.CY)

    # or1 cy,a.0                  ;61 8e
    def test_61_8e_or1_cy_a_bit0_turns_cy_on_preserves_other_bits(self):
        proc = Processor()
        code = [0x61, 0x8e]
        proc.write_memory(0, code)
        proc.write_psw(0b10101010) # carry off
        proc.write_gp_reg(Registers.A, 0b00000001)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0b10101011) # carry on

    # or1 cy,a.1                  ;61 9e
    def test_61_9e_or1_cy_a_bit1_turns_cy_on(self):
        proc = Processor()
        code = [0x61, 0x9e]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0b00000010)
        proc.write_psw(0) # carry off
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), Flags.CY)

    # or1 cy,a.2                  ;61 ae
    def test_61_ae_or1_cy_a_bit2_turns_cy_on(self):
        proc = Processor()
        code = [0x61, 0xae]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0b00000100)
        proc.write_psw(0) # carry off
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), Flags.CY)

    # or1 cy,a.3                  ;61 be
    def test_61_be_or1_cy_a_bit3_turns_cy_on(self):
        proc = Processor()
        code = [0x61, 0xbe]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0b00001000)
        proc.write_psw(0) # carry off
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), Flags.CY)

    # or1 cy,a.4                  ;61 ce
    def test_61_ce_or1_cy_a_bit4_turns_cy_on(self):
        proc = Processor()
        code = [0x61, 0xce]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0b00010000)
        proc.write_psw(0) # carry off
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), Flags.CY)

    # or1 cy,a.5                  ;61 de
    def test_61_de_or1_cy_a_bit5_turns_cy_on(self):
        proc = Processor()
        code = [0x61, 0xde]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0b00100000)
        proc.write_psw(0) # carry off
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), Flags.CY)

    # or1 cy,a.6                  ;61 ee
    def test_61_ee_or1_cy_a_bit6_turns_cy_on(self):
        proc = Processor()
        code = [0x61, 0xee]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0b01000000)
        proc.write_psw(0) # carry off
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), Flags.CY)

    # or1 cy,a.7                  ;61 fe
    def test_61_fe_or1_cy_a_bit7_turns_cy_on(self):
        proc = Processor()
        code = [0x61, 0xfe]
        proc.write_memory(0, code)
        proc.write_gp_reg(Registers.A, 0b10000000)
        proc.write_psw(0) # carry off
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), Flags.CY)

    # or1 cy,0fffeh.0             ;71 0e fe       sfr
    def test_71_0e_or1_cy_sfr_bit0_turns_cy_on(self):
        proc = Processor()
        code = [0x71, 0x0e, 0xfe]
        proc.write_memory(0, code)
        proc.memory[0xfffe] = 0b00000001
        proc.write_psw(0) # carry off
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), Flags.CY)

    # or1 cy,0fffeh.1             ;71 1e fe       sfr
    def test_71_1e_or1_cy_sfr_bit1_turns_cy_on(self):
        proc = Processor()
        code = [0x71, 0x1e, 0xfe]
        proc.write_memory(0, code)
        proc.memory[0xfffe] = 0b00000010
        proc.write_psw(0) # carry off
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), Flags.CY)

    # or1 cy,0fffeh.2             ;71 2e fe       sfr
    def test_71_2e_or1_cy_sfr_bit2_turns_cy_on(self):
        proc = Processor()
        code = [0x71, 0x2e, 0xfe]
        proc.write_memory(0, code)
        proc.memory[0xfffe] = 0b00000100
        proc.write_psw(0) # carry off
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), Flags.CY)

    # or1 cy,0fffeh.3             ;71 3e fe       sfr
    def test_71_3e_or1_cy_sfr_bit3_turns_cy_on(self):
        proc = Processor()
        code = [0x71, 0x3e, 0xfe]
        proc.write_memory(0, code)
        proc.memory[0xfffe] = 0b00001000
        proc.write_psw(0) # carry off
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), Flags.CY)

    # or1 cy,0fffeh.4             ;71 4e fe       sfr
    def test_71_4e_or1_cy_sfr_bit4_turns_cy_on(self):
        proc = Processor()
        code = [0x71, 0x4e, 0xfe]
        proc.write_memory(0, code)
        proc.memory[0xfffe] = 0b00010000
        proc.write_psw(0) # carry off
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), Flags.CY)

    # or1 cy,0fffeh.5             ;71 5e fe       sfr
    def test_71_5e_or1_cy_sfr_bit5_turns_cy_on(self):
        proc = Processor()
        code = [0x71, 0x5e, 0xfe]
        proc.write_memory(0, code)
        proc.memory[0xfffe] = 0b00100000
        proc.write_psw(0) # carry off
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), Flags.CY)

    # or1 cy,0fffeh.6             ;71 6e fe       sfr
    def test_71_6e_or1_cy_sfr_bit6_turns_cy_on(self):
        proc = Processor()
        code = [0x71, 0x6e, 0xfe]
        proc.write_memory(0, code)
        proc.memory[0xfffe] = 0b01000000
        proc.write_psw(0) # carry off
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), Flags.CY)

    # or1 cy,0fffeh.7             ;71 7e fe       sfr
    def test_71_7e_or1_cy_sfr_bit7_turns_cy_on(self):
        proc = Processor()
        code = [0x71, 0x7e, 0xfe]
        proc.write_memory(0, code)
        proc.memory[0xfffe] = 0b10000000
        proc.write_psw(0) # carry off
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), Flags.CY)

    # or1 cy,[hl].0               ;71 86
    def test_71_86_or1_cy_hl_bit0_turns_cy_on(self):
        proc = Processor()
        code = [0x71, 0x86]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0b00000001
        proc.write_psw(0) # carry off
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), Flags.CY)

    # or1 cy,[hl].1               ;71 96
    def test_71_96_or1_cy_hl_bit1_turns_cy_on(self):
        proc = Processor()
        code = [0x71, 0x96]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0b00000010
        proc.write_psw(0) # carry off
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), Flags.CY)

    # or1 cy,[hl].2               ;71 a6
    def test_71_a6_or1_cy_hl_bit2_turns_cy_on(self):
        proc = Processor()
        code = [0x71, 0xa6]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0b00000100
        proc.write_psw(0) # carry off
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), Flags.CY)

    # or1 cy,[hl].3               ;71 b6
    def test_71_b6_or1_cy_hl_bit3_turns_cy_on(self):
        proc = Processor()
        code = [0x71, 0xb6]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0b00001000
        proc.write_psw(0) # carry off
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), Flags.CY)

    # or1 cy,[hl].4               ;71 c6
    def test_71_c6_or1_cy_hl_bit4_turns_cy_on(self):
        proc = Processor()
        code = [0x71, 0xc6]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0b00010000
        proc.write_psw(0) # carry off
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), Flags.CY)

    # or1 cy,[hl].5               ;71 d6
    def test_71_d6_or1_cy_hl_bit5_turns_cy_on(self):
        proc = Processor()
        code = [0x71, 0xd6]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0b00100000
        proc.write_psw(0) # carry off
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), Flags.CY)

    # or1 cy,[hl].6               ;71 e6
    def test_71_e6_or1_cy_hl_bit6_turns_cy_on(self):
        proc = Processor()
        code = [0x71, 0xe6]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0b01000000
        proc.write_psw(0) # carry off
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), Flags.CY)

    # or1 cy,[hl].7               ;71 f6
    def test_71_f6_or1_cy_hl_bit6_turns_cy_on(self):
        proc = Processor()
        code = [0x71, 0xf6]
        proc.write_memory(0, code)
        proc.write_gp_regpair(RegisterPairs.HL, 0xabcd)
        proc.memory[0xabcd] = 0b10000000
        proc.write_psw(0) # carry off
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), Flags.CY)

    # or1 cy,0fe20h.0             ;71 06 20       saddr
    def test_71_06_or1_cy_saddr_bit0_turns_cy_on(self):
        proc = Processor()
        code = [0x71, 0x06, 0x20]
        proc.write_memory(0, code)
        proc.memory[0xfe20] = 0b00000001
        proc.write_psw(0) # carry off
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), Flags.CY)

    # or1 cy,0fe20h.1             ;71 16 20       saddr
    def test_71_16_or1_cy_saddr_bit1_turns_cy_on(self):
        proc = Processor()
        code = [0x71, 0x16, 0x20]
        proc.write_memory(0, code)
        proc.memory[0xfe20] = 0b00000010
        proc.write_psw(0) # carry off
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), Flags.CY)

    # or1 cy,0fe20h.2             ;71 26 20       saddr
    def test_71_26_or1_cy_saddr_bit2_turns_cy_on(self):
        proc = Processor()
        code = [0x71, 0x26, 0x20]
        proc.write_memory(0, code)
        proc.memory[0xfe20] = 0b00000100
        proc.write_psw(0) # carry off
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), Flags.CY)

    # or1 cy,0fe20h.3             ;71 36 20       saddr
    def test_71_36_or1_cy_saddr_bit3_turns_cy_on(self):
        proc = Processor()
        code = [0x71, 0x36, 0x20]
        proc.write_memory(0, code)
        proc.memory[0xfe20] = 0b00001000
        proc.write_psw(0) # carry off
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), Flags.CY)

    # or1 cy,0fe20h.4             ;71 46 20       saddr
    def test_71_46_or1_cy_saddr_bit4_turns_cy_on(self):
        proc = Processor()
        code = [0x71, 0x46, 0x20]
        proc.write_memory(0, code)
        proc.memory[0xfe20] = 0b00010000
        proc.write_psw(0) # carry off
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), Flags.CY)

    # or1 cy,0fe20h.5             ;71 56 20       saddr
    def test_71_56_or1_cy_saddr_bit5_turns_cy_on(self):
        proc = Processor()
        code = [0x71, 0x56, 0x20]
        proc.write_memory(0, code)
        proc.memory[0xfe20] = 0b00100000
        proc.write_psw(0) # carry off
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), Flags.CY)

    # or1 cy,0fe20h.6             ;71 66 20       saddr
    def test_71_66_or1_cy_saddr_bit6_turns_cy_on(self):
        proc = Processor()
        code = [0x71, 0x66, 0x20]
        proc.write_memory(0, code)
        proc.memory[0xfe20] = 0b01000000
        proc.write_psw(0) # carry off
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), Flags.CY)

    # or1 cy,0fe20h.7             ;71 76 20       saddr
    def test_71_76_or1_cy_saddr_bit7_turns_cy_on(self):
        proc = Processor()
        code = [0x71, 0x76, 0x20]
        proc.write_memory(0, code)
        proc.memory[0xfe20] = 0b10000000
        proc.write_psw(0) # carry off
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), Flags.CY)

    # or1 cy,psw.0                ;71 06 1e
    def test_71_06_or1_cy_psw_bit0_leaves_cy_off_since_cy_is_bit0(self):
        proc = Processor()
        code = [0x71, 0x06, 0x1e]
        proc.write_memory(0, code)
        proc.write_psw(0)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0)

    # or1 cy,psw.0                ;71 06 1e
    def test_71_06_or1_cy_psw_bit0_leaves_cy_on_since_cy_is_bit0(self):
        proc = Processor()
        code = [0x71, 0x06, 0x1e]
        proc.write_memory(0, code)
        proc.write_psw(0b00000001)
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0b00000001)

    # or1 cy,psw.1                ;71 16 1e
    def test_71_16_or1_cy_psw_bit1_turns_cy_on(self):
        proc = Processor()
        code = [0x71, 0x16, 0x1e]
        proc.write_memory(0, code)
        proc.write_psw(0b00000010) # bit 1 on, carry off
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0b00000011) # bit 1 on, carry on

    # or1 cy,psw.2                ;71 26 1e
    def test_71_16_or1_cy_psw_bit2_turns_cy_on(self):
        proc = Processor()
        code = [0x71, 0x26, 0x1e]
        proc.write_memory(0, code)
        proc.write_psw(0b00000100) # bit 2 on, carry off
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0b00000101) # bit 2 on, carry on

    # or1 cy,psw.3                ;71 36 1e
    def test_71_36_or1_cy_psw_bit3_turns_cy_on(self):
        proc = Processor()
        code = [0x71, 0x36, 0x1e]
        proc.write_memory(0, code)
        proc.write_psw(0b00001000) # bit 3 on, carry off
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0b00001001) # bit 3 on, carry on

    # or1 cy,psw.4                ;71 46 1e
    def test_71_46_or1_cy_psw_bit4_turns_cy_on(self):
        proc = Processor()
        code = [0x71, 0x46, 0x1e]
        proc.write_memory(0, code)
        proc.write_psw(0b00010000) # bit 4 on, carry off
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0b00010001) # bit 4 on, carry on

    # or1 cy,psw.5                ;71 56 1e
    def test_71_56_or1_cy_psw_bit5_turns_cy_on(self):
        proc = Processor()
        code = [0x71, 0x56, 0x1e]
        proc.write_memory(0, code)
        proc.write_psw(0b00100000) # bit 5 on, carry off
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0b00100001) # bit 5 on, carry on

    # or1 cy,psw.6                ;71 66 1e
    def test_71_66_or1_cy_psw_bit6_turns_cy_on(self):
        proc = Processor()
        code = [0x71, 0x66, 0x1e]
        proc.write_memory(0, code)
        proc.write_psw(0b01000000) # bit 6 on, carry off
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0b01000001) # bit 6 on, carry on

    # or1 cy,psw.7                ;71 76 1e
    def test_71_76_or1_cy_psw_bit7_turns_cy_on(self):
        proc = Processor()
        code = [0x71, 0x76, 0x1e]
        proc.write_memory(0, code)
        proc.write_psw(0b10000000) # bit 7 on, carry off
        proc.step()
        self.assertEqual(proc.pc, len(code))
        self.assertEqual(proc.read_psw(), 0b10000001) # bit 7 on, carry on


def test_suite():
    return unittest.findTestCases(sys.modules[__name__])

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
