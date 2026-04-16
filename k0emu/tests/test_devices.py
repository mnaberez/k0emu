import unittest
from k0emu.devices.devices import MemoryDevice


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


