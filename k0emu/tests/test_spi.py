import itertools
import unittest
from k0emu.spi import UPD16432B


def _send(upd, spi_bytes):
    """Send a complete SPI command (STB high, exchange bytes, STB low)."""
    upd.spi_begin()
    for b in spi_bytes:
        upd.spi_exchange(b)
    upd.spi_end()


class UPD16432B_InitTests(unittest.TestCase):

    def test_display_ram_initialized_to_zeros(self):
        upd = UPD16432B()
        self.assertEqual(upd.display_ram, bytearray(0x19))

    def test_pictograph_ram_initialized_to_zeros(self):
        upd = UPD16432B()
        self.assertEqual(upd.pictograph_ram, bytearray(0x08))

    def test_chargen_ram_initialized_to_zeros(self):
        upd = UPD16432B()
        self.assertEqual(upd.chargen_ram, bytearray(0x70))

    def test_led_ram_initialized_to_zeros(self):
        upd = UPD16432B()
        self.assertEqual(upd.led_ram, bytearray(0x01))

    def test_key_data_initialized_to_zeros(self):
        upd = UPD16432B()
        self.assertEqual(upd.key_data, bytearray(4))

    def test_current_ram_initially_none(self):
        upd = UPD16432B()
        self.assertIsNone(upd._current_ram)

    def test_address_initially_zero(self):
        upd = UPD16432B()
        self.assertEqual(upd._address, 0)

    def test_increment_initially_false(self):
        upd = UPD16432B()
        self.assertFalse(upd._increment)

    def test_empty_spi_command_does_not_raise(self):
        upd = UPD16432B()
        upd.spi_begin()
        upd.spi_end()


class UPD16432B_DataSettingTests(unittest.TestCase):

    def test_sets_display_ram_area_increment_off(self):
        upd = UPD16432B()
        cmd  = 0b01000000  # data setting command
        cmd |= 0b00000000  # display ram
        cmd |= 0b00001000  # increment off
        _send(upd, [cmd])
        self.assertIs(upd._current_ram, upd.display_ram)
        self.assertFalse(upd._increment)

    def test_sets_display_ram_area_increment_on(self):
        upd = UPD16432B()
        cmd  = 0b01000000  # data setting command
        cmd |= 0b00000000  # display ram
        cmd |= 0b00000000  # increment on
        _send(upd, [cmd])
        self.assertIs(upd._current_ram, upd.display_ram)
        self.assertTrue(upd._increment)

    def test_sets_pictograph_ram_area_increment_off(self):
        upd = UPD16432B()
        cmd  = 0b01000000  # data setting command
        cmd |= 0b00000001  # pictograph ram
        cmd |= 0b00001000  # increment off
        _send(upd, [cmd])
        self.assertIs(upd._current_ram, upd.pictograph_ram)
        self.assertFalse(upd._increment)

    def test_sets_chargen_ram_area_increment_on(self):
        upd = UPD16432B()
        cmd  = 0b01000000  # data setting command
        cmd |= 0b00000010  # chargen ram
        cmd |= 0b00000000  # increment on
        _send(upd, [cmd])
        self.assertIs(upd._current_ram, upd.chargen_ram)
        self.assertTrue(upd._increment)

    def test_sets_chargen_ram_area_ignores_increment_off(self):
        upd = UPD16432B()
        cmd  = 0b01000000  # data setting command
        cmd |= 0b00000010  # chargen ram
        cmd |= 0b00001000  # increment off (should be ignored)
        _send(upd, [cmd])
        self.assertIs(upd._current_ram, upd.chargen_ram)
        self.assertTrue(upd._increment)

    def test_sets_led_ram_area_increment_on(self):
        upd = UPD16432B()
        cmd  = 0b01000000  # data setting command
        cmd |= 0b00000011  # led output latch
        cmd |= 0b00000000  # increment on
        _send(upd, [cmd])
        self.assertIs(upd._current_ram, upd.led_ram)
        self.assertTrue(upd._increment)

    def test_sets_led_ram_area_ignores_increment_off(self):
        upd = UPD16432B()
        cmd  = 0b01000000  # data setting command
        cmd |= 0b00000011  # led output latch
        cmd |= 0b00001000  # increment off (should be ignored)
        _send(upd, [cmd])
        self.assertIs(upd._current_ram, upd.led_ram)
        self.assertTrue(upd._increment)

    def test_unrecognized_ram_area_sets_none(self):
        upd = UPD16432B()
        cmd  = 0b01000000  # data setting command
        cmd |= 0b00000111  # not a valid ram area
        _send(upd, [cmd])
        self.assertIsNone(upd._current_ram)
        self.assertEqual(upd._address, 0)

    def test_unrecognized_ram_area_ignores_increment_off(self):
        upd = UPD16432B()
        cmd  = 0b01000000  # data setting command
        cmd |= 0b00000111  # not a valid ram area
        cmd |= 0b00001000  # increment off (should be ignored)
        _send(upd, [cmd])
        self.assertIsNone(upd._current_ram)
        self.assertEqual(upd._address, 0)


class UPD16432B_AddressSettingTests(unittest.TestCase):

    def test_no_current_ram_sets_zero(self):
        upd = UPD16432B()
        self.assertIsNone(upd._current_ram)
        cmd  = 0b10000000  # address setting command
        cmd |= 0b00000011  # address 0x03
        _send(upd, [cmd])
        self.assertEqual(upd._address, 0)

    def test_sets_addresses_for_each_ram_area(self):
        tuples = (
            (0b00000000, 0,       0),  # display min
            (0b00000000, 0x18, 0x18),  # display max
            (0b00000000, 0x19,    0),  # display wraps

            (0b00000001,    0,    0),  # pictograph min
            (0b00000001, 0x07, 0x07),  # pictograph max
            (0b00000001, 0x08,    0),  # pictograph wraps

            (0b00000010,    0,    0),  # chargen min
            (0b00000010, 0x0f, 0x69),  # chargen max
            (0b00000010, 0x10,    0),  # chargen wraps

            (0b00000011,    0,    0),  # led min
            (0b00000011,    0,    0),  # led max
            (0b00000011,    1,    0),  # led wraps
        )
        for ram_select_bits, address, expected_address in tuples:
            upd = UPD16432B()
            # data setting command
            _send(upd, [0b01000000 | ram_select_bits])
            # address setting command
            _send(upd, [0b10000000 | address])
            self.assertEqual(upd._address, expected_address)


class UPD16432B_WritingDataTests(unittest.TestCase):

    def test_no_ram_area_ignores_data(self):
        upd = UPD16432B()
        old_display = bytes(upd.display_ram)
        old_picto = bytes(upd.pictograph_ram)
        old_chargen = bytes(upd.chargen_ram)
        old_led = bytes(upd.led_ram)
        # address setting command followed by data that should be ignored
        cmd = 0b10000000 | 0  # address 0
        data = list(range(1, 8))
        _send(upd, [cmd] + data)
        self.assertEqual(bytes(upd.display_ram), old_display)
        self.assertEqual(bytes(upd.pictograph_ram), old_picto)
        self.assertEqual(bytes(upd.chargen_ram), old_chargen)
        self.assertEqual(bytes(upd.led_ram), old_led)

    def test_display_ram_increment_on_writes_data(self):
        upd = UPD16432B()
        # data setting command
        cmd  = 0b01000000  # data setting command
        cmd |= 0b00000000  # display ram
        cmd |= 0b00000000  # increment on
        _send(upd, [cmd])
        # address setting command followed by 25 bytes of display data
        cmd = 0b10000000 | 0  # address 0
        data = list(range(1, 26))
        _send(upd, [cmd] + data)
        self.assertTrue(upd._increment)
        self.assertEqual(upd._address, 0)  # wrapped around
        self.assertEqual(upd.display_ram, bytearray(data))

    def test_display_ram_increment_off_rewrites_same_address(self):
        upd = UPD16432B()
        # data setting command
        cmd  = 0b01000000  # data setting command
        cmd |= 0b00000000  # display ram
        cmd |= 0b00001000  # increment off
        _send(upd, [cmd])
        # address setting command followed by data written to address 5 only
        cmd = 0b10000000 | 5  # address 5
        _send(upd, [cmd, 1, 2, 3, 4, 5, 6, 7])
        self.assertFalse(upd._increment)
        self.assertEqual(upd._address, 5)
        self.assertEqual(upd.display_ram[5], 7)

    def test_pictograph_ram_increment_on_writes_data(self):
        upd = UPD16432B()
        # data setting command
        cmd  = 0b01000000  # data setting command
        cmd |= 0b00000001  # pictograph ram
        cmd |= 0b00000000  # increment on
        _send(upd, [cmd])
        # address setting command followed by 8 bytes of pictograph data
        cmd = 0b10000000 | 0  # address 0
        data = list(range(1, 9))
        _send(upd, [cmd] + data)
        self.assertTrue(upd._increment)
        self.assertEqual(upd._address, 0)  # wrapped around
        self.assertEqual(upd.pictograph_ram, bytearray(data))

    def test_pictograph_ram_increment_off_rewrites_same_address(self):
        upd = UPD16432B()
        # data setting command
        cmd  = 0b01000000  # data setting command
        cmd |= 0b00000001  # pictograph ram
        cmd |= 0b00001000  # increment off
        _send(upd, [cmd])
        # address setting command followed by data written to address 5 only
        cmd = 0b10000000 | 5  # address 5
        _send(upd, [cmd, 1, 2, 3, 4, 5, 6, 7])
        self.assertFalse(upd._increment)
        self.assertEqual(upd._address, 5)
        self.assertEqual(upd.pictograph_ram[5], 7)

    def test_chargen_ram_increment_on_writes_data(self):
        upd = UPD16432B()
        # data setting command
        cmd  = 0b01000000  # data setting command
        cmd |= 0b00000010  # chargen ram
        cmd |= 0b00000000  # increment on
        _send(upd, [cmd])
        # write 16 characters (7 bytes each) in groups of 2
        data = []
        for charnum in range(16):
            offset = charnum * 7
            data.append(bytearray(range(offset, offset + 7)))
        for charnum in range(0, 16, 2):
            cmd = 0b10000000 | charnum  # address = character number
            _send(upd, bytearray([cmd]) + data[charnum] + data[charnum + 1])
        self.assertTrue(upd._increment)
        self.assertEqual(upd._address, 0)  # wrapped around
        flattened = bytearray(itertools.chain.from_iterable(data))
        self.assertEqual(upd.chargen_ram, flattened)

    def test_chargen_ram_ignores_increment_off_writes_data(self):
        upd = UPD16432B()
        # data setting command
        cmd  = 0b01000000  # data setting command
        cmd |= 0b00000010  # chargen ram
        cmd |= 0b00001000  # increment off (ignored)
        _send(upd, [cmd])
        # write 16 characters (7 bytes each) in groups of 2
        data = []
        for charnum in range(16):
            offset = charnum * 7
            data.append(bytearray(range(offset, offset + 7)))
        for charnum in range(0, 16, 2):
            cmd = 0b10000000 | charnum
            _send(upd, bytearray([cmd]) + data[charnum] + data[charnum + 1])
        self.assertTrue(upd._increment)  # should ignore increment off
        self.assertEqual(upd._address, 0)  # wrapped around
        flattened = bytearray(itertools.chain.from_iterable(data))
        self.assertEqual(upd.chargen_ram, flattened)

    def test_led_ram_increment_on_writes_data(self):
        upd = UPD16432B()
        # data setting command
        cmd  = 0b01000000  # data setting command
        cmd |= 0b00000011  # led output latch
        cmd |= 0b00000000  # increment on
        _send(upd, [cmd])
        # address setting command followed by led data
        cmd = 0b10000000 | 0  # address 0
        _send(upd, [cmd, 42])
        self.assertTrue(upd._increment)
        self.assertEqual(upd._address, 0)  # wrapped around
        self.assertEqual(upd.led_ram, bytearray([42]))

    def test_led_ram_ignores_increment_off_writes_data(self):
        upd = UPD16432B()
        # data setting command
        cmd  = 0b01000000  # data setting command
        cmd |= 0b00000011  # led output latch
        cmd |= 0b00001000  # increment off (ignored)
        _send(upd, [cmd])
        # address setting command followed by led data
        cmd = 0b10000000 | 0  # address 0
        _send(upd, [cmd, 42])
        self.assertTrue(upd._increment)  # should ignore increment off
        self.assertEqual(upd._address, 0)  # wrapped around
        self.assertEqual(upd.led_ram, bytearray([42]))


class UPD16432B_KeyDataTests(unittest.TestCase):

    def test_key_read_command_returns_key_data(self):
        upd = UPD16432B()
        upd.key_data[0] = 0x11
        upd.key_data[1] = 0x22
        upd.key_data[2] = 0x33
        upd.key_data[3] = 0x44
        cmd = 0x44  # key data read command
        upd.spi_begin()
        rx0 = upd.spi_exchange(cmd)
        rx1 = upd.spi_exchange(0x00)
        rx2 = upd.spi_exchange(0x00)
        rx3 = upd.spi_exchange(0x00)
        upd.spi_end()
        self.assertEqual(rx0, 0x11)
        self.assertEqual(rx1, 0x22)
        self.assertEqual(rx2, 0x33)
        self.assertEqual(rx3, 0x44)

    def test_key_read_does_not_modify_ram(self):
        upd = UPD16432B()
        old_display = bytes(upd.display_ram)
        cmd = 0x44  # key data read command
        _send(upd, [cmd, 0x00, 0x00, 0x00])
        self.assertEqual(bytes(upd.display_ram), old_display)


class UPD16432B_DirtyTests(unittest.TestCase):

    def test_not_dirty_initially(self):
        upd = UPD16432B()
        self.assertFalse(upd.dirty)

    def test_writing_new_value_sets_dirty(self):
        upd = UPD16432B()
        _send(upd, [0b01000000])  # data setting: display ram
        _send(upd, [0b10000000, 0x42])  # address 0, write 0x42
        self.assertTrue(upd.dirty)

    def test_writing_same_value_does_not_set_dirty(self):
        upd = UPD16432B()
        _send(upd, [0b01000000])  # data setting: display ram
        _send(upd, [0b10000000, 0x00])  # address 0, write 0x00 (same as init)
        self.assertFalse(upd.dirty)


class UPD16432B_DisplayPixelsTests(unittest.TestCase):

    def test_returns_correct_length(self):
        upd = UPD16432B()
        pixels = upd.get_display_pixels()
        self.assertEqual(len(pixels), 7 * len(upd.display_ram))

    def test_all_zeros_uses_chargen_char_0(self):
        upd = UPD16432B()
        pixels = upd.get_display_pixels()
        self.assertEqual(pixels[:7], bytearray(7))

    def test_charset_character(self):
        upd = UPD16432B()
        upd.display_ram[0] = 0x41  # 'A'
        pixels = upd.get_display_pixels()
        expected = bytearray([0x0E, 0x31, 0x51, 0x7F, 0x91, 0xB1, 0xD1])
        self.assertEqual(pixels[:7], expected)

    def test_chargen_character(self):
        upd = UPD16432B()
        upd.display_ram[0] = 0x05
        pattern = bytearray([0x01, 0x23, 0x45, 0x67, 0x89, 0xAB, 0xCD])
        upd.chargen_ram[0x05 * 7:0x05 * 7 + 7] = pattern
        pixels = upd.get_display_pixels()
        self.assertEqual(pixels[:7], pattern)

    def test_boundary_char_0x0f_uses_chargen(self):
        upd = UPD16432B()
        upd.display_ram[0] = 0x0F
        pattern = bytearray([0x10, 0x20, 0x30, 0x40, 0x50, 0x60, 0x70])
        upd.chargen_ram[0x0F * 7:0x0F * 7 + 7] = pattern
        pixels = upd.get_display_pixels()
        self.assertEqual(pixels[:7], pattern)

    def test_boundary_char_0x10_uses_charset(self):
        upd = UPD16432B()
        upd.display_ram[0] = 0x10
        pixels = upd.get_display_pixels()
        expected = bytearray([0x00, 0x20, 0x40, 0x60, 0x80, 0xA0, 0xC0])
        self.assertEqual(pixels[:7], expected)

    def test_multiple_positions(self):
        upd = UPD16432B()
        upd.display_ram[0] = 0x41  # 'A'
        upd.display_ram[1] = 0x42  # 'B'
        pixels = upd.get_display_pixels()
        expected_a = bytearray([0x0E, 0x31, 0x51, 0x7F, 0x91, 0xB1, 0xD1])
        expected_b = bytearray([0x1E, 0x31, 0x51, 0x7E, 0x91, 0xB1, 0xDE])
        self.assertEqual(pixels[0:7], expected_a)
        self.assertEqual(pixels[7:14], expected_b)

    def test_display_ram_write_updates_pixels(self):
        upd = UPD16432B()
        upd.display_ram[0] = 0x41
        upd.get_display_pixels()
        _send(upd, [0b01000000])  # data setting: display ram
        _send(upd, [0b10000000, 0x42])  # address 0, write 'B'
        pixels = upd.get_display_pixels()
        expected_b = bytearray([0x1E, 0x31, 0x51, 0x7E, 0x91, 0xB1, 0xDE])
        self.assertEqual(pixels[:7], expected_b)

    def test_chargen_ram_write_updates_pixels(self):
        upd = UPD16432B()
        upd.display_ram[0] = 0x05
        upd.get_display_pixels()
        pattern = bytearray([0x01, 0x23, 0x45, 0x67, 0x89, 0xAB, 0xCD])
        _send(upd, [0b01000010])  # data setting: chargen ram
        _send(upd, [0b10000101] + list(pattern))  # address 5, write pattern
        pixels = upd.get_display_pixels()
        self.assertEqual(pixels[:7], pattern)
