import unittest
from k0emu.bus import Bus
from k0emu.devices import (MemoryDevice, RegisterFileDevice,
                           ProcessorStatusDevice, InterruptControllerDevice,
                           I2CControllerDevice,
                           WatchdogDevice, WatchTimerDevice)
from k0emu.i2c import BaseI2CTarget, StubI2CTarget


class MemoryDeviceTests(unittest.TestCase):

    # read/write

    def test_read_returns_fill_value(self):
        mem = MemoryDevice("test", size=4)
        self.assertEqual(mem.read(0), 0x00)

    def test_read_returns_custom_fill_value(self):
        mem = MemoryDevice("test", size=4, fill=0xFF)
        self.assertEqual(mem.read(0), 0xFF)

    def test_write_then_read(self):
        mem = MemoryDevice("test", size=4)
        mem.write(0, 0x42)
        self.assertEqual(mem.read(0), 0x42)

    # write protection

    def test_write_ignored_when_not_writable(self):
        mem = MemoryDevice("test", size=4, fill=0xFF, writable=False)
        mem.write(0, 0x00)
        self.assertEqual(mem.read(0), 0xFF)

    def test_load_bypasses_write_protection(self):
        mem = MemoryDevice("test", size=4, fill=0xFF, writable=False)
        mem.load(0, [0x00, 0x01, 0x02, 0x03])
        self.assertEqual(mem.read(0), 0x00)
        self.assertEqual(mem.read(3), 0x03)

    # bounds checking

    def test_read_out_of_bounds_raises(self):
        mem = MemoryDevice("test", size=4)
        with self.assertRaises(IndexError):
            mem.read(4)

    def test_write_out_of_bounds_raises(self):
        mem = MemoryDevice("test", size=4)
        with self.assertRaises(IndexError):
            mem.write(4, 0x00)

    def test_load_out_of_bounds_raises(self):
        mem = MemoryDevice("test", size=4)
        with self.assertRaises(IndexError):
            mem.load(0, [0x00] * 5)

    def test_negative_offset_raises(self):
        mem = MemoryDevice("test", size=4)
        with self.assertRaises(IndexError):
            mem.read(-1)

    # properties

    def test_name(self):
        mem = MemoryDevice("my_rom", size=4)
        self.assertEqual(mem.name, "my_rom")

    def test_size(self):
        mem = MemoryDevice("test", size=256)
        self.assertEqual(mem.size, 256)

    # tick

    def test_tick_accumulates(self):
        mem = MemoryDevice("test", size=4)
        mem.tick(3)
        mem.tick(5)
        self.assertEqual(mem.ticks, 8)


class RegisterFileDeviceTests(unittest.TestCase):

    # defaults

    def test_name(self):
        rf = RegisterFileDevice("register_file")
        self.assertEqual(rf.name, "register_file")

    def test_size_is_32_bytes(self):
        rf = RegisterFileDevice("register_file")
        self.assertEqual(rf.size, 32)

    def test_initialized_to_zero(self):
        rf = RegisterFileDevice("register_file")
        for i in range(32):
            self.assertEqual(rf.read(i), 0)

    # layout: bank 3 at offset 0, bank 0 at offset 24

    def test_bank0_at_top(self):
        rf = RegisterFileDevice("register_file")
        rf.write(24, 0x42)  # bank 0, register X
        self.assertEqual(rf.read(24), 0x42)

    def test_bank3_at_bottom(self):
        rf = RegisterFileDevice("register_file")
        rf.write(0, 0x42)  # bank 3, register X
        self.assertEqual(rf.read(0), 0x42)

    def test_banks_are_independent(self):
        rf = RegisterFileDevice("register_file")
        rf.write(24, 0xAA)  # bank 0, register X
        rf.write(0, 0xBB)   # bank 3, register X
        self.assertEqual(rf.read(24), 0xAA)
        self.assertEqual(rf.read(0), 0xBB)

    # bounds

    def test_out_of_bounds_raises(self):
        rf = RegisterFileDevice("register_file")
        with self.assertRaises(IndexError):
            rf.read(32)


class ProcessorStatusDeviceTests(unittest.TestCase):

    # defaults

    def test_name(self):
        ps = ProcessorStatusDevice("processor_status")
        self.assertEqual(ps.name, "processor_status")

    def test_size(self):
        ps = ProcessorStatusDevice("processor_status")
        self.assertEqual(ps.size, 3)

    def test_initialized_to_zero(self):
        ps = ProcessorStatusDevice("processor_status")
        self.assertEqual(ps.read(0), 0x00)  # SPL
        self.assertEqual(ps.read(1), 0x00)  # SPH
        self.assertEqual(ps.read(2), 0x00)  # PSW

    # read/write

    def test_write_spl(self):
        ps = ProcessorStatusDevice("processor_status")
        ps.write(0, 0x1C)
        self.assertEqual(ps.read(0), 0x1C)

    def test_write_sph(self):
        ps = ProcessorStatusDevice("processor_status")
        ps.write(1, 0xFE)
        self.assertEqual(ps.read(1), 0xFE)

    def test_write_psw(self):
        ps = ProcessorStatusDevice("processor_status")
        ps.write(2, 0x42)
        self.assertEqual(ps.read(2), 0x42)

    # bus access

    def test_bus_write_sp(self):
        proc = _FakeProcessor()
        bus = Bus(proc)
        ps = ProcessorStatusDevice("processor_status")
        bus.add_device(ps, (0xFF1C, 0xFF1E))
        bus.write(0xFF1C, 0x1C)
        bus.write(0xFF1D, 0xFE)
        self.assertEqual(ps.read(0), 0x1C)
        self.assertEqual(ps.read(1), 0xFE)

    def test_bus_read_psw(self):
        proc = _FakeProcessor()
        bus = Bus(proc)
        ps = ProcessorStatusDevice("processor_status")
        bus.add_device(ps, (0xFF1C, 0xFF1E))
        ps.write(2, 0x42)
        self.assertEqual(bus.read(0xFF1E), 0x42)

    # bounds

    def test_out_of_bounds_raises(self):
        ps = ProcessorStatusDevice("processor_status")
        with self.assertRaises(IndexError):
            ps.read(3)


class _DummyDevice(object):
    """Minimal device for testing interrupt connections."""
    INT_0 = 0
    INT_1 = 1


def _make_intc_on_bus():
    """Create an InterruptControllerDevice on a bus with a dummy device
    connected to INTP0 and INTP1 for testing."""
    proc = _FakeProcessor()
    bus = Bus(proc)
    intc = InterruptControllerDevice("intc")
    bus.add_device(intc, (0xFFE0, 0xFFEB))
    bus.set_interrupt_controller(intc)
    dev = _DummyDevice()
    intc.connect(dev, _DummyDevice.INT_0, InterruptControllerDevice.INTP0)
    intc.connect(dev, _DummyDevice.INT_1, InterruptControllerDevice.INTP1)
    return intc, dev


class InterruptControllerDeviceTests(unittest.TestCase):

    # defaults

    def test_name(self):
        intc = InterruptControllerDevice("intc")
        self.assertEqual(intc.name, "intc")

    def test_size(self):
        intc = InterruptControllerDevice("intc")
        self.assertEqual(intc.size, 12)

    def test_if_registers_reset_to_zero(self):
        intc = InterruptControllerDevice("intc")
        for i in range(4):
            self.assertEqual(intc.read(i), 0x00)

    def test_mk_registers_reset_to_ff(self):
        intc = InterruptControllerDevice("intc")
        for i in range(4, 8):
            self.assertEqual(intc.read(i), 0xFF)

    def test_pr_registers_reset_to_ff(self):
        intc = InterruptControllerDevice("intc")
        for i in range(8, 12):
            self.assertEqual(intc.read(i), 0xFF)

    # read/write

    def test_write_then_read(self):
        intc = InterruptControllerDevice("intc")
        intc.write(InterruptControllerDevice.IF0L, 0x42)
        self.assertEqual(intc.read(InterruptControllerDevice.IF0L), 0x42)

    def test_write_mk_register(self):
        intc = InterruptControllerDevice("intc")
        intc.write(InterruptControllerDevice.MK0L, 0x00)
        self.assertEqual(intc.read(InterruptControllerDevice.MK0L), 0x00)

    def test_write_pr_register(self):
        intc = InterruptControllerDevice("intc")
        intc.write(InterruptControllerDevice.PR0L, 0x00)
        self.assertEqual(intc.read(InterruptControllerDevice.PR0L), 0x00)

    # reset

    def test_reset_clears_if(self):
        intc = InterruptControllerDevice("intc")
        intc.write(InterruptControllerDevice.IF0L, 0xFF)
        intc.reset()
        self.assertEqual(intc.read(InterruptControllerDevice.IF0L), 0x00)

    def test_reset_sets_mk_to_ff(self):
        intc = InterruptControllerDevice("intc")
        intc.write(InterruptControllerDevice.MK0L, 0x00)
        intc.reset()
        self.assertEqual(intc.read(InterruptControllerDevice.MK0L), 0xFF)

    def test_reset_sets_pr_to_ff(self):
        intc = InterruptControllerDevice("intc")
        intc.write(InterruptControllerDevice.PR0L, 0x00)
        intc.reset()
        self.assertEqual(intc.read(InterruptControllerDevice.PR0L), 0xFF)

    # interrupt

    def test_interrupt_sets_if_bit(self):
        intc, dev = _make_intc_on_bus()
        intc.interrupt(dev, _DummyDevice.INT_0)
        self.assertEqual(intc.read(InterruptControllerDevice.IF0L) & 0x02, 0x02)

    def test_interrupt_preserves_other_bits(self):
        intc, dev = _make_intc_on_bus()
        intc.interrupt(dev, _DummyDevice.INT_0)
        intc.interrupt(dev, _DummyDevice.INT_1)
        self.assertEqual(intc.read(InterruptControllerDevice.IF0L) & 0x06, 0x06)

    # pending interrupt (via tick -> bus.pending_interrupt)

    def _tick_intc(self, intc):
        """Tick the intc to evaluate pending interrupts onto the bus."""
        intc.tick(1)
        return intc.bus.pending_interrupt

    def test_no_interrupt_when_none_pending(self):
        proc = _FakeProcessor()
        bus = Bus(proc)
        intc = InterruptControllerDevice("intc")
        bus.add_device(intc, (0xFFE0, 0xFFEB))
        bus.set_interrupt_controller(intc)
        intc.write(InterruptControllerDevice.MK0L, 0x00)
        self.assertIsNone(self._tick_intc(intc))

    def test_no_interrupt_when_masked(self):
        proc = _FakeProcessor()
        bus = Bus(proc)
        intc = InterruptControllerDevice("intc")
        bus.add_device(intc, (0xFFE0, 0xFFEB))
        bus.set_interrupt_controller(intc)
        intc.write(InterruptControllerDevice.IF0L, intc.read(InterruptControllerDevice.IF0L) | 0x02)
        self.assertIsNone(self._tick_intc(intc))

    def test_low_priority_pending(self):
        proc = _FakeProcessor()
        bus = Bus(proc)
        intc = InterruptControllerDevice("intc")
        bus.add_device(intc, (0xFFE0, 0xFFEB))
        bus.set_interrupt_controller(intc)
        intc.write(InterruptControllerDevice.IF0L, intc.read(InterruptControllerDevice.IF0L) | 0x02)
        intc.write(InterruptControllerDevice.MK0L, 0xFD)
        pending = self._tick_intc(intc)
        self.assertEqual(pending.source_index, InterruptControllerDevice.INTP0)
        self.assertFalse(pending.high_priority)
        self.assertEqual(pending.vector_address, 0x0006)

    def test_high_priority_pending(self):
        proc = _FakeProcessor()
        bus = Bus(proc)
        intc = InterruptControllerDevice("intc")
        bus.add_device(intc, (0xFFE0, 0xFFEB))
        bus.set_interrupt_controller(intc)
        intc.write(InterruptControllerDevice.IF0L, intc.read(InterruptControllerDevice.IF0L) | 0x02)
        intc.write(InterruptControllerDevice.MK0L, 0xFD)
        intc.write(InterruptControllerDevice.PR0L, 0xFD)     # high priority
        pending = self._tick_intc(intc)
        self.assertEqual(pending.source_index, InterruptControllerDevice.INTP0)
        self.assertTrue(pending.high_priority)
        self.assertEqual(pending.vector_address, 0x0006)

    # priority

    def test_high_priority_wins_over_low_priority(self):
        proc = _FakeProcessor()
        bus = Bus(proc)
        intc = InterruptControllerDevice("intc")
        bus.add_device(intc, (0xFFE0, 0xFFEB))
        bus.set_interrupt_controller(intc)
        intc.write(InterruptControllerDevice.IF0L, intc.read(InterruptControllerDevice.IF0L) | 0x02); intc.write(InterruptControllerDevice.IF0L, intc.read(InterruptControllerDevice.IF0L) | 0x04)
        intc.write(InterruptControllerDevice.MK0L, 0xF9)
        intc.write(InterruptControllerDevice.PR0L, 0xFB)     # INTP1 high, INTP0 low
        pending = self._tick_intc(intc)
        self.assertEqual(pending.source_index, InterruptControllerDevice.INTP1)  # INTP1
        self.assertTrue(pending.high_priority)

    def test_default_priority_breaks_tie(self):
        proc = _FakeProcessor()
        bus = Bus(proc)
        intc = InterruptControllerDevice("intc")
        bus.add_device(intc, (0xFFE0, 0xFFEB))
        bus.set_interrupt_controller(intc)
        intc.write(InterruptControllerDevice.IF0L, intc.read(InterruptControllerDevice.IF0L) | 0x02); intc.write(InterruptControllerDevice.IF0L, intc.read(InterruptControllerDevice.IF0L) | 0x04)  # INTP0 + INTP1
        intc.write(InterruptControllerDevice.MK0L, 0xF9)
        pending = self._tick_intc(intc)
        self.assertEqual(pending.source_index, InterruptControllerDevice.INTP0)  # INTP0 wins

    def test_default_priority_breaks_tie_high(self):
        proc = _FakeProcessor()
        bus = Bus(proc)
        intc = InterruptControllerDevice("intc")
        bus.add_device(intc, (0xFFE0, 0xFFEB))
        bus.set_interrupt_controller(intc)
        intc.write(InterruptControllerDevice.IF0L, intc.read(InterruptControllerDevice.IF0L) | 0x02); intc.write(InterruptControllerDevice.IF0L, intc.read(InterruptControllerDevice.IF0L) | 0x04)  # INTP0 + INTP1
        intc.write(InterruptControllerDevice.MK0L, 0xF9)
        intc.write(InterruptControllerDevice.PR0L, 0xF9)
        pending = self._tick_intc(intc)
        self.assertEqual(pending.source_index, InterruptControllerDevice.INTP0)  # INTP0 wins

    # sources across registers

    def test_intwtni0_pending(self):
        proc = _FakeProcessor()
        bus = Bus(proc)
        intc = InterruptControllerDevice("intc")
        bus.add_device(intc, (0xFFE0, 0xFFEB))
        bus.set_interrupt_controller(intc)
        intc.write(InterruptControllerDevice.IF1L, intc.read(InterruptControllerDevice.IF1L) | 0x01)
        intc.write(InterruptControllerDevice.MK1L, 0xFE)
        pending = self._tick_intc(intc)
        self.assertEqual(pending.source_index, InterruptControllerDevice.INTWTNI0)
        self.assertEqual(pending.vector_address, 0x0024)

    def test_intwtn0_pending(self):
        proc = _FakeProcessor()
        bus = Bus(proc)
        intc = InterruptControllerDevice("intc")
        bus.add_device(intc, (0xFFE0, 0xFFEB))
        bus.set_interrupt_controller(intc)
        intc.write(InterruptControllerDevice.IF1H, intc.read(InterruptControllerDevice.IF1H) | 0x01)
        intc.write(InterruptControllerDevice.MK1H, 0xFE)
        pending = self._tick_intc(intc)
        self.assertEqual(pending.source_index, InterruptControllerDevice.INTWTN0)
        self.assertEqual(pending.vector_address, 0x0034)

    def test_intcsi30_pending(self):
        proc = _FakeProcessor()
        bus = Bus(proc)
        intc = InterruptControllerDevice("intc")
        bus.add_device(intc, (0xFFE0, 0xFFEB))
        bus.set_interrupt_controller(intc)
        intc.write(InterruptControllerDevice.IF0H, intc.read(InterruptControllerDevice.IF0H) | 0x10)
        intc.write(InterruptControllerDevice.MK0H, 0xEF)
        pending = self._tick_intc(intc)
        self.assertEqual(pending.source_index, InterruptControllerDevice.INTCSI30)
        self.assertEqual(pending.vector_address, 0x001C)

    def test_intwdt_pending(self):
        proc = _FakeProcessor()
        bus = Bus(proc)
        intc = InterruptControllerDevice("intc")
        bus.add_device(intc, (0xFFE0, 0xFFEB))
        bus.set_interrupt_controller(intc)
        intc.write(InterruptControllerDevice.IF0L, intc.read(InterruptControllerDevice.IF0L) | 0x01)
        intc.write(InterruptControllerDevice.MK0L, 0xFE)
        pending = self._tick_intc(intc)
        self.assertEqual(pending.source_index, InterruptControllerDevice.INTWDT)
        self.assertEqual(pending.vector_address, 0x0004)

    # acknowledge

    def test_acknowledge_clears_if_flag(self):
        intc = InterruptControllerDevice("intc")
        intc.write(InterruptControllerDevice.IF0L, intc.read(InterruptControllerDevice.IF0L) | 0x02)
        intc.acknowledge_interrupt(InterruptControllerDevice.INTP0)  # source 1 = INTP0
        self.assertEqual(intc.read(InterruptControllerDevice.IF0L), 0x00)

    def test_acknowledge_preserves_other_flags(self):
        intc = InterruptControllerDevice("intc")
        intc.write(InterruptControllerDevice.IF0L, intc.read(InterruptControllerDevice.IF0L) | 0x02); intc.write(InterruptControllerDevice.IF0L, intc.read(InterruptControllerDevice.IF0L) | 0x04)
        intc.acknowledge_interrupt(InterruptControllerDevice.INTP0)  # clear INTP0
        self.assertEqual(intc.read(InterruptControllerDevice.IF0L), 0x04)

    # bus access

    def test_bus_write_mk(self):
        proc = _FakeProcessor()
        bus = Bus(proc)
        intc = InterruptControllerDevice("intc")
        bus.add_device(intc, (0xFFE0, 0xFFEB))
        bus.set_interrupt_controller(intc)
        bus.write(0xFFE4, 0x00)  # MK0L
        self.assertEqual(intc.read(InterruptControllerDevice.MK0L), 0x00)

    def test_bus_read_if(self):
        proc = _FakeProcessor()
        bus = Bus(proc)
        intc = InterruptControllerDevice("intc")
        bus.add_device(intc, (0xFFE0, 0xFFEB))
        bus.set_interrupt_controller(intc)
        intc.write(InterruptControllerDevice.IF0L, intc.read(InterruptControllerDevice.IF0L) | 0x02)
        self.assertEqual(bus.read(0xFFE0), 0x02)

    # bounds

    def test_read_out_of_bounds_raises(self):
        intc = InterruptControllerDevice("intc")
        with self.assertRaises(IndexError):
            intc.read(12)

    def test_write_out_of_bounds_raises(self):
        intc = InterruptControllerDevice("intc")
        with self.assertRaises(IndexError):
            intc.write(12, 0x00)


class _FakeProcessor(object):
    def __init__(self):
        self.reset_count = 0

    def reset(self):
        self.reset_count += 1


class _FakeIntc(object):
    """Minimal stub for testing devices that fire interrupts."""
    def __init__(self):
        self.name = "intc"
        self.bus = None
        self.size = 12  # IF0L..PR1L
        self.ticks = 0
        self.requested = []  # list of (device, device_int) tuples

    def interrupt(self, device, device_int):
        self.requested.append((device, device_int))

    def acknowledge_interrupt(self, source_index):
        pass

    def read(self, register):
        return 0

    def write(self, register, value):
        pass

    def reset(self):
        self.requested = []

    def tick(self, cycles):
        self.ticks += cycles


def _make_watchdog_on_bus():
    """Create a WatchdogDevice on a bus with a fake processor and intc."""
    proc = _FakeProcessor()
    bus = Bus(proc)
    intc = _FakeIntc()
    bus.add_device(intc, (0xFFE0, 0xFFEB))
    bus.set_interrupt_controller(intc)
    wd = WatchdogDevice("watchdog")
    bus.add_device(wd, (0xFF42, 0xFF42), (0xFFF9, 0xFFF9))
    return wd, proc, intc


class WatchdogDeviceTests(unittest.TestCase):

    # defaults

    def test_name(self):
        wd = WatchdogDevice("watchdog")
        self.assertEqual(wd.name, "watchdog")

    def test_size(self):
        wd = WatchdogDevice("watchdog")
        self.assertEqual(wd.size, 2)

    def test_wdtm_initially_zero(self):
        wd = WatchdogDevice("watchdog")
        self.assertEqual(wd.read(WatchdogDevice.WDTM), 0x00)

    def test_wdcs_reads_as_zero(self):
        wd = WatchdogDevice("watchdog")
        wd.write(WatchdogDevice.WDCS, 0x07)
        self.assertEqual(wd.read(WatchdogDevice.WDCS), 0x00)

    def test_not_running_initially(self):
        wd = WatchdogDevice("watchdog")
        self.assertFalse(wd.running)

    def test_mode_initially_interval(self):
        wd = WatchdogDevice("watchdog")
        self.assertEqual(wd.mode, WatchdogDevice.MODE_INTERVAL)

    # WDCS

    def test_wdcs_selects_interval(self):
        wd = WatchdogDevice("watchdog")
        wd.write(WatchdogDevice.WDCS, 0x00)
        self.assertEqual(wd.interval, 1 << 12)

    def test_wdcs_7_selects_longest_interval(self):
        wd = WatchdogDevice("watchdog")
        wd.write(WatchdogDevice.WDCS, 0x07)
        self.assertEqual(wd.interval, 1 << 20)

    def test_wdcs_masks_to_3_bits(self):
        wd = WatchdogDevice("watchdog")
        wd.write(WatchdogDevice.WDCS, 0xFF)
        self.assertEqual(wd.interval, 1 << 20)

    # WDTM one-way latches

    def test_run_bit_latches(self):
        wd = WatchdogDevice("watchdog")
        wd.write(WatchdogDevice.WDTM, 0x80)  # set RUN
        self.assertTrue(wd.running)
        wd.write(WatchdogDevice.WDTM, 0x00)  # try to clear RUN
        self.assertTrue(wd.running)

    def test_wdtm4_latches(self):
        wd = WatchdogDevice("watchdog")
        wd.write(WatchdogDevice.WDTM, 0x90)  # set RUN + WDTM4
        self.assertEqual(wd.mode, WatchdogDevice.MODE_NMI)
        wd.write(WatchdogDevice.WDTM, 0x80)  # try to clear WDTM4
        self.assertEqual(wd.mode, WatchdogDevice.MODE_NMI)

    def test_wdtm3_latches(self):
        wd = WatchdogDevice("watchdog")
        wd.write(WatchdogDevice.WDTM, 0x98)  # set RUN + WDTM4 + WDTM3
        self.assertEqual(wd.mode, WatchdogDevice.MODE_RESET)
        wd.write(WatchdogDevice.WDTM, 0x90)  # try to clear WDTM3
        self.assertEqual(wd.mode, WatchdogDevice.MODE_RESET)

    def test_wdtm_read_reflects_latched_bits(self):
        wd = WatchdogDevice("watchdog")
        wd.write(WatchdogDevice.WDTM, 0x90)
        self.assertEqual(wd.read(WatchdogDevice.WDTM), 0x90)

    def test_wdtm_ignores_reserved_bits(self):
        wd = WatchdogDevice("watchdog")
        wd.write(WatchdogDevice.WDTM, 0xFF)
        self.assertEqual(wd.read(WatchdogDevice.WDTM), 0x98)

    # mode selection

    def test_mode_interval(self):
        wd = WatchdogDevice("watchdog")
        wd.write(WatchdogDevice.WDTM, 0x80)  # RUN=1, WDTM4=0
        self.assertEqual(wd.mode, WatchdogDevice.MODE_INTERVAL)

    def test_mode_nmi(self):
        wd = WatchdogDevice("watchdog")
        wd.write(WatchdogDevice.WDTM, 0x90)  # RUN=1, WDTM4=1, WDTM3=0
        self.assertEqual(wd.mode, WatchdogDevice.MODE_NMI)

    def test_mode_reset(self):
        wd = WatchdogDevice("watchdog")
        wd.write(WatchdogDevice.WDTM, 0x98)  # RUN=1, WDTM4=1, WDTM3=1
        self.assertEqual(wd.mode, WatchdogDevice.MODE_RESET)

    # reset

    def test_reset_clears_wdtm(self):
        wd = WatchdogDevice("watchdog")
        wd.write(WatchdogDevice.WDTM, 0x98)
        wd.reset()
        self.assertEqual(wd.read(WatchdogDevice.WDTM), 0x00)
        self.assertFalse(wd.running)

    def test_reset_clears_wdcs(self):
        wd = WatchdogDevice("watchdog")
        wd.write(WatchdogDevice.WDCS, 0x07)
        wd.reset()
        self.assertEqual(wd.interval, 1 << 12)

    # tick / counting

    def test_tick_does_nothing_when_stopped(self):
        wd, proc, intc = _make_watchdog_on_bus()
        wd.tick(100000)
        self.assertEqual(proc.reset_count, 0)
        self.assertEqual(intc.requested, [])

    def test_kick_clears_counter(self):
        wd, proc, intc = _make_watchdog_on_bus()
        wd.write(WatchdogDevice.WDCS, 0x00)  # interval = 4096
        wd.write(WatchdogDevice.WDTM, 0x98)  # mode 2 (reset), start
        wd.tick(4000)  # close to overflow
        wd.write(WatchdogDevice.WDTM, 0x98)  # kick
        wd.tick(4000)  # would have overflowed without kick
        self.assertEqual(proc.reset_count, 0)

    # overflow: mode 2 (reset)

    def test_overflow_mode_reset_triggers_bus_reset(self):
        wd, proc, intc = _make_watchdog_on_bus()
        wd.write(WatchdogDevice.WDCS, 0x00)  # interval = 4096
        wd.write(WatchdogDevice.WDTM, 0x98)  # mode 2 (reset), start
        wd.tick(4096)
        self.assertEqual(proc.reset_count, 1)

    def test_overflow_mode_reset_at_exact_interval(self):
        wd, proc, intc = _make_watchdog_on_bus()
        wd.write(WatchdogDevice.WDCS, 0x00)  # interval = 4096
        wd.write(WatchdogDevice.WDTM, 0x98)
        wd.tick(4095)
        self.assertEqual(proc.reset_count, 0)
        wd.tick(1)
        self.assertEqual(proc.reset_count, 1)

    def test_overflow_mode_reset_with_longest_interval(self):
        wd, proc, intc = _make_watchdog_on_bus()
        wd.write(WatchdogDevice.WDCS, 0x07)  # interval = 1048576
        wd.write(WatchdogDevice.WDTM, 0x98)
        wd.tick(1048575)
        self.assertEqual(proc.reset_count, 0)
        wd.tick(1)
        self.assertEqual(proc.reset_count, 1)

    # overflow: mode 0 (interval timer, maskable interrupt)

    def test_overflow_mode_interval_sets_wdtif(self):
        wd, proc, intc = _make_watchdog_on_bus()
        wd.write(WatchdogDevice.WDCS, 0x00)  # interval = 4096
        wd.write(WatchdogDevice.WDTM, 0x80)  # mode 0 (interval), start
        wd.tick(4096)
        self.assertEqual(intc.requested, [(wd, WatchdogDevice.INT_OVERFLOW)])

    def test_overflow_mode_interval_repeats(self):
        wd, proc, intc = _make_watchdog_on_bus()
        wd.write(WatchdogDevice.WDCS, 0x00)  # interval = 4096
        wd.write(WatchdogDevice.WDTM, 0x80)
        wd.tick(4096)
        wd.tick(4096)
        self.assertEqual(len(intc.requested), 2)

    def test_overflow_mode_interval_does_not_reset(self):
        wd, proc, intc = _make_watchdog_on_bus()
        wd.write(WatchdogDevice.WDCS, 0x00)
        wd.write(WatchdogDevice.WDTM, 0x80)
        wd.tick(4096)
        self.assertEqual(proc.reset_count, 0)

    # bus access

    def test_bus_write_wdcs(self):
        wd, proc, intc = _make_watchdog_on_bus()
        wd.bus.write(0xFF42, 0x07)
        self.assertEqual(wd.interval, 1 << 20)

    def test_bus_write_wdtm(self):
        wd, proc, intc = _make_watchdog_on_bus()
        wd.bus.write(0xFFF9, 0x90)
        self.assertTrue(wd.running)
        self.assertEqual(wd.mode, WatchdogDevice.MODE_NMI)

    def test_bus_read_wdtm(self):
        wd, proc, intc = _make_watchdog_on_bus()
        wd.bus.write(0xFFF9, 0x98)
        self.assertEqual(wd.bus.read(0xFFF9), 0x98)

    # bounds

    def test_read_out_of_bounds_raises(self):
        wd = WatchdogDevice("watchdog")
        with self.assertRaises(IndexError):
            wd.read(2)

    def test_write_out_of_bounds_raises(self):
        wd = WatchdogDevice("watchdog")
        with self.assertRaises(IndexError):
            wd.write(2, 0x00)


def _make_watch_timer_on_bus():
    """Create a WatchTimerDevice on a bus with a fake processor and intc."""
    proc = _FakeProcessor()
    bus = Bus(proc)
    intc = _FakeIntc()
    bus.add_device(intc, (0xFFE0, 0xFFEB))
    bus.set_interrupt_controller(intc)
    wt = WatchTimerDevice("watch_timer")
    bus.add_device(wt, (0xFF41, 0xFF41))
    return wt, proc, intc


class WatchTimerDeviceTests(unittest.TestCase):

    # defaults

    def test_name(self):
        wt = WatchTimerDevice("watch_timer")
        self.assertEqual(wt.name, "watch_timer")

    def test_size(self):
        wt = WatchTimerDevice("watch_timer")
        self.assertEqual(wt.size, 1)

    def test_wtnm0_initially_zero(self):
        wt = WatchTimerDevice("watch_timer")
        self.assertEqual(wt.read(WatchTimerDevice.WTNM0), 0x00)

    # register read/write

    def test_write_then_read(self):
        wt = WatchTimerDevice("watch_timer")
        wt.write(WatchTimerDevice.WTNM0, 0x73)
        self.assertEqual(wt.read(WatchTimerDevice.WTNM0), 0x73)

    # prescaler interval (INTWTNI0) - all 16 combinations

    def test_prescaler_interval_fw128_n0(self):
        wt = WatchTimerDevice("watch_timer")
        wt.write(WatchTimerDevice.WTNM0, 0x01)  # WTNM07=0, n=0
        self.assertEqual(wt.prescaler_interval, (1 << 4) * 128)

    def test_prescaler_interval_fw128_n1(self):
        wt = WatchTimerDevice("watch_timer")
        wt.write(WatchTimerDevice.WTNM0, 0x11)  # WTNM07=0, n=1
        self.assertEqual(wt.prescaler_interval, (1 << 5) * 128)

    def test_prescaler_interval_fw128_n2(self):
        wt = WatchTimerDevice("watch_timer")
        wt.write(WatchTimerDevice.WTNM0, 0x21)  # WTNM07=0, n=2
        self.assertEqual(wt.prescaler_interval, (1 << 6) * 128)

    def test_prescaler_interval_fw128_n3(self):
        wt = WatchTimerDevice("watch_timer")
        wt.write(WatchTimerDevice.WTNM0, 0x31)  # WTNM07=0, n=3
        self.assertEqual(wt.prescaler_interval, (1 << 7) * 128)

    def test_prescaler_interval_fw128_n4(self):
        wt = WatchTimerDevice("watch_timer")
        wt.write(WatchTimerDevice.WTNM0, 0x41)  # WTNM07=0, n=4
        self.assertEqual(wt.prescaler_interval, (1 << 8) * 128)

    def test_prescaler_interval_fw128_n5(self):
        wt = WatchTimerDevice("watch_timer")
        wt.write(WatchTimerDevice.WTNM0, 0x51)  # WTNM07=0, n=5
        self.assertEqual(wt.prescaler_interval, (1 << 9) * 128)

    def test_prescaler_interval_fw128_n6(self):
        wt = WatchTimerDevice("watch_timer")
        wt.write(WatchTimerDevice.WTNM0, 0x61)  # WTNM07=0, n=6
        self.assertEqual(wt.prescaler_interval, (1 << 10) * 128)

    def test_prescaler_interval_fw128_n7(self):
        wt = WatchTimerDevice("watch_timer")
        wt.write(WatchTimerDevice.WTNM0, 0x71)  # WTNM07=0, n=7
        self.assertEqual(wt.prescaler_interval, (1 << 11) * 128)

    def test_prescaler_interval_fw64_n0(self):
        wt = WatchTimerDevice("watch_timer")
        wt.write(WatchTimerDevice.WTNM0, 0x81)  # WTNM07=1, n=0
        self.assertEqual(wt.prescaler_interval, (1 << 4) * 64)

    def test_prescaler_interval_fw64_n1(self):
        wt = WatchTimerDevice("watch_timer")
        wt.write(WatchTimerDevice.WTNM0, 0x91)  # WTNM07=1, n=1
        self.assertEqual(wt.prescaler_interval, (1 << 5) * 64)

    def test_prescaler_interval_fw64_n2(self):
        wt = WatchTimerDevice("watch_timer")
        wt.write(WatchTimerDevice.WTNM0, 0xA1)  # WTNM07=1, n=2
        self.assertEqual(wt.prescaler_interval, (1 << 6) * 64)

    def test_prescaler_interval_fw64_n3(self):
        wt = WatchTimerDevice("watch_timer")
        wt.write(WatchTimerDevice.WTNM0, 0xB1)  # WTNM07=1, n=3
        self.assertEqual(wt.prescaler_interval, (1 << 7) * 64)

    def test_prescaler_interval_fw64_n4(self):
        wt = WatchTimerDevice("watch_timer")
        wt.write(WatchTimerDevice.WTNM0, 0xC1)  # WTNM07=1, n=4
        self.assertEqual(wt.prescaler_interval, (1 << 8) * 64)

    def test_prescaler_interval_fw64_n5(self):
        wt = WatchTimerDevice("watch_timer")
        wt.write(WatchTimerDevice.WTNM0, 0xD1)  # WTNM07=1, n=5
        self.assertEqual(wt.prescaler_interval, (1 << 9) * 64)

    def test_prescaler_interval_fw64_n6(self):
        wt = WatchTimerDevice("watch_timer")
        wt.write(WatchTimerDevice.WTNM0, 0xE1)  # WTNM07=1, n=6
        self.assertEqual(wt.prescaler_interval, (1 << 10) * 64)

    def test_prescaler_interval_fw64_n7(self):
        wt = WatchTimerDevice("watch_timer")
        wt.write(WatchTimerDevice.WTNM0, 0xF1)  # WTNM07=1, n=7
        self.assertEqual(wt.prescaler_interval, (1 << 11) * 64)

    # prescaler interval - firmware configs

    def test_prescaler_interval_firmware_conf_a(self):
        wt = WatchTimerDevice("watch_timer")
        wt.write(WatchTimerDevice.WTNM0, 0x13)  # wtnm0_conf_a
        self.assertEqual(wt.prescaler_interval, (1 << 5) * 128)  # 4096

    def test_prescaler_interval_firmware_conf_b(self):
        wt = WatchTimerDevice("watch_timer")
        wt.write(WatchTimerDevice.WTNM0, 0x73)  # wtnm0_conf_b
        self.assertEqual(wt.prescaler_interval, (1 << 11) * 128)  # 262144

    # watch interval (INTWTN0) - all 8 combinations

    def test_watch_interval_fw128_sel0(self):
        wt = WatchTimerDevice("watch_timer")
        wt.write(WatchTimerDevice.WTNM0, 0x03)  # WTNM07=0, sel=00
        self.assertEqual(wt.watch_interval, (1 << 14) * 128)

    def test_watch_interval_fw128_sel1(self):
        wt = WatchTimerDevice("watch_timer")
        wt.write(WatchTimerDevice.WTNM0, 0x07)  # WTNM07=0, sel=01
        self.assertEqual(wt.watch_interval, (1 << 13) * 128)

    def test_watch_interval_fw128_sel2(self):
        wt = WatchTimerDevice("watch_timer")
        wt.write(WatchTimerDevice.WTNM0, 0x0B)  # WTNM07=0, sel=10
        self.assertEqual(wt.watch_interval, (1 << 5) * 128)

    def test_watch_interval_fw128_sel3(self):
        wt = WatchTimerDevice("watch_timer")
        wt.write(WatchTimerDevice.WTNM0, 0x0F)  # WTNM07=0, sel=11
        self.assertEqual(wt.watch_interval, (1 << 4) * 128)

    def test_watch_interval_fw64_sel0(self):
        wt = WatchTimerDevice("watch_timer")
        wt.write(WatchTimerDevice.WTNM0, 0x83)  # WTNM07=1, sel=00
        self.assertEqual(wt.watch_interval, (1 << 14) * 64)

    def test_watch_interval_fw64_sel1(self):
        wt = WatchTimerDevice("watch_timer")
        wt.write(WatchTimerDevice.WTNM0, 0x87)  # WTNM07=1, sel=01
        self.assertEqual(wt.watch_interval, (1 << 13) * 64)

    def test_watch_interval_fw64_sel2(self):
        wt = WatchTimerDevice("watch_timer")
        wt.write(WatchTimerDevice.WTNM0, 0x8B)  # WTNM07=1, sel=10
        self.assertEqual(wt.watch_interval, (1 << 5) * 64)

    def test_watch_interval_fw64_sel3(self):
        wt = WatchTimerDevice("watch_timer")
        wt.write(WatchTimerDevice.WTNM0, 0x8F)  # WTNM07=1, sel=11
        self.assertEqual(wt.watch_interval, (1 << 4) * 64)

    # tick: disabled

    def test_tick_does_nothing_when_disabled(self):
        wt, proc, intc = _make_watch_timer_on_bus()
        wt.tick(1000000)
        self.assertEqual(intc.requested, [])

    # tick: INTWTNI0 (prescaler / interval timer)

    def test_prescaler_fires_intwtni0(self):
        wt, proc, intc = _make_watch_timer_on_bus()
        wt.write(WatchTimerDevice.WTNM0, 0x01)  # n=0, fw=128, interval=2048
        wt.tick(2048)
        self.assertEqual(intc.requested, [(wt, WatchTimerDevice.INT_PRESCALER)])

    def test_prescaler_fires_at_exact_interval(self):
        wt, proc, intc = _make_watch_timer_on_bus()
        wt.write(WatchTimerDevice.WTNM0, 0x01)  # interval=2048
        wt.tick(2047)
        self.assertEqual(intc.requested, [])
        wt.tick(1)
        self.assertEqual(intc.requested, [(wt, WatchTimerDevice.INT_PRESCALER)])

    def test_prescaler_repeats(self):
        wt, proc, intc = _make_watch_timer_on_bus()
        wt.write(WatchTimerDevice.WTNM0, 0x01)  # interval=2048
        wt.tick(2048)
        wt.tick(2048)
        self.assertEqual(len(intc.requested), 2)

    def test_prescaler_fires_without_wtnm01(self):
        wt, proc, intc = _make_watch_timer_on_bus()
        wt.write(WatchTimerDevice.WTNM0, 0x01)  # WTNM00=1, WTNM01=0
        wt.tick(2048)
        self.assertEqual(intc.requested, [(wt, WatchTimerDevice.INT_PRESCALER)])

    # tick: INTWTN0 (watch timer)

    def test_watch_fires_intwtn0(self):
        wt, proc, intc = _make_watch_timer_on_bus()
        wt.write(WatchTimerDevice.WTNM0, 0x0F)  # sel=11, fw=128, interval=2048, both started
        wt.tick(2048)
        # Both INTWTNI0 and INTWTN0 fire
        self.assertIn((wt, WatchTimerDevice.INT_WATCH), intc.requested)

    def test_watch_does_not_fire_without_wtnm01(self):
        wt, proc, intc = _make_watch_timer_on_bus()
        wt.write(WatchTimerDevice.WTNM0, 0x0D)  # WTNM01=0, WTNM00=1
        wt.tick(2048)
        self.assertNotIn((wt, WatchTimerDevice.INT_WATCH), intc.requested)  # No INTWTN0

    def test_watch_repeats(self):
        wt, proc, intc = _make_watch_timer_on_bus()
        wt.write(WatchTimerDevice.WTNM0, 0x0F)  # sel=11, interval=2048
        wt.tick(2048)
        wt.tick(2048)
        self.assertEqual(intc.requested.count((wt, WatchTimerDevice.INT_WATCH)), 2)

    # enable/disable

    def test_disable_clears_counters(self):
        wt, proc, intc = _make_watch_timer_on_bus()
        wt.write(WatchTimerDevice.WTNM0, 0x01)  # enable, interval=2048
        wt.tick(2000)  # close to overflow
        wt.write(WatchTimerDevice.WTNM0, 0x00)  # disable
        wt.write(WatchTimerDevice.WTNM0, 0x01)  # re-enable
        wt.tick(2000)  # would have overflowed without clear
        self.assertEqual(intc.requested, [])

    def test_clearing_wtnm01_clears_watch_counter(self):
        wt, proc, intc = _make_watch_timer_on_bus()
        wt.write(WatchTimerDevice.WTNM0, 0x0F)  # both started, watch interval=2048
        wt.tick(2000)  # close to watch overflow
        wt.write(WatchTimerDevice.WTNM0, 0x0D)  # clear WTNM01
        wt.write(WatchTimerDevice.WTNM0, 0x0F)  # restart WTNM01
        wt.tick(2000)  # would have overflowed without clear
        self.assertNotIn((wt, WatchTimerDevice.INT_WATCH), intc.requested)

    # reset

    def test_reset_clears_wtnm0(self):
        wt = WatchTimerDevice("watch_timer")
        wt.write(WatchTimerDevice.WTNM0, 0x73)
        wt.reset()
        self.assertEqual(wt.read(WatchTimerDevice.WTNM0), 0x00)

    # bus access

    def test_bus_write_wtnm0(self):
        wt, proc, intc = _make_watch_timer_on_bus()
        wt.bus.write(0xFF41, 0x73)
        self.assertEqual(wt.read(WatchTimerDevice.WTNM0), 0x73)

    def test_bus_read_wtnm0(self):
        wt, proc, intc = _make_watch_timer_on_bus()
        wt.bus.write(0xFF41, 0x73)
        self.assertEqual(wt.bus.read(0xFF41), 0x73)

    # bounds

    def test_read_out_of_bounds_raises(self):
        wt = WatchTimerDevice("watch_timer")
        with self.assertRaises(IndexError):
            wt.read(1)

    def test_write_out_of_bounds_raises(self):
        wt = WatchTimerDevice("watch_timer")
        with self.assertRaises(IndexError):
            wt.write(1, 0x00)


class _FakeProcessor(object):
    def __init__(self):
        self.reset_count = 0

    def reset(self):
        self.reset_count += 1


class _NackI2CTarget(BaseI2CTarget):
    """I2C target that NACKs all writes."""
    def i2c_start(self, is_read):
        pass
    def i2c_stop(self):
        pass
    def i2c_read(self):
        return 0xFF
    def i2c_write(self, data):
        return self.NACK


def _make_i2c_on_bus():
    proc = _FakeProcessor()
    bus = Bus(proc)
    intc = InterruptControllerDevice("intc")
    bus.add_device(intc, (0xFFE0, 0xFFEB))
    bus.set_interrupt_controller(intc)
    i2c = I2CControllerDevice("iic0")
    bus.add_device(i2c, (0xFF1F, 0xFF1F), (0xFFA8, 0xFFAA))
    intc.connect(i2c, i2c.INT_TRANSFER, intc.INTIIC0)
    return i2c, intc, bus


class I2CControllerTests(unittest.TestCase):

    def _iicif0_set(self, intc):
        return bool(intc.read(intc.IF0H) & 0x40)

    def _clear_iicif0(self, intc):
        intc.write(intc.IF0H, intc.read(intc.IF0H) & ~0x40)

    # basics

    def test_name(self):
        i2c = I2CControllerDevice("iic0")
        self.assertEqual(i2c.name, "iic0")

    def test_size(self):
        i2c = I2CControllerDevice("iic0")
        self.assertEqual(i2c.size, 4)

    def test_registers_initially_zero(self):
        i2c = I2CControllerDevice("iic0")
        for reg in range(4):
            self.assertEqual(i2c.read(reg), 0x00)

    def test_iic0_write_read(self):
        i2c = I2CControllerDevice("iic0")
        i2c.write(i2c.IIC0, 0x42)
        self.assertEqual(i2c.read(i2c.IIC0), 0x42)

    def test_iiccl0_write_read(self):
        i2c = I2CControllerDevice("iic0")
        i2c.write(i2c.IICCL0, 0x0C)
        self.assertEqual(i2c.read(i2c.IICCL0), 0x0C)

    def test_disable_clears_status(self):
        i2c = I2CControllerDevice("iic0")
        i2c.write(i2c.IICC0, i2c.IICE0)
        i2c.write(i2c.IICS0, 0xFF)
        i2c.write(i2c.IICC0, 0x00)  # disable
        self.assertEqual(i2c.read(i2c.IICS0), 0x00)

    # writing

    def _start_transaction(self, i2c, addr_byte):
        """Set STT0, then write address byte to IIC0 (triggers _do_start).
        This matches the firmware sequence: IICC0 first, then IIC0."""
        i2c.write(i2c.IICC0, i2c.IICE0 | i2c.WTIM0
                  | i2c.ACKE0 | i2c.STT0)
        i2c.write(i2c.IIC0, addr_byte)

    def test_start_sets_iicif0(self):
        i2c, intc, bus = _make_i2c_on_bus()
        stub = StubI2CTarget()
        i2c.add_target(0x50, stub)
        self._start_transaction(i2c, 0xA0)
        self.assertTrue(self._iicif0_set(intc))

    def test_start_sets_msts0_and_trc0(self):
        i2c, intc, bus = _make_i2c_on_bus()
        stub = StubI2CTarget()
        i2c.add_target(0x50, stub)
        self._start_transaction(i2c, 0xA0)
        iics0 = i2c.read(i2c.IICS0)
        self.assertTrue(iics0 & i2c.MSTS0)
        self.assertTrue(iics0 & i2c.TRC0)

    def test_start_sets_ackd0_when_target_present(self):
        i2c, intc, bus = _make_i2c_on_bus()
        stub = StubI2CTarget()
        i2c.add_target(0x50, stub)
        self._start_transaction(i2c, 0xA0)
        self.assertTrue(i2c.read(i2c.IICS0) & i2c.ACKD0)

    def test_start_clears_ackd0_when_no_target(self):
        i2c, intc, bus = _make_i2c_on_bus()
        self._start_transaction(i2c, 0xA0)
        self.assertFalse(i2c.read(i2c.IICS0) & i2c.ACKD0)

    def test_start_clears_stt0(self):
        i2c, intc, bus = _make_i2c_on_bus()
        stub = StubI2CTarget()
        i2c.add_target(0x50, stub)
        self._start_transaction(i2c, 0xA0)
        self.assertFalse(i2c.read(i2c.IICC0) & i2c.STT0)

    def test_start_enters_wait_state(self):
        i2c, intc, bus = _make_i2c_on_bus()
        stub = StubI2CTarget()
        i2c.add_target(0x50, stub)
        self._start_transaction(i2c, 0xA0)
        self.assertTrue(i2c._waiting)

    def test_data_write_triggers_transfer(self):
        i2c, intc, bus = _make_i2c_on_bus()
        stub = StubI2CTarget()
        i2c.add_target(0x50, stub)
        self._start_transaction(i2c, 0xA0)
        self._clear_iicif0(intc)
        i2c.write(i2c.IIC0, 0x42)
        self.assertTrue(self._iicif0_set(intc))

    def test_data_write_gets_ack_from_target(self):
        i2c, intc, bus = _make_i2c_on_bus()
        stub = StubI2CTarget()
        i2c.add_target(0x50, stub)
        self._start_transaction(i2c, 0xA0)
        self._clear_iicif0(intc)
        i2c.write(i2c.IIC0, 0x42)
        self.assertTrue(i2c.read(i2c.IICS0) & i2c.ACKD0)

    def test_stop_sets_std0(self):
        i2c, intc, bus = _make_i2c_on_bus()
        stub = StubI2CTarget()
        i2c.add_target(0x50, stub)
        self._start_transaction(i2c, 0xA0)
        i2c.write(i2c.IICC0, i2c.IICE0 | i2c.WTIM0
                  | i2c.ACKE0 | i2c.SPT0)
        self.assertTrue(i2c.read(i2c.IICS0) & i2c.STD0)

    def test_stop_clears_waiting(self):
        i2c, intc, bus = _make_i2c_on_bus()
        stub = StubI2CTarget()
        i2c.add_target(0x50, stub)
        self._start_transaction(i2c, 0xA0)
        i2c.write(i2c.IICC0, i2c.IICE0 | i2c.WTIM0
                  | i2c.ACKE0 | i2c.SPT0)
        self.assertFalse(i2c._waiting)

    def test_waiting_persists_across_bytes(self):
        i2c, intc, bus = _make_i2c_on_bus()
        stub = StubI2CTarget()
        i2c.add_target(0x50, stub)
        self._start_transaction(i2c, 0xA0)
        self._clear_iicif0(intc)
        self.assertTrue(i2c._waiting)
        i2c.write(i2c.IIC0, 0x10)
        self._clear_iicif0(intc)
        self.assertTrue(i2c._waiting)
        i2c.write(i2c.IIC0, 0x42)
        self._clear_iicif0(intc)
        self.assertTrue(i2c._waiting)
        i2c.write(i2c.IICC0, i2c.IICE0 | i2c.WTIM0
                  | i2c.ACKE0 | i2c.SPT0)
        self.assertFalse(i2c._waiting)

    def test_nack_from_target_clears_ackd0(self):
        i2c, intc, bus = _make_i2c_on_bus()
        nacker = _NackI2CTarget()
        i2c.add_target(0x50, nacker)
        self._start_transaction(i2c, 0xA0)
        self._clear_iicif0(intc)
        i2c.write(i2c.IIC0, 0x42)
        self.assertFalse(i2c.read(i2c.IICS0) & i2c.ACKD0)

    def test_wrel0_triggers_next_byte(self):
        i2c, intc, bus = _make_i2c_on_bus()
        stub = StubI2CTarget(read_value=0x77)
        i2c.add_target(0x50, stub)
        self._start_transaction(i2c, 0xA1)  # read mode
        self._clear_iicif0(intc)
        i2c.write(i2c.IICC0, i2c.IICE0 | i2c.WTIM0
                  | i2c.ACKE0 | i2c.WREL0)
        self.assertEqual(i2c.read(i2c.IIC0), 0x77)
        self.assertTrue(self._iicif0_set(intc))

    def test_read_clears_trc0(self):
        i2c, intc, bus = _make_i2c_on_bus()
        stub = StubI2CTarget(read_value=0x42)
        i2c.add_target(0x50, stub)
        self._start_transaction(i2c, 0xA1)  # read mode
        self.assertTrue(i2c.read(i2c.IICS0) & i2c.TRC0)  # TRC0 set after start
        self._clear_iicif0(intc)
        i2c.write(i2c.IIC0, 0xFF)  # trigger read
        self.assertFalse(i2c.read(i2c.IICS0) & i2c.TRC0)  # TRC0 cleared

    def test_disable_mid_transaction(self):
        i2c, intc, bus = _make_i2c_on_bus()
        stub = StubI2CTarget()
        i2c.add_target(0x50, stub)
        self._start_transaction(i2c, 0xA0)
        self.assertTrue(i2c._waiting)
        i2c.write(i2c.IICC0, 0x00)  # clear IICE0
        self.assertFalse(i2c._waiting)
        self.assertEqual(i2c.read(i2c.IICS0), 0x00)
        self.assertIsNone(i2c._active_target)

    def test_write_iic0_while_not_waiting_does_not_transfer(self):
        i2c, intc, bus = _make_i2c_on_bus()
        stub = StubI2CTarget()
        i2c.add_target(0x50, stub)
        i2c.write(i2c.IICC0, i2c.IICE0)  # enable but no start
        i2c.write(i2c.IIC0, 0x42)
        self.assertFalse(self._iicif0_set(intc))

    # reading

    def test_read_byte_from_target(self):
        i2c, intc, bus = _make_i2c_on_bus()
        stub = StubI2CTarget(read_value=0x42)
        i2c.add_target(0x50, stub)
        self._start_transaction(i2c, 0xA1)
        self._clear_iicif0(intc)
        i2c.write(i2c.IIC0, 0xFF)
        self.assertEqual(i2c.read(i2c.IIC0), 0x42)
        self.assertTrue(self._iicif0_set(intc))
