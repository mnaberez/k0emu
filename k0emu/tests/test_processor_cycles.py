import unittest
from k0emu.devices import MemoryDevice
from k0emu.processor import Processor, Registers, RegisterPairs, Flags


def _make_processor():
    proc = Processor()
    mem = MemoryDevice("test_memory", size=0x10000)
    proc.bus.add_device(mem, (0x0000, 0xFFFF))
    return proc


class CycleCountTests(unittest.TestCase):
    """Tests for instruction cycle counting.

    Cycle counts are from the uPD78F0833Y subseries user's manual
    (U13892EJ2V0UM00), Chapter 18 "Instruction Set", Operation List.

    Two clock columns exist:
      Note 1: internal high-speed RAM access (FB00h-FEFFh) or no data access
      Note 2: access to any other area (SFR at FF00h+, ROM, etc.)

    Tests verify both columns where applicable.
    """

    # reset

    def test_reset_clears_cycle_count(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x00])  # nop
        proc.step()
        self.assertNotEqual(proc.total_cycles, 0)
        proc.reset()
        self.assertEqual(proc.total_cycles, 0)

    def test_cycles_accumulate(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x00, 0x00, 0x00])  # 3x nop
        proc.step()
        proc.step()
        proc.step()
        self.assertEqual(proc.total_cycles, 6)

    # nop                             ;00
    def test_cycles_00_nop(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x00])
        proc.step()
        self.assertEqual(proc.total_cycles, 2)

    # not1 cy                         ;01
    def test_cycles_01_not1_cy(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x01])
        proc.step()
        self.assertEqual(proc.total_cycles, 2)

    # movw ax,!addr16p               ;02 (internal ram)
    def test_cycles_02_movw_ax_addr16p_internal_ram(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x02, 0x00, 0xFE])
        proc.step()
        self.assertEqual(proc.total_cycles, 10)  # addr=FE00 (internal RAM)

    # movw ax,!addr16p               ;02 (not internal ram)
    def test_cycles_02_movw_ax_addr16p_not_internal_ram(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x02, 0x00, 0x10])
        proc.step()
        self.assertEqual(proc.total_cycles, 12)  # addr=1000 (ROM)

    # movw !addr16p,ax               ;03 (internal ram)
    def test_cycles_03_movw_addr16p_ax_internal_ram(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x03, 0x00, 0xFE])
        proc.step()
        self.assertEqual(proc.total_cycles, 10)

    # movw !addr16p,ax               ;03 (not internal ram)
    def test_cycles_03_movw_addr16p_ax_not_internal_ram(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x03, 0x00, 0x10])
        proc.step()
        self.assertEqual(proc.total_cycles, 12)

    # dbnz saddr,$addr16             ;04 (internal ram)
    def test_cycles_04_dbnz_saddr_internal_ram(self):
        proc = _make_processor()
        proc.write_memory(0xFE20, 5)  # nonzero so it branches
        proc.write_memory_bytes(0, [0x04, 0x20, 0xFD])
        proc.step()
        self.assertEqual(proc.total_cycles, 8)

    # dbnz saddr,$addr16             ;04 (sfr = PSW area)
    def test_cycles_04_dbnz_saddr_sfr(self):
        proc = _make_processor()
        proc.write_memory(0xFF00, 5)
        proc.write_memory_bytes(0, [0x04, 0x00, 0xFD])
        proc.step()
        self.assertEqual(proc.total_cycles, 10)

    # xch a,[de]                     ;05 (internal ram)
    def test_cycles_05_xch_a_de_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.DE, 0xFB00)
        proc.write_memory_bytes(0, [0x05])
        proc.step()
        self.assertEqual(proc.total_cycles, 4)

    # xch a,[de]                     ;05 (not internal ram)
    def test_cycles_05_xch_a_de_not_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.DE, 0xFF00)
        proc.write_memory_bytes(0, [0x05])
        proc.step()
        self.assertEqual(proc.total_cycles, 6)

    # xch a,[hl]                     ;07 (internal ram)
    def test_cycles_07_xch_a_hl_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.HL, 0xFB00)
        proc.write_memory_bytes(0, [0x07])
        proc.step()
        self.assertEqual(proc.total_cycles, 4)

    # xch a,[hl]                     ;07 (not internal ram)
    def test_cycles_07_xch_a_hl_not_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.HL, 0xFF00)
        proc.write_memory_bytes(0, [0x07])
        proc.step()
        self.assertEqual(proc.total_cycles, 6)

    # add a,!addr16                  ;08 (internal ram)
    def test_cycles_08_add_a_addr16_internal_ram(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x08, 0x00, 0xFB])
        proc.step()
        self.assertEqual(proc.total_cycles, 8)

    # add a,!addr16                  ;08 (not internal ram)
    def test_cycles_08_add_a_addr16_not_internal_ram(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x08, 0x00, 0xFF])
        proc.step()
        self.assertEqual(proc.total_cycles, 9)

    # add a,[hl+byte]                ;09 (internal ram)
    def test_cycles_09_add_a_hl_byte_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.HL, 0xFB00)
        proc.write_memory_bytes(0, [0x09, 0x00])
        proc.step()
        self.assertEqual(proc.total_cycles, 8)

    # add a,[hl+byte]                ;09 (not internal ram)
    def test_cycles_09_add_a_hl_byte_not_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.HL, 0xFF00)
        proc.write_memory_bytes(0, [0x09, 0x00])
        proc.step()
        self.assertEqual(proc.total_cycles, 9)

    # set1 saddr.bit                 ;0a (internal ram)
    def test_cycles_0a_set1_saddr_internal_ram(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x0a, 0x20])
        proc.step()
        self.assertEqual(proc.total_cycles, 4)  # saddr=FE20

    # set1 saddr.bit                 ;0a (sfr via psw)
    def test_cycles_0a_set1_psw_bit_sfr(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x0a, 0x1e])
        proc.step()
        self.assertEqual(proc.total_cycles, 6)  # saddr=FF1E (PSW)

    # clr1 saddr.bit                 ;0b (internal ram)
    def test_cycles_0b_clr1_saddr_internal_ram(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x0b, 0x20])
        proc.step()
        self.assertEqual(proc.total_cycles, 4)

    # clr1 saddr.bit                 ;0b (sfr via psw)
    def test_cycles_0b_clr1_psw_bit_sfr(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x0b, 0x1e])
        proc.step()
        self.assertEqual(proc.total_cycles, 6)

    # callf !addr11                  ;0c
    def test_cycles_0c_callf(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x0c, 0x00])
        proc.step()
        self.assertEqual(proc.total_cycles, 5)

    # add a,#byte                    ;0d
    def test_cycles_0d_add_a_imm(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x0d, 0x42])
        proc.step()
        self.assertEqual(proc.total_cycles, 4)

    # add a,saddr                    ;0e (internal ram)
    def test_cycles_0e_add_a_saddr_internal_ram(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x0e, 0x20])
        proc.step()
        self.assertEqual(proc.total_cycles, 4)

    # add a,saddr                    ;0e (sfr)
    def test_cycles_0e_add_a_saddr_sfr(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x0e, 0x1e])
        proc.step()
        self.assertEqual(proc.total_cycles, 5)  # PSW at FF1E

    # add a,[hl]                     ;0f (internal ram)
    def test_cycles_0f_add_a_hl_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.HL, 0xFB00)
        proc.write_memory_bytes(0, [0x0f])
        proc.step()
        self.assertEqual(proc.total_cycles, 4)

    # add a,[hl]                     ;0f (not internal ram)
    def test_cycles_0f_add_a_hl_not_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.HL, 0xFF00)
        proc.write_memory_bytes(0, [0x0f])
        proc.step()
        self.assertEqual(proc.total_cycles, 5)

    # movw rp,#word                  ;10
    def test_cycles_10_movw_rp_imm(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x10, 0xCD, 0xAB])
        proc.step()
        self.assertEqual(proc.total_cycles, 6)

    # mov saddr,#byte                ;11 (internal ram)
    def test_cycles_11_mov_saddr_imm_internal_ram(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x11, 0x20, 0x42])
        proc.step()
        self.assertEqual(proc.total_cycles, 6)

    # mov psw,#byte                  ;11 (sfr: psw at ff1e)
    def test_cycles_11_mov_psw_imm_sfr(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x11, 0x1e, 0x00])
        proc.step()
        self.assertEqual(proc.total_cycles, 7)

    # mov sfr,#byte                  ;13
    def test_cycles_13_mov_sfr_imm(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x13, 0xfe, 0x42])
        proc.step()
        self.assertEqual(proc.total_cycles, 7)

    # sub a,!addr16                  ;18 (internal ram)
    def test_cycles_18_sub_a_addr16_internal_ram(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x18, 0x00, 0xFB])
        proc.step()
        self.assertEqual(proc.total_cycles, 8)

    # sub a,!addr16                  ;18 (not internal ram)
    def test_cycles_18_sub_a_addr16_not_internal_ram(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x18, 0x00, 0xFF])
        proc.step()
        self.assertEqual(proc.total_cycles, 9)

    # sub a,[hl+byte]                ;19
    def test_cycles_19_sub_a_hl_byte_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.HL, 0xFB00)
        proc.write_memory_bytes(0, [0x19, 0x00])
        proc.step()
        self.assertEqual(proc.total_cycles, 8)

    # sub a,#byte                    ;1d
    def test_cycles_1d_sub_a_imm(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x1d, 0x42])
        proc.step()
        self.assertEqual(proc.total_cycles, 4)

    # sub a,saddr                    ;1e (internal ram)
    def test_cycles_1e_sub_a_saddr_internal_ram(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x1e, 0x20])
        proc.step()
        self.assertEqual(proc.total_cycles, 4)

    # sub a,[hl]                     ;1f (internal ram)
    def test_cycles_1f_sub_a_hl_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.HL, 0xFB00)
        proc.write_memory_bytes(0, [0x1f])
        proc.step()
        self.assertEqual(proc.total_cycles, 4)

    # set1 cy                        ;20
    def test_cycles_20_set1_cy(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x20])
        proc.step()
        self.assertEqual(proc.total_cycles, 2)

    # clr1 cy                        ;21
    def test_cycles_21_clr1_cy(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x21])
        proc.step()
        self.assertEqual(proc.total_cycles, 2)

    # push psw                       ;22
    def test_cycles_22_push_psw(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x22])
        proc.step()
        self.assertEqual(proc.total_cycles, 2)

    # pop psw                        ;23
    def test_cycles_23_pop_psw(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x23])
        proc.step()
        self.assertEqual(proc.total_cycles, 2)

    # ror a,1                        ;24
    def test_cycles_24_ror(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x24])
        proc.step()
        self.assertEqual(proc.total_cycles, 2)

    # rorc a,1                       ;25
    def test_cycles_25_rorc(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x25])
        proc.step()
        self.assertEqual(proc.total_cycles, 2)

    # rol a,1                        ;26
    def test_cycles_26_rol(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x26])
        proc.step()
        self.assertEqual(proc.total_cycles, 2)

    # rolc a,1                       ;27
    def test_cycles_27_rolc(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x27])
        proc.step()
        self.assertEqual(proc.total_cycles, 2)

    # addc a,!addr16                 ;28 (internal ram)
    def test_cycles_28_addc_a_addr16_internal_ram(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x28, 0x00, 0xFB])
        proc.step()
        self.assertEqual(proc.total_cycles, 8)

    # addc a,!addr16                 ;28 (not internal ram)
    def test_cycles_28_addc_a_addr16_not_internal_ram(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x28, 0x00, 0xFF])
        proc.step()
        self.assertEqual(proc.total_cycles, 9)

    # addc a,[hl+byte]               ;29 (internal ram)
    def test_cycles_29_addc_a_hl_byte_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.HL, 0xFB00)
        proc.write_memory_bytes(0, [0x29, 0x00])
        proc.step()
        self.assertEqual(proc.total_cycles, 8)

    # addc a,#byte                   ;2d
    def test_cycles_2d_addc_a_imm(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x2d, 0x42])
        proc.step()
        self.assertEqual(proc.total_cycles, 4)

    # addc a,saddr                   ;2e (internal ram)
    def test_cycles_2e_addc_a_saddr_internal_ram(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x2e, 0x20])
        proc.step()
        self.assertEqual(proc.total_cycles, 4)

    # addc a,saddr                   ;2e (sfr)
    def test_cycles_2e_addc_a_saddr_sfr(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x2e, 0x1e])
        proc.step()
        self.assertEqual(proc.total_cycles, 5)

    # addc a,[hl]                    ;2f (internal ram)
    def test_cycles_2f_addc_a_hl_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.HL, 0xFB00)
        proc.write_memory_bytes(0, [0x2f])
        proc.step()
        self.assertEqual(proc.total_cycles, 4)

    # xch a,r                        ;30-37 except 31
    def test_cycles_30_xch_a_r(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x30])
        proc.step()
        self.assertEqual(proc.total_cycles, 2)  # xch a,x

    # subc a,!addr16                 ;38 (internal ram)
    def test_cycles_38_subc_a_addr16_internal_ram(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x38, 0x00, 0xFB])
        proc.step()
        self.assertEqual(proc.total_cycles, 8)

    # subc a,!addr16                 ;38 (not internal ram)
    def test_cycles_38_subc_a_addr16_not_internal_ram(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x38, 0x00, 0xFF])
        proc.step()
        self.assertEqual(proc.total_cycles, 9)

    # subc a,[hl+byte]               ;39
    def test_cycles_39_subc_a_hl_byte_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.HL, 0xFB00)
        proc.write_memory_bytes(0, [0x39, 0x00])
        proc.step()
        self.assertEqual(proc.total_cycles, 8)

    # subc a,#byte                   ;3d
    def test_cycles_3d_subc_a_imm(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x3d, 0x42])
        proc.step()
        self.assertEqual(proc.total_cycles, 4)

    # subc a,saddr                   ;3e (internal ram)
    def test_cycles_3e_subc_a_saddr_internal_ram(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x3e, 0x20])
        proc.step()
        self.assertEqual(proc.total_cycles, 4)

    # subc a,[hl]                    ;3f (internal ram)
    def test_cycles_3f_subc_a_hl_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.HL, 0xFB00)
        proc.write_memory_bytes(0, [0x3f])
        proc.step()
        self.assertEqual(proc.total_cycles, 4)

    # inc r                          ;40-47
    def test_cycles_40_inc_r(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x40])
        proc.step()
        self.assertEqual(proc.total_cycles, 2)  # inc x

    # cmp a,!addr16                  ;48 (internal ram)
    def test_cycles_48_cmp_a_addr16_internal_ram(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x48, 0x00, 0xFB])
        proc.step()
        self.assertEqual(proc.total_cycles, 8)

    # cmp a,!addr16                  ;48 (not internal ram)
    def test_cycles_48_cmp_a_addr16_not_internal_ram(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x48, 0x00, 0xFF])
        proc.step()
        self.assertEqual(proc.total_cycles, 9)

    # cmp a,[hl+byte]                ;49
    def test_cycles_49_cmp_a_hl_byte_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.HL, 0xFB00)
        proc.write_memory_bytes(0, [0x49, 0x00])
        proc.step()
        self.assertEqual(proc.total_cycles, 8)

    # cmp a,#byte                    ;4d
    def test_cycles_4d_cmp_a_imm(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x4d, 0x42])
        proc.step()
        self.assertEqual(proc.total_cycles, 4)

    # cmp a,saddr                    ;4e (internal ram)
    def test_cycles_4e_cmp_a_saddr_internal_ram(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x4e, 0x20])
        proc.step()
        self.assertEqual(proc.total_cycles, 4)

    # cmp a,[hl]                     ;4f (internal ram)
    def test_cycles_4f_cmp_a_hl_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.HL, 0xFB00)
        proc.write_memory_bytes(0, [0x4f])
        proc.step()
        self.assertEqual(proc.total_cycles, 4)

    # dec r                          ;50-57
    def test_cycles_50_dec_r(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x50])
        proc.step()
        self.assertEqual(proc.total_cycles, 2)  # dec x

    # and a,!addr16                  ;58 (internal ram)
    def test_cycles_58_and_a_addr16_internal_ram(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x58, 0x00, 0xFB])
        proc.step()
        self.assertEqual(proc.total_cycles, 8)

    # and a,!addr16                  ;58 (not internal ram)
    def test_cycles_58_and_a_addr16_not_internal_ram(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x58, 0x00, 0xFF])
        proc.step()
        self.assertEqual(proc.total_cycles, 9)

    # and a,[hl+byte]                ;59
    def test_cycles_59_and_a_hl_byte_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.HL, 0xFB00)
        proc.write_memory_bytes(0, [0x59, 0x00])
        proc.step()
        self.assertEqual(proc.total_cycles, 8)

    # and a,#byte                    ;5d
    def test_cycles_5d_and_a_imm(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x5d, 0x42])
        proc.step()
        self.assertEqual(proc.total_cycles, 4)

    # and a,saddr                    ;5e (internal ram)
    def test_cycles_5e_and_a_saddr_internal_ram(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x5e, 0x20])
        proc.step()
        self.assertEqual(proc.total_cycles, 4)

    # and a,[hl]                     ;5f (internal ram)
    def test_cycles_5f_and_a_hl_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.HL, 0xFB00)
        proc.write_memory_bytes(0, [0x5f])
        proc.step()
        self.assertEqual(proc.total_cycles, 4)

    # mov a,r                        ;60-67 except 61
    def test_cycles_60_mov_a_r(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x60])
        proc.step()
        self.assertEqual(proc.total_cycles, 2)  # mov a,x

    # or a,!addr16                   ;68 (internal ram)
    def test_cycles_68_or_a_addr16_internal_ram(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x68, 0x00, 0xFB])
        proc.step()
        self.assertEqual(proc.total_cycles, 8)

    # or a,!addr16                   ;68 (not internal ram)
    def test_cycles_68_or_a_addr16_not_internal_ram(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x68, 0x00, 0xFF])
        proc.step()
        self.assertEqual(proc.total_cycles, 9)

    # or a,[hl+byte]                 ;69
    def test_cycles_69_or_a_hl_byte_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.HL, 0xFB00)
        proc.write_memory_bytes(0, [0x69, 0x00])
        proc.step()
        self.assertEqual(proc.total_cycles, 8)

    # or a,#byte                     ;6d
    def test_cycles_6d_or_a_imm(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x6d, 0x42])
        proc.step()
        self.assertEqual(proc.total_cycles, 4)

    # or a,saddr                     ;6e (internal ram)
    def test_cycles_6e_or_a_saddr_internal_ram(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x6e, 0x20])
        proc.step()
        self.assertEqual(proc.total_cycles, 4)

    # or a,[hl]                      ;6f (internal ram)
    def test_cycles_6f_or_a_hl_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.HL, 0xFB00)
        proc.write_memory_bytes(0, [0x6f])
        proc.step()
        self.assertEqual(proc.total_cycles, 4)

    # mov r,a                        ;70-77 except 71
    def test_cycles_70_mov_r_a(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x72])
        proc.step()
        self.assertEqual(proc.total_cycles, 2)  # mov c,a

    # xor a,!addr16                  ;78 (internal ram)
    def test_cycles_78_xor_a_addr16_internal_ram(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x78, 0x00, 0xFB])
        proc.step()
        self.assertEqual(proc.total_cycles, 8)

    # xor a,!addr16                  ;78 (not internal ram)
    def test_cycles_78_xor_a_addr16_not_internal_ram(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x78, 0x00, 0xFF])
        proc.step()
        self.assertEqual(proc.total_cycles, 9)

    # xor a,[hl+byte]                ;79
    def test_cycles_79_xor_a_hl_byte_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.HL, 0xFB00)
        proc.write_memory_bytes(0, [0x79, 0x00])
        proc.step()
        self.assertEqual(proc.total_cycles, 8)

    # xor a,#byte                    ;7d
    def test_cycles_7d_xor_a_imm(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x7d, 0x42])
        proc.step()
        self.assertEqual(proc.total_cycles, 4)

    # xor a,saddr                    ;7e (internal ram)
    def test_cycles_7e_xor_a_saddr_internal_ram(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x7e, 0x20])
        proc.step()
        self.assertEqual(proc.total_cycles, 4)

    # xor a,[hl]                     ;7f (internal ram)
    def test_cycles_7f_xor_a_hl_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.HL, 0xFB00)
        proc.write_memory_bytes(0, [0x7f])
        proc.step()
        self.assertEqual(proc.total_cycles, 4)

    # incw rp                        ;80
    def test_cycles_80_incw_rp(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x80])
        proc.step()
        self.assertEqual(proc.total_cycles, 4)  # incw ax

    # inc saddr                      ;81 (internal ram)
    def test_cycles_81_inc_saddr_internal_ram(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x81, 0x20])
        proc.step()
        self.assertEqual(proc.total_cycles, 4)

    # inc saddr                      ;81 (sfr)
    def test_cycles_81_inc_saddr_sfr(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x81, 0x00])
        proc.step()
        self.assertEqual(proc.total_cycles, 6)  # saddr=FF00

    # xch a,saddr                    ;83 (internal ram)
    def test_cycles_83_xch_a_saddr_internal_ram(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x83, 0x20])
        proc.step()
        self.assertEqual(proc.total_cycles, 4)

    # xch a,saddr                    ;83 (sfr)
    def test_cycles_83_xch_a_saddr_sfr(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x83, 0x1e])
        proc.step()
        self.assertEqual(proc.total_cycles, 6)  # PSW

    # mov a,[de]                     ;85 (internal ram)
    def test_cycles_85_mov_a_de_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.DE, 0xFB00)
        proc.write_memory_bytes(0, [0x85])
        proc.step()
        self.assertEqual(proc.total_cycles, 4)

    # mov a,[de]                     ;85 (not internal ram)
    def test_cycles_85_mov_a_de_not_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.DE, 0xFF00)
        proc.write_memory_bytes(0, [0x85])
        proc.step()
        self.assertEqual(proc.total_cycles, 5)

    # mov a,[hl]                     ;87 (internal ram)
    def test_cycles_87_mov_a_hl_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.HL, 0xFB00)
        proc.write_memory_bytes(0, [0x87])
        proc.step()
        self.assertEqual(proc.total_cycles, 4)

    # mov a,[hl]                     ;87 (not internal ram)
    def test_cycles_87_mov_a_hl_not_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.HL, 0xFF00)
        proc.write_memory_bytes(0, [0x87])
        proc.step()
        self.assertEqual(proc.total_cycles, 5)

    # add saddr,#byte                ;88 (internal ram)
    def test_cycles_88_add_saddr_imm_internal_ram(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x88, 0x20, 0x01])
        proc.step()
        self.assertEqual(proc.total_cycles, 6)

    # add saddr,#byte                ;88 (sfr)
    def test_cycles_88_add_saddr_imm_sfr(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x88, 0x00, 0x01])
        proc.step()
        self.assertEqual(proc.total_cycles, 8)

    # movw ax,saddrp                 ;89 (internal ram)
    def test_cycles_89_movw_ax_saddrp_internal_ram(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x89, 0x20])
        proc.step()
        self.assertEqual(proc.total_cycles, 6)

    # movw ax,saddrp                 ;89 (sfr)
    def test_cycles_89_movw_ax_saddrp_sfr(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x89, 0x1c])
        proc.step()
        self.assertEqual(proc.total_cycles, 8)  # SP at FF1C

    # dbnz c,$addr16                 ;8a
    def test_cycles_8a_dbnz_c(self):
        proc = _make_processor()
        proc.write_gp_reg(Registers.C, 5)
        proc.write_memory_bytes(0, [0x8a, 0xFE])
        proc.step()
        self.assertEqual(proc.total_cycles, 6)

    # dbnz b,$addr16                 ;8b
    def test_cycles_8b_dbnz_b(self):
        proc = _make_processor()
        proc.write_gp_reg(Registers.B, 5)
        proc.write_memory_bytes(0, [0x8b, 0xFE])
        proc.step()
        self.assertEqual(proc.total_cycles, 6)

    # bt saddr.bit,$addr16           ;8c (internal ram)
    def test_cycles_8c_bt_saddr_internal_ram(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x8c, 0x20, 0xFD])
        proc.step()
        self.assertEqual(proc.total_cycles, 8)

    # bt saddr.bit,$addr16           ;8c (sfr via psw)
    def test_cycles_8c_bt_psw_sfr(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x8c, 0x1e, 0xFD])
        proc.step()
        self.assertEqual(proc.total_cycles, 9)

    # bc $addr16                     ;8d
    def test_cycles_8d_bc(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x8d, 0xFE])
        proc.step()
        self.assertEqual(proc.total_cycles, 6)

    # mov a,!addr16                  ;8e (internal ram)
    def test_cycles_8e_mov_a_addr16_internal_ram(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x8e, 0x00, 0xFB])
        proc.step()
        self.assertEqual(proc.total_cycles, 8)

    # mov a,!addr16                  ;8e (not internal ram)
    def test_cycles_8e_mov_a_addr16_not_internal_ram(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x8e, 0x00, 0xFF])
        proc.step()
        self.assertEqual(proc.total_cycles, 9)

    # reti                           ;8f
    def test_cycles_8f_reti(self):
        proc = _make_processor()
        proc.write_sp(0xFEFB)
        proc.write_memory(0xFEFB, 0x00)  # PC low
        proc.write_memory(0xFEFC, 0x10)  # PC high
        proc.write_memory(0xFEFD, 0x00)  # PSW
        proc.write_memory_bytes(0, [0x8f])
        proc.step()
        self.assertEqual(proc.total_cycles, 6)

    # decw rp                        ;90
    def test_cycles_90_decw_rp(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x90])
        proc.step()
        self.assertEqual(proc.total_cycles, 4)  # decw ax

    # dec saddr                      ;91 (internal ram)
    def test_cycles_91_dec_saddr_internal_ram(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x91, 0x20])
        proc.step()
        self.assertEqual(proc.total_cycles, 4)

    # dec saddr                      ;91 (sfr)
    def test_cycles_91_dec_saddr_sfr(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x91, 0x00])
        proc.step()
        self.assertEqual(proc.total_cycles, 6)

    # xch a,sfr                      ;93
    def test_cycles_93_xch_a_sfr(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x93, 0xfe])
        proc.step()
        self.assertEqual(proc.total_cycles, 6)

    # mov [de],a                     ;95 (internal ram)
    def test_cycles_95_mov_de_a_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.DE, 0xFB00)
        proc.write_memory_bytes(0, [0x95])
        proc.step()
        self.assertEqual(proc.total_cycles, 4)

    # mov [de],a                     ;95 (not internal ram)
    def test_cycles_95_mov_de_a_not_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.DE, 0xFF00)
        proc.write_memory_bytes(0, [0x95])
        proc.step()
        self.assertEqual(proc.total_cycles, 5)

    # mov [hl],a                     ;97 (internal ram)
    def test_cycles_97_mov_hl_a_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.HL, 0xFB00)
        proc.write_memory_bytes(0, [0x97])
        proc.step()
        self.assertEqual(proc.total_cycles, 4)

    # sub saddr,#byte                ;98 (internal ram)
    def test_cycles_98_sub_saddr_imm_internal_ram(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x98, 0x20, 0x01])
        proc.step()
        self.assertEqual(proc.total_cycles, 6)

    # sub saddr,#byte                ;98 (sfr)
    def test_cycles_98_sub_saddr_imm_sfr(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x98, 0x00, 0x01])
        proc.step()
        self.assertEqual(proc.total_cycles, 8)

    # movw saddrp,ax                 ;99 (internal ram)
    def test_cycles_99_movw_saddrp_ax_internal_ram(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x99, 0x20])
        proc.step()
        self.assertEqual(proc.total_cycles, 6)

    # movw saddrp,ax                 ;99 (sfr)
    def test_cycles_99_movw_saddrp_ax_sfr(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x99, 0x1c])
        proc.step()
        self.assertEqual(proc.total_cycles, 8)  # SP

    # call !addr16                   ;9a
    def test_cycles_9a_call(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x9a, 0x00, 0x10])
        proc.step()
        self.assertEqual(proc.total_cycles, 7)

    # br !addr16                     ;9b
    def test_cycles_9b_br_addr16(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x9b, 0x00, 0x10])
        proc.step()
        self.assertEqual(proc.total_cycles, 6)

    # bnc $addr16                    ;9d
    def test_cycles_9d_bnc(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x9d, 0xFE])
        proc.step()
        self.assertEqual(proc.total_cycles, 6)

    # mov !addr16,a                  ;9e (internal ram)
    def test_cycles_9e_mov_addr16_a_internal_ram(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x9e, 0x00, 0xFB])
        proc.step()
        self.assertEqual(proc.total_cycles, 8)

    # mov !addr16,a                  ;9e (not internal ram)
    def test_cycles_9e_mov_addr16_a_not_internal_ram(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x9e, 0x00, 0xFF])
        proc.step()
        self.assertEqual(proc.total_cycles, 9)

    # retb                           ;9f
    def test_cycles_9f_retb(self):
        proc = _make_processor()
        proc.write_sp(0xFEFB)
        proc.write_memory(0xFEFB, 0x00)
        proc.write_memory(0xFEFC, 0x10)
        proc.write_memory(0xFEFD, 0x00)
        proc.write_memory_bytes(0, [0x9f])
        proc.step()
        self.assertEqual(proc.total_cycles, 6)

    # mov r,#byte                    ;a0-a7
    def test_cycles_a0_mov_r_imm(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0xa0, 0x42])
        proc.step()
        self.assertEqual(proc.total_cycles, 4)  # mov x,#42h

    # addc saddr,#byte               ;a8 (internal ram)
    def test_cycles_a8_addc_saddr_imm_internal_ram(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0xa8, 0x20, 0x01])
        proc.step()
        self.assertEqual(proc.total_cycles, 6)

    # addc saddr,#byte               ;a8 (sfr)
    def test_cycles_a8_addc_saddr_imm_sfr(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0xa8, 0x00, 0x01])
        proc.step()
        self.assertEqual(proc.total_cycles, 8)

    # movw ax,sfrp                   ;a9
    def test_cycles_a9_movw_ax_sfrp(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0xa9, 0xfe])
        proc.step()
        self.assertEqual(proc.total_cycles, 8)

    # mov a,[hl+c]                   ;aa (internal ram)
    def test_cycles_aa_mov_a_hl_c_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.HL, 0xFB00)
        proc.write_gp_reg(Registers.C, 0)
        proc.write_memory_bytes(0, [0xaa])
        proc.step()
        self.assertEqual(proc.total_cycles, 6)

    # mov a,[hl+c]                   ;aa (not internal ram)
    def test_cycles_aa_mov_a_hl_c_not_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.HL, 0xFF00)
        proc.write_gp_reg(Registers.C, 0)
        proc.write_memory_bytes(0, [0xaa])
        proc.step()
        self.assertEqual(proc.total_cycles, 7)

    # mov a,[hl+b]                   ;ab (internal ram)
    def test_cycles_ab_mov_a_hl_b_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.HL, 0xFB00)
        proc.write_gp_reg(Registers.B, 0)
        proc.write_memory_bytes(0, [0xab])
        proc.step()
        self.assertEqual(proc.total_cycles, 6)

    # bz $addr16                     ;ad
    def test_cycles_ad_bz(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0xad, 0xFE])
        proc.step()
        self.assertEqual(proc.total_cycles, 6)

    # mov a,[hl+byte]                ;ae (internal ram)
    def test_cycles_ae_mov_a_hl_byte_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.HL, 0xFB00)
        proc.write_memory_bytes(0, [0xae, 0x00])
        proc.step()
        self.assertEqual(proc.total_cycles, 8)

    # mov a,[hl+byte]                ;ae (not internal ram)
    def test_cycles_ae_mov_a_hl_byte_not_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.HL, 0xFF00)
        proc.write_memory_bytes(0, [0xae, 0x00])
        proc.step()
        self.assertEqual(proc.total_cycles, 9)

    # ret                            ;af
    def test_cycles_af_ret(self):
        proc = _make_processor()
        proc.write_sp(0xFEFB)
        proc.write_memory(0xFEFB, 0x00)
        proc.write_memory(0xFEFC, 0x10)
        proc.write_memory_bytes(0, [0xaf])
        proc.step()
        self.assertEqual(proc.total_cycles, 6)

    # pop rp                         ;b0
    def test_cycles_b0_pop_rp(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0xb0])
        proc.step()
        self.assertEqual(proc.total_cycles, 4)  # pop ax

    # push rp                        ;b1
    def test_cycles_b1_push_rp(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0xb1])
        proc.step()
        self.assertEqual(proc.total_cycles, 4)  # push ax

    # subc saddr,#byte               ;b8 (internal ram)
    def test_cycles_b8_subc_saddr_imm_internal_ram(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0xb8, 0x20, 0x01])
        proc.step()
        self.assertEqual(proc.total_cycles, 6)

    # subc saddr,#byte               ;b8 (sfr)
    def test_cycles_b8_subc_saddr_imm_sfr(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0xb8, 0x00, 0x01])
        proc.step()
        self.assertEqual(proc.total_cycles, 8)

    # movw sfrp,ax                   ;b9
    def test_cycles_b9_movw_sfrp_ax(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0xb9, 0xfe])
        proc.step()
        self.assertEqual(proc.total_cycles, 8)

    # mov [hl+c],a                   ;ba (internal ram)
    def test_cycles_ba_mov_hl_c_a_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.HL, 0xFB00)
        proc.write_gp_reg(Registers.C, 0)
        proc.write_memory_bytes(0, [0xba])
        proc.step()
        self.assertEqual(proc.total_cycles, 6)

    # mov [hl+b],a                   ;bb (internal ram)
    def test_cycles_bb_mov_hl_b_a_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.HL, 0xFB00)
        proc.write_gp_reg(Registers.B, 0)
        proc.write_memory_bytes(0, [0xbb])
        proc.step()
        self.assertEqual(proc.total_cycles, 6)

    # bnz $addr16                    ;bd
    def test_cycles_bd_bnz(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0xbd, 0xFE])
        proc.step()
        self.assertEqual(proc.total_cycles, 6)

    # mov [hl+byte],a                ;be (internal ram)
    def test_cycles_be_mov_hl_byte_a_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.HL, 0xFB00)
        proc.write_memory_bytes(0, [0xbe, 0x00])
        proc.step()
        self.assertEqual(proc.total_cycles, 8)

    # mov [hl+byte],a                ;be (not internal ram)
    def test_cycles_be_mov_hl_byte_a_not_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.HL, 0xFF00)
        proc.write_memory_bytes(0, [0xbe, 0x00])
        proc.step()
        self.assertEqual(proc.total_cycles, 9)

    # brk                            ;bf
    def test_cycles_bf_brk(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0xbf])
        proc.step()
        self.assertEqual(proc.total_cycles, 6)

    # movw ax,rp                     ;c2
    def test_cycles_c2_movw_ax_rp(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0xc2])
        proc.step()
        self.assertEqual(proc.total_cycles, 4)  # movw ax,bc

    # cmp saddr,#byte                ;c8 (internal ram)
    def test_cycles_c8_cmp_saddr_imm_internal_ram(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0xc8, 0x20, 0x42])
        proc.step()
        self.assertEqual(proc.total_cycles, 6)

    # cmp saddr,#byte                ;c8 (sfr)
    def test_cycles_c8_cmp_saddr_imm_sfr(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0xc8, 0x00, 0x42])
        proc.step()
        self.assertEqual(proc.total_cycles, 8)

    # addw ax,#word                  ;ca
    def test_cycles_ca_addw_ax_imm(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0xca, 0xCD, 0xAB])
        proc.step()
        self.assertEqual(proc.total_cycles, 6)

    # callt [addr5]                  ;c1
    def test_cycles_c1_callt(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0xc1])
        proc.step()
        self.assertEqual(proc.total_cycles, 6)

    # xch a,!addr16                  ;ce (internal ram)
    def test_cycles_ce_xch_a_addr16_internal_ram(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0xce, 0x00, 0xFB])
        proc.step()
        self.assertEqual(proc.total_cycles, 8)

    # xch a,!addr16                  ;ce (not internal ram)
    def test_cycles_ce_xch_a_addr16_not_internal_ram(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0xce, 0x00, 0xFF])
        proc.step()
        self.assertEqual(proc.total_cycles, 10)

    # movw rp,ax                     ;d2
    def test_cycles_d2_movw_rp_ax(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0xd2])
        proc.step()
        self.assertEqual(proc.total_cycles, 4)  # movw bc,ax

    # and saddr,#byte                ;d8 (internal ram)
    def test_cycles_d8_and_saddr_imm_internal_ram(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0xd8, 0x20, 0xff])
        proc.step()
        self.assertEqual(proc.total_cycles, 6)

    # and saddr,#byte                ;d8 (sfr)
    def test_cycles_d8_and_saddr_imm_sfr(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0xd8, 0x00, 0xff])
        proc.step()
        self.assertEqual(proc.total_cycles, 8)

    # subw ax,#word                  ;da
    def test_cycles_da_subw_ax_imm(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0xda, 0xCD, 0xAB])
        proc.step()
        self.assertEqual(proc.total_cycles, 6)

    # xch a,[hl+byte]                ;de (internal ram)
    def test_cycles_de_xch_a_hl_byte_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.HL, 0xFB00)
        proc.write_memory_bytes(0, [0xde, 0x00])
        proc.step()
        self.assertEqual(proc.total_cycles, 8)

    # xch a,[hl+byte]                ;de (not internal ram)
    def test_cycles_de_xch_a_hl_byte_not_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.HL, 0xFF00)
        proc.write_memory_bytes(0, [0xde, 0x00])
        proc.step()
        self.assertEqual(proc.total_cycles, 10)

    # xchw ax,rp                     ;e2
    def test_cycles_e2_xchw_ax_rp(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0xe2])
        proc.step()
        self.assertEqual(proc.total_cycles, 4)  # xchw ax,bc

    # or saddr,#byte                 ;e8 (internal ram)
    def test_cycles_e8_or_saddr_imm_internal_ram(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0xe8, 0x20, 0x01])
        proc.step()
        self.assertEqual(proc.total_cycles, 6)

    # or saddr,#byte                 ;e8 (sfr)
    def test_cycles_e8_or_saddr_imm_sfr(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0xe8, 0x00, 0x01])
        proc.step()
        self.assertEqual(proc.total_cycles, 8)

    # cmpw ax,#word                  ;ea
    def test_cycles_ea_cmpw_ax_imm(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0xea, 0xCD, 0xAB])
        proc.step()
        self.assertEqual(proc.total_cycles, 6)

    # movw saddrp,#word              ;ee (internal ram)
    def test_cycles_ee_movw_saddrp_imm_internal_ram(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0xee, 0x20, 0xCD, 0xAB])
        proc.step()
        self.assertEqual(proc.total_cycles, 8)

    # movw sp,#word                  ;ee (sfr: SP at ff1c)
    def test_cycles_ee_movw_sp_imm_sfr(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0xee, 0x1c, 0xCD, 0xAB])
        proc.step()
        self.assertEqual(proc.total_cycles, 10)

    # mov a,saddr                    ;f0 (internal ram)
    def test_cycles_f0_mov_a_saddr_internal_ram(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0xf0, 0x20])
        proc.step()
        self.assertEqual(proc.total_cycles, 4)

    # mov a,psw                      ;f0 (sfr)
    def test_cycles_f0_mov_a_psw_sfr(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0xf0, 0x1e])
        proc.step()
        self.assertEqual(proc.total_cycles, 5)

    # mov saddr,a                    ;f2 (internal ram)
    def test_cycles_f2_mov_saddr_a_internal_ram(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0xf2, 0x20])
        proc.step()
        self.assertEqual(proc.total_cycles, 4)

    # mov psw,a                      ;f2 (sfr)
    def test_cycles_f2_mov_psw_a_sfr(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0xf2, 0x1e])
        proc.step()
        self.assertEqual(proc.total_cycles, 5)

    # mov a,sfr                      ;f4
    def test_cycles_f4_mov_a_sfr(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0xf4, 0xfe])
        proc.step()
        self.assertEqual(proc.total_cycles, 5)

    # mov sfr,a                      ;f6
    def test_cycles_f6_mov_sfr_a(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0xf6, 0xfe])
        proc.step()
        self.assertEqual(proc.total_cycles, 5)

    # xor saddr,#byte                ;f8 (internal ram)
    def test_cycles_f8_xor_saddr_imm_internal_ram(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0xf8, 0x20, 0x01])
        proc.step()
        self.assertEqual(proc.total_cycles, 6)

    # xor saddr,#byte                ;f8 (sfr)
    def test_cycles_f8_xor_saddr_imm_sfr(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0xf8, 0x00, 0x01])
        proc.step()
        self.assertEqual(proc.total_cycles, 8)

    # br $addr16                     ;fa
    def test_cycles_fa_br_rel(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0xfa, 0xFE])
        proc.step()
        self.assertEqual(proc.total_cycles, 6)

    # movw sfrp,#word                ;fe
    def test_cycles_fe_movw_sfrp_imm(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0xfe, 0xfe, 0xCD, 0xAB])
        proc.step()
        self.assertEqual(proc.total_cycles, 10)

    # === Prefix 0x31 opcodes ===

    # add a,[hl+c]                   ;31 0a (internal ram)
    def test_cycles_31_0a_add_a_hl_c_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.HL, 0xFB00)
        proc.write_gp_reg(Registers.C, 0)
        proc.write_memory_bytes(0, [0x31, 0x0a])
        proc.step()
        self.assertEqual(proc.total_cycles, 8)

    # add a,[hl+c]                   ;31 0a (not internal ram)
    def test_cycles_31_0a_add_a_hl_c_not_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.HL, 0xFF00)
        proc.write_gp_reg(Registers.C, 0)
        proc.write_memory_bytes(0, [0x31, 0x0a])
        proc.step()
        self.assertEqual(proc.total_cycles, 9)

    # add a,[hl+b]                   ;31 0b
    def test_cycles_31_0b_add_a_hl_b_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.HL, 0xFB00)
        proc.write_gp_reg(Registers.B, 0)
        proc.write_memory_bytes(0, [0x31, 0x0b])
        proc.step()
        self.assertEqual(proc.total_cycles, 8)

    # bt a.bit,$addr16               ;31 0e
    def test_cycles_31_0e_bt_a_bit(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x31, 0x0e, 0xFD])
        proc.step()
        self.assertEqual(proc.total_cycles, 8)

    # bf a.bit,$addr16               ;31 0f
    def test_cycles_31_0f_bf_a_bit(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x31, 0x0f, 0xFD])
        proc.step()
        self.assertEqual(proc.total_cycles, 8)

    # sub a,[hl+c]                   ;31 1a
    def test_cycles_31_1a_sub_a_hl_c_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.HL, 0xFB00)
        proc.write_gp_reg(Registers.C, 0)
        proc.write_memory_bytes(0, [0x31, 0x1a])
        proc.step()
        self.assertEqual(proc.total_cycles, 8)

    # sub a,[hl+b]                   ;31 1b
    def test_cycles_31_1b_sub_a_hl_b_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.HL, 0xFB00)
        proc.write_gp_reg(Registers.B, 0)
        proc.write_memory_bytes(0, [0x31, 0x1b])
        proc.step()
        self.assertEqual(proc.total_cycles, 8)

    # addc a,[hl+c]                  ;31 2a
    def test_cycles_31_2a_addc_a_hl_c_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.HL, 0xFB00)
        proc.write_gp_reg(Registers.C, 0)
        proc.write_memory_bytes(0, [0x31, 0x2a])
        proc.step()
        self.assertEqual(proc.total_cycles, 8)

    # addc a,[hl+b]                  ;31 2b
    def test_cycles_31_2b_addc_a_hl_b_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.HL, 0xFB00)
        proc.write_gp_reg(Registers.B, 0)
        proc.write_memory_bytes(0, [0x31, 0x2b])
        proc.step()
        self.assertEqual(proc.total_cycles, 8)

    # btclr saddr.bit,$addr16        ;31 01 (internal ram)
    def test_cycles_31_01_btclr_saddr_internal_ram(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x31, 0x01, 0x20, 0xFC])
        proc.step()
        self.assertEqual(proc.total_cycles, 10)

    # btclr saddr.bit,$addr16        ;31 01 (sfr)
    def test_cycles_31_01_btclr_saddr_sfr(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x31, 0x01, 0x1e, 0xFC])
        proc.step()
        self.assertEqual(proc.total_cycles, 12)

    # bf saddr.bit,$addr16           ;31 03 (internal ram)
    def test_cycles_31_03_bf_saddr_internal_ram(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x31, 0x03, 0x20, 0xFC])
        proc.step()
        self.assertEqual(proc.total_cycles, 10)

    # bf saddr.bit,$addr16           ;31 03 (sfr)
    def test_cycles_31_03_bf_saddr_sfr(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x31, 0x03, 0x1e, 0xFC])
        proc.step()
        self.assertEqual(proc.total_cycles, 11)

    # btclr sfr.bit,$addr16          ;31 05
    def test_cycles_31_05_btclr_sfr(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x31, 0x05, 0xfe, 0xFC])
        proc.step()
        self.assertEqual(proc.total_cycles, 12)

    # bt sfr.bit,$addr16             ;31 06
    def test_cycles_31_06_bt_sfr(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x31, 0x06, 0xfe, 0xFC])
        proc.step()
        self.assertEqual(proc.total_cycles, 11)

    # bf sfr.bit,$addr16             ;31 07
    def test_cycles_31_07_bf_sfr(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x31, 0x07, 0xfe, 0xFC])
        proc.step()
        self.assertEqual(proc.total_cycles, 11)

    # btclr a.bit,$addr16            ;31 0d
    def test_cycles_31_0d_btclr_a_bit(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x31, 0x0d, 0xFD])
        proc.step()
        self.assertEqual(proc.total_cycles, 8)

    # subc a,[hl+c]                  ;31 3a
    def test_cycles_31_3a_subc_a_hl_c_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.HL, 0xFB00)
        proc.write_gp_reg(Registers.C, 0)
        proc.write_memory_bytes(0, [0x31, 0x3a])
        proc.step()
        self.assertEqual(proc.total_cycles, 8)

    # subc a,[hl+b]                  ;31 3b
    def test_cycles_31_3b_subc_a_hl_b_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.HL, 0xFB00)
        proc.write_gp_reg(Registers.B, 0)
        proc.write_memory_bytes(0, [0x31, 0x3b])
        proc.step()
        self.assertEqual(proc.total_cycles, 8)

    # cmp a,[hl+c]                   ;31 4a
    def test_cycles_31_4a_cmp_a_hl_c_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.HL, 0xFB00)
        proc.write_gp_reg(Registers.C, 0)
        proc.write_memory_bytes(0, [0x31, 0x4a])
        proc.step()
        self.assertEqual(proc.total_cycles, 8)

    # cmp a,[hl+b]                   ;31 4b
    def test_cycles_31_4b_cmp_a_hl_b_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.HL, 0xFB00)
        proc.write_gp_reg(Registers.B, 0)
        proc.write_memory_bytes(0, [0x31, 0x4b])
        proc.step()
        self.assertEqual(proc.total_cycles, 8)

    # and a,[hl+c]                   ;31 5a
    def test_cycles_31_5a_and_a_hl_c_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.HL, 0xFB00)
        proc.write_gp_reg(Registers.C, 0)
        proc.write_memory_bytes(0, [0x31, 0x5a])
        proc.step()
        self.assertEqual(proc.total_cycles, 8)

    # or a,[hl+c]                    ;31 6a
    def test_cycles_31_6a_or_a_hl_c_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.HL, 0xFB00)
        proc.write_gp_reg(Registers.C, 0)
        proc.write_memory_bytes(0, [0x31, 0x6a])
        proc.step()
        self.assertEqual(proc.total_cycles, 8)

    # xor a,[hl+c]                   ;31 7a
    def test_cycles_31_7a_xor_a_hl_c_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.HL, 0xFB00)
        proc.write_gp_reg(Registers.C, 0)
        proc.write_memory_bytes(0, [0x31, 0x7a])
        proc.step()
        self.assertEqual(proc.total_cycles, 8)

    # rol4 [hl]                      ;31 80 (internal ram)
    def test_cycles_31_80_rol4_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.HL, 0xFB00)
        proc.write_memory_bytes(0, [0x31, 0x80])
        proc.step()
        self.assertEqual(proc.total_cycles, 10)

    # rol4 [hl]                      ;31 80 (not internal ram)
    def test_cycles_31_80_rol4_not_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.HL, 0x1000)
        proc.write_memory_bytes(0, [0x31, 0x80])
        proc.step()
        self.assertEqual(proc.total_cycles, 12)

    # divuw c                        ;31 82
    def test_cycles_31_82_divuw(self):
        proc = _make_processor()
        proc.write_gp_reg(Registers.C, 1)
        proc.write_memory_bytes(0, [0x31, 0x82])
        proc.step()
        self.assertEqual(proc.total_cycles, 25)

    # btclr [hl].bit,$addr16         ;31 85 (internal ram)
    def test_cycles_31_85_btclr_hl_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.HL, 0xFB00)
        proc.write_memory_bytes(0, [0x31, 0x85, 0xFD])
        proc.step()
        self.assertEqual(proc.total_cycles, 10)

    # btclr [hl].bit,$addr16         ;31 85 (not internal ram)
    def test_cycles_31_85_btclr_hl_not_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.HL, 0xFF00)
        proc.write_memory_bytes(0, [0x31, 0x85, 0xFD])
        proc.step()
        self.assertEqual(proc.total_cycles, 12)

    # bt [hl].bit,$addr16            ;31 86 (internal ram)
    def test_cycles_31_86_bt_hl_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.HL, 0xFB00)
        proc.write_memory_bytes(0, [0x31, 0x86, 0xFD])
        proc.step()
        self.assertEqual(proc.total_cycles, 10)

    # bt [hl].bit,$addr16            ;31 86 (not internal ram)
    def test_cycles_31_86_bt_hl_not_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.HL, 0xFF00)
        proc.write_memory_bytes(0, [0x31, 0x86, 0xFD])
        proc.step()
        self.assertEqual(proc.total_cycles, 11)

    # bf [hl].bit,$addr16            ;31 87 (internal ram)
    def test_cycles_31_87_bf_hl_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.HL, 0xFB00)
        proc.write_memory_bytes(0, [0x31, 0x87, 0xFD])
        proc.step()
        self.assertEqual(proc.total_cycles, 10)

    # bf [hl].bit,$addr16            ;31 87 (not internal ram)
    def test_cycles_31_87_bf_hl_not_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.HL, 0xFF00)
        proc.write_memory_bytes(0, [0x31, 0x87, 0xFD])
        proc.step()
        self.assertEqual(proc.total_cycles, 11)

    # mulu x                         ;31 88
    def test_cycles_31_88_mulu(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x31, 0x88])
        proc.step()
        self.assertEqual(proc.total_cycles, 16)

    # xch a,[hl+c]                   ;31 8a (internal ram)
    def test_cycles_31_8a_xch_a_hl_c_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.HL, 0xFB00)
        proc.write_gp_reg(Registers.C, 0)
        proc.write_memory_bytes(0, [0x31, 0x8a])
        proc.step()
        self.assertEqual(proc.total_cycles, 8)

    # xch a,[hl+c]                   ;31 8a (not internal ram)
    def test_cycles_31_8a_xch_a_hl_c_not_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.HL, 0xFF00)
        proc.write_gp_reg(Registers.C, 0)
        proc.write_memory_bytes(0, [0x31, 0x8a])
        proc.step()
        self.assertEqual(proc.total_cycles, 10)

    # xch a,[hl+b]                   ;31 8b (internal ram)
    def test_cycles_31_8b_xch_a_hl_b_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.HL, 0xFB00)
        proc.write_gp_reg(Registers.B, 0)
        proc.write_memory_bytes(0, [0x31, 0x8b])
        proc.step()
        self.assertEqual(proc.total_cycles, 8)

    # ror4 [hl]                      ;31 90 (internal ram)
    def test_cycles_31_90_ror4_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.HL, 0xFB00)
        proc.write_memory_bytes(0, [0x31, 0x90])
        proc.step()
        self.assertEqual(proc.total_cycles, 10)

    # br ax                          ;31 98
    def test_cycles_31_98_br_ax(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x31, 0x98])
        proc.step()
        self.assertEqual(proc.total_cycles, 8)

    # === Prefix 0x61 opcodes ===

    # add r,a                        ;61 00-07
    def test_cycles_61_00_add_r_a(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x61, 0x00])
        proc.step()
        self.assertEqual(proc.total_cycles, 4)

    # add a,r                        ;61 08-0f
    def test_cycles_61_08_add_a_r(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x61, 0x08])
        proc.step()
        self.assertEqual(proc.total_cycles, 4)

    # sub r,a                        ;61 10-17
    def test_cycles_61_10_sub_r_a(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x61, 0x10])
        proc.step()
        self.assertEqual(proc.total_cycles, 4)

    # sub a,r                        ;61 18-1f
    def test_cycles_61_18_sub_a_r(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x61, 0x18])
        proc.step()
        self.assertEqual(proc.total_cycles, 4)

    # addc r,a                       ;61 20-27
    def test_cycles_61_20_addc_r_a(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x61, 0x20])
        proc.step()
        self.assertEqual(proc.total_cycles, 4)

    # addc a,r                       ;61 28-2f
    def test_cycles_61_28_addc_a_r(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x61, 0x28])
        proc.step()
        self.assertEqual(proc.total_cycles, 4)

    # subc r,a                       ;61 30-37
    def test_cycles_61_30_subc_r_a(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x61, 0x30])
        proc.step()
        self.assertEqual(proc.total_cycles, 4)

    # subc a,r                       ;61 38-3f
    def test_cycles_61_38_subc_a_r(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x61, 0x38])
        proc.step()
        self.assertEqual(proc.total_cycles, 4)

    # cmp r,a                        ;61 40-47
    def test_cycles_61_40_cmp_r_a(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x61, 0x40])
        proc.step()
        self.assertEqual(proc.total_cycles, 4)

    # cmp a,r                        ;61 48-4f
    def test_cycles_61_48_cmp_a_r(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x61, 0x48])
        proc.step()
        self.assertEqual(proc.total_cycles, 4)

    # and r,a                        ;61 50-57
    def test_cycles_61_50_and_r_a(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x61, 0x50])
        proc.step()
        self.assertEqual(proc.total_cycles, 4)

    # and a,r                        ;61 58-5f
    def test_cycles_61_58_and_a_r(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x61, 0x58])
        proc.step()
        self.assertEqual(proc.total_cycles, 4)

    # or r,a                         ;61 60-67
    def test_cycles_61_60_or_r_a(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x61, 0x60])
        proc.step()
        self.assertEqual(proc.total_cycles, 4)

    # or a,r                         ;61 68-6f
    def test_cycles_61_68_or_a_r(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x61, 0x68])
        proc.step()
        self.assertEqual(proc.total_cycles, 4)

    # xor r,a                        ;61 70-77
    def test_cycles_61_70_xor_r_a(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x61, 0x70])
        proc.step()
        self.assertEqual(proc.total_cycles, 4)

    # xor a,r                        ;61 78-7f
    def test_cycles_61_78_xor_a_r(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x61, 0x78])
        proc.step()
        self.assertEqual(proc.total_cycles, 4)

    # adjba                          ;61 80
    def test_cycles_61_80_adjba(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x61, 0x80])
        proc.step()
        self.assertEqual(proc.total_cycles, 4)

    # set1 a.bit                     ;61 8a
    def test_cycles_61_8a_set1_a_bit(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x61, 0x8a])
        proc.step()
        self.assertEqual(proc.total_cycles, 4)

    # clr1 a.bit                     ;61 8b
    def test_cycles_61_8b_clr1_a_bit(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x61, 0x8b])
        proc.step()
        self.assertEqual(proc.total_cycles, 4)

    # mov1 cy,a.bit                  ;61 8c
    def test_cycles_61_8c_mov1_cy_a_bit(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x61, 0x8c])
        proc.step()
        self.assertEqual(proc.total_cycles, 4)

    # mov1 a.bit,cy                  ;61 89
    def test_cycles_61_89_mov1_a_bit_cy(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x61, 0x89])
        proc.step()
        self.assertEqual(proc.total_cycles, 4)

    # and1 cy,a.bit                  ;61 8d
    def test_cycles_61_8d_and1_cy_a_bit(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x61, 0x8d])
        proc.step()
        self.assertEqual(proc.total_cycles, 4)

    # or1 cy,a.bit                   ;61 8e
    def test_cycles_61_8e_or1_cy_a_bit(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x61, 0x8e])
        proc.step()
        self.assertEqual(proc.total_cycles, 4)

    # xor1 cy,a.bit                  ;61 8f
    def test_cycles_61_8f_xor1_cy_a_bit(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x61, 0x8f])
        proc.step()
        self.assertEqual(proc.total_cycles, 4)

    # adjbs                          ;61 90
    def test_cycles_61_90_adjbs(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x61, 0x90])
        proc.step()
        self.assertEqual(proc.total_cycles, 4)

    # sel rbn                        ;61 d0
    def test_cycles_61_d0_sel_rb(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x61, 0xd0])
        proc.step()
        self.assertEqual(proc.total_cycles, 4)

    # === Prefix 0x71 opcodes ===

    # mov1 saddr.bit,cy              ;71 01 (internal ram)
    def test_cycles_71_01_mov1_saddr_cy_internal_ram(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x71, 0x01, 0x20])
        proc.step()
        self.assertEqual(proc.total_cycles, 6)

    # mov1 saddr.bit,cy              ;71 01 (sfr)
    def test_cycles_71_01_mov1_saddr_cy_sfr(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x71, 0x01, 0x1e])
        proc.step()
        self.assertEqual(proc.total_cycles, 8)  # PSW

    # mov1 cy,saddr.bit              ;71 04 (internal ram)
    def test_cycles_71_04_mov1_cy_saddr_internal_ram(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x71, 0x04, 0x20])
        proc.step()
        self.assertEqual(proc.total_cycles, 6)

    # mov1 cy,saddr.bit              ;71 04 (sfr)
    def test_cycles_71_04_mov1_cy_saddr_sfr(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x71, 0x04, 0x1e])
        proc.step()
        self.assertEqual(proc.total_cycles, 7)

    # and1 cy,saddr.bit              ;71 05 (internal ram)
    def test_cycles_71_05_and1_cy_saddr_internal_ram(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x71, 0x05, 0x20])
        proc.step()
        self.assertEqual(proc.total_cycles, 6)

    # and1 cy,saddr.bit              ;71 05 (sfr)
    def test_cycles_71_05_and1_cy_saddr_sfr(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x71, 0x05, 0x1e])
        proc.step()
        self.assertEqual(proc.total_cycles, 7)

    # or1 cy,saddr.bit               ;71 06 (internal ram)
    def test_cycles_71_06_or1_cy_saddr_internal_ram(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x71, 0x06, 0x20])
        proc.step()
        self.assertEqual(proc.total_cycles, 6)

    # or1 cy,saddr.bit               ;71 06 (sfr)
    def test_cycles_71_06_or1_cy_saddr_sfr(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x71, 0x06, 0x1e])
        proc.step()
        self.assertEqual(proc.total_cycles, 7)

    # xor1 cy,saddr.bit              ;71 07 (internal ram)
    def test_cycles_71_07_xor1_cy_saddr_internal_ram(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x71, 0x07, 0x20])
        proc.step()
        self.assertEqual(proc.total_cycles, 6)

    # xor1 cy,saddr.bit              ;71 07 (sfr)
    def test_cycles_71_07_xor1_cy_saddr_sfr(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x71, 0x07, 0x1e])
        proc.step()
        self.assertEqual(proc.total_cycles, 7)

    # mov1 sfr.bit,cy                ;71 09
    def test_cycles_71_09_mov1_sfr_cy(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x71, 0x09, 0xfe])
        proc.step()
        self.assertEqual(proc.total_cycles, 8)

    # set1 sfr.bit                   ;71 0a
    def test_cycles_71_0a_set1_sfr(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x71, 0x0a, 0xfe])
        proc.step()
        self.assertEqual(proc.total_cycles, 8)

    # clr1 sfr.bit                   ;71 0b
    def test_cycles_71_0b_clr1_sfr(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x71, 0x0b, 0xfe])
        proc.step()
        self.assertEqual(proc.total_cycles, 8)

    # mov1 cy,sfr.bit                ;71 0c
    def test_cycles_71_0c_mov1_cy_sfr(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x71, 0x0c, 0xfe])
        proc.step()
        self.assertEqual(proc.total_cycles, 7)

    # and1 cy,sfr.bit                ;71 0d
    def test_cycles_71_0d_and1_cy_sfr(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x71, 0x0d, 0xfe])
        proc.step()
        self.assertEqual(proc.total_cycles, 7)

    # or1 cy,sfr.bit                 ;71 0e
    def test_cycles_71_0e_or1_cy_sfr(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x71, 0x0e, 0xfe])
        proc.step()
        self.assertEqual(proc.total_cycles, 7)

    # xor1 cy,sfr.bit                ;71 0f
    def test_cycles_71_0f_xor1_cy_sfr(self):
        proc = _make_processor()
        proc.write_memory_bytes(0, [0x71, 0x0f, 0xfe])
        proc.step()
        self.assertEqual(proc.total_cycles, 7)

    # mov1 [hl].bit,cy               ;71 81 (internal ram)
    def test_cycles_71_81_mov1_hl_cy_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.HL, 0xFB00)
        proc.write_memory_bytes(0, [0x71, 0x81])
        proc.step()
        self.assertEqual(proc.total_cycles, 6)

    # mov1 [hl].bit,cy               ;71 81 (not internal ram)
    def test_cycles_71_81_mov1_hl_cy_not_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.HL, 0xFF00)
        proc.write_memory_bytes(0, [0x71, 0x81])
        proc.step()
        self.assertEqual(proc.total_cycles, 8)

    # set1 [hl].bit                  ;71 82 (internal ram)
    def test_cycles_71_82_set1_hl_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.HL, 0xFB00)
        proc.write_memory_bytes(0, [0x71, 0x82])
        proc.step()
        self.assertEqual(proc.total_cycles, 6)

    # set1 [hl].bit                  ;71 82 (not internal ram)
    def test_cycles_71_82_set1_hl_not_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.HL, 0xFF00)
        proc.write_memory_bytes(0, [0x71, 0x82])
        proc.step()
        self.assertEqual(proc.total_cycles, 8)

    # clr1 [hl].bit                  ;71 83 (internal ram)
    def test_cycles_71_83_clr1_hl_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.HL, 0xFB00)
        proc.write_memory_bytes(0, [0x71, 0x83])
        proc.step()
        self.assertEqual(proc.total_cycles, 6)

    # clr1 [hl].bit                  ;71 83 (not internal ram)
    def test_cycles_71_83_clr1_hl_not_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.HL, 0xFF00)
        proc.write_memory_bytes(0, [0x71, 0x83])
        proc.step()
        self.assertEqual(proc.total_cycles, 8)

    # mov1 cy,[hl].bit               ;71 84 (internal ram)
    def test_cycles_71_84_mov1_cy_hl_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.HL, 0xFB00)
        proc.write_memory_bytes(0, [0x71, 0x84])
        proc.step()
        self.assertEqual(proc.total_cycles, 6)

    # mov1 cy,[hl].bit               ;71 84 (not internal ram)
    def test_cycles_71_84_mov1_cy_hl_not_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.HL, 0xFF00)
        proc.write_memory_bytes(0, [0x71, 0x84])
        proc.step()
        self.assertEqual(proc.total_cycles, 7)

    # and1 cy,[hl].bit               ;71 85 (internal ram)
    def test_cycles_71_85_and1_cy_hl_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.HL, 0xFB00)
        proc.write_memory_bytes(0, [0x71, 0x85])
        proc.step()
        self.assertEqual(proc.total_cycles, 6)

    # and1 cy,[hl].bit               ;71 85 (not internal ram)
    def test_cycles_71_85_and1_cy_hl_not_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.HL, 0xFF00)
        proc.write_memory_bytes(0, [0x71, 0x85])
        proc.step()
        self.assertEqual(proc.total_cycles, 7)

    # or1 cy,[hl].bit                ;71 86 (internal ram)
    def test_cycles_71_86_or1_cy_hl_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.HL, 0xFB00)
        proc.write_memory_bytes(0, [0x71, 0x86])
        proc.step()
        self.assertEqual(proc.total_cycles, 6)

    # or1 cy,[hl].bit                ;71 86 (not internal ram)
    def test_cycles_71_86_or1_cy_hl_not_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.HL, 0xFF00)
        proc.write_memory_bytes(0, [0x71, 0x86])
        proc.step()
        self.assertEqual(proc.total_cycles, 7)

    # xor1 cy,[hl].bit               ;71 87 (internal ram)
    def test_cycles_71_87_xor1_cy_hl_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.HL, 0xFB00)
        proc.write_memory_bytes(0, [0x71, 0x87])
        proc.step()
        self.assertEqual(proc.total_cycles, 6)

    # xor1 cy,[hl].bit               ;71 87 (not internal ram)
    def test_cycles_71_87_xor1_cy_hl_not_internal_ram(self):
        proc = _make_processor()
        proc.write_gp_regpair(RegisterPairs.HL, 0xFF00)
        proc.write_memory_bytes(0, [0x71, 0x87])
        proc.step()
        self.assertEqual(proc.total_cycles, 7)


