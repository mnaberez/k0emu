from k0emu.devices import MemoryDevice, RegisterFileDevice
from k0emu.processor import Processor


def make_processor():
    """Build a Processor with the default bus and memory layout
    for the uPD78F0831Y."""
    proc = Processor()

    rom = MemoryDevice("rom", size=0xF000, fill=0xFF, writable=False)
    proc.bus.add_device([(0x0000, 0xEFFF)], rom)

    expansion_ram = MemoryDevice("expansion_ram", size=0x0800)
    proc.bus.add_device([(0xF000, 0xF7FF)], expansion_ram)

    reserved = MemoryDevice("reserved", size=0x0300, fill=0x08, writable=False)
    proc.bus.add_device([(0xF800, 0xFAFF)], reserved)

    high_speed_ram = MemoryDevice("high_speed_ram", size=0x03E0)
    proc.bus.add_device([(0xFB00, 0xFEDF)], high_speed_ram)

    register_file = RegisterFileDevice()
    proc.bus.add_device([(0xFEE0, 0xFEFF)], register_file)

    return proc
