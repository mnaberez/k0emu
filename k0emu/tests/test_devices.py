import unittest
from k0emu.bus import Bus
from k0emu.devices import MemoryDevice, RegisterFileDevice, WatchdogDevice


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


class _FakeProcessor(object):
    def __init__(self):
        self.reset_count = 0

    def reset(self):
        self.reset_count += 1


class _FakeIntc(object):
    """Minimal stub for testing devices that set interrupt flags."""
    def __init__(self):
        self.name = "intc"
        self.bus = None
        self.size = 12  # IF0L..PR1L
        self.ticks = 0
        self.flags = []  # list of (reg_offset, bit) tuples

    def set_flag(self, reg_offset, bit):
        self.flags.append((reg_offset, bit))

    def read(self, offset):
        return 0

    def write(self, offset, value):
        pass

    def reset(self):
        self.flags = []

    def tick(self, cycles):
        self.ticks += cycles


def _make_watchdog_on_bus():
    """Create a WatchdogDevice on a bus with a fake processor and intc."""
    proc = _FakeProcessor()
    bus = Bus(proc)
    intc = _FakeIntc()
    bus.add_device(intc, (0xFFE0, 0xFFEB))
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
        self.assertEqual(intc.flags, [])

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
        self.assertEqual(intc.flags, [(0, 0x01)])

    def test_overflow_mode_interval_repeats(self):
        wd, proc, intc = _make_watchdog_on_bus()
        wd.write(WatchdogDevice.WDCS, 0x00)  # interval = 4096
        wd.write(WatchdogDevice.WDTM, 0x80)
        wd.tick(4096)
        wd.tick(4096)
        self.assertEqual(len(intc.flags), 2)

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


