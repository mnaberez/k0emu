
class Processor(object):
    REGISTERS_BASE = 0xFEF8

    def __init__(self):
        self.memory = bytearray(0x10000)
        self.pc = 0
        self.psw = 0
        self.rb = 0

    def step(self):
        opcode = self.memory[self.pc]
        if opcode == 0: # nop
            self.pc += 1
        elif opcode & 0b11111000 == 0b10100000: # mov r,#byte
            regnum = opcode & 0b00000111
            immbyte = self.memory[self.pc+1]
            self._op_mov(regnum, immbyte)
            self.pc += 2
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

Registers = {'X': 0,
             'A': 1,
             'C': 2,
             'B': 3,
             'E': 4,
             'D': 5,
             'L': 6,
             'H': 7}
