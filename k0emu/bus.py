from k0emu.devices import BaseDevice


class Bus(object):
    def __init__(self, processor):
        self.processor = processor
        self._unmapped = BaseDevice("unmapped")
        self._devices_by_address = [self._unmapped] * 0x10000
        self._dev_bases_by_address = [0] * 0x10000
        self._all_devices = set()

    def __getitem__(self, address):
        return self.read(address)

    def __setitem__(self, address, value):
        self.write(address, value)

    # device registration

    def add_device(self, start, end, device):
        """Register a device for an address range (inclusive).
        The device sees local addresses 0 through (end - start)."""
        for address in range(start, end + 1):
            self._devices_by_address[address] = device
            self._dev_bases_by_address[address] = start
        self._all_devices.add(device)

    def device(self, name):
        """Get a device by name."""
        for dev in self._all_devices:
            if dev.name == name:
                return dev
        raise KeyError("No device named %r" % name)

    # bus operations

    def reset(self):
        for device in self._all_devices:
            device.reset()
        self.processor.reset()

    def tick(self, cycles):
        """Inform all devices that cycles have elapsed."""
        for device in self._all_devices:
            device.tick(cycles)

    def read(self, address):
        device = self._devices_by_address[address]
        local_address = address - self._dev_bases_by_address[address]
        return device.read(local_address)

    def write(self, address, value):
        device = self._devices_by_address[address]
        local_address = address - self._dev_bases_by_address[address]
        device.write(local_address, value)
