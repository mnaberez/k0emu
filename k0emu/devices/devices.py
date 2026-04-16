from k0emu.devices.base import BaseDevice


class MemoryDevice(BaseDevice):
    """A generic read/write memory device (RAM or ROM).
    Covers a contiguous address range on the bus."""

    def __init__(self, name, *, size, fill=0x00, writable=True):
        super().__init__(name)
        self.size = size
        self._data = bytearray([fill]) * size
        self._writable = writable

    def read(self, offset):
        self._check_bounds(offset)
        return self._data[offset]

    def write(self, offset, value):
        self._check_bounds(offset)
        if self._writable:
            self._data[offset] = value

    def load(self, offset, data):
        """Write directly to backing store, bypassing the writable flag.
        Used for loading firmware images and test code."""
        self._check_bounds(offset)
        self._check_bounds(offset + len(data) - 1)
        self._data[offset:offset + len(data)] = data
