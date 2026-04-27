"""MFSW (Multi-Function Steering Wheel) transmitter.

Emulates the steering wheel controller that sends key presses to
the radio over a single-wire, active-low serial protocol.

The wire idles HIGH.  A packet consists of a start bit followed
by 32 data bits (4 bytes LSB-first), then a trailing pulse.

Timing is in CPU clock ticks at fx = 4.19 MHz.
"""

# Key codes (protocol values, transmitted LSB-first)
VOL_DOWN = 0x00
VOL_UP   = 0x01
UP       = 0x0A
DOWN     = 0x0B


class MFSWTransmitter(object):
    """Clocks out MFSW packets one tick at a time.

    Call send(key_code) to start a packet.  Call tick() on every
    CPU clock cycle.  Read the wire property for the current line state.

    The wire output is active-low (True=HIGH=idle, False=LOW=active).
    The caller is responsible for inverting it before driving P0.0.
    """

    # Packet header bytes
    HEADER_1 = 0x82
    HEADER_2 = 0x17

    # Timing in ticks at 4.19 MHz (midpoints of firmware valid ranges)
    PACKET_START_LOW_CYCLES  = 37710  # 9.0 ms  (valid: 6.0-12.0 ms)
    PACKET_START_HIGH_CYCLES = 18855  # 4.5 ms  (valid: 3.0-6.0 ms)
    BIT_START_LOW_CYCLES     =  2514  # 0.6 ms  (guess; firmware only validates total period)
    BIT_0_HIGH_CYCLES        =  2514  # 0.6 ms  (total period ~1.2 ms, < 1.8 ms threshold)
    BIT_1_HIGH_CYCLES        =  7123  # 1.7 ms  (total period ~2.3 ms, > 1.8 ms threshold)
    PACKET_STOP_LOW_CYCLES   =  1000  # ~0.24 ms (guess; just needs to trigger the Schmitt trigger)

    def __init__(self):
        self._waveform = []

    def send(self, key_code):
        """Build a new MFSW packet for the given key code and transmit it."""
        if self.busy:
            raise MFSWBusyError()

        packet = self._build_packet(key_code)
        self._waveform = self._build_waveform(packet)

    def tick(self, cycles=1):
        """Work through the current waveform.  The waveform is a FIFO buffer
        of (logic level, cycles remaining).  The number of cycles remaining in
        the first element of the waveform are decremented on tick().  When no
        more cycles are remaining, the element is popped off the waveform.  When
        all elements are popped off, the entire waveform for the full MFSW packet
        has been transmitted.  The system clock is 4.19 MHz, so 1 cycle = 0.239 us."""
        for _ in range(cycles):
            if not self._waveform:
                return

            step = self._waveform[0]
            step.cycles -= 1
            if step.cycles <= 0:
                self._waveform.pop(0)

    @property
    def wire(self):
        """Get the current state of the output line.  If no MFSW packet
        is being transmitted, the line idles high (True)."""
        if not self._waveform:
            return True  # idle HIGH

        return self._waveform[0].level

    @property
    def busy(self):
        """Returns true if an MFSW packet is currently being transmitted"""
        return bool(self._waveform)

    def _build_packet(self, key_code):
        """Build a complete MFSW packet for a key code."""
        checksum = (~key_code) & 0xFF
        return (self.HEADER_1, self.HEADER_2, key_code, checksum)

    def _build_waveform(self, packet):
        """Build a list of (logic level, cycles) pairs that will be used
        to transmit a packet.  A packet is a sequence of bytes that will
        be clocked out LSB-first (from bit 0 to bit 7).  Each entry
        means: set the wire to this level for this many cycles.
        The list alternates LOW/HIGH, starting with LOW (start bit).
        """
        wave = []

        # Packet start: LOW then HIGH
        wave.append(_WaveformStep(False, self.PACKET_START_LOW_CYCLES))
        wave.append(_WaveformStep(True, self.PACKET_START_HIGH_CYCLES))

        # Data bits (LSB-first): each is LOW then HIGH
        for byte_val in packet:
            for bit_pos in range(8):
                if (byte_val >> bit_pos) & 1: # bit is high
                    high_cycles = self.BIT_1_HIGH_CYCLES
                else:
                    high_cycles = self.BIT_0_HIGH_CYCLES

                wave.append(_WaveformStep(False, self.BIT_START_LOW_CYCLES))
                wave.append(_WaveformStep(True, high_cycles))

        # Stop: one more LOW so the firmware can measure the last data
        # bit's period (it needs 33 rising edges for 32 bits).
        wave.append(_WaveformStep(False, self.PACKET_STOP_LOW_CYCLES))

        return wave


class _WaveformStep(object):
    __slots__ = ('level', 'cycles')

    def __init__(self, level, cycles):
        self.level = level
        self.cycles = cycles


class MFSWBusyError(Exception):
    """ Attempt to send another MFSW byte while a MFSW packet is still
    being clocked out.  Callers should check the busy status before
    calling send() with another keycode. """
    pass
