k0emu
=====

Overview
--------

k0emu is an instruction set emulator for running Renesas (NEC) 78K0 binaries.  It executes all 78K0 instructions described in the `documentation <https://web.archive.org/web/20200214210657/https://www.renesas.com/us/en/doc/DocumentServer/021/U12326EJ4V0UM00.pdf>`_.  It can be used to study the behavior of 78K0 code but it does not emulate a particular microcontroller or any peripherals.

k0emu was developed to aid in reverse engineering of the `Volkswagen Premium V <https://github.com/mnaberez/vwradio>`_ car radios made by Delco.  These radios use the undocumented NEC µPD78F0831Y microcontroller, which is similar to the `µPD78F0833Y <https://web.archive.org/web/20180328161019/https://www.renesas.com/en-us/doc/DocumentServer/021/U13892EJ2V0UM00.pdf>`_.  A companion program, `k0dasm <https://github.com/mnaberez/k0dasm>`_, was also developed for this project.

Since no open source 78K0 emulator could be found at the time of development, a hardware test harness was built.  The harness is included with k0emu and is based on the µPD78F0831Y.  Instructions were first implemented as described in the documentation.  Test programs were then written and run on both k0emu and the real hardware.  When the results of k0emu were different, k0emu was fixed to behave like the hardware.  This process gives confidence that k0emu implements the instructions correctly.

Features
--------

- Executes all documented 78K0 instructions

- All instructions covered by unit tests

- At least one addressing mode of most operations was tested against hardware

Installation
------------

k0emu is written in Python and requires Python 3.4 or later.  Packages are `available <https://pypi.org/project/k0emu/>`_ on the Python Package Index (PyPI).  You can download them from there or you can use ``pip`` to install ``k0emu``::

    $ pip install setuptools k0emu

Usage
-----

k0emu accepts a plain binary file as input.  The file is assumed to be a ROM image that should be aligned to the bottom of memory.  For example, if a 32K file is given, k0emu will assume the image should be located at 0x0000-0x7FFF.  After loading the image, the emulator will start executing from the reset vector and will run until terminated::

    $ k0emu rom.bin

    0d88: 7b 1e        di                     AX=0000 BC=0000 DE=0000 HL=0000 SP=0000 [IE:0 RB:0 ISP:0 Z:0 AC:0 CY:0] ffe4=00000000 ffe5=00000000 ffe6=00000000 ffe7=00000000
    0d8a: 13 42 07     mov 0ff42h,#07h        AX=0000 BC=0000 DE=0000 HL=0000 SP=0000 [IE:0 RB:0 ISP:0 Z:0 AC:0 CY:0] ffe4=00000000 ffe5=00000000 ffe6=00000000 ffe7=00000000
    0d8d: 13 f9 90     mov 0fff9h,#90h        AX=0000 BC=0000 DE=0000 HL=0000 SP=0000 [IE:0 RB:0 ISP:0 Z:0 AC:0 CY:0] ffe4=00000000 ffe5=00000000 ffe6=00000000 ffe7=00000000
    0d90: 13 fb 00     mov 0fffbh,#00h        AX=0000 BC=0000 DE=0000 HL=0000 SP=0000 [IE:0 RB:0 ISP:0 Z:0 AC:0 CY:0] ffe4=00000000 ffe5=00000000 ffe6=00000000 ffe7=00000000
    0d93: ee 1c 1f fe  movw sp,#0fe1fh        AX=0000 BC=0000 DE=0000 HL=0000 SP=FE1F [IE:0 RB:0 ISP:0 Z:0 AC:0 CY:0] ffe4=00000000 ffe5=00000000 ffe6=00000000 ffe7=00000000
    0d97: 4b cd        clr1 0fecdh.4          AX=0000 BC=0000 DE=0000 HL=0000 SP=FE1F [IE:0 RB:0 ISP:0 Z:0 AC:0 CY:0] ffe4=00000000 ffe5=00000000 ffe6=00000000 ffe7=00000000
    0d99: 71 4b 23     clr1 0ff23h.4          AX=0000 BC=0000 DE=0000 HL=0000 SP=FE1F [IE:0 RB:0 ISP:0 Z:0 AC:0 CY:0] ffe4=00000000 ffe5=00000000 ffe6=00000000 ffe7=00000000
    0d9c: f0 cd        mov a,0fecdh           AX=0000 BC=0000 DE=0000 HL=0000 SP=FE1F [IE:0 RB:0 ISP:0 Z:0 AC:0 CY:0] ffe4=00000000 ffe5=00000000 ffe6=00000000 ffe7=00000000
    0d9e: f2 03        mov 0ff03h,a           AX=0000 BC=0000 DE=0000 HL=0000 SP=FE1F [IE:0 RB:0 ISP:0 Z:0 AC:0 CY:0] ffe4=00000000 ffe5=00000000 ffe6=00000000 ffe7=00000000
    0da0: 6b ce        clr1 0feceh.6          AX=0000 BC=0000 DE=0000 HL=0000 SP=FE1F [IE:0 RB:0 ISP:0 Z:0 AC:0 CY:0] ffe4=00000000 ffe5=00000000 ffe6=00000000 ffe7=00000000
    0da2: 71 6b 24     clr1 0ff24h.6          AX=0000 BC=0000 DE=0000 HL=0000 SP=FE1F [IE:0 RB:0 ISP:0 Z:0 AC:0 CY:0] ffe4=00000000 ffe5=00000000 ffe6=00000000 ffe7=00000000
    0da5: f0 ce        mov a,0feceh           AX=0000 BC=0000 DE=0000 HL=0000 SP=FE1F [IE:0 RB:0 ISP:0 Z:0 AC:0 CY:0] ffe4=00000000 ffe5=00000000 ffe6=00000000 ffe7=00000000
    0da7: f2 04        mov 0ff04h,a           AX=0000 BC=0000 DE=0000 HL=0000 SP=FE1F [IE:0 RB:0 ISP:0 Z:0 AC:0 CY:0] ffe4=00000000 ffe5=00000000 ffe6=00000000 ffe7=00000000
    ...

k0emu displays tracing information as it runs but it does not currently have any user interface to control the emulation.  Until that exists, you can modify the file ``run.py``.  The unit tests can also be used as a reference for how to run the emulator from your own Python programs.

Author
------

`Mike Naberezny <https://github.com/mnaberez>`_
