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


class WatchdogDevice(BaseDevice):
    """Watchdog timer.

    Registers:
        0: WDCS  (FF42) - clock selection, write-only
        1: WDTM  (FFF9) - mode control

    Three operating modes selected by WDTM4:WDTM3:
        0,x -> interval timer: maskable INTWDT on overflow
        1,0 -> watchdog mode 1: non-maskable INTWDT on overflow
        1,1 -> watchdog mode 2: internal reset on overflow

    Writing WDTM with RUN=1 clears the counter and restarts counting.
    RUN, WDTM4, and WDTM3 are one-way latches: once set to 1, they
    cannot be cleared to 0 by software.  Only hardware reset clears them.
    """

    # Local register offsets
    WDCS = 0   # FF42: clock selection
    WDTM = 1   # FFF9: mode control

    # WDTM bit masks
    RUN   = 0x80  # bit 7: start/restart (one-way latch)
    WDTM4 = 0x10  # bit 4: watchdog vs interval mode (one-way latch)
    WDTM3 = 0x08  # bit 3: reset vs NMI in watchdog mode (one-way latch)

    # Operating modes
    MODE_INTERVAL = 0  # WDTM4=0: maskable INTWDT
    MODE_NMI = 1       # WDTM4=1, WDTM3=0: non-maskable INTWDT
    MODE_RESET = 2     # WDTM4=1, WDTM3=1: internal reset

    # Overflow intervals in CPU cycles: 2^(12+n) for n=0..6, 2^20 for n=7
    _INTERVALS = [
        1 << 12,  # WDCS=0: 4096
        1 << 13,  # WDCS=1: 8192
        1 << 14,  # WDCS=2: 16384
        1 << 15,  # WDCS=3: 32768
        1 << 16,  # WDCS=4: 65536
        1 << 17,  # WDCS=5: 131072
        1 << 18,  # WDCS=6: 262144
        1 << 20,  # WDCS=7: 1048576
    ]

    def __init__(self, name):
        super().__init__(name)
        self.size = 2
        self.reset()

    def reset(self):
        self._wdcs = 0x00
        self._wdtm = 0x00
        self._counter = 0

    def read(self, register):
        self._check_bounds(register)
        if register == self.WDCS:
            return 0x00  # write-only, reads as 0
        return self._wdtm

    def write(self, register, value):
        self._check_bounds(register)
        if register == self.WDCS:
            self._wdcs = value & 0x07
        elif register == self.WDTM:
            # One-way latches: bits can go 0->1 but never 1->0
            self._wdtm |= value & (self.RUN | self.WDTM4 | self.WDTM3)
            if value & self.RUN:
                self._counter = 0  # kick: clear counter and restart

    def tick(self, cycles):
        if self.running:
            self._counter += cycles
            if self._counter >= self.interval:
                self._overflow()

    @property
    def mode(self):
        if not (self._wdtm & self.WDTM4):
            return self.MODE_INTERVAL
        if not (self._wdtm & self.WDTM3):
            return self.MODE_NMI
        return self.MODE_RESET

    @property
    def running(self):
        return bool(self._wdtm & self.RUN)

    @property
    def interval(self):
        return self._INTERVALS[self._wdcs]

    def _overflow(self):
        mode = self.mode
        if mode == self.MODE_RESET:
            self.bus.reset()
        elif mode == self.MODE_INTERVAL:
            self._counter = 0
            intc = self.bus.device("intc")
            intc.set_flag(0, 0x01)  # TODO: WDTIF: IF0L bit 0
        elif mode == self.MODE_NMI:
            self._counter = 0
            # TODO: non-maskable interrupt not yet implemented


class RegisterFileDevice(MemoryDevice):
    """The 4 register banks at FEE0-FEFF (32 bytes).
    Each bank has 8 registers: X, A, C, B, E, D, L, H."""

    NUM_BANKS = 4
    REGS_PER_BANK = 8
    SIZE = NUM_BANKS * REGS_PER_BANK

    def __init__(self, name):
        super().__init__(name, size=self.SIZE)
