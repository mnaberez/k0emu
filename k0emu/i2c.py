class BaseI2CTarget(object):
    """Base class for I2C target devices."""

    ACK = True
    NACK = False

    def i2c_start(self, is_read):
        """Controller has issued a start condition.
        is_read: True if reading, False if writing.
        No return value."""
        raise NotImplementedError

    def i2c_stop(self):
        """Controller has issued a stop condition.
        No return value."""
        raise NotImplementedError

    def i2c_read(self):
        """Controller is reading.
        Return the next byte (0x00-0xFF)."""
        raise NotImplementedError

    def i2c_write(self, data):
        """Controller is writing.
        data: byte received from controller (0x00-0xFF).
        Return ACK or NACK."""
        raise NotImplementedError


class StubI2CTarget(BaseI2CTarget):
    """Stub I2C target that ACKs everything and returns a configurable value.
    Used for peripherals we don't fully emulate yet."""

    def __init__(self, read_value=0xFF):
        self._read_value = read_value

    def i2c_start(self, is_read):
        pass

    def i2c_stop(self):
        pass

    def i2c_read(self):
        return self._read_value

    def i2c_write(self, data):
        return self.ACK
