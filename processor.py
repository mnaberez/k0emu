
class Processor(object):
    REGISTERS_BASE_ADDRESS = 0xFEF8
    PSW_ADDRESS = 0xFF1E

    def __init__(self):
        self.memory = bytearray(0x10000)
        self.pc = 0
        self.sp = 0xfe1f
        self._build_opcode_map()

    def step(self):
        opcode = self._consume_byte()
        handler = self._opcode_map[opcode]
        handler(opcode)

    def _build_opcode_map(self):
        self._opcode_map = {}
        for opcode in range(0x100):
            if opcode == 0x00:
                f = self._opcode_0x00 # nop
            elif opcode == 0x01:
                f = self._opcode_0x01 # not1 cy
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
            self._opcode_map[opcode] = f

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

    # call !0abcdh                ;9a cd ab
    def _opcode_0x9a(self, opcode):
        address = self._consume_addr16()
        self._push(self.pc >> 8)
        self._push(self.pc & 0xFF)
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

    # ret                         ;af
    def _opcode_0xaf(self, opcode):
        address_low = self._pop()
        address_high = self._pop()
        self.pc = (address_high << 8) + address_low

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

    def _push(self, value):
        """Push a byte onto the stack"""
        self.sp -= 1
        self.memory[self.sp] = value

    def _pop(self):
        """Pop a byte off the stack"""
        value = self.memory[self.sp]
        self.sp += 1
        return value

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
        self.pc += 1
        return value

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

    def read_gp_reg(self, regnum):
        address = self.address_of_gp_reg(regnum)
        return self.memory[address]

    def write_gp_reg(self, regnum, data):
        address = self.address_of_gp_reg(regnum)
        self.memory[address] = data

    def address_of_gp_reg(self, regnum):
        """Return the address in RAM of a general purpose register"""
        bank_addr = self.REGISTERS_BASE_ADDRESS - (self.read_rb() * 8)
        return bank_addr + regnum

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

def _addr16(low, high):
    return low + (high << 8)

def _addr16p(low, high):
    addr16p = _addr16(low, high)
    if addr16p & 1 != 0:
        raise Exception("addr16p must be an even address")
    return addr16p

def _reg(opcode):
    return opcode & 0b111

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
