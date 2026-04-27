import unittest
from k0emu.mfsw import MFSWTransmitter, MFSWBusyError, VOL_DOWN, VOL_UP, UP, DOWN


class MFSWTransmitterTests(unittest.TestCase):

    def test_wire_idles_high(self):
        tx = MFSWTransmitter()
        self.assertTrue(tx.wire)

    def test_not_busy_initially(self):
        tx = MFSWTransmitter()
        self.assertFalse(tx.busy)

    def test_send_while_busy_raises(self):
        tx = MFSWTransmitter()
        tx.send(UP)
        with self.assertRaises(MFSWBusyError):
            tx.send(DOWN)

    def test_busy_during_transmission(self):
        tx = MFSWTransmitter()
        tx.send(UP)
        self.assertTrue(tx.busy)

    def test_wire_goes_low_on_send(self):
        tx = MFSWTransmitter()
        tx.send(UP)
        self.assertFalse(tx.wire)

    def test_wire_returns_to_idle_after_packet(self):
        tx = MFSWTransmitter()
        tx.send(UP)
        for _ in range(10_000_000):
            tx.tick()
        self.assertTrue(tx.wire)
        self.assertFalse(tx.busy)

    def test_start_bit_timing(self):
        tx = MFSWTransmitter()
        tx.send(UP)
        # Wire starts LOW (start bit active)
        self.assertFalse(tx.wire)
        # Tick through the start LOW period
        for _ in range(37709):
            tx.tick()
            self.assertFalse(tx.wire)
        tx.tick()  # 37710th tick: transition to HIGH
        self.assertTrue(tx.wire)

    def test_tick_with_cycles(self):
        tx = MFSWTransmitter()
        tx.send(UP)
        tx.tick(37710)
        self.assertTrue(tx.wire)  # past start LOW, now in start HIGH

    def test_packet_produces_correct_bits(self):
        """Capture all wire transitions and verify the bit pattern."""
        tx = MFSWTransmitter()
        rx = self._receive_packet(tx, UP)  # key code 0x0A, checksum 0xF5
        self.assertEqual(rx[0], 0x82)  # header 1
        self.assertEqual(rx[1], 0x17)  # header 2
        self.assertEqual(rx[2], 0x0A)  # key code (UP)
        self.assertEqual(rx[3], 0xF5)  # checksum (~0x0A)

    def test_vol_down_packet(self):
        tx = MFSWTransmitter()
        rx = self._receive_packet(tx, VOL_DOWN)
        self.assertEqual(rx, [0x82, 0x17, 0x00, 0xFF])

    def test_vol_up_packet(self):
        tx = MFSWTransmitter()
        rx = self._receive_packet(tx, VOL_UP)
        self.assertEqual(rx, [0x82, 0x17, 0x01, 0xFE])

    def test_down_packet(self):
        tx = MFSWTransmitter()
        rx = self._receive_packet(tx, DOWN)
        self.assertEqual(rx, [0x82, 0x17, 0x0B, 0xF4])

    def test_can_send_after_complete(self):
        tx = MFSWTransmitter()
        tx.send(UP)
        for _ in range(10_000_000):
            tx.tick()
        self.assertFalse(tx.busy)
        tx.send(DOWN)  # should not raise
        self.assertTrue(tx.busy)

    def test_tick_while_idle_is_harmless(self):
        tx = MFSWTransmitter()
        for _ in range(1000):
            tx.tick()
        self.assertTrue(tx.wire)
        self.assertFalse(tx.busy)

    def _receive_packet(self, tx, key_code):
        """Send a packet, capture edges, decode 4 bytes.
        Each edge entry is (ticks_at_this_level, new_level_after_transition).
        edges[0] = start LOW period, edges[1] = start HIGH period,
        edges[2:] = data bit pairs (LOW pulse, HIGH gap)."""
        tx.send(key_code)
        edges = []
        prev = tx.wire
        total = 0
        for _ in range(10_000_000):
            tx.tick()
            total += 1
            if tx.wire != prev:
                edges.append((total, prev))
                total = 0
                prev = tx.wire
            if not tx.busy:
                if total > 0:
                    edges.append((total, prev))
                break
        # edges: (duration, wire_level_during_that_period)
        # [0]=start LOW, [1]=start HIGH, [2:]=data bit pairs (LOW, HIGH)
        bit_edges = edges[2:]
        bits = []
        for i in range(0, 64, 2):
            period = bit_edges[i][0] + bit_edges[i + 1][0]
            bits.append(1 if period > 7549 else 0)
        rx_bytes = []
        for byte_idx in range(4):
            val = 0
            for bit_idx in range(8):
                val |= bits[byte_idx * 8 + bit_idx] << bit_idx
            rx_bytes.append(val)
        return rx_bytes
