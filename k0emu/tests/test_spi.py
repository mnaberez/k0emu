import itertools
import unittest
from k0emu.spi import UPD16432B


def _send(upd, spi_bytes):
    """Send a complete SPI command (STB high, exchange bytes, STB low)."""
    upd.spi_select(True)
    for b in spi_bytes:
        upd.spi_exchange(b)
    upd.spi_select(False)


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
        upd.spi_select(True)
        upd.spi_select(False)


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
    """Key scan read: command byte 0x4C (or any byte matching (cmd & 0xC7) == 0x44),
    followed by 4 data bytes.  The command byte exchange returns 0x00; subsequent
    data byte exchanges return key_data[0] through key_data[3].

    The firmware sends [0x4C, 0xFF, 0xFF, 0xFF, 0xFF] in a single STB cycle.
    """

    def test_command_byte_returns_zero(self):
        upd = UPD16432B()
        upd.key_data[:] = [0x11, 0x22, 0x33, 0x44]
        upd.spi_select(True)
        rx = upd.spi_exchange(0x4C)
        upd.spi_select(False)
        self.assertEqual(rx, 0x00)

    def test_data_bytes_return_key_data(self):
        upd = UPD16432B()
        upd.key_data[:] = [0x11, 0x22, 0x33, 0x44]
        upd.spi_select(True)
        upd.spi_exchange(0x4C)         # command byte
        rx0 = upd.spi_exchange(0xFF)   # data byte 1
        rx1 = upd.spi_exchange(0xFF)   # data byte 2
        rx2 = upd.spi_exchange(0xFF)   # data byte 3
        rx3 = upd.spi_exchange(0xFF)   # data byte 4
        upd.spi_select(False)
        self.assertEqual(rx0, 0x11)
        self.assertEqual(rx1, 0x22)
        self.assertEqual(rx2, 0x33)
        self.assertEqual(rx3, 0x44)

    def test_full_firmware_transaction(self):
        """Firmware sends [0x4C, 0xFF, 0xFF, 0xFF, 0xFF] in one STB cycle."""
        upd = UPD16432B()
        upd.key_data[:] = [0xAA, 0xBB, 0xCC, 0xDD]
        upd.spi_select(True)
        rx_cmd  = upd.spi_exchange(0x4C)
        rx_dat0 = upd.spi_exchange(0xFF)
        rx_dat1 = upd.spi_exchange(0xFF)
        rx_dat2 = upd.spi_exchange(0xFF)
        rx_dat3 = upd.spi_exchange(0xFF)
        upd.spi_select(False)
        self.assertEqual(rx_cmd, 0x00)
        self.assertEqual(rx_dat0, 0xAA)
        self.assertEqual(rx_dat1, 0xBB)
        self.assertEqual(rx_dat2, 0xCC)
        self.assertEqual(rx_dat3, 0xDD)

    def test_key_data_wraps(self):
        upd = UPD16432B()
        upd.key_data[:] = [0x11, 0x22, 0x33, 0x44]
        upd.spi_select(True)
        upd.spi_exchange(0x4C)
        for _ in range(4):
            upd.spi_exchange(0xFF)
        rx_wrap = upd.spi_exchange(0xFF)  # 5th data byte wraps to key_data[0]
        upd.spi_select(False)
        self.assertEqual(rx_wrap, 0x11)

    def test_all_key_read_command_variants(self):
        """Any command byte where (cmd & 0xC7) == 0x44 is a key read.
        Bits 3-5 select key matrix rows but don't affect which bytes come back."""
        upd = UPD16432B()
        upd.key_data[:] = [0xDE, 0xAD, 0xBE, 0xEF]
        for cmd in range(256):
            if (cmd & 0xC7) == 0x44:
                upd.spi_select(True)
                upd.spi_exchange(cmd)
                rx = upd.spi_exchange(0xFF)
                upd.spi_select(False)
                self.assertEqual(rx, 0xDE,
                    "cmd 0x%02X: expected 0xDE, got 0x%02X" % (cmd, rx))

    def test_non_key_command_returns_zero(self):
        upd = UPD16432B()
        upd.key_data[:] = [0xFF, 0xFF, 0xFF, 0xFF]
        upd.spi_select(True)
        upd.spi_exchange(0x40)  # data setting, not key read
        rx = upd.spi_exchange(0xFF)
        upd.spi_select(False)
        self.assertEqual(rx, 0x00)

    def test_key_read_does_not_modify_any_ram(self):
        upd = UPD16432B()
        old_display = bytes(upd.display_ram)
        old_picto = bytes(upd.pictograph_ram)
        old_chargen = bytes(upd.chargen_ram)
        old_led = bytes(upd.led_ram)
        _send(upd, [0x4C, 0xFF, 0xFF, 0xFF, 0xFF])
        self.assertEqual(bytes(upd.display_ram), old_display)
        self.assertEqual(bytes(upd.pictograph_ram), old_picto)
        self.assertEqual(bytes(upd.chargen_ram), old_chargen)
        self.assertEqual(bytes(upd.led_ram), old_led)

    def test_back_to_back_key_reads(self):
        """Firmware sends two identical key read transactions per scan cycle."""
        upd = UPD16432B()
        upd.key_data[:] = [0x01, 0x02, 0x03, 0x04]
        for _ in range(2):
            upd.spi_select(True)
            upd.spi_exchange(0x4C)
            rx = [upd.spi_exchange(0xFF) for _ in range(4)]
            upd.spi_select(False)
            self.assertEqual(rx, [0x01, 0x02, 0x03, 0x04])

    def test_key_read_after_display_write(self):
        upd = UPD16432B()
        _send(upd, [0b01000000])  # select display ram
        _send(upd, [0b10000000, 0x41, 0x42, 0x43])  # write 'ABC'
        upd.key_data[:] = [0xDE, 0xAD, 0xBE, 0xEF]
        upd.spi_select(True)
        rx_cmd = upd.spi_exchange(0x4C)
        rx = [upd.spi_exchange(0xFF) for _ in range(4)]
        upd.spi_select(False)
        self.assertEqual(rx_cmd, 0x00)
        self.assertEqual(rx, [0xDE, 0xAD, 0xBE, 0xEF])

    def test_key_data_changes_between_reads(self):
        upd = UPD16432B()
        upd.key_data[:] = [0x00, 0x00, 0x00, 0x00]
        upd.spi_select(True)
        upd.spi_exchange(0x4C)
        rx0 = upd.spi_exchange(0xFF)
        upd.spi_select(False)
        self.assertEqual(rx0, 0x00)
        upd.key_data[0] = 0x80
        upd.spi_select(True)
        upd.spi_exchange(0x4C)
        rx0 = upd.spi_exchange(0xFF)
        upd.spi_select(False)
        self.assertEqual(rx0, 0x80)


class UPD16432B_SelectTests(unittest.TestCase):

    def test_select_resets_receive_state(self):
        upd = UPD16432B()
        upd._exc_func = None  # corrupt the state
        upd.spi_select(True)
        self.assertEqual(upd._exc_func, upd._exc_command)

    def test_deselect_after_write(self):
        upd = UPD16432B()
        _send(upd, [0b01000000])  # select display ram
        upd.spi_select(True)
        upd.spi_exchange(0b10000000)  # address 0
        upd.spi_exchange(0x42)  # write 'B'
        upd.spi_select(False)
        self.assertEqual(upd.display_ram[0], 0x42)

    def test_same_state_ignored(self):
        upd = UPD16432B()
        upd.spi_select(True)
        upd._exc_func = None
        upd.spi_select(True)
        self.assertIsNone(upd._exc_func)

    def test_exchange_while_deselected_ignored(self):
        upd = UPD16432B()
        _send(upd, [0b01000000])  # select display ram
        # deselected: write should be ignored
        upd.spi_exchange(0b10000000)  # address 0
        upd.spi_exchange(0x42)  # write 'B'
        self.assertEqual(upd.display_ram[0], 0x00)

    def test_exchange_while_deselected_returns_zero(self):
        upd = UPD16432B()
        rx = upd.spi_exchange(0xFF)
        self.assertEqual(rx, 0x00)

    def test_key_read_via_select(self):
        upd = UPD16432B()
        upd.key_data[:] = [0xAA, 0xBB, 0xCC, 0xDD]
        upd.spi_select(True)
        upd.spi_exchange(0x4C)
        rx = upd.spi_exchange(0xFF)
        upd.spi_select(False)
        self.assertEqual(rx, 0xAA)


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
