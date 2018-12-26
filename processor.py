
class Processor(object):
    REGISTERS_BASE = 0xFEF8

    def __init__(self):
        self.memory = bytearray(0x10000)
        self.pc = 0
        self.psw = 0
        self.rb = 0

    def step(self):
        opcode = self.memory[self.pc]
        # nop
        if opcode == 0x00:
            self.pc += 1

        # not1 cy
        elif opcode == 0x01:
            bitweight = Flags.CY
            carry = self.psw & bitweight
            if carry:
                self.psw &= ~bitweight
            else:
                self.psw |= bitweight
            self.pc += 1

        # movw ax,0fe20h              ;02 CE AB       addr16p
        elif opcode == 0x02:
            addr16p = _addr16p(self.memory[self.pc+1],
                               self.memory[self.pc+2])
            data = self.memory[addr16p]
            self._op_movw(addr16p, data)
            # TODO finish me

        # set1 cy
        elif opcode == 0x20:
            bitweight = Flags.CY
            self.psw |= bitweight
            self.pc += 1

        # clr1 cy
        elif opcode == 0x21:
            bitweight = Flags.CY
            self.psw &= ~bitweight
            self.pc += 1

        # xch a,REG                    ;32...
        elif opcode & 0b00110000 == 0b00110000:
            # TODO handle xch a,a which is illegal
            other_reg = opcode & 0b111
            a_value = self.read_gp_reg(Registers.A)
            other_value = self.read_gp_reg(other_reg)
            self.write_gp_reg(Registers.A, other_value)
            self.write_gp_reg(other_reg, a_value)
            self.pc += 1

        # xch a,!abcd                 ;ce cd ab
        elif opcode == 0xce:
            addr16 = _addr16(self.memory[self.pc+1],
                             self.memory[self.pc+2])
            a_value = self.read_gp_reg(Registers.A)
            other_value = self.memory[addr16]
            self.write_gp_reg(Registers.A, other_value)
            self.memory[addr16] = a_value
            self.pc += 3

        # xch a,0fe20h                ;83 20          saddr
        elif opcode == 0x83:
            saddr = _saddr(self.memory[self.pc+1])
            a_value = self.read_gp_reg(Registers.A)
            other_value = self.memory[saddr]
            self.write_gp_reg(Registers.A, other_value)
            self.memory[saddr] = a_value
            self.pc += 2

        # xch a,0fffeh                ;93 fe          sfr
        elif opcode == 0x93:
            sfr = _sfr(self.memory[self.pc+1])
            a_value = self.read_gp_reg(Registers.A)
            other_value = self.memory[sfr]
            self.write_gp_reg(Registers.A, other_value)
            self.memory[sfr] = a_value
            self.pc += 2

        # br !0abcdh                  ;9b cd ab
        elif opcode == 0x9b:
            addr16 = _addr16(self.memory[self.pc+1],
                             self.memory[self.pc+2])
            self.pc = addr16

        # mov r,#byte
        elif opcode & 0b11111000 == 0b10100000:
            regnum = opcode & 0b00000111
            immbyte = self.memory[self.pc+1]
            self._op_mov(regnum, immbyte)
            self.pc += 2

        # sel rbn
        elif opcode & 0b01100001:
            opcode2 = self.memory[self.pc+1]
            if opcode2 & 0b1100111 == 0b1100000: # sel rbn
                self.rb = opcode2 >> 3
                self.pc += 1
            else:
                raise NotImplementedError()
        else:
            raise NotImplementedError()

    def _op_mov(self, regnum, data):
        self.write_gp_reg(regnum, data)

    def _op_movw(self, regpairnum, data):
        pass

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
