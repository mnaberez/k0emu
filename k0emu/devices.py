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


class FreeRunningTimerDevice(BaseDevice):
    """Free-running 16-bit timer counter.

    Increments by the number of elapsed CPU clocks on each tick.
    Read as a 16-bit word (low byte at register 0, high byte at register 1).
    Wraps at 0xFFFF -> 0x0000."""

    def __init__(self, name):
        super().__init__(name)
        self.size = 2
        self._counter = 0

    def read(self, register):
        self._check_bounds(register)
        if register == 0:
            return self._counter & 0xFF
        return (self._counter >> 8) & 0xFF

    def write(self, register, value):
        self._check_bounds(register)

    def tick(self, cycles):
        self._counter = (self._counter + cycles) & 0xFFFF


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


class I2CControllerDevice(BaseDevice):
    """I2C serial interface controller (IIC0).

    Registers:
        0: IIC0   (FF1F) - shift register (data)
        1: IICC0  (FFA8) - control
        2: IICS0  (FFA9) - status
        3: IICCL0 (FFAA) - clock selection

    Operates as I2C bus controller.  When firmware triggers a start
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
    MSTS0 = 0x80  # controller status
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
        self._waiting = False
        self._start_pending = False

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
            if self._start_pending:
                # The firmware sets STT0 first, then writes the address
                # byte to IIC0.  We deferred _do_start until now so that
                # IIC0 contains the address byte, not stale data from
                # the previous transaction.
                self._start_pending = False
                self._do_start()
            elif self._waiting:
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
            # On real hardware, setting STT0 generates a START condition
            # on the I2C bus but does not send the address byte yet.
            # The firmware writes the address byte to IIC0 after setting
            # STT0.  We defer _do_start until the next IIC0 write so
            # that we read the correct address byte.
            self._start_pending = True

        if (value & self.SPT0) and not (old & self.SPT0):
            self._do_stop()

        if (value & self.WREL0) and not (old & self.WREL0):
            self._do_next_byte()

    def _do_start(self):
        """Handle start condition: read address byte from IIC0."""
        addr_byte = self._iic0
        i2c_addr = addr_byte >> 1
        self._is_read = bool(addr_byte & 0x01)

        self._iics0 = self.MSTS0 | self.TRC0  # controller, transmit mode

        if i2c_addr in self._targets:
            target = self._targets[i2c_addr]
            target.i2c_start(self._is_read)
            self._active_target = target
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



class BasePortDevice(BaseDevice):
    """GPIO port with output latch (Pn) and port mode register (PMn).

    Write to DATA stores to the output latch.
    Read from DATA returns the pin state:
      - Output-mode pins (PMn bit = 0): pin reflects the output latch
      - Input-mode pins (PMn bit = 1): pin reflects external_inputs
    """

    DATA = 0
    MODE = 1

    def __init__(self, name):
        super().__init__(name)
        self.size = 2
        self._latch = 0x00
        self._mode = 0xFF
        self.external_inputs = 0xFF
        self._pin_change_callbacks = []

    def on_pin_change(self, callback):
        self._pin_change_callbacks.append(callback)

    def pin_state(self):
        output_bits = self._latch & ~self._mode
        input_bits = self.external_inputs & self._mode
        return output_bits | input_bits

    def read(self, register):
        self._check_bounds(register)
        if register == self.DATA:
            return self.pin_state()
        return self._mode

    def write(self, register, value):
        self._check_bounds(register)
        if register == self.DATA:
            self._latch = value
        else:
            self._mode = value
        if self._pin_change_callbacks:
            state = self.pin_state()
            for cb in self._pin_change_callbacks:
                cb(state)

    def reset(self):
        self._latch = 0x00
        self._mode = 0xFF
        self.external_inputs = 0xFF


class PortWithPullupsDevice(BasePortDevice):
    """GPIO port with an additional pull-up resistor option register (PUn)."""

    PULLUP = 2

    def __init__(self, name):
        super().__init__(name)
        self.size = 3
        self._pullup = 0x00

    def read(self, register):
        if register == self.PULLUP:
            return self._pullup
        return super().read(register)

    def write(self, register, value):
        if register == self.PULLUP:
            self._pullup = value
        else:
            super().write(register, value)

    def reset(self):
        super().reset()
        self._pullup = 0x00


class Port0Device(PortWithPullupsDevice):
    """Port 0: 8-bit I/O port with external interrupt edge detection.
    P00/INTP0: input  MFSW (inverted; from HEF40106BT)
    P01/INTP1: input  Unknown
    P02/INTP2: input  Unknown (must be low or firmware stays in halt/sleep loop)
    P03/INTP3: input  Unknown (not used as INTP3)
    P04/INTP4: input  POWER key (0=pressed)
    P05/INTP5: input  uPD16432B KEYREQ (not used in firmware)
    P06/INTP6: input  STOP/EJECT key (0=pressed)
    P07/INTP7: input  Unknown
    Pull-up resistors on all pins.

    Also owns the EGP/EGN edge selection registers (0xFF48/0xFF49)
    which control which edges on P0 pins trigger INTP0-INTP7.

    Use set_external_input(pin, state) to change pin levels.  Edge
    detection compares old vs new and fires INTPn for each pin
    that changed in a direction enabled by EGP/EGN.  Interrupt
    source indices 0-7 correspond to INTP0-INTP7."""

    EGP = 3   # register index for external interrupt rising edge enable
    EGN = 4   # register index for external interrupt falling edge enable

    def __init__(self):
        super().__init__("p0")
        self.size = 5
        self._egp = 0x00
        self._egn = 0x00

    def read(self, register):
        if register == self.EGP:
            return self._egp
        if register == self.EGN:
            return self._egn
        return super().read(register)

    def write(self, register, value):
        if register == self.EGP:
            self._egp = value
        elif register == self.EGN:
            self._egn = value
        else:
            super().write(register, value)

    def reset(self):
        super().reset()
        self._egp = 0x00
        self._egn = 0x00

    def set_external_input(self, pin, state):
        """Set one external input pin and fire INTPn if the edge matches EGP/EGN."""
        mask = 1 << pin
        old_state = bool(self.external_inputs & mask)

        self.external_inputs &= ~mask
        if state:
            self.external_inputs |= mask

        if state != old_state:
            # rising (positive) edge detect
            if (self._egp & mask) and state:
                self.bus.interrupt(self, pin)

            # falling (negative) edge detect
            if (self._egn & mask) and (not state):
                self.bus.interrupt(self, pin)


class Port2Device(PortWithPullupsDevice):
    """Port 2: 8-bit I/O port.
    P20/SI31:  input   CDC DI (inverted; from HEF40106BT)
    P21/SO31:  output  Unknown
    P22/SCK31: output  CDC CLK (inverted; from HEF40106BT)
    P23:       input   Tape METAL sense (1=metal)
    P24/RxD0:  input   L9637D RX (K-line)
    P25/TxD0:  output  L9637D TX (K-line)
    P26:       output  K-line resistor (0=disconnected, 1=connected)
    P27:       output  Unknown
    Pull-up resistors on all pins."""
    def __init__(self):
        super().__init__("p2")


class Port3Device(PortWithPullupsDevice):
    """Port 3: 7-bit I/O port (bit 7 fixed at 1).
    P30/SI30:  input   uPD16432B DAT in
    P31/SO30:  output  uPD16432B DAT out
    P32/SCK30: output  uPD16432B CLK
    P33:       output  Alarm LED (0=on, 1=off), N-ch open-drain
    P34/TO00:  output  Unknown
    P35/TI000: input   Unknown
    P36/TI010: unknown Unknown
    Pull-up resistors on P30-P32, P34-P36 (not P33)."""
    def __init__(self):
        super().__init__("p3")


class Port4Device(PortWithPullupsDevice):
    """Port 4: 8-bit I/O port.
    P40: input   Unknown
    P41: input   Unknown
    P42: input   Unknown
    P43: output  Unknown
    P44: output  FIS ENA
    P45: input   Unknown
    P46: output  uPD16432B /LCDOFF
    P47: output  uPD16432B STB
    Pull-up resistors on all pins."""
    def __init__(self):
        super().__init__("p4")


class Port5Device(PortWithPullupsDevice):
    """Port 5: 8-bit I/O port, TTL level input.
    P50: output  Unknown
    P51: output  Unknown
    P52: output  Unknown
    P53: output  Unknown
    P54: output  Unknown
    P55: output  Unknown
    P56: unknown Unknown
    P57: output  CDC DO (inverted; to HEF40106BT)
    Pull-up resistors on all pins."""
    def __init__(self):
        super().__init__("p5")


class Port6Device(PortWithPullupsDevice):
    """Port 6: 4-bit I/O port (P64-P67 only, lower 4 bits read as 1).
    P64: unknown Unknown
    P65: unknown Unknown
    P66: unknown Unknown
    P67: unknown Unknown
    Pull-up resistors on P64-P67."""
    def __init__(self):
        super().__init__("p6")


class Port7Device(PortWithPullupsDevice):
    """Port 7: 6-bit I/O port (bits 6-7 read as 1).
    P70/PCL:   unknown Unknown
    P71/SDA0:  output  I2C SDA, N-ch open-drain
    P72/SCL0:  output  I2C SCL, N-ch open-drain
    P73/TO01:  output  Bit-banged I2C SCL to TEA6840H NICE only
    P74/TI001: input   Bit-banged I2C SDA to TEA6840H NICE only
    P75/TI011: input   Unknown
    Pull-up resistors on P70, P73-P75 (not P71, P72)."""
    def __init__(self):
        super().__init__("p7")


class Port8Device(BasePortDevice):
    """Port 8: 8-bit I/O port.  No pull-up resistors.
    P80/ANI01: output  Switched 5V supply control (0=off, 1=on)
    P81/ANI11: output  Antenna phantom power out (0=off, 1=on)
    P82/ANI21: output  Monsoon amplifier power 12V out (0=off, 1=on)
    P83/ANI31: input   Unknown
    P84/ANI41: input   Unknown
    P85/ANI51: input   Unknown
    P86/ANI61: input   Unknown
    P87/ANI71: unknown Unknown"""
    def __init__(self):
        super().__init__("p8")


class Port9Device(BasePortDevice):
    """Port 9: 8-bit I/O port.  No pull-up resistors.
    P90/ANI00: input   S-Contact (0=off, 1=on)
    P91/ANI10: input   Terminal 30 Constant B+ analog input
    P92/ANI20: input   Terminal 58b Illumination analog input
    P93/ANI30: input   Unknown
    P94/ANI40: output  Unknown
    P95/ANI50: input   Unknown analog input
    P96/ANI60: input   Unknown
    P97/ANI70: output  Unknown"""
    def __init__(self):
        super().__init__("p9")
    def reset(self):
        super().reset()
        self.external_inputs = 0xFE  # P9.0=0: S-Contact off (ignition off)



class SPIControllerDevice(BaseDevice):
    """3-wire serial I/O (clocked serial interface).

    The uPD78F0833Y has two identical channels: CSI30 and CSI31.

    Registers:
        0: SIO3x  - shift register
        1: CSIM3x - mode control

    When firmware writes a byte to SIO3x, a transfer is initiated
    and completed immediately.  Sets the channel's interrupt flag.

    An optional SPI target can be attached.  When attached, the
    stb_port and stb_bit parameters specify which port pin is used
    as the chip select (active high).
    """

    SIO  = 0
    CSIM = 1

    INT_TRANSFER = 0

    def __init__(self, name):
        super().__init__(name)
        self.size = 2
        self.target = None
        self.reset()

    def reset(self):
        self._sio = 0x00
        self._csim = 0x00

    def read(self, register):
        self._check_bounds(register)
        if register == self.SIO:
            return self._sio
        return self._csim

    def write(self, register, value):
        self._check_bounds(register)
        if register == self.CSIM:
            self._csim = value
            return

        if self.target is not None:
            self._sio = self.target.spi_exchange(value)
        else:
            self._sio = 0xFF

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
