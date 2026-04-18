from k0emu.devices import (MemoryDevice, RegisterFileDevice,
                           ProcessorStatusDevice, PortDevice,
                           ADCDevice, I2CDevice, I2CTargetStub,
                           EepromDevice, CSI30Device, UPD16432BDevice,
                           InterruptControllerDevice,
                           WatchdogDevice, WatchTimerDevice)
from k0emu.processor import Processor


def make_processor():
    """Build a Processor with the default bus and memory layout
    for the uPD78F0831Y."""
    proc = Processor()

    rom = MemoryDevice("rom", size=0xF000, fill=0xFF, writable=False)
    proc.bus.add_device(rom, (0x0000, 0xEFFF))

    expansion_ram = MemoryDevice("expansion_ram", size=0x0800)
    proc.bus.add_device(expansion_ram, (0xF000, 0xF7FF))

    reserved = MemoryDevice("reserved", size=0x0300, fill=0x08, writable=False)
    proc.bus.add_device(reserved, (0xF800, 0xFAFF))

    high_speed_ram = MemoryDevice("high_speed_ram", size=0x03E0, high_speed=True)
    proc.bus.add_device(high_speed_ram, (0xFB00, 0xFEDF))

    register_file = RegisterFileDevice("register_file", high_speed=True)
    proc.bus.add_device(register_file, (0xFEE0, 0xFEFF))

    ports = PortDevice("ports")
    proc.bus.add_device(ports, (0xFF00, 0xFF09))


    processor_status = ProcessorStatusDevice("processor_status")
    proc.bus.add_device(processor_status, (0xFF1C, 0xFF1E))

    intc = InterruptControllerDevice("intc")
    proc.bus.add_device(intc, (0xFFE0, 0xFFEB))
    proc.bus.set_interrupt_controller(intc)

    i2c = I2CDevice("i2c")
    proc.bus.add_device(i2c, (0xFF1F, 0xFF1F), (0xFFA8, 0xFFAA))
    intc.connect(i2c, i2c.INT_TRANSFER, intc.INTIIC0)
    eeprom_data = bytearray(512)
    i2c.add_target(0x50, EepromDevice(eeprom_data, page_offset=0))
    i2c.add_target(0x51, EepromDevice(eeprom_data, page_offset=256))
    i2c.add_target(0x1C, I2CTargetStub())  # SAA7705H audio DSP
    i2c.add_target(0x22, I2CTargetStub())  # TDA7476 audio

    upd = UPD16432BDevice()
    csi30 = CSI30Device("csi30")
    csi30.upd = upd
    proc.bus.add_device(csi30, (0xFF1A, 0xFF1A), (0xFFB0, 0xFFB0))
    intc.connect(csi30, csi30.INT_TRANSFER, intc.INTCSI30)

    adc = ADCDevice("adc", result=0xF0)
    proc.bus.add_device(adc, (0xFF17, 0xFF17), (0xFF80, 0xFF81))
    intc.connect(adc, adc.INT_COMPLETE, intc.INTAD00)

    watch_timer = WatchTimerDevice("watch_timer")
    proc.bus.add_device(watch_timer, (0xFF41, 0xFF41))
    intc.connect(watch_timer, watch_timer.INT_PRESCALER, intc.INTWTNI0)
    intc.connect(watch_timer, watch_timer.INT_WATCH, intc.INTWTN0)

    watchdog = WatchdogDevice("watchdog")
    proc.bus.add_device(watchdog, (0xFF42, 0xFF42), (0xFFF9, 0xFFF9))
    intc.connect(watchdog, watchdog.INT_OVERFLOW, intc.INTWDT)

    return proc


def populate_eeprom(proc):
    """Populate the EEPROM with defaults from the firmware ROM.

    The firmware copies two blocks from ROM into EEPROM mirror RAM
    at startup.  We pre-populate the EEPROM with the same data and
    valid checksums so integrity checks pass.

    Must be called after loading firmware into ROM.
    """
    rom = proc.bus.device("rom")
    i2c = proc.bus.device("i2c")
    eeprom_data = i2c._targets[0x50]._data

    # Block 1: ROM 0x0080 (0x4F bytes) -> EEPROM 0x0010
    for i in range(0x4F):
        eeprom_data[0x0010 + i] = rom.read(0x0080 + i)

    # Block 2: ROM 0x00CF (0x66 bytes) -> EEPROM 0x0063
    for i in range(0x66):
        eeprom_data[0x0063 + i] = rom.read(0x00CF + i)

    # Checksum 1: EEPROM 0x0010 to 0x0060, stored at 0x0061-0x0062
    csum1 = _eeprom_checksum(eeprom_data, 0x0010, 0x0061 - 0x0010)
    eeprom_data[0x0061] = csum1 & 0xFF
    eeprom_data[0x0062] = (csum1 >> 8) & 0xFF

    # Checksum 2: EEPROM 0x0063 to 0x00C8, stored at 0x00C9-0x00CA
    csum2 = _eeprom_checksum(eeprom_data, 0x0063, 0x00C9 - 0x0063)
    eeprom_data[0x00C9] = csum2 & 0xFF
    eeprom_data[0x00CA] = (csum2 >> 8) & 0xFF


def _eeprom_checksum(data, start, length):
    """Compute the EEPROM checksum the same way the firmware does.
    Initial X=0x55, A=0x00.  For each byte: add to X, carry into A."""
    x = 0x55
    a = 0x00
    for i in range(length):
        sum_x = x + data[start + i]
        carry = 1 if sum_x > 0xFF else 0
        x = sum_x & 0xFF
        a = (a + carry) & 0xFF
    return (a << 8) | x


def configure_interrupts(proc):
    """Pre-configure interrupt priorities to match firmware expectations.
    Must be called after bus.reset().

    The firmware sets INTWTNI0 to high priority on every ISR entry,
    but the very first interrupt fires with the default low priority.
    Pre-setting it avoids the low-priority first entry whose pushed
    PSW has ISP=0, which allows nesting on the return.
    """
    intc = proc.bus.device("intc")
    # Set INTWTNI0 to high priority (clear bit 0 of PR1L)
    pr1l = intc.read(intc.PR1L)
    intc.write(intc.PR1L, pr1l & 0xFE)


def patch_rom(proc):
    """Apply ROM patches for running under emulation.
    Must be called after loading firmware into ROM and before reset."""
    rom = proc.bus.device("rom")

    # Patch bit-banged I2C to TEA6840H to return success immediately.
    # Without port I/O emulation, the bit-bang loops forever.
    # i2c_tea6840_read at 0x5D99: clr1 cy; ret
    rom.load(0x5D99, [0x21, 0xAF])
    # i2c_tea6840_write at 0x5E2A: clr1 cy; ret
    rom.load(0x5E2A, [0x21, 0xAF])

    _fix_rom_checksum(rom)


def _fix_rom_checksum(rom):
    """Recompute and store the ROM checksum after patching.

    The firmware checksums ROM 0x0000-0xEFFD with initial AX=0x5555,
    adding each byte to A with carry into X.  The expected result is
    stored at 0xEFFE (high) and 0xEFFF (low).
    """
    a = 0x55
    x = 0x55
    for addr in range(0xEFFE):
        a += rom.read(addr)
        if a > 0xFF:
            a &= 0xFF
            x = (x + 1) & 0xFF
    rom.load(0xEFFE, [a, x])  # low byte at EFFE, high byte at EFFF
