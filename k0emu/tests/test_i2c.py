import unittest
from k0emu.bus import Bus
from k0emu.devices import I2CControllerDevice, InterruptControllerDevice
from k0emu.i2c import M24C04


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


class M24C04Tests(unittest.TestCase):

    def _clear_iicif0(self, intc):
        intc.write(InterruptControllerDevice.IF0H,
                   intc.read(InterruptControllerDevice.IF0H) & ~0x40)

    def _start(self, i2c, intc, addr_byte):
        i2c.write(I2CControllerDevice.IIC0, addr_byte)
        i2c.write(I2CControllerDevice.IICC0, I2CControllerDevice.IICE0 | I2CControllerDevice.WTIM0
                  | I2CControllerDevice.ACKE0 | I2CControllerDevice.STT0)
        self._clear_iicif0(intc)

    def _write_byte(self, i2c, intc, data):
        i2c.write(I2CControllerDevice.IIC0, data)
        self._clear_iicif0(intc)

    def _read_byte(self, i2c, intc):
        i2c.write(I2CControllerDevice.IIC0, 0xFF)
        val = i2c.read(I2CControllerDevice.IIC0)
        self._clear_iicif0(intc)
        return val

    def _stop(self, i2c, intc):
        iicc0 = i2c.read(I2CControllerDevice.IICC0)
        i2c.write(I2CControllerDevice.IICC0, (iicc0 & ~I2CControllerDevice.STT0) | I2CControllerDevice.SPT0)
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
