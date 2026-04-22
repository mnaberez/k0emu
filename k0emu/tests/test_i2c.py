import unittest
from k0emu.bus import Bus
from k0emu.devices import I2CControllerDevice, InterruptControllerDevice
from k0emu.i2c import M24C04


class M24C04Tests(unittest.TestCase):

    def test_write_sets_address(self):
        data = bytearray(512)
        eeprom = M24C04(data, page_offset=0)
        eeprom.i2c_start(is_read=False)
        eeprom.i2c_write(0x10)  # set address
        eeprom.i2c_write(0x42)  # write data
        eeprom.i2c_stop()
        self.assertEqual(data[0x10], 0x42)

    def test_write_increments_address(self):
        data = bytearray(512)
        eeprom = M24C04(data, page_offset=0)
        eeprom.i2c_start(is_read=False)
        eeprom.i2c_write(0x20)
        eeprom.i2c_write(0xAA)
        eeprom.i2c_write(0xBB)
        eeprom.i2c_write(0xCC)
        eeprom.i2c_stop()
        self.assertEqual(data[0x20], 0xAA)
        self.assertEqual(data[0x21], 0xBB)
        self.assertEqual(data[0x22], 0xCC)

    def test_read_returns_data(self):
        data = bytearray(512)
        data[0x10] = 0x42
        eeprom = M24C04(data, page_offset=0)
        eeprom.i2c_start(is_read=False)
        eeprom.i2c_write(0x10)  # set address
        eeprom.i2c_stop()
        eeprom.i2c_start(is_read=True)
        self.assertEqual(eeprom.i2c_read(), 0x42)
        eeprom.i2c_stop()

    def test_read_increments_address(self):
        data = bytearray(512)
        data[0x20] = 0xAA
        data[0x21] = 0xBB
        data[0x22] = 0xCC
        eeprom = M24C04(data, page_offset=0)
        eeprom.i2c_start(is_read=False)
        eeprom.i2c_write(0x20)
        eeprom.i2c_stop()
        eeprom.i2c_start(is_read=True)
        self.assertEqual(eeprom.i2c_read(), 0xAA)
        self.assertEqual(eeprom.i2c_read(), 0xBB)
        self.assertEqual(eeprom.i2c_read(), 0xCC)
        eeprom.i2c_stop()

    def test_address_wraps_at_256(self):
        data = bytearray(512)
        data[0] = 0x99
        eeprom = M24C04(data, page_offset=0)
        eeprom.i2c_start(is_read=False)
        eeprom.i2c_write(0xFF)  # address 255
        eeprom.i2c_stop()
        eeprom.i2c_start(is_read=True)
        eeprom.i2c_read()       # read 255, address wraps to 0
        self.assertEqual(eeprom.i2c_read(), 0x99)
        eeprom.i2c_stop()

    def test_page_offset(self):
        data = bytearray(512)
        eeprom = M24C04(data, page_offset=256)
        eeprom.i2c_start(is_read=False)
        eeprom.i2c_write(0x10)
        eeprom.i2c_write(0x42)
        eeprom.i2c_stop()
        self.assertEqual(data[256 + 0x10], 0x42)

    def test_write_acks(self):
        data = bytearray(512)
        eeprom = M24C04(data, page_offset=0)
        eeprom.i2c_start(is_read=False)
        self.assertTrue(eeprom.i2c_write(0x10))
        self.assertTrue(eeprom.i2c_write(0x42))
        eeprom.i2c_stop()

    def test_shared_backing_store(self):
        data = bytearray(512)
        lower = M24C04(data, page_offset=0)
        upper = M24C04(data, page_offset=256)
        lower.i2c_start(is_read=False)
        lower.i2c_write(0x10)
        lower.i2c_write(0x11)
        lower.i2c_stop()
        upper.i2c_start(is_read=False)
        upper.i2c_write(0x10)
        upper.i2c_write(0x22)
        upper.i2c_stop()
        self.assertEqual(data[0x10], 0x11)
        self.assertEqual(data[0x110], 0x22)


    def test_write_wraps_within_page(self):
        """M24C04 page write: address wraps within 16-byte page boundary."""
        data = bytearray(512)
        eeprom = M24C04(data, page_offset=0)
        eeprom.i2c_start(is_read=False)
        eeprom.i2c_write(0x1E)  # address 0x1E (page 1, offset 14)
        eeprom.i2c_write(0xAA)  # -> 0x1E
        eeprom.i2c_write(0xBB)  # -> 0x1F
        eeprom.i2c_write(0xCC)  # -> 0x10 (wraps within page 0x10-0x1F)
        eeprom.i2c_stop()
        self.assertEqual(data[0x1E], 0xAA)
        self.assertEqual(data[0x1F], 0xBB)
        self.assertEqual(data[0x10], 0xCC)  # wrapped within page
        self.assertEqual(data[0x20], 0x00)  # next page untouched

    def test_write_does_not_wrap_across_pages(self):
        """Writing past end of page wraps to start of same page, not next."""
        data = bytearray(512)
        eeprom = M24C04(data, page_offset=0)
        eeprom.i2c_start(is_read=False)
        eeprom.i2c_write(0x0F)  # last byte of page 0
        eeprom.i2c_write(0x11)  # -> 0x0F
        eeprom.i2c_write(0x22)  # -> 0x00 (wraps to start of page 0)
        eeprom.i2c_stop()
        self.assertEqual(data[0x0F], 0x11)
        self.assertEqual(data[0x00], 0x22)  # wrapped to page start
        self.assertEqual(data[0x10], 0x00)  # page 1 untouched

    def test_read_wraps_at_256(self):
        """Reads wrap across the full 256-byte address space, not per page."""
        data = bytearray(512)
        data[0xFF] = 0xAA
        data[0x00] = 0xBB
        eeprom = M24C04(data, page_offset=0)
        eeprom.i2c_start(is_read=False)
        eeprom.i2c_write(0xFF)
        eeprom.i2c_stop()
        eeprom.i2c_start(is_read=True)
        self.assertEqual(eeprom.i2c_read(), 0xAA)  # 0xFF
        self.assertEqual(eeprom.i2c_read(), 0xBB)  # wraps to 0x00
        eeprom.i2c_stop()

    def test_current_address_read(self):
        """After setting address and stopping, a read starts from that address."""
        data = bytearray(512)
        data[0x42] = 0x99
        eeprom = M24C04(data, page_offset=0)
        eeprom.i2c_start(is_read=False)
        eeprom.i2c_write(0x42)  # set address
        eeprom.i2c_stop()
        eeprom.i2c_start(is_read=True)
        self.assertEqual(eeprom.i2c_read(), 0x99)
        eeprom.i2c_stop()

    def test_write_address_byte_always_acks(self):
        data = bytearray(512)
        eeprom = M24C04(data, page_offset=0)
        eeprom.i2c_start(is_read=False)
        self.assertTrue(eeprom.i2c_write(0x00))

    def test_page_offset_read(self):
        data = bytearray(512)
        data[256 + 0x10] = 0x77
        eeprom = M24C04(data, page_offset=256)
        eeprom.i2c_start(is_read=False)
        eeprom.i2c_write(0x10)
        eeprom.i2c_stop()
        eeprom.i2c_start(is_read=True)
        self.assertEqual(eeprom.i2c_read(), 0x77)
        eeprom.i2c_stop()


class _FakeProcessor(object):
    def __init__(self):
        self.reset_count = 0

    def reset(self):
        self.reset_count += 1


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


class M24C04IntegrationTests(unittest.TestCase):

    def _clear_iicif0(self, intc):
        intc.write(intc.IF0H, intc.read(intc.IF0H) & ~0x40)

    def _start(self, i2c, intc, addr_byte):
        i2c.write(i2c.IICC0, i2c.IICE0 | i2c.WTIM0
                  | i2c.ACKE0 | i2c.STT0)
        i2c.write(i2c.IIC0, addr_byte)
        self._clear_iicif0(intc)

    def _write_byte(self, i2c, intc, data):
        i2c.write(i2c.IIC0, data)
        self._clear_iicif0(intc)

    def _read_byte(self, i2c, intc):
        i2c.write(i2c.IIC0, 0xFF)
        val = i2c.read(i2c.IIC0)
        self._clear_iicif0(intc)
        return val

    def _stop(self, i2c, intc):
        iicc0 = i2c.read(i2c.IICC0)
        i2c.write(i2c.IICC0, (iicc0 & ~i2c.STT0) | i2c.SPT0)
        self._clear_iicif0(intc)

    def test_write_one_byte_read_back(self):
        i2c, intc, bus = _make_i2c_on_bus()
        eeprom_data = bytearray(512)
        i2c.add_target(0x50, M24C04(eeprom_data, page_offset=0))

        self._start(i2c, intc, 0xA0)
        self._write_byte(i2c, intc, 0x10)
        self._write_byte(i2c, intc, 0x42)
        self._stop(i2c, intc)

        self._start(i2c, intc, 0xA0)
        self._write_byte(i2c, intc, 0x10)
        self._stop(i2c, intc)
        self._start(i2c, intc, 0xA1)
        val = self._read_byte(i2c, intc)
        self._stop(i2c, intc)

        self.assertEqual(val, 0x42)

    def test_write_multiple_bytes_read_back(self):
        i2c, intc, bus = _make_i2c_on_bus()
        eeprom_data = bytearray(512)
        i2c.add_target(0x50, M24C04(eeprom_data, page_offset=0))

        self._start(i2c, intc, 0xA0)
        self._write_byte(i2c, intc, 0x20)
        self._write_byte(i2c, intc, 0xAA)
        self._write_byte(i2c, intc, 0xBB)
        self._write_byte(i2c, intc, 0xCC)
        self._stop(i2c, intc)

        self._start(i2c, intc, 0xA0)
        self._write_byte(i2c, intc, 0x20)
        self._stop(i2c, intc)
        self._start(i2c, intc, 0xA1)
        self.assertEqual(self._read_byte(i2c, intc), 0xAA)
        self.assertEqual(self._read_byte(i2c, intc), 0xBB)
        self.assertEqual(self._read_byte(i2c, intc), 0xCC)
        self._stop(i2c, intc)

    def test_write_lower_and_upper_pages(self):
        i2c, intc, bus = _make_i2c_on_bus()
        eeprom_data = bytearray(512)
        i2c.add_target(0x50, M24C04(eeprom_data, page_offset=0))
        i2c.add_target(0x51, M24C04(eeprom_data, page_offset=256))

        self._start(i2c, intc, 0xA0)
        self._write_byte(i2c, intc, 0x10)
        self._write_byte(i2c, intc, 0x11)
        self._stop(i2c, intc)

        self._start(i2c, intc, 0xA2)
        self._write_byte(i2c, intc, 0x10)
        self._write_byte(i2c, intc, 0x22)
        self._stop(i2c, intc)

        self.assertEqual(eeprom_data[0x10], 0x11)
        self.assertEqual(eeprom_data[0x110], 0x22)

    def test_eeprom_backed_by_shared_data(self):
        i2c, intc, bus = _make_i2c_on_bus()
        eeprom_data = bytearray(512)
        eeprom_data[0x42] = 0x99
        i2c.add_target(0x50, M24C04(eeprom_data, page_offset=0))

        self._start(i2c, intc, 0xA0)
        self._write_byte(i2c, intc, 0x42)
        self._stop(i2c, intc)
        self._start(i2c, intc, 0xA1)
        self.assertEqual(self._read_byte(i2c, intc), 0x99)
        self._stop(i2c, intc)
