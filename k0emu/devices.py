class BaseDevice(object):
    def __init__(self, name):
        self.name = name
        self.bus = None
        self.size = 0
        self.ticks = 0

    def _check_bounds(self, register):
        if register < 0 or register >= self.size:
            raise IndexError("%s: register 0x%04X out of range (size=0x%04X)" %
                             (self.name, register, self.size))

    def read(self, register):
        return 0

    def write(self, register, value):
        pass

    def reset(self):
        pass

    def tick(self, cycles):
        self.ticks += cycles


class MemoryDevice(BaseDevice):
    """A generic read/write memory device (RAM or ROM).
    Covers a contiguous address range on the bus."""

    def __init__(self, name, *, size, fill=0x00, writable=True):
        super().__init__(name)
        self.size = size
        self._data = bytearray([fill]) * size
        self._writable = writable

    def read(self, register):
        self._check_bounds(register)
        return self._data[register]

    def write(self, register, value):
        self._check_bounds(register)
        if self._writable:
            self._data[register] = value

    def load(self, register, data):
        """Write directly to backing store, bypassing the writable flag.
        Used for loading firmware images and test code."""
        self._check_bounds(register)
        self._check_bounds(register + len(data) - 1)
        self._data[register:register + len(data)] = data


class RegisterFileDevice(MemoryDevice):
    """The 4 register banks at FEE0-FEFF (32 bytes).
    Each bank has 8 registers: X, A, C, B, E, D, L, H."""

    NUM_BANKS = 4
    REGS_PER_BANK = 8
    SIZE = NUM_BANKS * REGS_PER_BANK

    def __init__(self, name):
        super().__init__(name, size=self.SIZE)
