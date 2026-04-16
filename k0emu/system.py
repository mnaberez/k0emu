from k0emu.devices import (MemoryDevice, RegisterFileDevice,
                           ProcessorStatusDevice, InterruptControllerDevice,
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

    processor_status = ProcessorStatusDevice("processor_status")
    proc.bus.add_device(processor_status, (0xFF1C, 0xFF1E))

    intc = InterruptControllerDevice("intc")
    proc.bus.add_device(intc, (0xFFE0, 0xFFEB))
    proc.bus.set_interrupt_controller(intc)

    watch_timer = WatchTimerDevice("watch_timer")
    proc.bus.add_device(watch_timer, (0xFF41, 0xFF41))
    intc.connect(watch_timer, watch_timer.INT_PRESCALER, intc.INTWTNI0)
    intc.connect(watch_timer, watch_timer.INT_WATCH, intc.INTWTN0)

    watchdog = WatchdogDevice("watchdog")
    proc.bus.add_device(watchdog, (0xFF42, 0xFF42), (0xFFF9, 0xFFF9))
    intc.connect(watchdog, watchdog.INT_OVERFLOW, intc.INTWDT)

    return proc
