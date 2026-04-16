from k0emu.devices import BaseDevice


class Bus(object):
    ADDRESS_SPACE_SIZE = 2**16  # 64K address space

    def __init__(self, processor):
        self.processor = processor
        self._unmapped = BaseDevice("unmapped")
        self._devices_by_address = [self._unmapped] * self.ADDRESS_SPACE_SIZE
        self._device_registers_by_address = [0] * self.ADDRESS_SPACE_SIZE
        self._all_devices = set()
        self._intc = None
        self.pending_interrupt = None

    def __getitem__(self, address):
        return self.read(address)

    def __setitem__(self, address, value):
        self.write(address, value)

    # device registration

    def add_device(self, device, *address_ranges):
        """Register a device for one or more address ranges.

        address_ranges: (start, end) tuples of bus addresses, inclusive.
                The device's registers are mapped sequentially across
                the given ranges, allowing a single device model to
                be mapped to non-contigous addresses in the memory map.
        """
        register = 0
        for start, end in address_ranges:
            if (start < 0) or (end >= self.ADDRESS_SPACE_SIZE) or (start > end):
                raise ValueError("address range 0x%04X-0x%04X out of bounds" %
                                 (start, end))

            for address in range(start, end + 1):
                existing_device = self._devices_by_address[address]
                if existing_device is not self._unmapped:
                    raise ValueError("address 0x%04X already mapped to %s" %
                                     (address, existing_device.name))

                self._devices_by_address[address] = device
                self._device_registers_by_address[address] = register
                register += 1

        if register != device.size:
            raise ValueError("%s: ranges cover %d bytes but device size is %d" %
                             (device.name, register, device.size))

        device.bus = self
        self._all_devices.add(device)

    def device(self, name):
        """Get a device by name."""
        for dev in self._all_devices:
            if dev.name == name:
                return dev
        raise KeyError("No device named %r" % name)

    def memory_map(self):
        """Return a list of (start, end, device) tuples describing the
        memory map.  Contiguous addresses mapped to the same device
        are collapsed into a single entry."""
        entries = []
        start = 0
        current = self._devices_by_address[0]
        for address in range(self.ADDRESS_SPACE_SIZE):
            device = self._devices_by_address[address]
            if device is not current:
                entries.append((start, address - 1, current))
                start = address
                current = device
        entries.append((start, self.ADDRESS_SPACE_SIZE - 1, current))
        return entries

    def reset(self):
        self.pending_interrupt = None
        for device in self._all_devices:
            device.reset()
        self.processor.reset()

    def tick(self, cycles):
        """Inform all devices that cycles have elapsed."""
        for device in self._all_devices:
            device.tick(cycles)

    # data operations

    def is_high_speed(self, address):
        return self._devices_by_address[address].high_speed

    def read(self, address):
        device = self._devices_by_address[address]
        register = self._device_registers_by_address[address]
        return device.read(register)

    def write(self, address, value):
        device = self._devices_by_address[address]
        register = self._device_registers_by_address[address]
        device.write(register, value)

    # interrupts

    def set_interrupt_controller(self, intc_device):
        self._intc = intc_device

    def interrupt(self, device, device_int):
        """Request an interrupt.  Called by peripheral devices."""
        self._intc.interrupt(device, device_int)

    def acknowledge_interrupt(self, pending):
        """Clear the IF flag for the given pending interrupt."""
        self._intc.acknowledge_interrupt(pending.source_index)
        self.pending_interrupt = None


class PendingInterrupt(object):
    """Interrupt waiting to be serviced.

    Created by the interrupt controller during tick() and placed
    on the bus for the processor to consume.
    """
    def __init__(self, source_index, high_priority, vector_address):
        self.source_index = source_index
        self.high_priority = high_priority
        self.vector_address = vector_address
