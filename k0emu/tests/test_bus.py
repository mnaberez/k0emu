import unittest
from k0emu.bus import Bus
from k0emu.devices import MemoryDevice


class _FakeProcessor(object):
    def __init__(self):
        self.reset_count = 0

    def reset(self):
        self.reset_count += 1


class BusTests(unittest.TestCase):

    # read/write routing

    def test_read_routes_to_device(self):
        proc = _FakeProcessor()
        bus = Bus(proc)
        mem = MemoryDevice("test", size=4)
        bus.add_device(0x1000, 0x1003, mem)
        mem.write(2, 0x42)
        self.assertEqual(bus.read(0x1002), 0x42)

    def test_write_routes_to_device(self):
        proc = _FakeProcessor()
        bus = Bus(proc)
        mem = MemoryDevice("test", size=4)
        bus.add_device(0x1000, 0x1003, mem)
        bus.write(0x1001, 0x42)
        self.assertEqual(mem.read(1), 0x42)

    # address translation

    def test_device_sees_local_address(self):
        proc = _FakeProcessor()
        bus = Bus(proc)
        mem = MemoryDevice("test", size=4)
        bus.add_device(0x8000, 0x8003, mem)
        bus.write(0x8003, 0x42)
        self.assertEqual(mem.read(3), 0x42)

    # unmapped addresses

    def test_read_unmapped_returns_zero(self):
        proc = _FakeProcessor()
        bus = Bus(proc)
        self.assertEqual(bus.read(0x0000), 0)

    def test_write_unmapped_does_not_raise(self):
        proc = _FakeProcessor()
        bus = Bus(proc)
        bus.write(0x0000, 0x42)  # should not raise

    # multiple devices

    def test_two_devices_at_different_ranges(self):
        proc = _FakeProcessor()
        bus = Bus(proc)
        mem_a = MemoryDevice("a", size=4)
        mem_b = MemoryDevice("b", size=4)
        bus.add_device(0x1000, 0x1003, mem_a)
        bus.add_device(0x2000, 0x2003, mem_b)
        bus.write(0x1000, 0x11)
        bus.write(0x2000, 0x22)
        self.assertEqual(bus.read(0x1000), 0x11)
        self.assertEqual(bus.read(0x2000), 0x22)

    def test_later_device_overlays_earlier(self):
        proc = _FakeProcessor()
        bus = Bus(proc)
        mem_a = MemoryDevice("a", size=4, fill=0xAA)
        mem_b = MemoryDevice("b", size=2, fill=0xBB)
        bus.add_device(0x1000, 0x1003, mem_a)
        bus.add_device(0x1000, 0x1001, mem_b)
        self.assertEqual(bus.read(0x1000), 0xBB)  # overlaid by b
        self.assertEqual(bus.read(0x1002), 0xAA)  # still a

    # reset

    def test_reset_resets_all_devices(self):
        proc = _FakeProcessor()
        bus = Bus(proc)
        mem = MemoryDevice("test", size=4)
        bus.add_device(0x1000, 0x1003, mem)
        mem.ticks = 99
        bus.reset()
        # BaseDevice.reset() is a no-op, but processor.reset() is called
        self.assertEqual(proc.reset_count, 1)

    def test_reset_resets_processor(self):
        proc = _FakeProcessor()
        bus = Bus(proc)
        bus.reset()
        self.assertEqual(proc.reset_count, 1)

    # tick

    def test_tick_fans_out_to_all_devices(self):
        proc = _FakeProcessor()
        bus = Bus(proc)
        mem_a = MemoryDevice("a", size=4)
        mem_b = MemoryDevice("b", size=4)
        bus.add_device(0x1000, 0x1003, mem_a)
        bus.add_device(0x2000, 0x2003, mem_b)
        bus.tick(5)
        self.assertEqual(mem_a.ticks, 5)
        self.assertEqual(mem_b.ticks, 5)

    def test_tick_accumulates(self):
        proc = _FakeProcessor()
        bus = Bus(proc)
        mem = MemoryDevice("test", size=4)
        bus.add_device(0x1000, 0x1003, mem)
        bus.tick(3)
        bus.tick(7)
        self.assertEqual(mem.ticks, 10)

    # device lookup by name

    def test_device_finds_by_name(self):
        proc = _FakeProcessor()
        bus = Bus(proc)
        mem = MemoryDevice("my_ram", size=4)
        bus.add_device(0x1000, 0x1003, mem)
        self.assertIs(bus.device("my_ram"), mem)

    def test_device_raises_for_unknown_name(self):
        proc = _FakeProcessor()
        bus = Bus(proc)
        with self.assertRaises(KeyError):
            bus.device("nonexistent")

    # subscript access

    def test_getitem_reads_address(self):
        proc = _FakeProcessor()
        bus = Bus(proc)
        mem = MemoryDevice("test", size=4)
        bus.add_device(0x1000, 0x1003, mem)
        mem.write(0, 0x42)
        self.assertEqual(bus[0x1000], 0x42)

    def test_setitem_writes_address(self):
        proc = _FakeProcessor()
        bus = Bus(proc)
        mem = MemoryDevice("test", size=4)
        bus.add_device(0x1000, 0x1003, mem)
        bus[0x1001] = 0x42
        self.assertEqual(mem.read(1), 0x42)


