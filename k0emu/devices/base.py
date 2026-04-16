class BaseDevice(object):
    def __init__(self, name):
        self.name = name
        self.size = 0
        self.ticks = 0

    def _check_bounds(self, offset):
        if offset < 0 or offset >= self.size:
            raise IndexError("%s: offset 0x%04X out of range (size=0x%04X)" %
                             (self.name, offset, self.size))

    def read(self, address):
        return 0

    def write(self, address, value):
        pass

    def reset(self):
        pass

    def tick(self, cycles):
        self.ticks += cycles
