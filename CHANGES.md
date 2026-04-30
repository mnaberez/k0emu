## 2.0.0.dev0 (2026-04-30)

- Dropped support for Python versions below 3.8.

- Added a bus architecture with memory-mapped peripheral devices.  The
  processor, memory, and peripherals are now wired together on a bus.

- Added support for interrupts, including HALT with wake-on-interrupt.

- Added minimal implementations of some peripheral devices (GPIO, timers,
  I2C and SPI controllers).

- Added cycle counting for all instructions.

- Fixed BRK vector address (was 0x003F, now 0x003E).

- Fixed `mov1 cy,sfr.bit` overwriting PSW with register A.

## 1.0.0 (2020-02-15)

- Initial release.
