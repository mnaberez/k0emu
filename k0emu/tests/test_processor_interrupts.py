import unittest
from k0emu.devices import MemoryDevice, InterruptControllerDevice, WatchTimerDevice
from k0emu.processor import Processor, Flags, Registers


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
        proc.write_psw(Flags.IE | Flags.ISP)
        proc.write_sp(0xFE00)
        proc.pc = 0
        proc.step()
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
        proc.step()
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
        proc.step()
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
