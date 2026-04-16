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
        bus.add_device(mem, (0x1000, 0x1003))
        mem.write(2, 0x42)
        self.assertEqual(bus.read(0x1002), 0x42)

    def test_write_routes_to_device(self):
        proc = _FakeProcessor()
        bus = Bus(proc)
        mem = MemoryDevice("test", size=4)
        bus.add_device(mem, (0x1000, 0x1003))
        bus.write(0x1001, 0x42)
        self.assertEqual(mem.read(1), 0x42)

    # address translation

    def test_device_sees_local_address(self):
        proc = _FakeProcessor()
        bus = Bus(proc)
        mem = MemoryDevice("test", size=4)
        bus.add_device(mem, (0x8000, 0x8003))
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
        bus.add_device(mem_a, (0x1000, 0x1003))
        bus.add_device(mem_b, (0x2000, 0x2003))
        bus.write(0x1000, 0x11)
        bus.write(0x2000, 0x22)
        self.assertEqual(bus.read(0x1000), 0x11)
        self.assertEqual(bus.read(0x2000), 0x22)

    # registration validation

    def test_overlapping_device_raises(self):
        proc = _FakeProcessor()
        bus = Bus(proc)
        mem_a = MemoryDevice("a", size=4)
        mem_b = MemoryDevice("b", size=2)
        bus.add_device(mem_a, (0x1000, 0x1003))
        with self.assertRaises(ValueError):
            bus.add_device(mem_b, (0x1000, 0x1001))

    def test_start_negative_raises(self):
        proc = _FakeProcessor()
        bus = Bus(proc)
        mem = MemoryDevice("test", size=1)
        with self.assertRaises(ValueError):
            bus.add_device(mem, (-1, -1))

    def test_end_past_address_space_raises(self):
        proc = _FakeProcessor()
        bus = Bus(proc)
        mem = MemoryDevice("test", size=2)
        with self.assertRaises(ValueError):
            bus.add_device(mem, (0xFFFF, 0x10000))

    def test_start_greater_than_end_raises(self):
        proc = _FakeProcessor()
        bus = Bus(proc)
        mem = MemoryDevice("test", size=4)
        with self.assertRaises(ValueError):
            bus.add_device(mem, (0x1003, 0x1000))

    def test_range_size_mismatch_raises(self):
        proc = _FakeProcessor()
        bus = Bus(proc)
        mem = MemoryDevice("test", size=4)
        with self.assertRaises(ValueError):
            bus.add_device(mem, (0x1000, 0x1001))

    # non-contiguous ranges

    def test_non_contiguous_ranges_assign_sequential_registers(self):
        proc = _FakeProcessor()
        bus = Bus(proc)
        mem = MemoryDevice("test", size=3)
        bus.add_device(mem, (0x1000, 0x1000), (0x2000, 0x2001))
        bus.write(0x1000, 0xAA)  # register 0
        bus.write(0x2000, 0xBB)  # register 1
        bus.write(0x2001, 0xCC)  # register 2
        self.assertEqual(mem.read(0), 0xAA)
        self.assertEqual(mem.read(1), 0xBB)
        self.assertEqual(mem.read(2), 0xCC)

    # add_device sets bus reference

    def test_add_device_sets_bus_on_device(self):
        proc = _FakeProcessor()
        bus = Bus(proc)
        mem = MemoryDevice("test", size=4)
        self.assertIsNone(mem.bus)
        bus.add_device(mem, (0x1000, 0x1003))
        self.assertIs(mem.bus, bus)

    # reset

    def test_reset_resets_all_devices(self):
        proc = _FakeProcessor()
        bus = Bus(proc)
        mem = MemoryDevice("test", size=4)
        bus.add_device(mem, (0x1000, 0x1003))
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
        bus.add_device(mem_a, (0x1000, 0x1003))
        bus.add_device(mem_b, (0x2000, 0x2003))
        bus.tick(5)
        self.assertEqual(mem_a.ticks, 5)
        self.assertEqual(mem_b.ticks, 5)

    def test_tick_accumulates(self):
        proc = _FakeProcessor()
        bus = Bus(proc)
        mem = MemoryDevice("test", size=4)
        bus.add_device(mem, (0x1000, 0x1003))
        bus.tick(3)
        bus.tick(7)
        self.assertEqual(mem.ticks, 10)

    # device lookup by name

    def test_device_finds_by_name(self):
        proc = _FakeProcessor()
        bus = Bus(proc)
        mem = MemoryDevice("my_ram", size=4)
        bus.add_device(mem, (0x1000, 0x1003))
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
        bus.add_device(mem, (0x1000, 0x1003))
        mem.write(0, 0x42)
        self.assertEqual(bus[0x1000], 0x42)

    def test_setitem_writes_address(self):
        proc = _FakeProcessor()
        bus = Bus(proc)
        mem = MemoryDevice("test", size=4)
        bus.add_device(mem, (0x1000, 0x1003))
        bus[0x1001] = 0x42
        self.assertEqual(mem.read(1), 0x42)

    # memory map

    def test_memory_map_empty_bus(self):
        proc = _FakeProcessor()
        bus = Bus(proc)
        entries = bus.memory_map()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0][0], 0x0000)
        self.assertEqual(entries[0][1], 0xFFFF)
        self.assertEqual(entries[0][2].name, "unmapped")

    def test_memory_map_single_device(self):
        proc = _FakeProcessor()
        bus = Bus(proc)
        mem = MemoryDevice("ram", size=4)
        bus.add_device(mem, (0x1000, 0x1003))
        entries = bus.memory_map()
        self.assertEqual(entries[0], (0x0000, 0x0FFF, bus._unmapped))
        self.assertEqual(entries[1], (0x1000, 0x1003, mem))
        self.assertEqual(entries[2], (0x1004, 0xFFFF, bus._unmapped))
        self.assertEqual(len(entries), 3)

    def test_memory_map_contiguous_addresses_collapsed(self):
        proc = _FakeProcessor()
        bus = Bus(proc)
        mem = MemoryDevice("ram", size=0x1000)
        bus.add_device(mem, (0x2000, 0x2FFF))
        entries = [(s, e, d.name) for s, e, d in bus.memory_map()]
        self.assertEqual(entries[1], (0x2000, 0x2FFF, "ram"))

    def test_memory_map_non_contiguous_device_has_two_entries(self):
        proc = _FakeProcessor()
        bus = Bus(proc)
        mem = MemoryDevice("scattered", size=3)
        bus.add_device(mem, (0x1000, 0x1000), (0x2000, 0x2001))
        names = [(s, e, d.name) for s, e, d in bus.memory_map()]
        self.assertIn((0x1000, 0x1000, "scattered"), names)
        self.assertIn((0x2000, 0x2001, "scattered"), names)

    def test_memory_map_returns_device_objects(self):
        proc = _FakeProcessor()
        bus = Bus(proc)
        mem = MemoryDevice("ram", size=4)
        bus.add_device(mem, (0x1000, 0x1003))
        entries = bus.memory_map()
        self.assertIs(entries[1][2], mem)


