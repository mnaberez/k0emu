
class Processor(object):
    REGISTERS_BASE = 0xFEF8

    def __init__(self):
        self.memory = bytearray(0x10000)
        self.pc = 0
        self.psw = 0
        self.rb = 0

    def step(self):
        opcode = self._consume_byte()
        # nop
        if opcode == 0x00:
            pass

        # not1 cy
        elif opcode == 0x01:
            bitweight = Flags.CY
            carry = self.psw & bitweight
            if carry:
                self.psw &= ~bitweight
            else:
                self.psw |= bitweight

        # set1 cy
        elif opcode == 0x20:
            bitweight = Flags.CY
            self.psw |= bitweight

        # clr1 cy
        elif opcode == 0x21:
            bitweight = Flags.CY
            self.psw &= ~bitweight

        # xch a,REG                    ;32...37 except 31
        elif opcode in (0x30, 0x32, 0x33, 0x34, 0x35, 0x36, 0x37):
            other_reg = opcode & 0b111
            a_value = self.read_gp_reg(Registers.A)
            other_value = self.read_gp_reg(other_reg)
            self.write_gp_reg(Registers.A, other_value)
            self.write_gp_reg(other_reg, a_value)

        # xch a,!abcd                 ;ce cd ab
        elif opcode == 0xce:
            address = self._consume_addr16()
            a_value = self.read_gp_reg(Registers.A)
            other_value = self.memory[address]
            self.write_gp_reg(Registers.A, other_value)
            self.memory[address] = a_value

        # xch a,0fe20h                ;83 20          saddr
        elif opcode == 0x83:
            address = self._consume_saddr()
            a_value = self.read_gp_reg(Registers.A)
            other_value = self.memory[address]
            self.write_gp_reg(Registers.A, other_value)
            self.memory[address] = a_value

        # xch a,0fffeh                ;93 fe          sfr
        elif opcode == 0x93:
            address = self._consume_sfr()
            a_value = self.read_gp_reg(Registers.A)
            other_value = self.memory[address]
            self.write_gp_reg(Registers.A, other_value)
            self.memory[address] = a_value

        # br !0abcdh                  ;9b cd ab
        elif opcode == 0x9b:
            address = self._consume_addr16()
            self.pc = address

        # mov r,#byte                 ;a0..a7 xx
        elif opcode & 0b11111000 == 0b10100000:
            regnum = opcode & 0b00000111
            immbyte = self._consume_byte()
            self.write_gp_reg(regnum, immbyte)

        # mov a,x ... mov a,h           ;60..67 except 61
        elif opcode in (0x60, 0x62, 0x63, 0x64, 0x65, 0x66, 0x67):
            reg = _reg(opcode)
            value = self.read_gp_reg(reg)
            self.write_gp_reg(Registers.A, value)

        # mov x,a ... mov h,a           ;70..77 except 71
        elif opcode in (0x70, 0x72, 0x73, 0x74, 0x75, 0x76, 0x77):
            reg = _reg(opcode)
            value = self.read_gp_reg(Registers.A)
            self.write_gp_reg(reg, value)

        # mov a,!addr16                 ;8e
        elif opcode == 0x8e:
            address = self._consume_addr16()
            value = self.memory[address]
            self.write_gp_reg(Registers.A, value)

        # mov !addr16,a               ;9e cd ab
        elif opcode == 0x9e:
            address = self._consume_addr16()
            value = self.read_gp_reg(Registers.A)
            self.memory[address] = value

        # mov a,0fe20h                ;F0 20          saddr
        elif opcode == 0xf0:
            address = self._consume_saddr()
            value = self.memory[address]
            self.write_gp_reg(Registers.A, value)

        # mov 0fe20h,a                ;f2 20          saddr
        elif opcode == 0xf2:
            address = self._consume_saddr()
            value = self.read_gp_reg(Registers.A)
            self.memory[address] = value

        # mov a,0fffeh                ;f4 fe          sfr
        elif opcode == 0xf4:
            address = self._consume_sfr()
            value = self.memory[address]
            self.write_gp_reg(Registers.A, value)
            self.memory[address] = value

        # mov 0fffeh,a                ;f6 fe          sfr
        elif opcode == 0xf6:
            address = self._consume_sfr()
            value = self.read_gp_reg(Registers.A)
            self.memory[address] = value

        # mov 0fe20h,#0abh            ;11 20 ab       saddr
        elif opcode == 0x11:
            address = self._consume_saddr()
            value = self._consume_byte()
            self.memory[address] = value

        # mov 0fffeh, #0abh           ;13 fe ab       sfr
        elif opcode == 0x13:
            address = self._consume_sfr()
            value = self._consume_byte()
            self.memory[address] = value

        elif opcode == 0x61:
            opcode2 = self._consume_byte()

            # sel rbn
            if opcode2 in (0xD0, 0xD8, 0xF0, 0xF8): # sel rbn
                banks_by_opcode2 = {0xD0: 0, 0xD8: 1, 0xF0: 2, 0xF8: 3}
                self.rb = banks_by_opcode2[opcode2]
            else:
                raise NotImplementedError()
        else:
            raise NotImplementedError()

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
        # General Purpose Registers: Page 17
        # Bank 3 = FEE0 - FEE7
        # Bank 2 = FEE8 - FEEF
        # Bank 1 = FEF0 - FEF7
        # Bank 0 = FEF8 - FEFF
        bank_addr = self.REGISTERS_BASE - (self.rb * 8)
        return bank_addr + regnum

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
