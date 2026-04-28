class BaseSPITarget(object):
    """Base class for SPI target devices."""

    def spi_select(self, selected):
        """Chip select.  When true, the device is selected.  The
        device detects asserted on the rising edge (False->True)
        and deasserted on the falling edge (True->False)."""
        raise NotImplementedError

    def spi_exchange(self, rx_byte):
        """Exchange one SPI byte.  Returns the byte to send back."""
        raise NotImplementedError
