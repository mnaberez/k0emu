import unittest
from k0emu.devices import MemoryDevice, InterruptControllerDevice, WatchTimerDevice
from k0emu.processor import Processor, Flags


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
    """Tests for IE and ISP gating in the processor."""

    def test_no_interrupt_when_ie_disabled(self):
        proc, mem, intc, dev = _make_processor()
        # Put a NOP at 0x0000
        mem.write(0, 0x00)
        # Set up ISR at vector 0x0006 (INTP0, source 1)
        mem.write(0x0006, 0x00)
        mem.write(0x0007, 0x10)  # ISR at 0x1000
        # Request INTP0 and unmask it
        intc.interrupt(dev, _TestPeripheral.INT_0)
        intc.write(intc.MK0L, 0xFD)
        # IE is off (default PSW = 0)
        proc.pc = 0
        proc.step()
        # Should NOT have vectored to ISR
        self.assertEqual(proc.pc, 1)  # just past the NOP

    def test_interrupt_when_ie_enabled(self):
        proc, mem, intc, dev = _make_processor()
        mem.write(0, 0x00)  # NOP
        mem.write(0x0006, 0x00)
        mem.write(0x0007, 0x10)  # ISR at 0x1000
        intc.interrupt(dev, _TestPeripheral.INT_0)
        intc.write(intc.MK0L, 0xFD)
        proc.write_psw(Flags.IE)
        proc.pc = 0
        proc.step()
        self.assertEqual(proc.pc, 0x1000)

    def test_low_priority_blocked_when_isp_set(self):
        proc, mem, intc, dev = _make_processor()
        mem.write(0, 0x00)  # NOP
        mem.write(0x0006, 0x00)
        mem.write(0x0007, 0x10)
        intc.interrupt(dev, _TestPeripheral.INT_0)
        intc.write(intc.MK0L, 0xFD)
        # PR defaults to 0xFF = all low priority
        proc.write_psw(Flags.IE | Flags.ISP)
        proc.pc = 0
        proc.step()
        self.assertEqual(proc.pc, 1)  # blocked, not vectored

    def test_high_priority_blocked_when_isp_set(self):
        proc, mem, intc, dev = _make_processor()
        mem.write(0, 0x00)  # NOP
        mem.write(0x0006, 0x00)
        mem.write(0x0007, 0x10)
        intc.interrupt(dev, _TestPeripheral.INT_0)
        intc.write(intc.MK0L, 0xFD)
        intc.write(intc.PR0L, 0xFD)    # INTP0 = high priority
        proc.write_psw(Flags.IE | Flags.ISP)
        proc.pc = 0
        proc.step()
        self.assertEqual(proc.pc, 1)  # blocked, not vectored


class InterruptEntryTests(unittest.TestCase):
    """Tests for the interrupt entry sequence: push PSW, push PC, set flags."""

    def test_ie_cleared_on_entry(self):
        proc, mem, intc, dev = _make_processor()
        mem.write(0, 0x00)
        mem.write(0x0006, 0x00)
        mem.write(0x0007, 0x10)
        intc.interrupt(dev, _TestPeripheral.INT_0)
        intc.write(intc.MK0L, 0xFD)
        proc.write_psw(Flags.IE)
        proc.pc = 0
        proc.step()
        self.assertFalse(proc.read_psw() & Flags.IE)

    def test_isp_set_for_high_priority(self):
        proc, mem, intc, dev = _make_processor()
        mem.write(0, 0x00)
        mem.write(0x0006, 0x00)
        mem.write(0x0007, 0x10)
        intc.interrupt(dev, _TestPeripheral.INT_0)
        intc.write(intc.MK0L, 0xFD)
        intc.write(intc.PR0L, 0xFD)  # high priority
        proc.write_psw(Flags.IE)
        proc.pc = 0
        proc.step()
        self.assertTrue(proc.read_psw() & Flags.ISP)

    def test_isp_not_set_for_low_priority(self):
        proc, mem, intc, dev = _make_processor()
        mem.write(0, 0x00)
        mem.write(0x0006, 0x00)
        mem.write(0x0007, 0x10)
        intc.interrupt(dev, _TestPeripheral.INT_0)
        intc.write(intc.MK0L, 0xFD)
        # PR defaults to 0xFF = low priority
        proc.write_psw(Flags.IE)
        proc.pc = 0
        proc.step()
        self.assertFalse(proc.read_psw() & Flags.ISP)

    def test_pc_pushed_on_stack(self):
        proc, mem, intc, dev = _make_processor()
        mem.write(0, 0x00)  # NOP at 0x0000
        mem.write(0x0006, 0x00)
        mem.write(0x0007, 0x10)
        intc.interrupt(dev, _TestPeripheral.INT_0)
        intc.write(intc.MK0L, 0xFD)
        proc.write_psw(Flags.IE)
        proc.write_sp(0xFE00)
        proc.pc = 0
        proc.step()
        # Stack: push PSW at FDFF, push PC high at FDFE, push PC low at FDFD
        # PC after NOP was 0x0001
        self.assertEqual(mem.read(0xFDFD), 0x01)  # PC low byte
        self.assertEqual(mem.read(0xFDFE), 0x00)  # PC high byte

    def test_psw_pushed_on_stack(self):
        proc, mem, intc, dev = _make_processor()
        mem.write(0, 0x00)
        mem.write(0x0006, 0x00)
        mem.write(0x0007, 0x10)
        intc.interrupt(dev, _TestPeripheral.INT_0)
        intc.write(intc.MK0L, 0xFD)
        proc.write_psw(Flags.IE)
        proc.write_sp(0xFE00)
        proc.pc = 0
        proc.step()
        # PSW was pushed first (before PC), so it's at SP+4
        # Stack grows down: push PSW at FE00-1=FDFF, push PC_hi at FDFF-1=FDFE, etc.
        # Actually: _push(PSW) writes at FDFF, _push_word(PC) pushes hi at FDFE, lo at FDFD
        # SP ends at FDFD
        pushed_psw = mem.read(0xFDFF)
        self.assertEqual(pushed_psw, Flags.IE)

    def test_if_flag_cleared_on_acknowledge(self):
        proc, mem, intc, dev = _make_processor()
        mem.write(0, 0x00)
        mem.write(0x0006, 0x00)
        mem.write(0x0007, 0x10)
        intc.interrupt(dev, _TestPeripheral.INT_0)
        intc.write(intc.MK0L, 0xFD)
        proc.write_psw(Flags.IE)
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
        proc.write_psw(Flags.IE)
        proc.write_sp(0xFE00)
        proc.pc = 0
        proc.step()
        self.assertEqual(proc.read_sp(), 0xFDFD)  # 3 bytes pushed: PSW + PC(2)


class InterruptVectorTests(unittest.TestCase):
    """Tests for correct vector table lookup."""

    def test_intwdt_vectors_to_0004(self):
        proc, mem, intc, dev = _make_processor()
        mem.write(0, 0x00)
        mem.write(0x0004, 0x00)
        mem.write(0x0005, 0x20)  # ISR at 0x2000
        intc.write(intc.IF0L, 0x01)  # INTWDT
        intc.write(intc.MK0L, 0xFE)
        proc.write_psw(Flags.IE)
        proc.pc = 0
        proc.step()
        self.assertEqual(proc.pc, 0x2000)

    def test_intp0_vectors_to_0006(self):
        proc, mem, intc, dev = _make_processor()
        mem.write(0, 0x00)
        mem.write(0x0006, 0x00)
        mem.write(0x0007, 0x20)
        intc.write(intc.IF0L, 0x02)  # INTP0
        intc.write(intc.MK0L, 0xFD)
        proc.write_psw(Flags.IE)
        proc.pc = 0
        proc.step()
        self.assertEqual(proc.pc, 0x2000)

    def test_intcsi30_vectors_to_001c(self):
        proc, mem, intc, dev = _make_processor()
        mem.write(0, 0x00)
        mem.write(0x001C, 0x00)
        mem.write(0x001D, 0x20)
        intc.write(intc.IF0H, 0x10)  # INTCSI30
        intc.write(intc.MK0H, 0xEF)
        proc.write_psw(Flags.IE)
        proc.pc = 0
        proc.step()
        self.assertEqual(proc.pc, 0x2000)

    def test_intwtni0_vectors_to_0024(self):
        proc, mem, intc, dev = _make_processor()
        mem.write(0, 0x00)
        mem.write(0x0024, 0x00)
        mem.write(0x0025, 0x20)
        intc.write(intc.IF1L, 0x01)  # INTWTNI0
        intc.write(intc.MK1L, 0xFE)
        proc.write_psw(Flags.IE)
        proc.pc = 0
        proc.step()
        self.assertEqual(proc.pc, 0x2000)

    def test_intwtn0_vectors_to_0034(self):
        proc, mem, intc, dev = _make_processor()
        mem.write(0, 0x00)
        mem.write(0x0034, 0x00)
        mem.write(0x0035, 0x20)
        intc.write(intc.IF1H, 0x01)  # INTWTN0
        intc.write(intc.MK1H, 0xFE)
        proc.write_psw(Flags.IE)
        proc.pc = 0
        proc.step()
        self.assertEqual(proc.pc, 0x2000)

    def test_inttm52_vectors_to_003c(self):
        proc, mem, intc, dev = _make_processor()
        mem.write(0, 0x00)
        mem.write(0x003C, 0x00)
        mem.write(0x003D, 0x20)
        intc.write(intc.IF1H, 0x10)  # INTTM52
        intc.write(intc.MK1H, 0xEF)
        proc.write_psw(Flags.IE)
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

    def test_halt_wakes_on_pending_interrupt(self):
        proc, mem, intc, wt = _make_processor_with_timer()
        # HALT at address 0
        mem.write(0, 0x71)
        mem.write(1, 0x10)
        # ISR at vector 0x0024 (INTWTNI0) points to 0x2000
        mem.write(0x0024, 0x00)
        mem.write(0x0025, 0x20)
        # Enable watch timer: WTNM00=1, n=0, fw=128 -> interval=2048
        wt.write(0, 0x01)
        # Unmask INTWTNI0
        intc.write(intc.MK1L, intc.read(intc.MK1L) & 0xFE)
        proc.write_psw(Flags.IE)
        proc.write_sp(0xFE00)
        proc.pc = 0
        proc.step()
        # HALT should have waited for the timer, then serviced the interrupt
        self.assertEqual(proc.pc, 0x2000)

    def test_halt_advances_cycles(self):
        proc, mem, intc, wt = _make_processor_with_timer()
        mem.write(0, 0x71)
        mem.write(1, 0x10)
        mem.write(0x0024, 0x00)
        mem.write(0x0025, 0x20)
        wt.write(0, 0x01)  # interval=2048
        intc.write(intc.MK1L, intc.read(intc.MK1L) & 0xFE)
        proc.write_psw(Flags.IE)
        proc.write_sp(0xFE00)
        proc.pc = 0
        cycles_before = proc.total_cycles
        proc.step()
        # Should have waited ~2048 cycles for the timer
        elapsed = proc.total_cycles - cycles_before
        self.assertGreaterEqual(elapsed, 2048)

    def test_halt_does_not_double_tick(self):
        proc, mem, intc, wt = _make_processor_with_timer()
        mem.write(0, 0x71)
        mem.write(1, 0x10)
        mem.write(0x0024, 0x00)
        mem.write(0x0025, 0x20)
        wt.write(0, 0x01)  # interval=2048
        intc.write(intc.MK1L, intc.read(intc.MK1L) & 0xFE)
        proc.write_psw(Flags.IE)
        proc.write_sp(0xFE00)
        proc.pc = 0
        proc.step()
        # The timer should have fired exactly once (no double-ticking).
        # After firing, the prescaler counter resets to a small remainder.
        self.assertLess(wt._prescaler_counter, 100)

    def test_halt_with_interrupt_already_pending(self):
        proc, mem, intc, wt = _make_processor_with_timer()
        mem.write(0, 0x71)
        mem.write(1, 0x10)
        mem.write(0x0024, 0x00)
        mem.write(0x0025, 0x20)
        # Set IF flag before HALT
        intc.write(intc.IF1L, 0x01)  # INTWTNI0 already pending
        intc.write(intc.MK1L, intc.read(intc.MK1L) & 0xFE)
        proc.write_psw(Flags.IE)
        proc.write_sp(0xFE00)
        proc.pc = 0
        cycles_before = proc.total_cycles
        proc.step()
        # Should wake almost immediately
        self.assertEqual(proc.pc, 0x2000)
        elapsed = proc.total_cycles - cycles_before
        # Only the HALT fetch cycles + 1 tick to detect the pending interrupt
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
