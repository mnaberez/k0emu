class BaseDevice(object):
    def __init__(self, name, high_speed=False):
        """
        high_speed: if True, the processor does not add an extra wait
            state when accessing this device.  On the 78K/0, data operand
            accesses cost 1 bus clock, plus 1 additional clock for devices
            outside the internal high-speed RAM (FB00-FEFF).
        """
        self.name = name
        self.bus = None
        self.size = 0
        self.ticks = 0
        self.high_speed = high_speed

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

    def __init__(self, name, *, size, fill=0x00, writable=True, high_speed=False):
        super().__init__(name, high_speed=high_speed)
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

    def __init__(self, name, high_speed=False):
        super().__init__(name, size=self.SIZE, high_speed=high_speed)


class ProcessorStatusDevice(MemoryDevice):
    """Stack pointer and program status word at FF1C-FF1E.

    Registers:
        0: SPL  (FF1C) - stack pointer low byte
        1: SPH  (FF1D) - stack pointer high byte
        2: PSW  (FF1E) - program status word
    """

    SIZE = 3

    def __init__(self, name, high_speed=False):
        super().__init__(name, size=self.SIZE, high_speed=high_speed)


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

    # Device interrupts
    INT_OVERFLOW = 0

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
            self.bus.interrupt(self, self.INT_OVERFLOW)
        elif mode == self.MODE_NMI:
            self._counter = 0
            # TODO: non-maskable interrupt not yet implemented


class WatchTimerDevice(BaseDevice):
    """Watch timer.

    Registers:
        0: WTNM0 (FF41) - mode control

    Contains two independent timer functions controlled by a single register:

    Interval timer (INTWTNI0): 11-bit prescaler generates periodic interrupts.
        Interval selected by WTNM06:WTNM04 and WTNM07.
        Runs when WTNM00=1.

    Watch timer (INTWTN0): generates longer-interval interrupts (e.g. 0.5s).
        Interval selected by WTNM03:WTNM02 and WTNM07.
        Runs when WTNM00=1 and WTNM01=1.

    Setting WTNM00=0 stops everything and clears both counters.
    Setting WTNM01=0 stops and clears only the watch timer counter.
    """

    # Local register offsets
    WTNM0 = 0  # FF41: mode control

    # WTNM0 bit masks
    WTNM07 = 0x80  # bit 7: fW clock select
    WTNM01 = 0x02  # bit 1: 5-bit counter start
    WTNM00 = 0x01  # bit 0: watch timer enable

    # Device interrupts
    INT_PRESCALER = 0  # interval timer (INTWTNI0)
    INT_WATCH = 1      # watch timer (INTWTN0)

    # INTWTNI0 intervals in CPU cycles, indexed by WTNM06:04 (0-7).
    # interval = 2^(4+n) * fw_divisor
    _PRESCALER_EXPONENTS = [4, 5, 6, 7, 8, 9, 10, 11]

    # INTWTN0 intervals: exponent of fW cycles, indexed by WTNM03:02 (0-3).
    _WATCH_EXPONENTS = [14, 13, 5, 4]

    def __init__(self, name):
        super().__init__(name)
        self.size = 1
        self.reset()

    def reset(self):
        self._wtnm0 = 0x00
        self._prescaler_counter = 0
        self._watch_counter = 0

    def read(self, register):
        self._check_bounds(register)
        return self._wtnm0

    def write(self, register, value):
        self._check_bounds(register)
        old = self._wtnm0
        self._wtnm0 = value

        if not (value & self.WTNM00):
            # Timer disabled: clear both counters
            self._prescaler_counter = 0
            self._watch_counter = 0
        elif not (old & self.WTNM00):
            # Just enabled: clear both counters
            self._prescaler_counter = 0
            self._watch_counter = 0

        if not (value & self.WTNM01):
            # 5-bit counter stopped: clear it
            self._watch_counter = 0

    def tick(self, cycles):
        if not (self._wtnm0 & self.WTNM00):
            return

        prescaler_interval = self.prescaler_interval
        self._prescaler_counter += cycles
        while self._prescaler_counter >= prescaler_interval:
            self._prescaler_counter -= prescaler_interval
            self.bus.interrupt(self, self.INT_PRESCALER)

        if not (self._wtnm0 & self.WTNM01):
            return

        watch_interval = self.watch_interval
        self._watch_counter += cycles
        while self._watch_counter >= watch_interval:
            self._watch_counter -= watch_interval
            self.bus.interrupt(self, self.INT_WATCH)

    @property
    def _fw_divisor(self):
        """CPU cycles per fW clock tick."""
        if self._wtnm0 & self.WTNM07:
            return 1 << 6   # fX / 2^6
        return 1 << 7       # fX / 2^7

    @property
    def prescaler_interval(self):
        """INTWTNI0 interval in CPU cycles."""
        n = (self._wtnm0 >> 4) & 0x07
        exp = self._PRESCALER_EXPONENTS[n]
        return (1 << exp) * self._fw_divisor

    @property
    def watch_interval(self):
        """INTWTN0 interval in CPU cycles."""
        n = (self._wtnm0 >> 2) & 0x03
        exp = self._WATCH_EXPONENTS[n]
        return (1 << exp) * self._fw_divisor


class InterruptControllerDevice(BaseDevice):
    """Interrupt controller for the uPD780833Y subseries.

    The source table and vector addresses are specific to this subseries.
    The uPD78F0831Y is a reduced variant that may not have all sources.

    Registers:
         0: IF0L  (FFE0) - interrupt request flags 0 low
         1: IF0H  (FFE1) - interrupt request flags 0 high
         2: IF1L  (FFE2) - interrupt request flags 1 low
         3: IF1H  (FFE3) - interrupt request flags 1 high
         4: MK0L  (FFE4) - interrupt mask flags 0 low
         5: MK0H  (FFE5) - interrupt mask flags 0 high
         6: MK1L  (FFE6) - interrupt mask flags 1 low
         7: MK1H  (FFE7) - interrupt mask flags 1 high
         8: PR0L  (FFE8) - priority flags 0 low
         9: PR0H  (FFE9) - priority flags 0 high
        10: PR1L  (FFEA) - priority flags 1 low
        11: PR1H  (FFEB) - priority flags 1 high

    Each bit in the IF/MK/PR registers corresponds to an interrupt source
    with a fixed vector address.  Peripherals request interrupts via
    bus.interrupt().  The interrupt controller evaluates pending
    interrupts during tick() and posts the result to bus.pending_interrupt.

    Priority: each source has a default priority (position in _SOURCES).
    The PR bit selects high (0) or low (1) priority.  High-priority
    interrupts can preempt low-priority ISRs.  Among same-priority
    sources, default priority order wins.
    """

    # Register offsets
    IF0L = 0   # FFE0
    IF0H = 1   # FFE1
    IF1L = 2   # FFE2
    IF1H = 3   # FFE3
    MK0L = 4   # FFE4
    MK0H = 5   # FFE5
    MK1L = 6   # FFE6
    MK1H = 7   # FFE7
    PR0L = 8   # FFE8
    PR0H = 9   # FFE9
    PR1L = 10  # FFEA
    PR1H = 11  # FFEB

    SIZE = 12

    # Source indices
    INTWDT    =  0
    INTP0     =  1
    INTP1     =  2
    INTP2     =  3
    INTP3     =  4
    INTP4     =  5
    INTP5     =  6
    INTP6     =  7
    INTP7     =  8
    INTSER0   =  9
    INTSR0    = 10
    INTST0    = 11
    INTCSI30  = 12
    INTCSI31  = 13
    INTIIC0   = 14
    INTC2     = 15
    INTWTNI0  = 16
    INTTM000  = 17
    INTTM010  = 18
    INTTM001  = 19
    INTTM011  = 20
    INTAD00   = 21
    INTAD01   = 22
    INTWTN0   = 23
    INTKR     = 24
    INTTM50   = 25
    INTTM51   = 26
    INTTM52   = 27

    # Interrupt sources: (IF/MK/PR register offset, bit mask, vector address)
    # Ordered by default priority (index 0 = highest).
    _SOURCES = [
        # IF0L / MK0L / PR0L
        (0, 0x01, 0x0004),  # INTWDT
        (0, 0x02, 0x0006),  # INTP0
        (0, 0x04, 0x0008),  # INTP1
        (0, 0x08, 0x000A),  # INTP2
        (0, 0x10, 0x000C),  # INTP3
        (0, 0x20, 0x000E),  # INTP4
        (0, 0x40, 0x0010),  # INTP5
        (0, 0x80, 0x0012),  # INTP6
        # IF0H / MK0H / PR0H
        (1, 0x01, 0x0014),  # INTP7
        (1, 0x02, 0x0016),  # INTSER0
        (1, 0x04, 0x0018),  # INTSR0
        (1, 0x08, 0x001A),  # INTST0
        (1, 0x10, 0x001C),  # INTCSI30
        (1, 0x20, 0x001E),  # INTCSI31
        (1, 0x40, 0x0020),  # INTIIC0
        (1, 0x80, 0x0022),  # INTC2
        # IF1L / MK1L / PR1L
        (2, 0x01, 0x0024),  # INTWTNI0
        (2, 0x02, 0x0026),  # INTTM000
        (2, 0x04, 0x0028),  # INTTM010
        (2, 0x08, 0x002A),  # INTTM001
        (2, 0x10, 0x002C),  # INTTM011
        (2, 0x20, 0x002E),  # INTAD00
        (2, 0x40, 0x0030),  # INTAD01
        # IF1L bit 7 is reserved
        # IF1H / MK1H / PR1H
        (3, 0x01, 0x0034),  # INTWTN0
        (3, 0x02, 0x0036),  # INTKR
        (3, 0x04, 0x0038),  # INTTM50
        (3, 0x08, 0x003A),  # INTTM51
        (3, 0x10, 0x003C),  # INTTM52
        # IF1H bits 5-7 are reserved
    ]

    NUM_SOURCES = len(_SOURCES)

    def __init__(self, name):
        super().__init__(name)
        self.size = self.SIZE
        self._connections = {}  # (device, device_int) -> source_index
        self.reset()

    def connect(self, device, device_int, source_index):
        """Connect a device interrupt to a source channel."""
        self._connections[(id(device), device_int)] = source_index

    def interrupt(self, device, device_int):
        """Set the IF flag for a connected device interrupt."""
        source_index = self._connections[(id(device), device_int)]
        reg_offset, bit, vector = self._SOURCES[source_index]
        self._regs[reg_offset] |= bit

    def reset(self):
        self._regs = bytearray(self.SIZE)
        # MK registers reset to 0xFF (all interrupts masked)
        for i in range(4, 8):
            self._regs[i] = 0xFF
        # PR registers reset to 0xFF (all low priority)
        for i in range(8, 12):
            self._regs[i] = 0xFF

    def read(self, register):
        self._check_bounds(register)
        return self._regs[register]

    def write(self, register, value):
        self._check_bounds(register)
        self._regs[register] = value

    def tick(self, cycles):
        """Evaluate pending interrupts and post result to the bus."""
        from k0emu.bus import PendingInterrupt
        best = None

        for index, (reg_offset, bit, vector) in enumerate(self._SOURCES):
            if_val = self._regs[reg_offset]
            mk_val = self._regs[reg_offset + 4]
            pr_val = self._regs[reg_offset + 8]

            if not (if_val & bit):
                continue  # not requested
            if mk_val & bit:
                continue  # masked

            is_high = not (pr_val & bit)  # PR bit 0 = high priority

            if is_high:
                best = PendingInterrupt(index, True, vector)
                break

            if best is None:
                best = PendingInterrupt(index, False, vector)
            # First match wins (default priority order)

        self.bus.pending_interrupt = best

    def acknowledge_interrupt(self, source_index):
        """Clear the IF flag for the given source."""
        reg_offset, bit, vector = self._SOURCES[source_index]
        self._regs[reg_offset] &= ~bit
