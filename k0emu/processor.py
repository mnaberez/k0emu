
class Processor(object):
    REGISTERS_BASE_ADDRESS = 0xFEF8
    RESET_VECTOR_ADDRESS = 0x0000
    SP_ADDRESS = 0xFF1C
    PSW_ADDRESS = 0xFF1E

    def __init__(self):
        self.memory = bytearray(0x10000)
        self._build_opcode_map()
        self.reset()

    def reset(self):
        self.sp = 0
        low = self.memory[self.RESET_VECTOR_ADDRESS]
        high = self.memory[self.RESET_VECTOR_ADDRESS+1]
        self.pc = (high << 8) + low

    def step(self):
        opcode = self._consume_byte()
        handler = self._opcode_map[opcode]
        handler(opcode)

    def __str__(self):
        return RegisterTrace.generate(self)

    def _build_opcode_map(self):
        self._opcode_map = {}
        for opcode in range(0x100):
            if opcode == 0x00:
                f = self._opcode_0x00 # nop
            elif opcode == 0x01:
                f = self._opcode_0x01 # not1 cy
            elif opcode == 0x05:
                f = self._opcode_0x05 # xch a,[de]                  ;05
            elif opcode == 0x07:
                f = self._opcode_0x07 # xch a,[hl]                  ;07
            elif opcode == 0x20:
                f = self._opcode_0x20 # set1 cy
            elif opcode == 0x21:
                f = self._opcode_0x21 # clr1 cy
            elif opcode == 0x22:
                f = self._opcode_0x22 # push psw                    ;22
            elif opcode == 0x23:
                f = self._opcode_0x23 # pop psw                     ;23
            elif opcode in (0x30, 0x32, 0x33, 0x34, 0x35, 0x36, 0x37):
                f = self._opcode_0x30_to_0x37_except_0x31 # xch a,REG                    ;32...37 except 31
            elif opcode == 0xce:
                f = self._opcode_0xce # xch a,!abcd                 ;ce cd ab
            elif opcode == 0x83:
                f = self._opcode_0x83 # xch a,0fe20h                ;83 20          saddr
            elif opcode == 0x93:
                f = self._opcode_0x93 # xch a,0fffeh                ;93 fe          sfr
            elif opcode == 0x9b:
                f = self._opcode_0x9b # br !0abcdh                  ;9b cd ab
            elif opcode & 0b11111000 == 0b10100000:
                f = self._opcode_0xa0_to_0xa7 # mov r,#byte                 ;a0..a7 xx
            elif opcode in (0x60, 0x62, 0x63, 0x64, 0x65, 0x66, 0x67):
                f = self._opcode_0x60_to_0x67_except_0x61 # mov a,x ... mov a,h           ;60..67 except 61
            elif opcode in (0x70, 0x72, 0x73, 0x74, 0x75, 0x76, 0x77):
                f = self._opcode_0x70_to_0x77_except_0x71 # mov x,a ... mov h,a           ;70..77 except 71
            elif opcode == 0x8e:
                f = self._opcode_0x8e # mov a,!addr16                 ;8e
            elif opcode == 0x9e:
                f = self._opcode_0x9e # mov !addr16,a               ;9e cd ab
            elif opcode == 0xf0:
                f = self._opcode_0xf0 # mov a,0fe20h                ;F0 20          saddr
            elif opcode == 0xf2:
                f = self._opcode_0xf2 # mov 0fe20h,a                ;f2 20          saddr
            elif opcode == 0xf4:
                f = self._opcode_0xf4 # mov a,0fffeh                ;f4 fe          sfr
            elif opcode == 0xf6:
                f = self._opcode_0xf6 # mov 0fffeh,a                ;f6 fe          sfr
            elif opcode == 0x11:
                f = self._opcode_0x11 # mov 0fe20h,#0abh            ;11 20 ab       saddr
            elif opcode == 0x13:
                f = self._opcode_0x13 # mov 0fffeh, #0abh           ;13 fe ab       sfr
            elif opcode == 0x31:
                f = self._opcode_0x31
            elif opcode == 0x61:
                f = self._opcode_0x61
            elif opcode == 0x71:
                f = self._opcode_0x71
            elif opcode == 0x6d:
                f = self._opcode_0x6d # or a,#0abh                  ;6d ab
            elif opcode == 0x6e:
                f = self._opcode_0x6e # or a,0fe20h                 ;6e 20          saddr
            elif opcode == 0xe8:
                f = self._opcode_0xe8 # or 0fe20h,#0abh             ;e8 20 ab
            elif opcode == 0x68:
                f = self._opcode_0x68 # or a,!0abcdh                ;68 cd ab
            elif opcode == 0x5d:
                f = self._opcode_0x5d # and a,#0abh                 ;5d ab
            elif opcode == 0x5e:
                f = self._opcode_0x5e # and a,0fe20h                ;5e 20          saddr
            elif opcode == 0x58:
                f = self._opcode_0x58 # and a,!0abcdh               ;58 cd ab
            elif opcode == 0xd8:
                f = self._opcode_0xd8 # and 0fe20h,#0abh            ;d8 20 ab       saddr
            elif opcode == 0x9a:
                f = self._opcode_0x9a # call !0abcdh                ;9a cd ab
            elif opcode == 0xaf:
                f = self._opcode_0xaf # ret                         ;af
            elif opcode == 0x8f:
                f = self._opcode_0x8f # reti                        ;8f
            elif opcode == 0x7d:
                f = self._opcode_0x7d # xor a,#0abh                 ;7d ab
            elif opcode == 0x7e:
                f = self._opcode_0x7e # xor a,0fe20h                ;7e 20          saddr
            elif opcode == 0x78:
                f = self._opcode_0x78 # xor a,!0abcdh               ;78 cd ab
            elif opcode == 0xf8:
                f = self._opcode_0xf8 # xor 0fe20h,#0abh            ;f8 20 ab       saddr
            elif opcode in (0x0a, 0x1a, 0x2a, 0x3a, 0x4a, 0x5a, 0x6a, 0x7a):
                # SET1 0fe20h.7               ;7A 20          saddr
                # SET1 PSW.7                  ;7A 1E
                # EI                          ;7A 1E          alias for SET1 PSW.7
                f = self._opcode_0x0a_to_0x7a_set1
            elif opcode in (0x0b, 0x1b, 0x2b, 0x3b, 0x4b, 0x5b, 0x6b, 0x7b):
                # clr1 0fe20h.0               ;0b 20          saddr
                # clr1 psw.0                  ;0b 1e
                # di                          ;7b 1e          alias for clr1 psw.7
                f = self._opcode_0x0b_to_0x7b_clr
            elif opcode == 0xfa:
                f = self._opcode_0xfa # br $label7                  ;fa fe
            elif opcode == 0x8d:
                f = self._opcode_0x8d # bc $label3                  ;8d fe
            elif opcode == 0x9d:
                f = self._opcode_0x9d # bnc $label3                 ;8d fe
            elif opcode == 0xad:
                f = self._opcode_0xad # bz $label5                  ;ad fe
            elif opcode == 0xbd:
                f = self._opcode_0xbd # bnz $label5                 ;bd fe
            elif opcode == 0xee:
                f = self._opcode_0xee # movw sp,#0abcdh             ;ee 1c cd ab
            elif opcode in (0x40, 0x41, 0x42, 0x43, 0x44, 0x45, 0x46, 0x47):
                f = self._opcode_0x40_to_0x47_inc # inc x ;40 .. inc h ;47
            elif opcode in (0x50, 0x51, 0x52, 0x53, 0x54, 0x55, 0x56, 0x57):
                f = self._opcode_0x50_to_0x57_dec # dec x ;50 .. dec h ;57
            elif opcode == 0x81:
                f = self._opcode_0x81  # inc 0fe20h                  ;81 20          saddr
            elif opcode == 0x91:
                f = self._opcode_0x91  # dec 0fe20h                  ;91 20          saddr
            elif opcode in (0x0c, 0x1c, 0x2c, 0x3c, 0x4c, 0x5c, 0x6c, 0x7c):
                f = self._opcode_0x0c_to_0x7c_callf
            elif opcode & 0b11000001 == 0b11000001:
                f = self._opcode_0xc1_to_0xff_callt
            elif opcode == 0x24:
                f = self._opcode_0x24  # ror a,1                     ;24
            elif opcode == 0x25:
                f = self._opcode_0x25  # rorc a,1                    ;25
            elif opcode == 0x26:
                f = self._opcode_0x26  # rol a,1                     ;26
            elif opcode == 0x27:
                f = self._opcode_0x27  # rolc a,1                    ;27
            elif opcode == 0x8a:
                f = self._opcode_0x8a  # dbnz c,$label1              ;8a fe
            elif opcode == 0x8b:
                f = self._opcode_0x8b  # dbnz c,$label1              ;8a fe
            elif opcode == 0x04:
                f = self._opcode_0x04  # dbnz 0fe20h,$label0         ;04 20 fd       saddr
            elif opcode in (0x8c, 0x9c, 0xac, 0xbc, 0xcc, 0xdc, 0xec, 0xfc):
                f = self._opcode_0x8c_to_0xfc_bt # bt 0fe20h.bit,$label8         ;8c 20 fd       saddr
            elif opcode in (0x10, 0x12, 0x14, 0x16):
                f = self._opcode_0x10_to_0x16_movw
            elif opcode in (0xe2, 0xe4, 0xe6):
                f = self._opcode_0xe2_to_0xe6_xchw
            elif opcode == 0x85:
                f = self._opcode_0x85 # mov a,[de]                  ;85
            elif opcode == 0x95:
                f = self._opcode_0x95 # mov [de],a                  ;95
            elif opcode == 0x87:
                f = self._opcode_0x87 # mov a,[hl]                  ;87
            elif opcode == 0x97:
                f = self._opcode_0x97 # mov [hl],a                  ;97
            elif opcode in (0xb1, 0xb3, 0xb5, 0xb7):
                f = self._opcode_0xb1_to_0xb7_push_rp # push ax                     ;b1
            elif opcode in (0xb0, 0xb2, 0xb4, 0xb6):
                f = self._opcode_0xb0_to_0xb6_pop_rp # pop ax                      ;b0
            else:
                f = self._opcode_not_implemented

            self._opcode_map[opcode] = f

    # not implemented
    def _opcode_not_implemented(self, opcode):
        raise NotImplementedError()

    # nop
    def _opcode_0x00(self, opcode):
        return

    # not1 cy
    def _opcode_0x01(self, opcode):
        bitweight = Flags.CY
        carry = self.read_psw() & bitweight
        if carry:
            self.write_psw(self.read_psw() & ~bitweight)
        else:
            self.write_psw(self.read_psw() | bitweight)

    # xch a,[de]                  ;05
    def _opcode_0x05(self, opcode):
        a_value = self.read_gp_reg(Registers.A)
        address = self.read_gp_regpair(RegisterPairs.DE)
        other_value = self.memory[address]
        self.write_gp_reg(Registers.A, other_value)
        self.memory[address] = a_value

    # xch a,[hl]                  ;07
    def _opcode_0x07(self, opcode):
        a_value = self.read_gp_reg(Registers.A)
        address = self.read_gp_regpair(RegisterPairs.HL)
        other_value = self.memory[address]
        self.write_gp_reg(Registers.A, other_value)
        self.memory[address] = a_value

    # movw regpair,#0abcdh             ;10..16 cd ab
    def _opcode_0x10_to_0x16_movw(self, opcode):
        regpair = _regpair(opcode)
        value = self._consume_word()
        self.write_gp_regpair(regpair, value)

    # xchw ax,bc                  ;e2
    # xchw ax,de                  ;e4
    # xchw ax,hl                  ;e6
    def _opcode_0xe2_to_0xe6_xchw(self, opcode):
        ax_value = self.read_gp_regpair(RegisterPairs.AX)
        other_regpair = _regpair(opcode)
        other_value = self.read_gp_regpair(other_regpair)
        self.write_gp_regpair(RegisterPairs.AX, other_value)
        self.write_gp_regpair(other_regpair, ax_value)

    # set1 cy
    def _opcode_0x20(self, opcode):
        bitweight = Flags.CY
        self.write_psw(self.read_psw() | bitweight)

    # clr1 cy
    def _opcode_0x21(self, opcode):
        bitweight = Flags.CY
        self.write_psw(self.read_psw() & ~bitweight)

    # push psw                    ;22
    def _opcode_0x22(self, opcode):
        self._push(self.read_psw())

    # pop psw                     ;23
    def _opcode_0x23(self, opcode):
        self.write_psw(self._pop())

    # ror a,1                     ;24
    def _opcode_0x24(self, opcode):
        value = self.read_gp_reg(Registers.A)
        original_bit_0 = value & 1
        rotated = value >> 1

        psw = self.read_psw()

        if original_bit_0:
            rotated |= 0x80
            psw |= Flags.CY
        else:
            psw &= ~Flags.CY
        rotated &= 0xFF

        self.write_psw(psw)
        self.write_gp_reg(Registers.A, rotated)

    # rorc a,1                    ;25
    def _opcode_0x25(self, opcode):
        value = self.read_gp_reg(Registers.A)
        original_bit_0 = value & 1
        rotated = value >> 1

        psw = self.read_psw()

        if psw & Flags.CY:
            rotated |= 0x80

        if original_bit_0:
            psw |= Flags.CY
        else:
            psw &= ~Flags.CY
        rotated &= 0xFF

        self.write_psw(psw)
        self.write_gp_reg(Registers.A, rotated)

    # rol a,1                     ;26
    def _opcode_0x26(self, opcode):
        rotated = self.read_gp_reg(Registers.A) << 1
        psw = self.read_psw()

        if rotated & 0x100:
            rotated |= 1
            psw |= Flags.CY
        else:
            psw &= ~Flags.CY
        rotated &= 0xFF

        self.write_psw(psw)
        self.write_gp_reg(Registers.A, rotated)

    # rolc a,1                    ;27
    def _opcode_0x27(self, opcode):
        rotated = self.read_gp_reg(Registers.A) << 1
        psw = self.read_psw()

        if psw & Flags.CY:
             rotated |= 1

        if rotated & 0x100:
            psw |= Flags.CY
        else:
            psw &= ~Flags.CY
        rotated &= 0xFF

        self.write_psw(psw)
        self.write_gp_reg(Registers.A, rotated)

    # xch a,REG                    ;32...37 except 31
    def _opcode_0x30_to_0x37_except_0x31(self, opcode):
        other_reg = opcode & 0b111
        a_value = self.read_gp_reg(Registers.A)
        other_value = self.read_gp_reg(other_reg)
        self.write_gp_reg(Registers.A, other_value)
        self.write_gp_reg(other_reg, a_value)

    # xch a,!abcd                 ;ce cd ab
    def _opcode_0xce(self, opcode):
        address = self._consume_addr16()
        a_value = self.read_gp_reg(Registers.A)
        other_value = self.memory[address]
        self.write_gp_reg(Registers.A, other_value)
        self.memory[address] = a_value

    # xch a,0fe20h                ;83 20          saddr
    def _opcode_0x83(self, opcode):
        address = self._consume_saddr()
        a_value = self.read_gp_reg(Registers.A)
        other_value = self.memory[address]
        self.write_gp_reg(Registers.A, other_value)
        self.memory[address] = a_value

    # xch a,0fffeh                ;93 fe          sfr
    def _opcode_0x93(self, opcode):
        address = self._consume_sfr()
        a_value = self.read_gp_reg(Registers.A)
        other_value = self.memory[address]
        self.write_gp_reg(Registers.A, other_value)
        self.memory[address] = a_value

    # br !0abcdh                  ;9b cd ab
    def _opcode_0x9b(self, opcode):
        address = self._consume_addr16()
        self.pc = address

    # mov r,#byte                 ;a0..a7 xx
    def _opcode_0xa0_to_0xa7(self, opcode):
        regnum = opcode & 0b00000111
        immbyte = self._consume_byte()
        self.write_gp_reg(regnum, immbyte)

    # mov a,x ... mov a,h           ;60..67 except 61
    def _opcode_0x60_to_0x67_except_0x61(self, opcode):
        reg = _reg(opcode)
        value = self.read_gp_reg(reg)
        self.write_gp_reg(Registers.A, value)

    # mov x,a ... mov h,a           ;70..77 except 71
    def _opcode_0x70_to_0x77_except_0x71(self, opcode):
        reg = _reg(opcode)
        value = self.read_gp_reg(Registers.A)
        self.write_gp_reg(reg, value)

    # mov a,!addr16                 ;8e
    def _opcode_0x8e(self, opcode):
        address = self._consume_addr16()
        value = self.memory[address]
        self.write_gp_reg(Registers.A, value)

    # mov !addr16,a               ;9e cd ab
    def _opcode_0x9e(self, opcode):
        address = self._consume_addr16()
        value = self.read_gp_reg(Registers.A)
        self.memory[address] = value

    # mov a,0fe20h                ;F0 20          saddr
    # mov a,psw                   ;f0 1e          (psw=saddr ff1e)
    def _opcode_0xf0(self, opcode):
        address = self._consume_saddr()
        value = self.memory[address]
        self.write_gp_reg(Registers.A, value)

    # mov 0fe20h,a                ;f2 20          saddr
    # mov psw,a                   ;f2 1e          (psw=saddr ff1e)
    def _opcode_0xf2(self, opcode):
        address = self._consume_saddr()
        value = self.read_gp_reg(Registers.A)
        self.memory[address] = value

    # mov a,0fffeh                ;f4 fe          sfr
    def _opcode_0xf4(self, opcode):
        address = self._consume_sfr()
        value = self.memory[address]
        self.write_gp_reg(Registers.A, value)
        self.memory[address] = value

    # mov 0fffeh,a                ;f6 fe          sfr
    def _opcode_0xf6(self, opcode):
        address = self._consume_sfr()
        value = self.read_gp_reg(Registers.A)
        self.memory[address] = value

    # mov 0fe20h,#0abh            ;11 20 ab       saddr
    # mov psw,#0abh               ;11 1e ab
    def _opcode_0x11(self, opcode):
        address = self._consume_saddr()
        value = self._consume_byte()
        if address == 0xff1e: # psw
            self.write_psw(value) # TODO also write it to memory?
        else:
            self.memory[address] = value

    # mov 0fffeh, #0abh           ;13 fe ab       sfr
    def _opcode_0x13(self, opcode):
        address = self._consume_sfr()
        value = self._consume_byte()
        self.memory[address] = value

    def _opcode_0x31(self, opcode):
        opcode2 = self._consume_byte()

        # bt a.bit,$label32             ;31 0e fd
        if opcode2 in (0x0e, 0x1e, 0x2e, 0x3e, 0x4e, 0x5e, 0x6e, 0x7e):
            bit = _bit(opcode2)
            displacement = self._consume_byte()
            value = self.read_gp_reg(Registers.A)
            self._operation_bt(value, bit, displacement)

        # bt 0fffeh.bit,$label24        ;31 06 fe fc    sfr
        elif opcode2 in (0x06, 0x16, 0x26, 0x36, 0x46, 0x56, 0x66, 0x76):
            bit = _bit(opcode2)
            address = self._consume_sfr()
            displacement = self._consume_byte()
            value = self.memory[address]
            self._operation_bt(value, bit, displacement)

        else:
            raise NotImplementedError

    def _opcode_0x61(self, opcode):
        opcode2 = self._consume_byte()

        # sel rbn
        if opcode2 in (0xD0, 0xD8, 0xF0, 0xF8):
            banks_by_opcode2 = {0xD0: 0, 0xD8: 1, 0xF0: 2, 0xF8: 3}
            self.write_rb(banks_by_opcode2[opcode2])

        # or a,reg (except: or a,reg=a)
        elif opcode2 in (0x68, 0x6a, 0x6b, 0x6c, 0x6d, 0x6e, 0x6f):
            a = self.read_gp_reg(Registers.A)
            reg = _reg(opcode2)
            b = self.read_gp_reg(reg)
            result = self._operation_or(a, b)
            self.write_gp_reg(Registers.A, result)

        # or reg,a
        elif opcode2 in (0x60, 0x61, 0x62, 0x63, 0x64, 0x65, 0x66, 0x67):
            a = self.read_gp_reg(Registers.A)
            reg = _reg(opcode2)
            b = self.read_gp_reg(reg)
            result = self._operation_or(a, b)
            self.write_gp_reg(reg, result)

        # and a,reg (except: and a,reg=a)
        elif opcode2 in (0x58, 0x5a, 0x5b, 0x5c, 0x5d, 0x5e, 0x5f):
            a = self.read_gp_reg(Registers.A)
            reg = _reg(opcode2)
            b = self.read_gp_reg(reg)
            result = self._operation_and(a, b)
            self.write_gp_reg(Registers.A, result)

        # and reg,a
        elif opcode2 in (0x50, 0x51, 0x52, 0x53, 0x54, 0x55, 0x56, 0x57):
            a = self.read_gp_reg(Registers.A)
            reg = _reg(opcode2)
            b = self.read_gp_reg(reg)
            result = self._operation_and(a, b)
            self.write_gp_reg(reg, result)

        # xor a,reg (except: xor a,reg=a)
        elif opcode2 in (0x78, 0x7a, 0x7b, 0x7c, 0x7d, 0x7e, 0x7f):
            a = self.read_gp_reg(Registers.A)
            reg = _reg(opcode2)
            b = self.read_gp_reg(reg)
            result = self._operation_xor(a, b)
            self.write_gp_reg(Registers.A, result)

        # xor reg,a
        elif opcode2 in (0x70, 0x71, 0x72, 0x73, 0x74, 0x75, 0x76, 0x77):
            a = self.read_gp_reg(Registers.A)
            reg = _reg(opcode2)
            b = self.read_gp_reg(reg)
            result = self._operation_xor(a, b)
            self.write_gp_reg(reg, result)

        # set1 a.bit
        elif opcode2 in (0x8a, 0x9a, 0xaa, 0xba, 0xca, 0xda, 0xea, 0xfa):
            a = self.read_gp_reg(Registers.A)
            bit = _bit(opcode2)
            result = self._operation_set1(a, bit)
            self.write_gp_reg(Registers.A, result)

        # clr1 a.bit
        elif opcode2 in (0x8b, 0x9b, 0xab, 0xbb, 0xcb, 0xdb, 0xeb, 0xfb):
            a = self.read_gp_reg(Registers.A)
            bit = _bit(opcode2)
            result = self._operation_clr1(a, bit)
            self.write_gp_reg(Registers.A, result)

        # mov1 cy,a.bit
        elif opcode2 in (0x8c, 0x9c, 0xac, 0xbc, 0xcc, 0xdc, 0xec, 0xfc):
            bit = _bit(opcode2)
            src = self.read_gp_reg(Registers.A)
            dest = self.read_psw()
            result = self._operation_mov1(src, bit, dest, 0) # TODO remove hardcoded bit 0 for CY
            self.write_psw(result)

        # mov1 a.bit,cy                 ;61 89
        elif opcode2 in (0x89, 0x99, 0xa9, 0xb9, 0xc9, 0xd9, 0xe9, 0xf9):
            bit = _bit(opcode2)
            src = self.read_psw()
            dest = self.read_gp_reg(Registers.A)
            result = self._operation_mov1(src, 0, dest, bit) # TODO remove hardcoded bit 0 for CY
            self.write_gp_reg(Registers.A, result)

        else:
            raise NotImplementedError()

    def _opcode_0x71(self, opcode):
        opcode2 = self._consume_byte()

        # set1 sfr.bit
        if opcode2 in (0x0a, 0x1a, 0x2a, 0x3a, 0x4a, 0x5a, 0x6a, 0x7a):
            bit = _bit(opcode2)
            address = self._consume_sfr()
            value = self.memory[address]
            result = self._operation_set1(value, bit)
            self.memory[address] = result

        # clr1 sfr.bit
        elif opcode2 in (0x0b, 0x1b, 0x2b, 0x3b, 0x4b, 0x5b, 0x6b, 0x7b):
            bit = _bit(opcode2)
            address = self._consume_sfr()
            value = self.memory[address]
            result = self._operation_clr1(value, bit)
            self.memory[address] = result

        # mov1 cy,0fffeh.bit            ;71 0c fe       sfr
        elif opcode2 in (0x0c, 0x1c, 0x2c, 0x3c, 0x4c, 0x5c, 0x6c, 0x7c):
            bit = _bit(opcode2)
            address = self._consume_sfr()
            src = self.memory[address]
            dest = self.read_gp_reg(Registers.A)
            result = self._operation_mov1(src, bit, dest, 0) # TODO remove hardcoded bit 0 for CY
            self.write_psw(result)

        # mov1 0fffeh.bit,cy            ;71 09 fe       sfr
        elif opcode2 in (0x09, 0x19, 0x29, 0x39, 0x49, 0x59, 0x69, 0x79):
            bit = _bit(opcode2)
            address = self._consume_sfr()
            src = self.read_psw()
            dest = self.memory[address]
            result = self._operation_mov1(src, 0, dest, bit) # TODO remove hardcoded bit 0 for CY
            self.memory[address] = result

        # mov1 0fe20h.bit,cy            ;71 01 20       saddr
        elif opcode2 in (0x01, 0x11, 0x21, 0x31, 0x41, 0x51, 0x61, 0x71):
            bit = _bit(opcode2)
            address = self._consume_saddr()
            src = self.read_psw()
            dest = self.memory[address]
            result = self._operation_mov1(src, 0, dest, bit) # TODO remove hardcoded bit 0 for CY
            self.memory[address] = result

        # mov1 cy,0fe20h.bit            ;71 04 20       saddr
        elif opcode2 in (0x04, 0x14, 0x24, 0x34, 0x44, 0x54, 0x64, 0x74):
            bit = _bit(opcode2)
            address = self._consume_saddr()
            src = self.memory[address]
            dest = self.read_psw()
            result = self._operation_mov1(src, bit, dest, 0) # TODO remove hardcoded bit 0 for CY
            self.write_psw(result)

        else:
            raise NotImplementedError()

    # or a,#0abh                  ;6d ab
    def _opcode_0x6d(self, opcode):
        a = self.read_gp_reg(Registers.A)
        b = self._consume_byte()
        result = self._operation_or(a, b)
        self.write_gp_reg(Registers.A, result)

    # or a,0fe20h                 ;6e 20          saddr
    def _opcode_0x6e(self, opcode):
        a = self.read_gp_reg(Registers.A)
        address = self._consume_saddr()
        b = self.memory[address]
        result = self._operation_or(a, b)
        self.write_gp_reg(Registers.A, result)

    # bt 0fe20h.bit,$label8         ;8c 20 fd       saddr
    def _opcode_0x8c_to_0xfc_bt(self, opcode):
        bit = _bit(opcode)
        address = self._consume_saddr()
        displacement = self._consume_byte()
        value = self.memory[address]
        self._operation_bt(value, bit, displacement)

    # or 0fe20h,#0abh             ;e8 20 ab      saddr
    def _opcode_0xe8(self, opcode):
        address = self._consume_saddr()
        a = self.memory[address]
        b = self._consume_byte()
        result = self._operation_or(a, b)
        self.memory[address] = result

    # or a,!0abcdh                ;68 cd ab
    def _opcode_0x68(self, opcode):
        address = self._consume_addr16()
        a = self.read_gp_reg(Registers.A)
        b = self.memory[address]
        result = self._operation_or(a, b)
        self.write_gp_reg(Registers.A, result)

    # and a,#0abh                 ;5d ab
    def _opcode_0x5d(self, opcode):
        a = self.read_gp_reg(Registers.A)
        b = self._consume_byte()
        result = self._operation_and(a, b)
        self.write_gp_reg(Registers.A, result)

    # and a,0fe20h                ;5e 20          saddr
    def _opcode_0x5e(self, opcode):
        a = self.read_gp_reg(Registers.A)
        address = self._consume_saddr()
        b = self.memory[address]
        result = self._operation_and(a, b)
        self.write_gp_reg(Registers.A, result)

    # and a,!0abcdh               ;58 cd ab
    def _opcode_0x58(self, opcode):
        a = self.read_gp_reg(Registers.A)
        address = self._consume_addr16()
        b = self.memory[address]
        result = self._operation_and(a, b)
        self.write_gp_reg(Registers.A, result)

    # and 0fe20h,#0abh            ;d8 20 ab       saddr
    def _opcode_0xd8(self, opcode):
        address = self._consume_saddr()
        a = self.memory[address]
        b = self._consume_byte()
        result = self._operation_and(a, b)
        self.memory[address] = result

    # xor a,!0abcdh               ;78 cd ab
    def _opcode_0x78(self, opcode):
        a = self.read_gp_reg(Registers.A)
        address = self._consume_addr16()
        b = self.memory[address]
        result = self._operation_xor(a, b)
        self.write_gp_reg(Registers.A, result)

    # xor 0fe20h,#0abh            ;f8 20 ab       saddr
    def _opcode_0xf8(self, opcode):
        address = self._consume_saddr()
        a = self.memory[address]
        b = self._consume_byte()
        result = self._operation_xor(a, b)
        self.memory[address] = result

    # xor a,#0abh                 ;7d ab
    def _opcode_0x7d(self, opcode):
        a = self.read_gp_reg(Registers.A)
        b = self._consume_byte()
        result = self._operation_xor(a, b)
        self.write_gp_reg(Registers.A, result)

    # xor a,0fe20h                ;7e 20          saddr
    def _opcode_0x7e(self, opcode):
        a = self.read_gp_reg(Registers.A)
        address = self._consume_saddr()
        b = self.memory[address]
        result = self._operation_xor(a, b)
        self.write_gp_reg(Registers.A, result)

    # mov a,[de]                  ;85
    def _opcode_0x85(self, opcode):
        address = self.read_gp_regpair(RegisterPairs.DE)
        value = self.memory[address]
        self.write_gp_reg(Registers.A, value)

    # mov [de],a                  ;95
    def _opcode_0x95(self, opcode):
        address = self.read_gp_regpair(RegisterPairs.DE)
        value = self.read_gp_reg(Registers.A)
        self.memory[address] = value

    # mov a,[hl]                  ;87
    def _opcode_0x87(self, opcode):
        address = self.read_gp_regpair(RegisterPairs.HL)
        value = self.memory[address]
        self.write_gp_reg(Registers.A, value)

    # mov [hl],a                  ;97
    def _opcode_0x97(self, opcode):
        address = self.read_gp_regpair(RegisterPairs.HL)
        value = self.read_gp_reg(Registers.A)
        self.memory[address] = value

    # call !0abcdh                ;9a cd ab
    def _opcode_0x9a(self, opcode):
        address = self._consume_addr16()
        self._push_word(self.pc)
        self.pc = address

    # SET1 0fe20h.7               ;7A 20          saddr
    # SET1 PSW.7                  ;7A 1E          (psw=saddr ff1e)
    # EI                          ;7A 1E          alias for SET1 PSW.7
    def _opcode_0x0a_to_0x7a_set1(self, opcode):
        bit = _bit(opcode)
        address = self._consume_saddr()
        value = self.memory[address]
        result = self._operation_set1(value, bit)
        self.memory[address] = result

    # clr1 0fe20h.0               ;0b 20          saddr
    # clr1 psw.0                  ;0b 1e
    # di                          ;7b 1e          alias for clr1 psw.7
    def _opcode_0x0b_to_0x7b_clr(self, opcode):
        bit = _bit(opcode)
        address = self._consume_saddr()
        value = self.memory[address]
        result = self._operation_clr1(value, bit)
        self.memory[address] = result

    # ret                         ;af
    def _opcode_0xaf(self, opcode):
        self.pc = self._pop_word()

    # reti                        ;8f
    def _opcode_0x8f(self, opcode):
        self.pc = self._pop_word()
        self.write_psw(self._pop())

    # br $label7                  ;fa fe
    def _opcode_0xfa(self, opcode):
        displacement = self._consume_byte()
        address = _resolve_rel(self.pc, displacement)
        self.pc = address

    # bc $label3                  ;8d fe
    def _opcode_0x8d(self, opcode):
        displacement = self._consume_byte()
        if self.read_psw() & Flags.CY:
            address = _resolve_rel(self.pc, displacement)
            self.pc = address

    # bnc $label3                 ;9d fe
    def _opcode_0x9d(self, opcode):
        displacement = self._consume_byte()
        if self.read_psw() & Flags.CY == 0:
            address = _resolve_rel(self.pc, displacement)
            self.pc = address

    # bz $label5                  ;ad fe
    def _opcode_0xad(self, opcode):
        displacement = self._consume_byte()
        if self.read_psw() & Flags.Z:
            address = _resolve_rel(self.pc, displacement)
            self.pc = address

    # bnz $label5                 ;bd fe
    def _opcode_0xbd(self, opcode):
        displacement = self._consume_byte()
        if self.read_psw() & Flags.Z == 0:
            address = _resolve_rel(self.pc, displacement)
            self.pc = address

    # movw sp,#0abcdh             ;ee 1c cd ab  (SP=0xFF1C)
    def _opcode_0xee(self, opcode):
        address = self._consume_saddrp()
        address = address # TODO handle saddr's besides sp
        low = self._consume_byte()
        high = self._consume_byte()
        self.sp = (high << 8) + low

    # inc x                       ;40
    # ...
    # inc h                       ;47
    def _opcode_0x40_to_0x47_inc(self, opcode):
        reg = _reg(opcode)
        value = self.read_gp_reg(reg)
        result = self._operation_inc(value)
        self.write_gp_reg(reg, result)

    # dec x                       ;50
    # ...
    # dec h                       ;57
    def _opcode_0x50_to_0x57_dec(self, opcode):
        reg = _reg(opcode)
        value = self.read_gp_reg(reg)
        result = self._operation_dec(value)
        self.write_gp_reg(reg, result)

    # inc 0fe20h                  ;81 20          saddr
    def _opcode_0x81(self, opcode):
        address = self._consume_saddr()
        value = self.memory[address]
        result = self._operation_inc(value)
        self.memory[address] = result

    # dec 0fe20h                  ;91 20          saddr
    def _opcode_0x91(self, opcode):
        address = self._consume_saddr()
        value = self.memory[address]
        result = self._operation_dec(value)
        self.memory[address] = result

    # 0c 00          0c = callf 0800h-08ffh
    # ...
    # 7c 00          7c = callf 0f00h-0fffh
    def _opcode_0x0c_to_0x7c_callf(self, opcode):
        base = 0x0800 + ((opcode >> 4) << 8)
        offset = self._consume_byte()
        self._push_word(self.pc)
        self.pc = base + offset

    # callt [0040h]               ;c1
    # ...
    # callt [007eh]               ;ff
    def _opcode_0xc1_to_0xff_callt(self, opcode):
        # parse vector address from opcode
        offset = (opcode & 0b00111110) >> 1
        vector_address = 0x40 + (offset * 2)

        # read address in vector
        address_low = self.memory[vector_address]
        address_high = self.memory[vector_address+1]
        address = (address_high << 8) + address_low

        self._push_word(self.pc)
        self.pc = address

    # dbnz c,$label1              ;8a fe
    def _opcode_0x8a(self, opcode):
        displacement = self._consume_byte()
        c = self.read_gp_reg(Registers.C) - 1
        if c < 0:
            c = 0xFF
        self.write_gp_reg(Registers.C, c)
        if c != 0:
            address = _resolve_rel(self.pc, displacement)
            self.pc = address

    # dbnz b,$label2              ;8b fe
    def _opcode_0x8b(self, opcode):
        displacement = self._consume_byte()
        c = self.read_gp_reg(Registers.B) - 1
        if c < 0:
            c = 0xFF
        self.write_gp_reg(Registers.B, c)
        if c != 0:
            address = _resolve_rel(self.pc, displacement)
            self.pc = address

    # dbnz 0fe20h,$label0         ;04 20 fd       saddr
    def _opcode_0x04(self, opcode):
        value_address = self._consume_saddr()
        displacement = self._consume_byte()
        value = self.memory[value_address] - 1
        if value < 0:
            value = 0xFF
        self.memory[value_address] = value
        if value != 0:
            address = _resolve_rel(self.pc, displacement)
            self.pc = address

    # push ax                     ;b1
    # ...
    # push hl                     ;b7
    def _opcode_0xb1_to_0xb7_push_rp(self, opcode):
        regpair = _regpair(opcode)
        value = self.read_gp_regpair(regpair)
        self._push_word(value)

    # pop ax                      ;b0
    # ...
    # pop hl                      ;b6
    def _opcode_0xb0_to_0xb6_pop_rp(self, opcode):
        regpair = _regpair(opcode)
        value = self._pop_word()
        self.write_gp_regpair(regpair, value)

    def _operation_bt(self, value, bit, displacement):
        bitweight = 2 ** bit
        if value & bitweight:
            address = _resolve_rel(self.pc, displacement)
            self.pc = address

    def _operation_mov1(self, src, src_bit, dest, dest_bit):
        src_bitweight = 2 ** src_bit
        dest_bitweight = 2 ** dest_bit
        result = dest & ~dest_bitweight
        if src & src_bitweight:
            result |= dest_bitweight
        return result

    def _operation_inc(self, value):
        result = (value + 1) & 0xFF

        psw = self.read_psw() & ~(Flags.Z + Flags.AC)
        if result == 0:
            psw |= Flags.Z
        if (value == 0x0f) and (result == 0x10):
            psw |= Flags.AC
        self.write_psw(psw)

        return result

    def _operation_dec(self, value):
        result = value - 1
        if result < 0:
            result = 0xFF

        psw = self.read_psw() & ~(Flags.Z + Flags.AC)
        if result == 0:
            psw |= Flags.Z
        if (value == 0x10) and (result == 0x0f):
            psw |= Flags.AC
        self.write_psw(psw)

        return result

    def _operation_set1(self, value, bit):
        return value | (2 ** bit)

    def _operation_clr1(self, value, bit):
        return value & ~(2 ** bit)

    def _operation_or(self, a, b):
        result = a | b
        self._update_psw_z(result)
        return result

    def _operation_and(self, a, b):
        result = a & b
        self._update_psw_z(result)
        return result

    def _operation_xor(self, a, b):
        result = a ^ b
        self._update_psw_z(result)
        return result

    def _consume_byte(self):
        value = self.memory[self.pc]
        self.pc = (self.pc + 1) & 0xFFFF
        return value

    def _consume_word(self):
        low = self._consume_byte()
        high = self._consume_byte()
        return _word(low, high)

    def _consume_addr16(self):
        low = self._consume_byte()
        high = self._consume_byte()
        return _addr16(low, high)

    def _consume_sfr(self):
        offset = self._consume_byte()
        return _sfr(offset)

    def _consume_saddr(self):
        offset = self._consume_byte()
        return _saddr(offset)

    def _consume_saddrp(self):
        offset = self._consume_byte()
        return _saddrp(offset)

    # Stack

    def _push(self, value):
        """Push a byte onto the stack"""
        self.sp -= 1
        self.memory[self.sp] = value

    def _pop(self):
        """Pop a byte off the stack"""
        value = self.memory[self.sp]
        self.sp += 1
        return value

    def _push_word(self, value):
        """Push a word onto the stack"""
        self._push(value >> 8)
        self._push(value & 0xFF)

    def _pop_word(self):
        """Pop a word off the stack"""
        low = self._pop()
        high = self._pop()
        return (high << 8) + low

    # Registers

    def read_gp_reg(self, regnum):
        address = self.address_of_gp_reg(regnum)
        return self.memory[address]

    def write_gp_reg(self, regnum, data):
        address = self.address_of_gp_reg(regnum)
        self.memory[address] = data

    def address_of_gp_reg(self, regnum):
        """Return the address in RAM of a general purpose register:
           A, X, B, C, etc."""
        bank_addr = self.REGISTERS_BASE_ADDRESS - (self.read_rb() * 8)
        return bank_addr + regnum

    # Register Pairs

    def read_gp_regpair(self, regpairnum):
        address = self.address_of_gp_regpair(regpairnum)
        low = self.memory[address]
        high = self.memory[address+1]
        return _word(low, high)

    def write_gp_regpair(self, regpairnum, value):
        address = self.address_of_gp_regpair(regpairnum)
        low = value & 0xFF
        high = value >> 8
        self.memory[address] = low
        self.memory[address+1] = high

    def address_of_gp_regpair(self, regpairnum):
        """Return the address in RAM of a general purpose register
           pair: AX, BC, DE, etc.  The pair is stored in two bytes:
           low then high"""
        return self.address_of_gp_reg(regpairnum << 1)

    # Register Banks

    def read_rb(self):
        """Reads PSW and returns a register bank number 0..3"""
        rbs0 = (self.read_psw() & Flags.RBS0) >> 3
        rbs1 = (self.read_psw() & Flags.RBS1) >> 4
        return rbs0 + rbs1

    def write_rb(self, value):
        """Writes a register bank number 0..3 to the PSW"""
        rbs0 = (value & 1) << 3
        rbs1 = (value & 2) << 4
        self.write_psw(self.read_psw() & ~(Flags.RBS0 + Flags.RBS1))
        self.write_psw(self.read_psw() | (rbs0 + rbs1))

    # PSW

    def read_psw(self):
        """Read the PSW"""
        return self.memory[self.PSW_ADDRESS]

    def write_psw(self, value):
        """Write the PSW"""
        self.memory[self.PSW_ADDRESS] = value

    def _update_psw_z(self, value):
        """Set the Z flag in PSW if value is zero, clear otherwise"""
        self.write_psw(self.read_psw() & ~Flags.Z)
        if value == 0:
            self.write_psw(self.read_psw() | Flags.Z)

    def write_memory(self, address, data):
        for address, value in enumerate(data, address):
            self.memory[address] = value

def _sfr(low):
    sfr = 0xff00 + low
    return sfr

def _saddr(low):
    saddr = 0xfe00 + low
    if low < 0x20:
        saddr += 0x100
    return saddr

def _saddrp(low):
    saddrp = _saddr(low)
    if saddrp & 1 != 0:
        raise Exception("saddrp must be an even address")
    return _saddr(low)

def _word(low, high):
    return low + (high << 8)

_addr16 = _word

def _addr16p(low, high):
    addr16p = _addr16(low, high)
    if addr16p & 1 != 0:
        raise Exception("addr16p must be an even address")
    return addr16p

def _reg(opcode):
    return opcode & 0b111

def _regpair(opcode):
    return (opcode >> 1) & 0b11

def _bit(opcode):
    return (opcode & 0b01110000) >> 4

def _resolve_rel(pc, displacement):
    if displacement & 0x80:
        displacement = -((displacement ^ 0xFF) + 1)
    return (pc + displacement) & 0xffff

class Registers(object):
    X = 0
    A = 1
    C = 2
    B = 3
    E = 4
    D = 5
    L = 6
    H = 7

class RegisterPairs(object):
    AX = 0
    BC = 1
    DE = 2
    HL = 3

class Flags(object):
    CY     = 2**0
    ISP    = 2**1
    UNUSED = 2**2
    RBS0   = 2**3
    AC     = 2**4
    RBS1   = 2**5
    Z      = 2**6
    IE     = 2**7


class RegisterTrace:
    NamedRegisters = (
        ('X', Registers.X), ('A', Registers.A), ('C', Registers.C),
        ('B', Registers.B), ('E', Registers.E), ('D', Registers.D),
        ('L', Registers.L), ('H', Registers.H)
    )

    NamedFlags = (
        ('C', Flags.CY), ('I', Flags.ISP), ('U', Flags.UNUSED),
        ('R', Flags.RBS0), ('A', Flags.AC), ('R', Flags.RBS1),
        ('Z', Flags.Z), ('I', Flags.IE)
    )

    @classmethod
    def generate(klass, processor):
        s = ""
        for name, reg in klass.NamedRegisters:
            s += "%s=%02X " % (name, processor.read_gp_reg(reg))
        s += "SP=%04X" % processor.sp
        s += " ["
        psw = processor.read_psw()
        for name, flag in klass.NamedFlags:
            if psw & flag:
                s += name
            else:
                s += '.'
        s += "]"
        return s
