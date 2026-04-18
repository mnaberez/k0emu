import unittest
from k0emu.bus import Bus
from k0emu.devices import (BaseDevice, MemoryDevice, I2CControllerDevice,
                           InterruptControllerDevice)
from k0emu.i2c import StubI2CTarget, M24C04


class _FakeProcessor(object):
    def __init__(self):
        self.reset_count = 0

    def reset(self):
        self.reset_count += 1


def _make_i2c_on_bus():
    """Create an I2C device on a bus with an interrupt controller."""
    proc = _FakeProcessor()
    bus = Bus(proc)
    intc = InterruptControllerDevice("intc")
    bus.add_device(intc, (0xFFE0, 0xFFEB))
    bus.set_interrupt_controller(intc)
    i2c = I2CControllerDevice("iic0")
    bus.add_device(i2c, (0xFF1F, 0xFF1F), (0xFFA8, 0xFFAA))
    intc.connect(i2c, i2c.INT_TRANSFER, intc.INTIIC0)
    return i2c, intc, bus


class I2CControllerDeviceBasicTests(unittest.TestCase):

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
        i2c.write(I2CControllerDevice.IIC0, 0x42)
        self.assertEqual(i2c.read(I2CControllerDevice.IIC0), 0x42)

    def test_iiccl0_write_read(self):
        i2c = I2CControllerDevice("iic0")
        i2c.write(I2CControllerDevice.IICCL0, 0x0C)
        self.assertEqual(i2c.read(I2CControllerDevice.IICCL0), 0x0C)

    def test_disable_clears_status(self):
        i2c = I2CControllerDevice("iic0")
        i2c.write(I2CControllerDevice.IICC0, I2CControllerDevice.IICE0)
        i2c.write(I2CControllerDevice.IICS0, 0xFF)
        i2c.write(I2CControllerDevice.IICC0, 0x00)  # disable
        self.assertEqual(i2c.read(I2CControllerDevice.IICS0), 0x00)


class I2CMasterWriteTests(unittest.TestCase):
    """Test controller write: start -> address+W -> data bytes -> stop."""

    def _iicif0_set(self, intc):
        return bool(intc.read(InterruptControllerDevice.IF0H) & 0x40)

    def _clear_iicif0(self, intc):
        intc.write(InterruptControllerDevice.IF0H,
                   intc.read(InterruptControllerDevice.IF0H) & ~0x40)

    def test_start_sets_iicif0(self):
        i2c, intc, bus = _make_i2c_on_bus()
        stub = StubI2CTarget()
        i2c.add_target(0x50, stub)
        # Write address byte (0x50 write = 0xA0)
        i2c.write(I2CControllerDevice.IIC0, 0xA0)
        # Enable + start
        i2c.write(I2CControllerDevice.IICC0, I2CControllerDevice.IICE0 | I2CControllerDevice.WTIM0
                  | I2CControllerDevice.ACKE0 | I2CControllerDevice.STT0)
        self.assertTrue(self._iicif0_set(intc))

    def test_start_sets_msts0_and_trc0(self):
        i2c, intc, bus = _make_i2c_on_bus()
        stub = StubI2CTarget()
        i2c.add_target(0x50, stub)
        i2c.write(I2CControllerDevice.IIC0, 0xA0)
        i2c.write(I2CControllerDevice.IICC0, I2CControllerDevice.IICE0 | I2CControllerDevice.WTIM0
                  | I2CControllerDevice.ACKE0 | I2CControllerDevice.STT0)
        iics0 = i2c.read(I2CControllerDevice.IICS0)
        self.assertTrue(iics0 & I2CControllerDevice.MSTS0)  # controller mode
        self.assertTrue(iics0 & I2CControllerDevice.TRC0)    # transmit mode

    def test_start_sets_ackd0_when_target_present(self):
        i2c, intc, bus = _make_i2c_on_bus()
        stub = StubI2CTarget()
        i2c.add_target(0x50, stub)
        i2c.write(I2CControllerDevice.IIC0, 0xA0)
        i2c.write(I2CControllerDevice.IICC0, I2CControllerDevice.IICE0 | I2CControllerDevice.WTIM0
                  | I2CControllerDevice.ACKE0 | I2CControllerDevice.STT0)
        self.assertTrue(i2c.read(I2CControllerDevice.IICS0) & I2CControllerDevice.ACKD0)

    def test_start_clears_ackd0_when_no_target(self):
        i2c, intc, bus = _make_i2c_on_bus()
        # No target at 0x50
        i2c.write(I2CControllerDevice.IIC0, 0xA0)
        i2c.write(I2CControllerDevice.IICC0, I2CControllerDevice.IICE0 | I2CControllerDevice.WTIM0
                  | I2CControllerDevice.ACKE0 | I2CControllerDevice.STT0)
        self.assertFalse(i2c.read(I2CControllerDevice.IICS0) & I2CControllerDevice.ACKD0)

    def test_start_clears_stt0(self):
        i2c, intc, bus = _make_i2c_on_bus()
        stub = StubI2CTarget()
        i2c.add_target(0x50, stub)
        i2c.write(I2CControllerDevice.IIC0, 0xA0)
        i2c.write(I2CControllerDevice.IICC0, I2CControllerDevice.IICE0 | I2CControllerDevice.WTIM0
                  | I2CControllerDevice.ACKE0 | I2CControllerDevice.STT0)
        self.assertFalse(i2c.read(I2CControllerDevice.IICC0) & I2CControllerDevice.STT0)

    def test_start_enters_wait_state(self):
        i2c, intc, bus = _make_i2c_on_bus()
        stub = StubI2CTarget()
        i2c.add_target(0x50, stub)
        i2c.write(I2CControllerDevice.IIC0, 0xA0)
        i2c.write(I2CControllerDevice.IICC0, I2CControllerDevice.IICE0 | I2CControllerDevice.WTIM0
                  | I2CControllerDevice.ACKE0 | I2CControllerDevice.STT0)
        self.assertTrue(i2c._waiting)

    def test_data_write_triggers_transfer(self):
        i2c, intc, bus = _make_i2c_on_bus()
        stub = StubI2CTarget()
        i2c.add_target(0x50, stub)
        # Start
        i2c.write(I2CControllerDevice.IIC0, 0xA0)
        i2c.write(I2CControllerDevice.IICC0, I2CControllerDevice.IICE0 | I2CControllerDevice.WTIM0
                  | I2CControllerDevice.ACKE0 | I2CControllerDevice.STT0)
        self._clear_iicif0(intc)
        # Write data byte
        i2c.write(I2CControllerDevice.IIC0, 0x42)
        self.assertTrue(self._iicif0_set(intc))

    def test_data_write_gets_ack_from_target(self):
        i2c, intc, bus = _make_i2c_on_bus()
        stub = StubI2CTarget()
        i2c.add_target(0x50, stub)
        i2c.write(I2CControllerDevice.IIC0, 0xA0)
        i2c.write(I2CControllerDevice.IICC0, I2CControllerDevice.IICE0 | I2CControllerDevice.WTIM0
                  | I2CControllerDevice.ACKE0 | I2CControllerDevice.STT0)
        self._clear_iicif0(intc)
        i2c.write(I2CControllerDevice.IIC0, 0x42)
        self.assertTrue(i2c.read(I2CControllerDevice.IICS0) & I2CControllerDevice.ACKD0)

    def test_stop_sets_std0(self):
        i2c, intc, bus = _make_i2c_on_bus()
        stub = StubI2CTarget()
        i2c.add_target(0x50, stub)
        i2c.write(I2CControllerDevice.IIC0, 0xA0)
        i2c.write(I2CControllerDevice.IICC0, I2CControllerDevice.IICE0 | I2CControllerDevice.WTIM0
                  | I2CControllerDevice.ACKE0 | I2CControllerDevice.STT0)
        # Stop
        i2c.write(I2CControllerDevice.IICC0, I2CControllerDevice.IICE0 | I2CControllerDevice.WTIM0
                  | I2CControllerDevice.ACKE0 | I2CControllerDevice.SPT0)
        self.assertTrue(i2c.read(I2CControllerDevice.IICS0) & I2CControllerDevice.STD0)

    def test_stop_clears_waiting(self):
        i2c, intc, bus = _make_i2c_on_bus()
        stub = StubI2CTarget()
        i2c.add_target(0x50, stub)
        i2c.write(I2CControllerDevice.IIC0, 0xA0)
        i2c.write(I2CControllerDevice.IICC0, I2CControllerDevice.IICE0 | I2CControllerDevice.WTIM0
                  | I2CControllerDevice.ACKE0 | I2CControllerDevice.STT0)
        i2c.write(I2CControllerDevice.IICC0, I2CControllerDevice.IICE0 | I2CControllerDevice.WTIM0
                  | I2CControllerDevice.ACKE0 | I2CControllerDevice.SPT0)
        self.assertFalse(i2c._waiting)


class I2CMasterReadTests(unittest.TestCase):
    """Test controller read: start -> address+R -> read bytes -> stop."""

    def _iicif0_set(self, intc):
        return bool(intc.read(InterruptControllerDevice.IF0H) & 0x40)

    def _clear_iicif0(self, intc):
        intc.write(InterruptControllerDevice.IF0H,
                   intc.read(InterruptControllerDevice.IF0H) & ~0x40)

    def test_read_byte_from_target(self):
        i2c, intc, bus = _make_i2c_on_bus()
        stub = StubI2CTarget(read_value=0x42)
        i2c.add_target(0x50, stub)
        # Start with read bit set (0xA1)
        i2c.write(I2CControllerDevice.IIC0, 0xA1)
        i2c.write(I2CControllerDevice.IICC0, I2CControllerDevice.IICE0 | I2CControllerDevice.WTIM0
                  | I2CControllerDevice.ACKE0 | I2CControllerDevice.STT0)
        self._clear_iicif0(intc)
        # Trigger read by writing dummy byte to IIC0
        i2c.write(I2CControllerDevice.IIC0, 0xFF)
        self.assertEqual(i2c.read(I2CControllerDevice.IIC0), 0x42)
        self.assertTrue(self._iicif0_set(intc))


class EepromWriteReadTests(unittest.TestCase):
    """Integration: write to EEPROM via I2C, read back."""

    def _iicif0_set(self, intc):
        return bool(intc.read(InterruptControllerDevice.IF0H) & 0x40)

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

        # Write: start(0xA0) -> address(0x10) -> data(0x42) -> stop
        self._start(i2c, intc, 0xA0)     # address 0x50 write
        self._write_byte(i2c, intc, 0x10) # EEPROM address
        self._write_byte(i2c, intc, 0x42) # data
        self._stop(i2c, intc)

        # Read: start(0xA0) -> address(0x10) -> stop ->
        #        start(0xA1) -> read -> stop
        self._start(i2c, intc, 0xA0)     # address 0x50 write
        self._write_byte(i2c, intc, 0x10) # EEPROM address
        self._stop(i2c, intc)
        self._start(i2c, intc, 0xA1)     # address 0x50 read
        val = self._read_byte(i2c, intc)
        self._stop(i2c, intc)

        self.assertEqual(val, 0x42)

    def test_write_multiple_bytes_read_back(self):
        i2c, intc, bus = _make_i2c_on_bus()
        eeprom_data = bytearray(512)
        i2c.add_target(0x50, M24C04(eeprom_data, page_offset=0))

        # Write 3 bytes starting at address 0x20
        self._start(i2c, intc, 0xA0)
        self._write_byte(i2c, intc, 0x20)  # EEPROM address
        self._write_byte(i2c, intc, 0xAA)
        self._write_byte(i2c, intc, 0xBB)
        self._write_byte(i2c, intc, 0xCC)
        self._stop(i2c, intc)

        # Read back: set address, then read 3 bytes
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

        # Write to lower page (address 0x50, offset 0x10)
        self._start(i2c, intc, 0xA0)
        self._write_byte(i2c, intc, 0x10)
        self._write_byte(i2c, intc, 0x11)
        self._stop(i2c, intc)

        # Write to upper page (address 0x51, offset 0x10 = physical 0x110)
        self._start(i2c, intc, 0xA2)  # 0x51 write
        self._write_byte(i2c, intc, 0x10)
        self._write_byte(i2c, intc, 0x22)
        self._stop(i2c, intc)

        self.assertEqual(eeprom_data[0x10], 0x11)
        self.assertEqual(eeprom_data[0x110], 0x22)

    def test_eeprom_backed_by_shared_data(self):
        i2c, intc, bus = _make_i2c_on_bus()
        eeprom_data = bytearray(512)
        eeprom_data[0x42] = 0x99  # pre-load
        i2c.add_target(0x50, M24C04(eeprom_data, page_offset=0))

        # Read from pre-loaded address
        self._start(i2c, intc, 0xA0)
        self._write_byte(i2c, intc, 0x42)
        self._stop(i2c, intc)
        self._start(i2c, intc, 0xA1)
        self.assertEqual(self._read_byte(i2c, intc), 0x99)
        self._stop(i2c, intc)

    def test_waiting_persists_across_bytes(self):
        """After start, _waiting should remain True across multiple
        byte writes.  Each IIC0 write triggers a transfer but the
        controller stays in wait state for the next byte."""
        i2c, intc, bus = _make_i2c_on_bus()
        stub = StubI2CTarget()
        i2c.add_target(0x50, stub)

        self._start(i2c, intc, 0xA0)
        self.assertTrue(i2c._waiting)

        self._write_byte(i2c, intc, 0x10)
        self.assertTrue(i2c._waiting)

        self._write_byte(i2c, intc, 0x42)
        self.assertTrue(i2c._waiting)

        self._stop(i2c, intc)
        self.assertFalse(i2c._waiting)
