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
        if self._prescaler_counter >= prescaler_interval:
            self._prescaler_counter %= prescaler_interval
            self.bus.interrupt(self, self.INT_PRESCALER)

        if not (self._wtnm0 & self.WTNM01):
            return

        watch_interval = self.watch_interval
        self._watch_counter += cycles
        if self._watch_counter >= watch_interval:
            self._watch_counter %= watch_interval
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


class I2CDevice(BaseDevice):
    """I2C serial interface controller (IIC0).

    Registers:
        0: IIC0   (FF1F) - shift register (data)
        1: IICC0  (FFA8) - control
        2: IICS0  (FFA9) - status
        3: IICCL0 (FFAA) - clock selection

    Operates as I2C bus master.  When firmware triggers a start
    condition, the controller reads the address byte from IIC0,
    matches it against registered target devices, and completes
    the transfer immediately (no clock-level simulation).

    Each completed byte transfer sets the IICIF0 interrupt flag.
    """

    # Register offsets
    IIC0   = 0  # FF1F: shift register
    IICC0  = 1  # FFA8: control
    IICS0  = 2  # FFA9: status
    IICCL0 = 3  # FFAA: clock selection

    # IICC0 bits
    IICE0 = 0x80  # I2C enable
    LREL0 = 0x40  # exit communications
    WREL0 = 0x20  # cancel wait
    SPIE0 = 0x10  # stop interrupt enable
    WTIM0 = 0x08  # wait timing
    ACKE0 = 0x04  # acknowledge enable
    STT0  = 0x02  # start condition trigger
    SPT0  = 0x01  # stop condition trigger

    # IICS0 bits
    MSTS0 = 0x80  # master status
    EXC0  = 0x40  # extension code
    COI0  = 0x20  # address match
    TRC0  = 0x08  # transmit/receive
    ACKD0 = 0x04  # ACK detected
    STD0  = 0x01  # stop detected

    # Device interrupt
    INT_TRANSFER = 0

    def __init__(self, name):
        super().__init__(name)
        self.size = 4
        self._targets = {}  # I2C 7-bit address -> target object
        self.reset()

    def add_target(self, i2c_address, target):
        """Register an I2C target device at the given 7-bit address."""
        self._targets[i2c_address] = target

    def reset(self):
        self._iic0 = 0x00
        self._iicc0 = 0x00
        self._iics0 = 0x00
        self._iiccl0 = 0x00
        self._active_target = None
        self._is_read = False
        self._waiting = False  # controller is in wait state

    def read(self, register):
        self._check_bounds(register)
        if register == self.IIC0:
            return self._iic0
        elif register == self.IICC0:
            return self._iicc0
        elif register == self.IICS0:
            return self._iics0
        elif register == self.IICCL0:
            val = self._iiccl0
            if self._iicc0 & self.IICE0:
                val |= 0x30  # DAD0=1, CLD0=1 (bus idle, lines high)
            return val
        return 0

    def write(self, register, value):
        self._check_bounds(register)
        if register == self.IIC0:
            self._iic0 = value
            if self._waiting:
                self._do_next_byte()
        elif register == self.IICC0:
            self._write_iicc0(value)
        elif register == self.IICS0:
            self._iics0 = value
        elif register == self.IICCL0:
            self._iiccl0 = value

    def _write_iicc0(self, value):
        old = self._iicc0
        self._iicc0 = value

        if not (value & self.IICE0):
            self._iics0 = 0x00
            self._active_target = None
            self._waiting = False
            return

        if (value & self.STT0) and not (old & self.STT0):
            self._do_start()

        if (value & self.SPT0) and not (old & self.SPT0):
            self._do_stop()

        if (value & self.WREL0) and not (old & self.WREL0):
            self._do_next_byte()

    def _do_start(self):
        """Handle start condition: read address byte from IIC0."""
        addr_byte = self._iic0
        i2c_addr = addr_byte >> 1
        self._is_read = bool(addr_byte & 0x01)

        self._iics0 = self.MSTS0 | self.TRC0  # master, transmit mode

        if i2c_addr in self._targets:
            self._active_target = self._targets[i2c_addr]
            self._active_target.i2c_start(self._is_read)
            self._iics0 |= self.ACKD0
        else:
            self._active_target = None

        self._iicc0 &= ~self.STT0
        self._waiting = True
        self.bus.interrupt(self, self.INT_TRANSFER)

    def _do_stop(self):
        """Handle stop condition."""
        if self._active_target is not None:
            self._active_target.i2c_stop()
            self._active_target = None
        self._waiting = False
        self._iics0 |= self.STD0
        self._iicc0 &= ~self.SPT0
        self.bus.interrupt(self, self.INT_TRANSFER)

    def _do_next_byte(self):
        """Handle wait release: transfer next data byte."""
        self._iicc0 &= ~self.WREL0

        if self._active_target is None:
            self._iics0 &= ~self.ACKD0
            self.bus.interrupt(self, self.INT_TRANSFER)
            return

        if self._is_read:
            self._iic0 = self._active_target.i2c_read()
            self._iics0 &= ~self.TRC0
            self._iics0 |= self.ACKD0
        else:
            ack = self._active_target.i2c_write(self._iic0)
            self._iics0 |= self.TRC0
            if ack:
                self._iics0 |= self.ACKD0
            else:
                self._iics0 &= ~self.ACKD0

        self._waiting = True
        self.bus.interrupt(self, self.INT_TRANSFER)


class I2CTargetStub(object):
    """Stub I2C target that ACKs everything and returns a configurable value.
    Used for peripherals we don't fully emulate yet."""

    def __init__(self, read_value=0xFF):
        self._read_value = read_value

    def i2c_start(self, is_read):
        pass

    def i2c_stop(self):
        pass

    def i2c_read(self):
        return self._read_value

    def i2c_write(self, data):
        return True  # ACK


class EepromDevice(object):
    """M24C04 I2C EEPROM (512 bytes).

    This is an I2C target, not a bus device.  It is registered on the
    I2CDevice via add_target() at two I2C addresses: 0x50 for the lower
    256 bytes and 0x51 for the upper 256 bytes.

    Both addresses share the same backing store.  The page_offset
    parameter to the constructor selects which half (0 or 256).
    """

    def __init__(self, data, page_offset):
        self._data = data
        self._page_offset = page_offset
        self._address = 0
        self._address_set = False

    def i2c_start(self, is_read):
        if not is_read:
            self._address_set = False

    def i2c_stop(self):
        pass

    def i2c_read(self):
        addr = self._page_offset + self._address
        value = self._data[addr]
        self._address = (self._address + 1) % 256
        return value

    def i2c_write(self, data):
        if not self._address_set:
            self._address = data
            self._address_set = True
        else:
            addr = self._page_offset + self._address
            self._data[addr] = data
            self._address = (self._address + 1) % 256
        return True  # ACK


class PortDevice(MemoryDevice):
    """Port I/O data registers (P0-P9 at FF00-FF09).

    This is a simplified implementation that returns whatever was last
    written, with initial values chosen to make the firmware boot into
    normal operation.  A proper implementation would model input vs
    output pins using the port mode registers.

    Initial values and the reasons they are needed:
        P0 (FF00): 0xFB - P0.2 low prevents halt/wakeup mode
        P1 (FF01): 0xFF - all high (pull-ups)
        P2 (FF02): 0xFF - all high (pull-ups)
        P3 (FF03): 0xFF - all high (pull-ups)
        P4 (FF04): 0xFF - all high (pull-ups)
        P5 (FF05): 0xFF - all high (pull-ups)
        P6 (FF06): 0xFF - all high (pull-ups)
        P7 (FF07): 0xFF - all high (pull-ups)
        P8 (FF08): 0xFF - all high (pull-ups)
        P9 (FF09): 0xFF - all high (pull-ups)
    """

    NUM_PORTS = 10

    # Default pin states for normal radio operation
    _DEFAULTS = [
        0xFB,  # P0: P0.2 low prevents halt/wakeup mode
        0xFF,  # P1
        0xFF,  # P2
        0xFF,  # P3
        0xFF,  # P4
        0xFF,  # P5
        0xFF,  # P6
        0xFF,  # P7
        0xFF,  # P8
        0xFF,  # P9: P9.0 high = S-Contact (ignition) on
    ]

    # Bits forced high on read (external input pins active)
    _FORCE_HIGH = [
        0x00,  # P0
        0x00,  # P1
        0x00,  # P2
        0x00,  # P3
        0x00,  # P4
        0x00,  # P5
        0x00,  # P6
        0x00,  # P7
        0x00,  # P8
        0x00,  # P9: S-Contact off at boot
    ]

    def __init__(self, name):
        super().__init__(name, size=self.NUM_PORTS)

    def read(self, register):
        self._check_bounds(register)
        return self._data[register] | self._FORCE_HIGH[register]

    def reset(self):
        for i in range(self.NUM_PORTS):
            self._data[i] = self._DEFAULTS[i]


class UPD16432BDevice(object):
    """NEC uPD16432B LCD controller.

    This is an SPI target behind CSI30, not a bus device.  It processes
    commands from the radio to update display RAM, pictograph RAM,
    chargen RAM, and LED output latches.  It also provides key scan data.
    """

    RAM_NONE = 0xFF
    RAM_DISPLAY = 0
    RAM_PICTOGRAPH = 1
    RAM_CHARGEN = 2
    RAM_LED = 3

    DISPLAY_RAM_SIZE = 0x19
    PICTOGRAPH_RAM_SIZE = 0x08
    CHARGEN_RAM_SIZE = 0x70
    LED_RAM_SIZE = 0x01

    def __init__(self):
        self.display_ram = bytearray(self.DISPLAY_RAM_SIZE)
        self.pictograph_ram = bytearray(self.PICTOGRAPH_RAM_SIZE)
        self.chargen_ram = bytearray(self.CHARGEN_RAM_SIZE)
        self.led_ram = bytearray(self.LED_RAM_SIZE)
        self.key_data = bytearray(4)
        self.dirty_flags = 0
        self._ram_area = self.RAM_NONE
        self._ram_size = 0
        self._address = 0
        self._increment = False
        self._cmd_buf = []

    def spi_begin(self):
        """STB asserted (high) — start of SPI command."""
        self._cmd_buf = []

    def spi_exchange(self, tx_byte):
        """Exchange one SPI byte.  Returns the byte to send back (MISO)."""
        self._cmd_buf.append(tx_byte)
        index = len(self._cmd_buf) - 1
        if index < len(self.key_data) and len(self._cmd_buf) > 0:
            if (self._cmd_buf[0] & 0x44) == 0x44:
                return self.key_data[index]
        return 0x00

    def spi_end(self):
        """STB deasserted (low) — end of SPI command, process it."""
        if len(self._cmd_buf) == 0:
            return
        if (self._cmd_buf[0] & 0x44) == 0x44:
            return
        self._process_command()

    def _process_command(self):
        cmd_type = self._cmd_buf[0] & 0xC0
        if cmd_type == 0x40:
            self._process_data_setting()
        elif cmd_type == 0x80:
            self._process_address_setting()
        if self._ram_area != self.RAM_NONE and len(self._cmd_buf) > 1:
            for b in self._cmd_buf[1:]:
                self._write_data_byte(b)

    def _process_data_setting(self):
        mode = self._cmd_buf[0] & 0x07
        ram_map = {
            self.RAM_DISPLAY:    (self.display_ram, self.DISPLAY_RAM_SIZE),
            self.RAM_PICTOGRAPH: (self.pictograph_ram, self.PICTOGRAPH_RAM_SIZE),
            self.RAM_CHARGEN:    (self.chargen_ram, self.CHARGEN_RAM_SIZE),
            self.RAM_LED:        (self.led_ram, self.LED_RAM_SIZE),
        }
        if mode in ram_map:
            self._ram_area = mode
            _, self._ram_size = ram_map[mode]
        else:
            self._ram_area = self.RAM_NONE
            self._ram_size = 0
            self._address = 0
        if mode in (self.RAM_DISPLAY, self.RAM_PICTOGRAPH):
            self._increment = not bool(self._cmd_buf[0] & 0x08)
        else:
            self._increment = True
            self._address = 0

    def _process_address_setting(self):
        address = self._cmd_buf[0] & 0x1F
        if self._ram_area == self.RAM_CHARGEN:
            if address < 0x10:
                self._address = address * 7
            else:
                self._address = 0
        else:
            self._address = address
            self._wrap_address()

    def _write_data_byte(self, b):
        if self._ram_area == self.RAM_DISPLAY:
            if self._address < self.DISPLAY_RAM_SIZE:
                if self.display_ram[self._address] != b:
                    self.display_ram[self._address] = b
                    self.dirty_flags |= (1 << self.RAM_DISPLAY)
        elif self._ram_area == self.RAM_PICTOGRAPH:
            if self._address < self.PICTOGRAPH_RAM_SIZE:
                if self.pictograph_ram[self._address] != b:
                    self.pictograph_ram[self._address] = b
                    self.dirty_flags |= (1 << self.RAM_PICTOGRAPH)
        elif self._ram_area == self.RAM_CHARGEN:
            if self._address < self.CHARGEN_RAM_SIZE:
                if self.chargen_ram[self._address] != b:
                    self.chargen_ram[self._address] = b
                    self.dirty_flags |= (1 << self.RAM_CHARGEN)
        elif self._ram_area == self.RAM_LED:
            if self._address < self.LED_RAM_SIZE:
                if self.led_ram[self._address] != b:
                    self.led_ram[self._address] = b
                    self.dirty_flags |= (1 << self.RAM_LED)
        else:
            return
        if self._increment:
            self._address += 1
            self._wrap_address()

    def _wrap_address(self):
        if self._ram_size > 0 and self._address >= self._ram_size:
            self._address = 0


class CSI30Device(BaseDevice):
    """CSI30 serial interface.

    Registers:
        0: SIO30  (FF1A) - shift register
        1: CSIM30 (FFB0) - mode control

    When firmware writes a byte to SIO30, a transfer is initiated
    and completed immediately.  Sets CSIIF30 interrupt flag.

    Optionally has a UPD16432BDevice attached as the SPI target.
    STB (chip select) is detected from P4.7 on each SIO30 write.
    """

    # Register offsets
    SIO30  = 0  # FF1A: shift register
    CSIM30 = 1  # FFB0: mode control

    # Device interrupt
    INT_TRANSFER = 0

    def __init__(self, name):
        super().__init__(name)
        self.size = 2
        self.upd = None  # optional UPD16432B target
        self.reset()

    def reset(self):
        self._sio30 = 0x00
        self._csim30 = 0x00
        self._stb_high = False

    def read(self, register):
        self._check_bounds(register)
        if register == self.SIO30:
            return self._sio30
        return self._csim30

    def write(self, register, value):
        self._check_bounds(register)
        if register == self.CSIM30:
            self._csim30 = value
            return

        # SIO30 write — initiate transfer
        if self.upd is not None:
            # Check STB state from P4.7 (FF04 bit 7)
            p4 = self.bus.read(0xFF04)
            stb_high = bool(p4 & 0x80)
            if stb_high != self._stb_high:
                if stb_high:
                    self.upd.spi_begin()
                else:
                    self.upd.spi_end()
                self._stb_high = stb_high

            if self._stb_high:
                self._sio30 = self.upd.spi_exchange(value)
            else:
                self._sio30 = 0xFF
        else:
            self._sio30 = 0xFF

        self.bus.interrupt(self, self.INT_TRANSFER)


class ADCDevice(BaseDevice):
    """A/D converter (ADC00).

    Registers:
        0: ADCR00 (FF17) - conversion result
        1: ADM00  (FF80) - mode control
        2: ADS00  (FF81) - channel selection

    When ADM00 bit 7 is set (conversion start), the conversion
    completes immediately and ADIF00 is set in the interrupt
    controller.  ADCR00 returns a fixed value.
    """

    ADCR00 = 0  # FF17: result
    ADM00  = 1  # FF80: mode
    ADS00  = 2  # FF81: channel select

    INT_COMPLETE = 0

    def __init__(self, name, result=0xFF):
        super().__init__(name)
        self.size = 3
        self._result = result
        self.reset()

    def reset(self):
        self._adcr00 = self._result
        self._adm00 = 0x00
        self._ads00 = 0x00

    def read(self, register):
        self._check_bounds(register)
        if register == self.ADCR00:
            return self._adcr00
        elif register == self.ADM00:
            return self._adm00
        return self._ads00

    def write(self, register, value):
        self._check_bounds(register)
        if register == self.ADCR00:
            pass  # read-only
        elif register == self.ADM00:
            old = self._adm00
            self._adm00 = value
            if (value & 0x80) and not (old & 0x80):
                self._adcr00 = self._result
                self.bus.interrupt(self, self.INT_COMPLETE)
        elif register == self.ADS00:
            self._ads00 = value


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
        """Evaluate pending interrupts and post result to the bus.
        Only updates if no interrupt is already waiting to be acknowledged."""
        if self.bus.pending_interrupt is not None:
            return

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
