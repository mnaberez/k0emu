import unittest
from k0emu.bus import Bus
from k0emu.devices import MemoryDevice, RegisterFileDevice


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
        rf = RegisterFileDevice()
        self.assertEqual(rf.name, "register_file")

    def test_size_is_32_bytes(self):
        rf = RegisterFileDevice()
        self.assertEqual(rf.size, 32)

    def test_initialized_to_zero(self):
        rf = RegisterFileDevice()
        for i in range(32):
            self.assertEqual(rf.read(i), 0)

    # layout: bank 3 at offset 0, bank 0 at offset 24

    def test_bank0_at_top(self):
        rf = RegisterFileDevice()
        rf.write(24, 0x42)  # bank 0, register X
        self.assertEqual(rf.read(24), 0x42)

    def test_bank3_at_bottom(self):
        rf = RegisterFileDevice()
        rf.write(0, 0x42)  # bank 3, register X
        self.assertEqual(rf.read(0), 0x42)

    def test_banks_are_independent(self):
        rf = RegisterFileDevice()
        rf.write(24, 0xAA)  # bank 0, register X
        rf.write(0, 0xBB)   # bank 3, register X
        self.assertEqual(rf.read(24), 0xAA)
        self.assertEqual(rf.read(0), 0xBB)

    # bounds

    def test_out_of_bounds_raises(self):
        rf = RegisterFileDevice()
        with self.assertRaises(IndexError):
            rf.read(32)
