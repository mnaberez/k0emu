import unittest
from k0emu.devices import MemoryDevice, InterruptControllerDevice, WatchTimerDevice
from k0emu.processor import Processor, Flags, Registers, RunState


class _TestPeripheral(object):
    """Dummy peripheral for triggering interrupts in tests."""
    INT_0 = 0


def _make_processor():
    """Create a processor with memory, an interrupt controller,
    and a test peripheral connected to INTP0."""
    proc = Processor()
    mem = MemoryDevice("test_memory", size=0xFFE0)
    proc.bus.add_device(mem, (0x0000, 0xFFDF))
    intc = InterruptControllerDevice("intc")
    proc.bus.add_device(intc, (0xFFE0, 0xFFEB))
    proc.bus.set_interrupt_controller(intc)
    dev = _TestPeripheral()
    intc.connect(dev, _TestPeripheral.INT_0, InterruptControllerDevice.INTP0)
    return proc, mem, intc, dev


class InterruptGatingTests(unittest.TestCase):
    """Tests for IE and ISP gating in the processor.

    ISP semantics (after polarity fix):
      ISP=1: normal state, all maskable interrupts acknowledgeable
      ISP=0: high-priority interrupt being serviced, low-priority blocked
    Reset sets PSW=0x02 (ISP=1)."""

    def test_no_interrupt_when_ie_disabled(self):
        proc, mem, intc, dev = _make_processor()
        mem.write(0, 0x00)
        mem.write(0x0006, 0x00)
        mem.write(0x0007, 0x10)
        intc.interrupt(dev, _TestPeripheral.INT_0)
        intc.write(intc.MK0L, 0xFD)
        proc.write_psw(Flags.ISP)  # ISP=1 (normal) but IE=0
        proc.pc = 0
        proc.step()
        self.assertEqual(proc.pc, 1)

    def test_interrupt_when_ie_enabled(self):
        proc, mem, intc, dev = _make_processor()
        mem.write(0, 0x00)
        mem.write(0x0006, 0x00)
        mem.write(0x0007, 0x10)
        intc.interrupt(dev, _TestPeripheral.INT_0)
        intc.write(intc.MK0L, 0xFD)
        proc.write_psw(Flags.IE | Flags.ISP)  # IE=1, ISP=1 (normal)
        proc.pc = 0
        proc.step()
        self.assertEqual(proc.pc, 0x1000)

    def test_low_priority_blocked_when_isp_clear(self):
        """ISP=0 means high-priority ISR is running; low-priority is blocked."""
        proc, mem, intc, dev = _make_processor()
        mem.write(0, 0x00)
        mem.write(0x0006, 0x00)
        mem.write(0x0007, 0x10)
        intc.interrupt(dev, _TestPeripheral.INT_0)
        intc.write(intc.MK0L, 0xFD)
        # PR defaults to 0xFF = all low priority
        proc.write_psw(Flags.IE)  # IE=1 but ISP=0 (high-pri servicing)
        proc.pc = 0
        proc.step()
        self.assertEqual(proc.pc, 1)  # blocked

    def test_high_priority_not_blocked_when_isp_clear(self):
        """ISP=0 blocks low-priority but high-priority can still nest."""
        proc, mem, intc, dev = _make_processor()
        mem.write(0, 0x00)
        mem.write(0x0006, 0x00)
        mem.write(0x0007, 0x10)
        intc.interrupt(dev, _TestPeripheral.INT_0)
        intc.write(intc.MK0L, 0xFD)
        intc.write(intc.PR0L, 0xFD)  # INTP0 = high priority
        proc.write_psw(Flags.IE)  # IE=1 but ISP=0
        proc.pc = 0
        proc.step()
        self.assertEqual(proc.pc, 0x1000)  # high-priority fires


class InterruptEntryTests(unittest.TestCase):
    """Tests for the interrupt entry sequence: push PSW, push PC, set flags.

    ISP on acknowledge: ISP ← PR value for that source.
      High-priority (PR=0) → ISP=0
      Low-priority  (PR=1) → ISP=1"""

    def test_ie_cleared_on_entry(self):
        proc, mem, intc, dev = _make_processor()
        mem.write(0, 0x00)
        mem.write(0x0006, 0x00)
        mem.write(0x0007, 0x10)
        intc.interrupt(dev, _TestPeripheral.INT_0)
        intc.write(intc.MK0L, 0xFD)
        proc.write_psw(Flags.IE | Flags.ISP)
        proc.pc = 0
        proc.step()
        self.assertFalse(proc.read_psw() & Flags.IE)

    def test_isp_clear_after_high_priority_entry(self):
        """High-priority (PR=0) → ISP=0 on acknowledge."""
        proc, mem, intc, dev = _make_processor()
        mem.write(0, 0x00)
        mem.write(0x0006, 0x00)
        mem.write(0x0007, 0x10)
        intc.interrupt(dev, _TestPeripheral.INT_0)
        intc.write(intc.MK0L, 0xFD)
        intc.write(intc.PR0L, 0xFD)  # INTP0 = high priority (PR bit=0)
        proc.write_psw(Flags.IE | Flags.ISP)
        proc.pc = 0
        proc.step()
        self.assertFalse(proc.read_psw() & Flags.ISP)

    def test_isp_set_after_low_priority_entry(self):
        """Low-priority (PR=1) → ISP=1 on acknowledge."""
        proc, mem, intc, dev = _make_processor()
        mem.write(0, 0x00)
        mem.write(0x0006, 0x00)
        mem.write(0x0007, 0x10)
        intc.interrupt(dev, _TestPeripheral.INT_0)
        intc.write(intc.MK0L, 0xFD)
        # PR defaults to 0xFF = low priority (PR bit=1)
        proc.write_psw(Flags.IE | Flags.ISP)
        proc.pc = 0
        proc.step()
        self.assertTrue(proc.read_psw() & Flags.ISP)

    def test_pc_pushed_on_stack(self):
        proc, mem, intc, dev = _make_processor()
        mem.write(0, 0x00)
        mem.write(0x0006, 0x00)
        mem.write(0x0007, 0x10)
        intc.interrupt(dev, _TestPeripheral.INT_0)
        intc.write(intc.MK0L, 0xFD)
        proc.write_psw(Flags.IE | Flags.ISP)
        proc.write_sp(0xFE00)
        proc.pc = 0
        proc.step()
        self.assertEqual(mem.read(0xFDFD), 0x01)
        self.assertEqual(mem.read(0xFDFE), 0x00)

    def test_psw_pushed_on_stack(self):
        proc, mem, intc, dev = _make_processor()
        mem.write(0, 0x00)
        mem.write(0x0006, 0x00)
        mem.write(0x0007, 0x10)
        intc.interrupt(dev, _TestPeripheral.INT_0)
        intc.write(intc.MK0L, 0xFD)
        proc.write_psw(Flags.IE | Flags.ISP)
        proc.write_sp(0xFE00)
        proc.pc = 0
        proc.step()
        pushed_psw = mem.read(0xFDFF)
        self.assertEqual(pushed_psw, Flags.IE | Flags.ISP)

    def test_if_flag_cleared_on_acknowledge(self):
        proc, mem, intc, dev = _make_processor()
        mem.write(0, 0x00)
        mem.write(0x0006, 0x00)
        mem.write(0x0007, 0x10)
        intc.interrupt(dev, _TestPeripheral.INT_0)
        intc.write(intc.MK0L, 0xFD)
        proc.write_psw(Flags.IE | Flags.ISP)
        proc.pc = 0
        proc.step()
        self.assertEqual(intc.read(intc.IF0L) & 0x02, 0)

    def test_sp_decremented_by_3(self):
        proc, mem, intc, dev = _make_processor()
        mem.write(0, 0x00)
        mem.write(0x0006, 0x00)
        mem.write(0x0007, 0x10)
        intc.interrupt(dev, _TestPeripheral.INT_0)
        intc.write(intc.MK0L, 0xFD)
        proc.write_psw(Flags.IE | Flags.ISP)
        proc.write_sp(0xFE00)
        proc.pc = 0
        proc.step()
        self.assertEqual(proc.read_sp(), 0xFDFD)


class InterruptVectorTests(unittest.TestCase):
    """Tests for correct vector table lookup."""

    def test_intwdt_vectors_to_0004(self):
        proc, mem, intc, dev = _make_processor()
        mem.write(0, 0x00)
        mem.write(0x0004, 0x00)
        mem.write(0x0005, 0x20)
        intc.write(intc.IF0L, 0x01)
        intc.write(intc.MK0L, 0xFE)
        proc.write_psw(Flags.IE | Flags.ISP)
        proc.pc = 0
        proc.step()
        self.assertEqual(proc.pc, 0x2000)

    def test_intp0_vectors_to_0006(self):
        proc, mem, intc, dev = _make_processor()
        mem.write(0, 0x00)
        mem.write(0x0006, 0x00)
        mem.write(0x0007, 0x20)
        intc.write(intc.IF0L, 0x02)
        intc.write(intc.MK0L, 0xFD)
        proc.write_psw(Flags.IE | Flags.ISP)
        proc.pc = 0
        proc.step()
        self.assertEqual(proc.pc, 0x2000)

    def test_intcsi30_vectors_to_001c(self):
        proc, mem, intc, dev = _make_processor()
        mem.write(0, 0x00)
        mem.write(0x001C, 0x00)
        mem.write(0x001D, 0x20)
        intc.write(intc.IF0H, 0x10)
        intc.write(intc.MK0H, 0xEF)
        proc.write_psw(Flags.IE | Flags.ISP)
        proc.pc = 0
        proc.step()
        self.assertEqual(proc.pc, 0x2000)

    def test_intwtni0_vectors_to_0024(self):
        proc, mem, intc, dev = _make_processor()
        mem.write(0, 0x00)
        mem.write(0x0024, 0x00)
        mem.write(0x0025, 0x20)
        intc.write(intc.IF1L, 0x01)
        intc.write(intc.MK1L, 0xFE)
        proc.write_psw(Flags.IE | Flags.ISP)
        proc.pc = 0
        proc.step()
        self.assertEqual(proc.pc, 0x2000)

    def test_intwtn0_vectors_to_0034(self):
        proc, mem, intc, dev = _make_processor()
        mem.write(0, 0x00)
        mem.write(0x0034, 0x00)
        mem.write(0x0035, 0x20)
        intc.write(intc.IF1H, 0x01)
        intc.write(intc.MK1H, 0xFE)
        proc.write_psw(Flags.IE | Flags.ISP)
        proc.pc = 0
        proc.step()
        self.assertEqual(proc.pc, 0x2000)

    def test_inttm52_vectors_to_003c(self):
        proc, mem, intc, dev = _make_processor()
        mem.write(0, 0x00)
        mem.write(0x003C, 0x00)
        mem.write(0x003D, 0x20)
        intc.write(intc.IF1H, 0x10)
        intc.write(intc.MK1H, 0xEF)
        proc.write_psw(Flags.IE | Flags.ISP)
        proc.pc = 0
        proc.step()
        self.assertEqual(proc.pc, 0x2000)


def _make_processor_with_timer():
    """Create a processor with memory, interrupt controller, and watch timer."""
    proc = Processor()
    mem = MemoryDevice("test_memory", size=0xFF41)
    proc.bus.add_device(mem, (0x0000, 0xFF40))
    intc = InterruptControllerDevice("intc")
    proc.bus.add_device(intc, (0xFFE0, 0xFFEB))
    proc.bus.set_interrupt_controller(intc)
    wt = WatchTimerDevice("watch_timer")
    proc.bus.add_device(wt, (0xFF41, 0xFF41))
    intc.connect(wt, wt.INT_PRESCALER, intc.INTWTNI0)
    return proc, mem, intc, wt


class HaltTests(unittest.TestCase):
    """Tests for the HALT instruction (0x71 0x10)."""

    def _run_until_halt_wakes(self, proc, max_steps=5000):
        """Step until HALT wakes (PC leaves address 0)."""
        for _ in range(max_steps):
            proc.step()
            if proc.pc != 0:
                return
        self.fail("HALT did not wake within %d steps" % max_steps)

    def test_halt_wakes_on_pending_interrupt(self):
        proc, mem, intc, wt = _make_processor_with_timer()
        mem.write(0, 0x71)
        mem.write(1, 0x10)
        mem.write(0x0024, 0x00)
        mem.write(0x0025, 0x20)
        wt.write(0, 0x01)
        intc.write(intc.MK1L, intc.read(intc.MK1L) & 0xFE)
        proc.write_psw(Flags.IE | Flags.ISP)
        proc.write_sp(0xFE00)
        proc.pc = 0
        self._run_until_halt_wakes(proc)
        self.assertEqual(proc.pc, 0x2000)

    def test_halt_advances_cycles(self):
        proc, mem, intc, wt = _make_processor_with_timer()
        mem.write(0, 0x71)
        mem.write(1, 0x10)
        mem.write(0x0024, 0x00)
        mem.write(0x0025, 0x20)
        wt.write(0, 0x01)
        intc.write(intc.MK1L, intc.read(intc.MK1L) & 0xFE)
        proc.write_psw(Flags.IE | Flags.ISP)
        proc.write_sp(0xFE00)
        proc.pc = 0
        cycles_before = proc.total_cycles
        self._run_until_halt_wakes(proc)
        elapsed = proc.total_cycles - cycles_before
        self.assertGreaterEqual(elapsed, 2048)

    def test_halt_does_not_double_tick(self):
        proc, mem, intc, wt = _make_processor_with_timer()
        mem.write(0, 0x71)
        mem.write(1, 0x10)
        mem.write(0x0024, 0x00)
        mem.write(0x0025, 0x20)
        wt.write(0, 0x01)
        intc.write(intc.MK1L, intc.read(intc.MK1L) & 0xFE)
        proc.write_psw(Flags.IE | Flags.ISP)
        proc.write_sp(0xFE00)
        proc.pc = 0
        self._run_until_halt_wakes(proc)
        self.assertLess(wt._prescaler_counter, 100)

    def test_halt_with_interrupt_already_pending(self):
        proc, mem, intc, wt = _make_processor_with_timer()
        mem.write(0, 0x71)
        mem.write(1, 0x10)
        mem.write(0x0024, 0x00)
        mem.write(0x0025, 0x20)
        intc.write(intc.IF1L, 0x01)
        intc.write(intc.MK1L, intc.read(intc.MK1L) & 0xFE)
        proc.write_psw(Flags.IE | Flags.ISP)
        proc.write_sp(0xFE00)
        proc.pc = 0
        cycles_before = proc.total_cycles
        proc.step()
        self.assertEqual(proc.pc, 0x2000)
        elapsed = proc.total_cycles - cycles_before
        self.assertLess(elapsed, 20)

    def test_halt_resumes_at_next_instruction_when_ie_disabled(self):
        proc, mem, intc, wt = _make_processor_with_timer()
        # HALT at address 0, NOP at address 2
        mem.write(0, 0x71)
        mem.write(1, 0x10)
        mem.write(2, 0x00)  # NOP
        # Set IF flag but IE=0 so interrupt won't be serviced
        intc.write(intc.IF1L, 0x01)
        intc.write(intc.MK1L, intc.read(intc.MK1L) & 0xFE)
        proc.write_psw(0)  # IE=0
        proc.write_sp(0xFE00)
        proc.pc = 0
        proc.step()
        # HALT wakes on the unmasked interrupt request but since IE=0,
        # it executes the next instruction instead of vectoring
        self.assertEqual(proc.pc, 2)


class HaltReturnAddressTests(unittest.TestCase):
    """Tests that HALT pushes the correct return address.

    The HALT instruction is 2 bytes (0x71 0x10).  When a timer interrupt
    wakes the CPU from HALT, the ISR must return to the instruction AFTER
    HALT, not to HALT itself.
    """

    HALT_ADDR = 0x0100
    AFTER_HALT = 0x0102
    ISR_ADDR = 0x2000
    WTNI_VECTOR = 0x0024
    SP_INIT = 0xFE00

    def _make_halt_test(self, prescaler_preload=0):
        """Set up a processor with HALT, a timer ISR, and a NOP after HALT.

        The ISR does: EI, RETI (so the processor returns to AFTER_HALT
        with interrupts re-enabled).

        prescaler_preload: initial value for the watch timer prescaler
        counter.  Use this to control exactly when the interrupt fires.
        """
        proc, mem, intc, wt = _make_processor_with_timer()

        # HALT at HALT_ADDR
        mem.write(self.HALT_ADDR, 0x71)
        mem.write(self.HALT_ADDR + 1, 0x10)

        # NOP at AFTER_HALT (instruction after HALT)
        mem.write(self.AFTER_HALT, 0x00)

        # ISR: EI (7A 1E), RETI (8F)
        mem.write(self.ISR_ADDR, 0x7A)
        mem.write(self.ISR_ADDR + 1, 0x1E)
        mem.write(self.ISR_ADDR + 2, 0x8F)

        # INTWTNI0 vector -> ISR_ADDR
        mem.write(self.WTNI_VECTOR, self.ISR_ADDR & 0xFF)
        mem.write(self.WTNI_VECTOR + 1, self.ISR_ADDR >> 8)

        # Enable watch timer with shortest interval (WTNM0=0x01, 2048 cycles)
        wt.write(0, 0x01)
        wt._prescaler_counter = prescaler_preload

        # Unmask INTWTNI0
        intc.write(intc.MK1L, intc.read(intc.MK1L) & 0xFE)

        # IE=1, ISP=1
        proc.write_psw(Flags.IE | Flags.ISP)
        proc.write_sp(self.SP_INIT)
        proc.pc = self.HALT_ADDR

        return proc, mem, intc, wt

    def _run_until_pc_at(self, proc, target, max_steps=5000):
        """Step until PC reaches target address."""
        for _ in range(max_steps):
            proc.step()
            if proc.pc == target:
                return
        self.fail("PC did not reach 0x%04X within %d steps" % (target, max_steps))

    def test_reti_returns_to_instruction_after_halt(self):
        """After HALT wakes and ISR runs, RETI goes to HALT+2, not HALT."""
        proc, mem, intc, wt = self._make_halt_test()
        self._run_until_pc_at(proc, self.ISR_ADDR)
        # ISR entered; now run EI + RETI
        proc.step()  # EI
        proc.step()  # RETI
        self.assertEqual(proc.pc, self.AFTER_HALT)

    def test_return_address_on_stack_is_after_halt(self):
        """When the ISR is entered, the stack contains HALT+2."""
        proc, mem, intc, wt = self._make_halt_test()
        self._run_until_pc_at(proc, self.ISR_ADDR)
        # Read the return address from the stack (SP was decremented by 3:
        # 1 byte for PSW + 2 bytes for PC)
        sp = proc.read_sp()
        ret_lo = mem.read(sp)
        ret_hi = mem.read(sp + 1)
        ret_addr = ret_lo | (ret_hi << 8)
        self.assertEqual(ret_addr, self.AFTER_HALT)

    def test_halt_at_nonzero_address_returns_correctly(self):
        """HALT is not always at address 0; verify with HALT at 0x0100."""
        proc, mem, intc, wt = self._make_halt_test()
        self.assertEqual(proc.pc, self.HALT_ADDR)
        self._run_until_pc_at(proc, self.ISR_ADDR)
        proc.step()  # EI
        proc.step()  # RETI
        self.assertEqual(proc.pc, self.AFTER_HALT)

    def test_prescaler_fires_on_last_cycle_of_tick(self):
        """Prescaler counter 1 cycle below threshold fires during the tick.

        The HALT instruction consumes 3 cycles (2 fetch + 1 execute).
        If the prescaler is 1 cycle away from firing, it fires during
        step()'s bus.tick(3).  The IF flag is set but the intc has
        already ticked in this same bus.tick, so pending_interrupt is
        not populated until the next step's intc tick.  After 2 steps
        the ISR must be entered with the correct return address.
        """
        proc, mem, intc, wt = self._make_halt_test()
        interval = wt.prescaler_interval  # 2048
        wt._prescaler_counter = interval - 1
        proc.step()  # timer fires, sets IF flag
        proc.step()  # intc sees IF flag, vectors to ISR
        self.assertEqual(proc.pc, self.ISR_ADDR)

    def test_prescaler_fires_on_first_cycle_of_tick(self):
        """Prescaler counter exactly at threshold fires on the first cycle."""
        proc, mem, intc, wt = self._make_halt_test()
        interval = wt.prescaler_interval  # 2048
        wt._prescaler_counter = interval - 2
        proc.step()  # timer fires, sets IF flag
        proc.step()  # intc sees IF flag, vectors to ISR
        self.assertEqual(proc.pc, self.ISR_ADDR)

    def test_return_address_correct_at_prescaler_boundary(self):
        """The return address must be HALT+2 even when the timer fires at
        the exact prescaler boundary."""
        proc, mem, intc, wt = self._make_halt_test()
        interval = wt.prescaler_interval
        wt._prescaler_counter = interval - 1
        proc.step()  # timer fires, sets IF flag
        proc.step()  # intc sees IF flag, vectors to ISR
        self.assertEqual(proc.pc, self.ISR_ADDR)
        # Verify the return address on the stack
        sp = proc.read_sp()
        ret_lo = mem.read(sp)
        ret_hi = mem.read(sp + 1)
        ret_addr = ret_lo | (ret_hi << 8)
        self.assertEqual(ret_addr, self.AFTER_HALT)

    def test_prescaler_one_cycle_short_does_not_fire(self):
        """Prescaler 3 cycles below threshold does not fire (tick is 2 cycles)."""
        proc, mem, intc, wt = self._make_halt_test()
        interval = wt.prescaler_interval  # 2048
        wt._prescaler_counter = interval - 3
        proc.step()
        # Should have re-executed HALT (still at HALT_ADDR)
        self.assertEqual(proc.pc, self.HALT_ADDR)

    def test_full_round_trip_halt_isr_reti_nop(self):
        """Full cycle: HALT -> timer fires -> ISR -> RETI -> NOP after HALT."""
        proc, mem, intc, wt = self._make_halt_test()
        # Step through HALT (many steps until timer fires)
        self._run_until_pc_at(proc, self.ISR_ADDR)
        # Step through ISR: EI (7A 1E = 2 bytes, needs 1 step)
        proc.step()
        self.assertEqual(proc.pc, self.ISR_ADDR + 2)
        # RETI
        proc.step()
        self.assertEqual(proc.pc, self.AFTER_HALT)
        # NOP
        proc.step()
        self.assertEqual(proc.pc, self.AFTER_HALT + 1)

    def test_halt_isr_runs_twice(self):
        """HALT can be followed by another HALT; both wake correctly.

        Layout: HALT at 0x0100, HALT at 0x0102, NOP at 0x0104.
        The ISR does EI + RETI.  First wake returns to 0x0102 (second
        HALT), second wake returns to 0x0104 (NOP).
        """
        proc, mem, intc, wt = self._make_halt_test()
        # Replace the NOP at 0x0102 with a second HALT
        mem.write(self.AFTER_HALT, 0x71)
        mem.write(self.AFTER_HALT + 1, 0x10)
        # NOP at 0x0104
        mem.write(self.AFTER_HALT + 2, 0x00)

        # First HALT -> ISR -> RETI -> second HALT
        self._run_until_pc_at(proc, self.ISR_ADDR)
        proc.step()  # EI
        proc.step()  # RETI
        self.assertEqual(proc.pc, self.AFTER_HALT)

        # Second HALT -> ISR -> RETI -> NOP
        self._run_until_pc_at(proc, self.ISR_ADDR)
        proc.step()  # EI
        proc.step()  # RETI
        self.assertEqual(proc.pc, self.AFTER_HALT + 2)

    def test_halt_rewind_pending_flag_cleared_after_wake(self):
        """The _halt_rewind_pending flag is cleared after the interrupt fires,
        so a subsequent non-HALT instruction is not affected."""
        proc, mem, intc, wt = self._make_halt_test()
        self.assertFalse(proc._halt_rewind_pending)
        # Run until ISR entered
        self._run_until_pc_at(proc, self.ISR_ADDR)
        self.assertFalse(proc._halt_rewind_pending)

    def test_halt_rewind_pending_flag_cleared_after_rewind(self):
        """The _halt_rewind_pending flag is cleared even when HALT re-executes."""
        proc, mem, intc, wt = self._make_halt_test()
        proc.step()  # HALT with no interrupt yet
        self.assertEqual(proc.pc, self.HALT_ADDR)
        self.assertFalse(proc._halt_rewind_pending)

    def test_halt_rewind_pending_flag_not_set_by_other_instructions(self):
        """Non-HALT instructions do not set the _halt_rewind_pending flag."""
        proc, mem, intc, wt = self._make_halt_test()
        # Write a NOP at HALT_ADDR instead
        mem.write(self.HALT_ADDR, 0x00)
        proc.step()
        self.assertFalse(proc._halt_rewind_pending)
        self.assertEqual(proc.pc, self.HALT_ADDR + 1)

    def test_stack_pointer_correct_after_halt_wake(self):
        """SP is decremented by 3 (PSW + 2-byte PC) when ISR is entered."""
        proc, mem, intc, wt = self._make_halt_test()
        self._run_until_pc_at(proc, self.ISR_ADDR)
        self.assertEqual(proc.read_sp(), self.SP_INIT - 3)

    def test_stack_pointer_restored_after_reti(self):
        """SP is restored to its original value after RETI."""
        proc, mem, intc, wt = self._make_halt_test()
        self._run_until_pc_at(proc, self.ISR_ADDR)
        proc.step()  # EI
        proc.step()  # RETI
        self.assertEqual(proc.read_sp(), self.SP_INIT)
        self.assertEqual(proc.pc, self.AFTER_HALT)

    def test_halt_with_high_priority_interrupt(self):
        """HALT wakes on a high-priority interrupt and returns correctly."""
        proc, mem, intc, wt = self._make_halt_test()
        # Set INTWTNI0 to high priority (clear bit 0 of PR1L)
        intc.write(intc.PR1L, intc.read(intc.PR1L) & 0xFE)
        self._run_until_pc_at(proc, self.ISR_ADDR)
        proc.step()  # EI
        proc.step()  # RETI
        self.assertEqual(proc.pc, self.AFTER_HALT)

    def test_halt_with_low_priority_interrupt(self):
        """HALT wakes on a low-priority interrupt and returns correctly."""
        proc, mem, intc, wt = self._make_halt_test()
        # Set INTWTNI0 to low priority (set bit 0 of PR1L)
        intc.write(intc.PR1L, intc.read(intc.PR1L) | 0x01)
        self._run_until_pc_at(proc, self.ISR_ADDR)
        proc.step()  # EI
        proc.step()  # RETI
        self.assertEqual(proc.pc, self.AFTER_HALT)

    def test_many_halt_reexecutions_then_correct_wake(self):
        """HALT re-executes many times before the timer fires.
        When it finally fires, the return address is still correct."""
        proc, mem, intc, wt = self._make_halt_test()
        # Step 100 times — all should re-execute HALT
        for _ in range(100):
            proc.step()
            if proc.pc != self.HALT_ADDR:
                break
        else:
            # Timer hasn't fired after 100 steps; expected with 2048 interval
            pass
        # Now run to ISR
        self._run_until_pc_at(proc, self.ISR_ADDR)
        proc.step()  # EI
        proc.step()  # RETI
        self.assertEqual(proc.pc, self.AFTER_HALT)

    def test_halt_at_address_zero(self):
        """HALT at address 0 returns to address 2."""
        proc, mem, intc, wt = _make_processor_with_timer()
        mem.write(0, 0x71)
        mem.write(1, 0x10)
        mem.write(2, 0x00)  # NOP
        # ISR: EI, RETI
        mem.write(self.ISR_ADDR, 0x7A)
        mem.write(self.ISR_ADDR + 1, 0x1E)
        mem.write(self.ISR_ADDR + 2, 0x8F)
        mem.write(self.WTNI_VECTOR, self.ISR_ADDR & 0xFF)
        mem.write(self.WTNI_VECTOR + 1, self.ISR_ADDR >> 8)
        wt.write(0, 0x01)
        intc.write(intc.MK1L, intc.read(intc.MK1L) & 0xFE)
        proc.write_psw(Flags.IE | Flags.ISP)
        proc.write_sp(self.SP_INIT)
        proc.pc = 0
        self._run_until_pc_at(proc, self.ISR_ADDR)
        proc.step()  # EI
        proc.step()  # RETI
        self.assertEqual(proc.pc, 2)

    def test_halt_at_high_address(self):
        """HALT near the top of memory returns correctly."""
        halt_addr = 0x8000
        proc, mem, intc, wt = _make_processor_with_timer()
        mem.write(halt_addr, 0x71)
        mem.write(halt_addr + 1, 0x10)
        mem.write(halt_addr + 2, 0x00)  # NOP
        mem.write(self.ISR_ADDR, 0x7A)
        mem.write(self.ISR_ADDR + 1, 0x1E)
        mem.write(self.ISR_ADDR + 2, 0x8F)
        mem.write(self.WTNI_VECTOR, self.ISR_ADDR & 0xFF)
        mem.write(self.WTNI_VECTOR + 1, self.ISR_ADDR >> 8)
        wt.write(0, 0x01)
        intc.write(intc.MK1L, intc.read(intc.MK1L) & 0xFE)
        proc.write_psw(Flags.IE | Flags.ISP)
        proc.write_sp(self.SP_INIT)
        proc.pc = halt_addr
        self._run_until_pc_at(proc, self.ISR_ADDR)
        proc.step()  # EI
        proc.step()  # RETI
        self.assertEqual(proc.pc, halt_addr + 2)


class RunStateTests(unittest.TestCase):
    """Tests for the run_state property on the Processor.

    run_state is RUNNING while executing any instruction, including HALT
    itself.  It becomes HALTED only after HALT completes and PC rewinds.
    When an interrupt wakes the CPU from HALT, run_state returns to RUNNING.
    """

    HALT_ADDR = 0x0100
    ISR_ADDR = 0x2000
    WTNI_VECTOR = 0x0024

    def _make_halt_test(self):
        proc, mem, intc, wt = _make_processor_with_timer()
        mem.write(self.HALT_ADDR, 0x71)
        mem.write(self.HALT_ADDR + 1, 0x10)
        mem.write(self.HALT_ADDR + 2, 0x00)  # NOP after HALT
        mem.write(self.ISR_ADDR, 0x7A)       # EI
        mem.write(self.ISR_ADDR + 1, 0x1E)
        mem.write(self.ISR_ADDR + 2, 0x8F)   # RETI
        mem.write(self.WTNI_VECTOR, self.ISR_ADDR & 0xFF)
        mem.write(self.WTNI_VECTOR + 1, self.ISR_ADDR >> 8)
        wt.write(0, 0x01)
        intc.write(intc.MK1L, intc.read(intc.MK1L) & 0xFE)
        proc.write_psw(Flags.IE | Flags.ISP)
        proc.write_sp(0xFE00)
        proc.pc = self.HALT_ADDR
        return proc, mem, intc, wt

    def test_initial_run_state_is_running(self):
        """A freshly created processor is in the RUNNING state."""
        proc = Processor()
        self.assertEqual(proc.run_state, RunState.RUNNING)

    def test_nop_stays_running(self):
        """Executing a NOP leaves run_state as RUNNING."""
        proc, mem, intc, wt = _make_processor_with_timer()
        mem.write(0, 0x00)  # NOP
        proc.pc = 0
        proc.step()
        self.assertEqual(proc.run_state, RunState.RUNNING)

    def test_halt_without_interrupt_becomes_halted(self):
        """After HALT executes with no interrupt pending, run_state is HALTED."""
        proc, mem, intc, wt = self._make_halt_test()
        proc.step()
        self.assertEqual(proc.run_state, RunState.HALTED)

    def test_halt_stays_halted_on_reexecution(self):
        """Repeated HALT re-executions remain HALTED."""
        proc, mem, intc, wt = self._make_halt_test()
        proc.step()
        self.assertEqual(proc.run_state, RunState.HALTED)
        proc.step()
        self.assertEqual(proc.run_state, RunState.HALTED)
        proc.step()
        self.assertEqual(proc.run_state, RunState.HALTED)

    def test_halt_with_pending_interrupt_stays_running(self):
        """HALT with an interrupt already pending does not become HALTED."""
        proc, mem, intc, wt = self._make_halt_test()
        intc.write(intc.IF1L, 0x01)
        proc.step()
        self.assertEqual(proc.run_state, RunState.RUNNING)
        self.assertEqual(proc.pc, self.ISR_ADDR)

    def test_halt_wake_returns_to_running(self):
        """When a timer interrupt wakes the CPU from HALT, run_state
        returns to RUNNING."""
        proc, mem, intc, wt = self._make_halt_test()
        proc.step()
        self.assertEqual(proc.run_state, RunState.HALTED)
        # Set the IF flag as if the timer fired
        intc.write(intc.IF1L, 0x01)
        proc.step()
        self.assertEqual(proc.run_state, RunState.RUNNING)

    def test_instruction_after_halt_is_running(self):
        """After HALT wakes and ISR returns, the next instruction is RUNNING."""
        proc, mem, intc, wt = self._make_halt_test()
        proc.step()  # HALT, becomes HALTED
        intc.write(intc.IF1L, 0x01)
        proc.step()  # HALT wakes, dispatches to ISR, RUNNING
        proc.step()  # EI
        self.assertEqual(proc.run_state, RunState.RUNNING)
        proc.step()  # RETI
        self.assertEqual(proc.run_state, RunState.RUNNING)
        proc.step()  # NOP after HALT
        self.assertEqual(proc.run_state, RunState.RUNNING)

    def test_run_state_after_reset(self):
        """After a bus reset, run_state is RUNNING."""
        proc, mem, intc, wt = self._make_halt_test()
        proc.step()
        self.assertEqual(proc.run_state, RunState.HALTED)
        proc.bus.reset()
        self.assertEqual(proc.run_state, RunState.RUNNING)


class InterruptHoldTests(unittest.TestCase):
    """Instructions that access PSW or interrupt control registers (IF, MK, PR)
    suppress interrupt acknowledgment until after the next instruction.

    Each test places the hold-triggering instruction at address 0, followed
    by a NOP.  An interrupt is pending.  After stepping the trigger, the
    interrupt must NOT have fired (PC past the trigger, not at ISR).  After
    stepping the NOP, the interrupt fires."""

    ISR_ADDR = 0x1000

    def _setup(self):
        proc, mem, intc, dev = _make_processor()
        # ISR at vector 0x0006 (INTP0)
        mem.write(0x0006, self.ISR_ADDR & 0xFF)
        mem.write(0x0007, self.ISR_ADDR >> 8)
        # Request and unmask INTP0
        intc.interrupt(dev, _TestPeripheral.INT_0)
        intc.write(intc.MK0L, 0xFD)
        proc.write_psw(Flags.IE | Flags.ISP)
        proc.write_sp(0xFE00)
        return proc, mem, intc, dev

    def _write_code(self, mem, *instructions):
        """Write instruction bytes starting at address 0, append a NOP."""
        addr = 0
        for b in instructions:
            mem.write(addr, b)
            addr += 1
        nop_addr = addr
        mem.write(addr, 0x00)  # NOP
        return nop_addr

    def _assert_hold(self, proc, nop_addr):
        """Step once: trigger instruction runs, interrupt is held.
        Step again: NOP runs, then interrupt fires."""
        proc.pc = 0
        proc.step()
        self.assertEqual(proc.pc, nop_addr,
            "Interrupt should be held, but PC jumped to 0x%04X" % proc.pc)
        proc.step()
        self.assertEqual(proc.pc, self.ISR_ADDR,
            "Interrupt should fire after NOP, but PC is 0x%04X" % proc.pc)

    def test_nop_does_not_hold(self):
        """Baseline: NOP does not suppress the interrupt."""
        proc, mem, intc, dev = self._setup()
        mem.write(0, 0x00)  # NOP
        proc.pc = 0
        proc.step()
        self.assertEqual(proc.pc, self.ISR_ADDR)

    def test_ei_holds(self):
        """EI = SET1 PSW.7"""
        proc, mem, intc, dev = self._setup()
        proc.write_psw(Flags.ISP)  # IE off, ISP=1 (normal); EI will set IE
        intc.write(intc.MK0L, 0xFD)
        nop_addr = self._write_code(mem, 0x7A, 0x1E)  # SET1 PSW.7
        self._assert_hold(proc, nop_addr)

    def test_di_holds(self):
        """DI = CLR1 PSW.7.  After DI, IE is off so we must re-enable
        before the NOP step to verify the hold released."""
        proc, mem, intc, dev = self._setup()
        nop_addr = self._write_code(mem, 0x7B, 0x1E)  # CLR1 PSW.7
        proc.pc = 0
        proc.step()
        self.assertEqual(proc.pc, nop_addr)
        # DI cleared IE; re-enable so the interrupt can fire after NOP
        proc.write_psw(proc.read_psw() | Flags.IE)
        proc.step()
        self.assertEqual(proc.pc, self.ISR_ADDR)

    def test_push_psw_holds(self):
        proc, mem, intc, dev = self._setup()
        nop_addr = self._write_code(mem, 0x22)  # PUSH PSW
        self._assert_hold(proc, nop_addr)

    def test_pop_psw_holds(self):
        proc, mem, intc, dev = self._setup()
        proc.write_sp(0xFE00)
        proc.bus.write(0xFDFF, Flags.IE | Flags.ISP)
        proc.write_sp(0xFDFF)
        nop_addr = self._write_code(mem, 0x23)  # POP PSW
        self._assert_hold(proc, nop_addr)

    def test_mov_psw_imm_holds(self):
        proc, mem, intc, dev = self._setup()
        nop_addr = self._write_code(mem, 0x11, 0x1E, Flags.IE | Flags.ISP)
        self._assert_hold(proc, nop_addr)

    def test_mov_psw_a_holds(self):
        proc, mem, intc, dev = self._setup()
        proc.write_gp_reg(Registers.A, Flags.IE | Flags.ISP)
        nop_addr = self._write_code(mem, 0xF2, 0x1E)  # MOV PSW,A
        self._assert_hold(proc, nop_addr)

    def test_mov_a_psw_holds(self):
        """Reading PSW also triggers the hold."""
        proc, mem, intc, dev = self._setup()
        nop_addr = self._write_code(mem, 0xF0, 0x1E)  # MOV A,PSW
        self._assert_hold(proc, nop_addr)

    def test_set1_psw_bit0_holds(self):
        """Any bit of PSW, not just bit 7."""
        proc, mem, intc, dev = self._setup()
        nop_addr = self._write_code(mem, 0x0A, 0x1E)  # SET1 PSW.0
        self._assert_hold(proc, nop_addr)

    def test_mov_saddr_non_psw_does_not_hold(self):
        proc, mem, intc, dev = self._setup()
        proc.write_gp_reg(Registers.A, 0x42)  # A = 0x42
        mem.write(0, 0xF2)  # MOV saddr,A
        mem.write(1, 0x30)  # saddr 0x30 -> address 0xFE30 (not PSW)
        proc.pc = 0
        proc.step()
        self.assertEqual(proc.pc, self.ISR_ADDR)

    def test_mov_mk0l_holds(self):
        """Writing to MK0L (0xFFE4) triggers interrupt hold."""
        proc, mem, intc, dev = self._setup()
        proc.write_gp_reg(Registers.A, 0xFD)  # A = keep INTP0 unmasked
        nop_addr = self._write_code(mem, 0xF6, 0xE4)  # MOV MK0L,A
        self._assert_hold(proc, nop_addr)

    def test_mov_a_if0l_holds(self):
        """Reading IF0L (0xFFE0) triggers interrupt hold."""
        proc, mem, intc, dev = self._setup()
        nop_addr = self._write_code(mem, 0xF4, 0xE0)  # MOV A,IF0L
        self._assert_hold(proc, nop_addr)

    def test_mov_sfr_non_interrupt_does_not_hold(self):
        proc, mem, intc, dev = self._setup()
        proc.write_gp_reg(Registers.A, 0x00)
        mem.write(0, 0xF6)  # MOV sfr,A
        mem.write(1, 0x80)  # sfr 0x80 -> address 0xFF80 (not IF/MK/PR)
        proc.pc = 0
        proc.step()
        self.assertEqual(proc.pc, self.ISR_ADDR)

    def test_reti_holds(self):
        proc, mem, intc, dev = self._setup()
        mem.write(0, 0x8F)  # RETI
        mem.write(1, 0x00)  # NOP
        proc.bus.write(0xFDFF, Flags.IE | Flags.ISP)
        proc.bus.write(0xFDFE, 0x00)
        proc.bus.write(0xFDFD, 0x01)
        proc.write_sp(0xFDFD)
        intc.interrupt(dev, _TestPeripheral.INT_0)
        proc.pc = 0
        proc.step()
        self.assertEqual(proc.pc, 1)
        proc.step()
        self.assertEqual(proc.pc, self.ISR_ADDR)

    def test_retb_holds(self):
        proc, mem, intc, dev = self._setup()
        mem.write(0, 0x9F)  # RETB
        mem.write(1, 0x00)  # NOP
        proc.bus.write(0xFDFF, Flags.IE | Flags.ISP)
        proc.bus.write(0xFDFE, 0x00)
        proc.bus.write(0xFDFD, 0x01)
        proc.write_sp(0xFDFD)
        proc.pc = 0
        proc.step()
        self.assertEqual(proc.pc, 1)
        proc.step()
        self.assertEqual(proc.pc, self.ISR_ADDR)
