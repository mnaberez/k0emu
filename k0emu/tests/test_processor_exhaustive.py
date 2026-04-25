"""Exhaustive tests for the processor emulation

Tests operation helpers with brute-force 256x256 input combinations,
verifies instruction side effects (only documented destinations change),
and validates flag preservation rules.
"""

import random
import unittest
from k0emu.devices import MemoryDevice
from k0emu.processor import Processor, Registers, RegisterPairs, Flags


def _make_processor():
    proc = Processor()
    mem = MemoryDevice("test_memory", size=0x10000)
    proc.bus.add_device(mem, (0x0000, 0xFFFF))
    return proc, mem


# PSW bit 2 is always stuck off
PSW_MASK = 0b11111011

# Valid PSW bits (excluding stuck-zero bit 2)
VALID_PSW_BITS = Flags.CY | Flags.ISP | Flags.RBS0 | Flags.AC | Flags.RBS1 | Flags.Z | Flags.IE

# Flags that arithmetic operations modify
ARITHMETIC_FLAGS = Flags.CY | Flags.AC | Flags.Z

# Flags that should never change
PRESERVED_FLAGS = Flags.IE | Flags.ISP | Flags.RBS0 | Flags.RBS1


def _snapshot(proc):
    """Capture all mutable processor state."""
    regs = {}
    for r in range(8):
        regs[r] = proc.read_gp_reg(r)
    return {
        'regs': regs,
        'sp': proc.read_sp(),
        'psw': proc.read_psw(),
        'pc': proc.pc,
    }


def _assert_unchanged(test, before, after, *, changed_regs=None, changed_sp=False,
                       changed_psw_bits=0, changed_pc=True):
    """Assert that only the specified parts of processor state changed.

    changed_regs: set of register numbers that may have changed
    changed_sp: True if SP may have changed
    changed_psw_bits: bitmask of PSW bits that may have changed
    changed_pc: True if PC may have changed (almost always True for instructions)
    """
    if changed_regs is None:
        changed_regs = set()

    for r in range(8):
        if r not in changed_regs:
            test.assertEqual(before['regs'][r], after['regs'][r],
                             "Register %d changed unexpectedly: 0x%02x -> 0x%02x" %
                             (r, before['regs'][r], after['regs'][r]))

    if not changed_sp:
        test.assertEqual(before['sp'], after['sp'],
                         "SP changed unexpectedly: 0x%04x -> 0x%04x" %
                         (before['sp'], after['sp']))

    preserved_mask = PSW_MASK & ~changed_psw_bits
    test.assertEqual(before['psw'] & preserved_mask, after['psw'] & preserved_mask,
                     "PSW preserved bits changed: before=0x%02x after=0x%02x mask=0x%02x" %
                     (before['psw'], after['psw'], preserved_mask))


class TestOperationAdd(unittest.TestCase):
    """Test _operation_add for all 256x256 input combinations."""

    def test_all_256x256(self):
        proc, _ = _make_processor()
        for a in range(256):
            for b in range(256):
                # Set up clean PSW with known preserved bits
                init_psw = Flags.IE | Flags.ISP | Flags.RBS0 | Flags.RBS1
                proc.write_psw(init_psw)

                result = proc._operation_add(a, b)
                psw = proc.read_psw()

                expected = (a + b) & 0xFF
                self.assertEqual(result, expected,
                    "add(0x%02x, 0x%02x): result 0x%02x != expected 0x%02x" %
                    (a, b, result, expected))

                # Z flag
                if expected == 0:
                    self.assertTrue(psw & Flags.Z,
                        "add(0x%02x, 0x%02x): Z should be set" % (a, b))
                else:
                    self.assertFalse(psw & Flags.Z,
                        "add(0x%02x, 0x%02x): Z should be clear" % (a, b))

                # CY flag
                if (a + b) > 0xFF:
                    self.assertTrue(psw & Flags.CY,
                        "add(0x%02x, 0x%02x): CY should be set" % (a, b))
                else:
                    self.assertFalse(psw & Flags.CY,
                        "add(0x%02x, 0x%02x): CY should be clear" % (a, b))

                # AC flag (half-carry)
                if ((a & 0x0F) + (b & 0x0F)) > 0x0F:
                    self.assertTrue(psw & Flags.AC,
                        "add(0x%02x, 0x%02x): AC should be set" % (a, b))
                else:
                    self.assertFalse(psw & Flags.AC,
                        "add(0x%02x, 0x%02x): AC should be clear" % (a, b))

                # Preserved bits
                self.assertEqual(psw & PRESERVED_FLAGS, init_psw & PRESERVED_FLAGS,
                    "add(0x%02x, 0x%02x): preserved flags changed" % (a, b))


class TestOperationSub(unittest.TestCase):
    """Test _operation_sub for all 256x256 input combinations."""

    def test_all_256x256(self):
        proc, _ = _make_processor()
        for a in range(256):
            for b in range(256):
                init_psw = Flags.IE | Flags.ISP | Flags.RBS0 | Flags.RBS1
                proc.write_psw(init_psw)

                result = proc._operation_sub(a, b)
                psw = proc.read_psw()

                expected = (a - b) & 0xFF
                self.assertEqual(result, expected,
                    "sub(0x%02x, 0x%02x): result 0x%02x != expected 0x%02x" %
                    (a, b, result, expected))

                # Z flag
                if expected == 0:
                    self.assertTrue(psw & Flags.Z,
                        "sub(0x%02x, 0x%02x): Z should be set" % (a, b))
                else:
                    self.assertFalse(psw & Flags.Z,
                        "sub(0x%02x, 0x%02x): Z should be clear" % (a, b))

                # CY flag (borrow)
                if a < b:
                    self.assertTrue(psw & Flags.CY,
                        "sub(0x%02x, 0x%02x): CY should be set" % (a, b))
                else:
                    self.assertFalse(psw & Flags.CY,
                        "sub(0x%02x, 0x%02x): CY should be clear" % (a, b))

                # AC flag (half-borrow)
                if ((a & 0x0F) - (b & 0x0F)) & 0x10:
                    self.assertTrue(psw & Flags.AC,
                        "sub(0x%02x, 0x%02x): AC should be set" % (a, b))
                else:
                    self.assertFalse(psw & Flags.AC,
                        "sub(0x%02x, 0x%02x): AC should be clear" % (a, b))

                # Preserved bits
                self.assertEqual(psw & PRESERVED_FLAGS, init_psw & PRESERVED_FLAGS,
                    "sub(0x%02x, 0x%02x): preserved flags changed" % (a, b))


class TestOperationAddc(unittest.TestCase):
    """Test _operation_addc for all 256x256 input combinations with CY=0 and CY=1."""

    def test_all_256x256_cy0(self):
        proc, _ = _make_processor()
        for a in range(256):
            for b in range(256):
                init_psw = (Flags.IE | Flags.ISP | Flags.RBS0 | Flags.RBS1) & ~Flags.CY
                proc.write_psw(init_psw)

                result = proc._operation_addc(a, b)
                psw = proc.read_psw()

                total = a + b + 0  # CY=0
                expected = total & 0xFF

                self.assertEqual(result, expected,
                    "addc(0x%02x, 0x%02x, CY=0): result 0x%02x != expected 0x%02x" %
                    (a, b, result, expected))

                if expected == 0:
                    self.assertTrue(psw & Flags.Z,
                        "addc(0x%02x, 0x%02x, CY=0): Z should be set" % (a, b))
                else:
                    self.assertFalse(psw & Flags.Z,
                        "addc(0x%02x, 0x%02x, CY=0): Z should be clear" % (a, b))

                if total > 0xFF:
                    self.assertTrue(psw & Flags.CY,
                        "addc(0x%02x, 0x%02x, CY=0): CY should be set" % (a, b))
                else:
                    self.assertFalse(psw & Flags.CY,
                        "addc(0x%02x, 0x%02x, CY=0): CY should be clear" % (a, b))

                if ((a & 0x0F) + (b & 0x0F) + 0) > 0x0F:
                    self.assertTrue(psw & Flags.AC,
                        "addc(0x%02x, 0x%02x, CY=0): AC should be set" % (a, b))
                else:
                    self.assertFalse(psw & Flags.AC,
                        "addc(0x%02x, 0x%02x, CY=0): AC should be clear" % (a, b))

                self.assertEqual(psw & PRESERVED_FLAGS, init_psw & PRESERVED_FLAGS,
                    "addc(0x%02x, 0x%02x, CY=0): preserved flags changed" % (a, b))

    def test_all_256x256_cy1(self):
        proc, _ = _make_processor()
        for a in range(256):
            for b in range(256):
                init_psw = Flags.IE | Flags.ISP | Flags.RBS0 | Flags.RBS1 | Flags.CY
                proc.write_psw(init_psw)

                result = proc._operation_addc(a, b)
                psw = proc.read_psw()

                total = a + b + 1  # CY=1
                expected = total & 0xFF

                self.assertEqual(result, expected,
                    "addc(0x%02x, 0x%02x, CY=1): result 0x%02x != expected 0x%02x" %
                    (a, b, result, expected))

                if expected == 0:
                    self.assertTrue(psw & Flags.Z,
                        "addc(0x%02x, 0x%02x, CY=1): Z should be set" % (a, b))
                else:
                    self.assertFalse(psw & Flags.Z,
                        "addc(0x%02x, 0x%02x, CY=1): Z should be clear" % (a, b))

                if total > 0xFF:
                    self.assertTrue(psw & Flags.CY,
                        "addc(0x%02x, 0x%02x, CY=1): CY should be set" % (a, b))
                else:
                    self.assertFalse(psw & Flags.CY,
                        "addc(0x%02x, 0x%02x, CY=1): CY should be clear" % (a, b))

                if ((a & 0x0F) + (b & 0x0F) + 1) > 0x0F:
                    self.assertTrue(psw & Flags.AC,
                        "addc(0x%02x, 0x%02x, CY=1): AC should be set" % (a, b))
                else:
                    self.assertFalse(psw & Flags.AC,
                        "addc(0x%02x, 0x%02x, CY=1): AC should be clear" % (a, b))

                self.assertEqual(psw & PRESERVED_FLAGS, init_psw & PRESERVED_FLAGS,
                    "addc(0x%02x, 0x%02x, CY=1): preserved flags changed" % (a, b))


class TestOperationSubc(unittest.TestCase):
    """Test _operation_subc for all 256x256 input combinations with CY=0 and CY=1."""

    def test_all_256x256_cy0(self):
        proc, _ = _make_processor()
        for a in range(256):
            for b in range(256):
                init_psw = (Flags.IE | Flags.ISP | Flags.RBS0 | Flags.RBS1) & ~Flags.CY
                proc.write_psw(init_psw)

                result = proc._operation_subc(a, b)
                psw = proc.read_psw()

                diff = a - b - 0  # CY=0
                expected = diff & 0xFF

                self.assertEqual(result, expected,
                    "subc(0x%02x, 0x%02x, CY=0): result 0x%02x != expected 0x%02x" %
                    (a, b, result, expected))

                if expected == 0:
                    self.assertTrue(psw & Flags.Z,
                        "subc(0x%02x, 0x%02x, CY=0): Z should be set" % (a, b))
                else:
                    self.assertFalse(psw & Flags.Z,
                        "subc(0x%02x, 0x%02x, CY=0): Z should be clear" % (a, b))

                if diff < 0:
                    self.assertTrue(psw & Flags.CY,
                        "subc(0x%02x, 0x%02x, CY=0): CY should be set" % (a, b))
                else:
                    self.assertFalse(psw & Flags.CY,
                        "subc(0x%02x, 0x%02x, CY=0): CY should be clear" % (a, b))

                if ((a & 0x0F) - (b & 0x0F) - 0) & 0x10:
                    self.assertTrue(psw & Flags.AC,
                        "subc(0x%02x, 0x%02x, CY=0): AC should be set" % (a, b))
                else:
                    self.assertFalse(psw & Flags.AC,
                        "subc(0x%02x, 0x%02x, CY=0): AC should be clear" % (a, b))

                self.assertEqual(psw & PRESERVED_FLAGS, init_psw & PRESERVED_FLAGS,
                    "subc(0x%02x, 0x%02x, CY=0): preserved flags changed" % (a, b))

    def test_all_256x256_cy1(self):
        proc, _ = _make_processor()
        for a in range(256):
            for b in range(256):
                init_psw = Flags.IE | Flags.ISP | Flags.RBS0 | Flags.RBS1 | Flags.CY
                proc.write_psw(init_psw)

                result = proc._operation_subc(a, b)
                psw = proc.read_psw()

                diff = a - b - 1  # CY=1
                expected = diff & 0xFF

                self.assertEqual(result, expected,
                    "subc(0x%02x, 0x%02x, CY=1): result 0x%02x != expected 0x%02x" %
                    (a, b, result, expected))

                if expected == 0:
                    self.assertTrue(psw & Flags.Z,
                        "subc(0x%02x, 0x%02x, CY=1): Z should be set" % (a, b))
                else:
                    self.assertFalse(psw & Flags.Z,
                        "subc(0x%02x, 0x%02x, CY=1): Z should be clear" % (a, b))

                if diff < 0:
                    self.assertTrue(psw & Flags.CY,
                        "subc(0x%02x, 0x%02x, CY=1): CY should be set" % (a, b))
                else:
                    self.assertFalse(psw & Flags.CY,
                        "subc(0x%02x, 0x%02x, CY=1): CY should be clear" % (a, b))

                if ((a & 0x0F) - (b & 0x0F) - 1) & 0x10:
                    self.assertTrue(psw & Flags.AC,
                        "subc(0x%02x, 0x%02x, CY=1): AC should be set" % (a, b))
                else:
                    self.assertFalse(psw & Flags.AC,
                        "subc(0x%02x, 0x%02x, CY=1): AC should be clear" % (a, b))

                self.assertEqual(psw & PRESERVED_FLAGS, init_psw & PRESERVED_FLAGS,
                    "subc(0x%02x, 0x%02x, CY=1): preserved flags changed" % (a, b))


class TestOperationInc(unittest.TestCase):
    """Test _operation_inc for all 256 values. Inc does NOT modify CY."""

    def test_all_256(self):
        proc, _ = _make_processor()
        for val in range(256):
            for init_cy in (0, Flags.CY):
                init_psw = Flags.IE | Flags.ISP | init_cy
                proc.write_psw(init_psw)

                result = proc._operation_inc(val)
                psw = proc.read_psw()

                expected = (val + 1) & 0xFF
                self.assertEqual(result, expected,
                    "inc(0x%02x): result 0x%02x != expected 0x%02x" % (val, result, expected))

                # Z flag
                if expected == 0:
                    self.assertTrue(psw & Flags.Z,
                        "inc(0x%02x): Z should be set" % val)
                else:
                    self.assertFalse(psw & Flags.Z,
                        "inc(0x%02x): Z should be clear" % val)

                # AC flag
                if (val & 0x0F) == 0x0F:
                    self.assertTrue(psw & Flags.AC,
                        "inc(0x%02x): AC should be set" % val)
                else:
                    self.assertFalse(psw & Flags.AC,
                        "inc(0x%02x): AC should be clear" % val)

                # CY must NOT be modified
                self.assertEqual(psw & Flags.CY, init_cy,
                    "inc(0x%02x): CY was modified (init_cy=%d)" % (val, init_cy))


class TestOperationDec(unittest.TestCase):
    """Test _operation_dec for all 256 values. Dec does NOT modify CY."""

    def test_all_256(self):
        proc, _ = _make_processor()
        for val in range(256):
            for init_cy in (0, Flags.CY):
                init_psw = Flags.IE | Flags.ISP | init_cy
                proc.write_psw(init_psw)

                result = proc._operation_dec(val)
                psw = proc.read_psw()

                expected = (val - 1) & 0xFF
                self.assertEqual(result, expected,
                    "dec(0x%02x): result 0x%02x != expected 0x%02x" % (val, result, expected))

                # Z flag
                if expected == 0:
                    self.assertTrue(psw & Flags.Z,
                        "dec(0x%02x): Z should be set" % val)
                else:
                    self.assertFalse(psw & Flags.Z,
                        "dec(0x%02x): Z should be clear" % val)

                # AC flag (half-borrow)
                if (val & 0x0F) == 0x00:
                    self.assertTrue(psw & Flags.AC,
                        "dec(0x%02x): AC should be set" % val)
                else:
                    self.assertFalse(psw & Flags.AC,
                        "dec(0x%02x): AC should be clear" % val)

                # CY must NOT be modified
                self.assertEqual(psw & Flags.CY, init_cy,
                    "dec(0x%02x): CY was modified (init_cy=%d)" % (val, init_cy))


class TestOperationAddw(unittest.TestCase):
    """Test _operation_addw with boundary values and random sampling."""

    def test_boundary_values(self):
        proc, _ = _make_processor()
        boundary = [0x0000, 0x0001, 0x7FFF, 0x8000, 0xFFFE, 0xFFFF]
        for a in boundary:
            for b in range(0x10000):
                init_psw = Flags.IE | Flags.ISP
                proc.write_psw(init_psw)

                result = proc._operation_addw(a, b)
                psw = proc.read_psw()

                total = a + b
                expected = total & 0xFFFF
                self.assertEqual(result, expected,
                    "addw(0x%04x, 0x%04x): result 0x%04x != expected 0x%04x" %
                    (a, b, result, expected))

                if expected == 0:
                    self.assertTrue(psw & Flags.Z,
                        "addw(0x%04x, 0x%04x): Z should be set" % (a, b))
                else:
                    self.assertFalse(psw & Flags.Z,
                        "addw(0x%04x, 0x%04x): Z should be clear" % (a, b))

                if total > 0xFFFF:
                    self.assertTrue(psw & Flags.CY,
                        "addw(0x%04x, 0x%04x): CY should be set" % (a, b))
                else:
                    self.assertFalse(psw & Flags.CY,
                        "addw(0x%04x, 0x%04x): CY should be clear" % (a, b))

                self.assertEqual(psw & PRESERVED_FLAGS, init_psw & PRESERVED_FLAGS,
                    "addw(0x%04x, 0x%04x): preserved flags changed" % (a, b))

    def test_random_sampling(self):
        proc, _ = _make_processor()
        rng = random.Random(42)
        for _ in range(100000):
            a = rng.randint(0, 0xFFFF)
            b = rng.randint(0, 0xFFFF)
            init_psw = Flags.IE | Flags.ISP
            proc.write_psw(init_psw)

            result = proc._operation_addw(a, b)
            psw = proc.read_psw()

            total = a + b
            expected = total & 0xFFFF
            self.assertEqual(result, expected)

            if expected == 0:
                self.assertTrue(psw & Flags.Z)
            else:
                self.assertFalse(psw & Flags.Z)

            if total > 0xFFFF:
                self.assertTrue(psw & Flags.CY)
            else:
                self.assertFalse(psw & Flags.CY)


class TestOperationSubw(unittest.TestCase):
    """Test _operation_subw with boundary values and random sampling."""

    def test_boundary_values(self):
        proc, _ = _make_processor()
        boundary = [0x0000, 0x0001, 0x7FFF, 0x8000, 0xFFFE, 0xFFFF]
        for a in boundary:
            for b in range(0x10000):
                init_psw = Flags.IE | Flags.ISP
                proc.write_psw(init_psw)

                result = proc._operation_subw(a, b)
                psw = proc.read_psw()

                diff = a - b
                expected = diff & 0xFFFF
                self.assertEqual(result, expected,
                    "subw(0x%04x, 0x%04x): result 0x%04x != expected 0x%04x" %
                    (a, b, result, expected))

                if expected == 0:
                    self.assertTrue(psw & Flags.Z,
                        "subw(0x%04x, 0x%04x): Z should be set" % (a, b))
                else:
                    self.assertFalse(psw & Flags.Z,
                        "subw(0x%04x, 0x%04x): Z should be clear" % (a, b))

                if diff < 0:
                    self.assertTrue(psw & Flags.CY,
                        "subw(0x%04x, 0x%04x): CY should be set" % (a, b))
                else:
                    self.assertFalse(psw & Flags.CY,
                        "subw(0x%04x, 0x%04x): CY should be clear" % (a, b))

                self.assertEqual(psw & PRESERVED_FLAGS, init_psw & PRESERVED_FLAGS,
                    "subw(0x%04x, 0x%04x): preserved flags changed" % (a, b))

    def test_random_sampling(self):
        proc, _ = _make_processor()
        rng = random.Random(42)
        for _ in range(100000):
            a = rng.randint(0, 0xFFFF)
            b = rng.randint(0, 0xFFFF)
            init_psw = Flags.IE | Flags.ISP
            proc.write_psw(init_psw)

            result = proc._operation_subw(a, b)
            psw = proc.read_psw()

            diff = a - b
            expected = diff & 0xFFFF
            self.assertEqual(result, expected)

            if expected == 0:
                self.assertTrue(psw & Flags.Z)
            else:
                self.assertFalse(psw & Flags.Z)

            if diff < 0:
                self.assertTrue(psw & Flags.CY)
            else:
                self.assertFalse(psw & Flags.CY)


class TestOperationAnd(unittest.TestCase):
    """Test _operation_and for all 256x256 combinations."""

    def test_all_256x256(self):
        proc, _ = _make_processor()
        for a in range(256):
            for b in range(256):
                # Set CY and AC to verify they are NOT modified
                init_psw = Flags.IE | Flags.ISP | Flags.CY | Flags.AC
                proc.write_psw(init_psw)

                result = proc._operation_and(a, b)
                psw = proc.read_psw()

                expected = a & b
                self.assertEqual(result, expected,
                    "and(0x%02x, 0x%02x): result 0x%02x != expected 0x%02x" %
                    (a, b, result, expected))

                if expected == 0:
                    self.assertTrue(psw & Flags.Z,
                        "and(0x%02x, 0x%02x): Z should be set" % (a, b))
                else:
                    self.assertFalse(psw & Flags.Z,
                        "and(0x%02x, 0x%02x): Z should be clear" % (a, b))

                # CY and AC must NOT be modified by AND
                self.assertEqual(psw & Flags.CY, Flags.CY,
                    "and(0x%02x, 0x%02x): CY was modified" % (a, b))
                self.assertEqual(psw & Flags.AC, Flags.AC,
                    "and(0x%02x, 0x%02x): AC was modified" % (a, b))


class TestOperationOr(unittest.TestCase):
    """Test _operation_or for all 256x256 combinations."""

    def test_all_256x256(self):
        proc, _ = _make_processor()
        for a in range(256):
            for b in range(256):
                init_psw = Flags.IE | Flags.ISP | Flags.CY | Flags.AC
                proc.write_psw(init_psw)

                result = proc._operation_or(a, b)
                psw = proc.read_psw()

                expected = a | b
                self.assertEqual(result, expected,
                    "or(0x%02x, 0x%02x): result 0x%02x != expected 0x%02x" %
                    (a, b, result, expected))

                if expected == 0:
                    self.assertTrue(psw & Flags.Z,
                        "or(0x%02x, 0x%02x): Z should be set" % (a, b))
                else:
                    self.assertFalse(psw & Flags.Z,
                        "or(0x%02x, 0x%02x): Z should be clear" % (a, b))

                # CY and AC must NOT be modified by OR
                self.assertEqual(psw & Flags.CY, Flags.CY,
                    "or(0x%02x, 0x%02x): CY was modified" % (a, b))
                self.assertEqual(psw & Flags.AC, Flags.AC,
                    "or(0x%02x, 0x%02x): AC was modified" % (a, b))


class TestOperationXor(unittest.TestCase):
    """Test _operation_xor for all 256x256 combinations."""

    def test_all_256x256(self):
        proc, _ = _make_processor()
        for a in range(256):
            for b in range(256):
                init_psw = Flags.IE | Flags.ISP | Flags.CY | Flags.AC
                proc.write_psw(init_psw)

                result = proc._operation_xor(a, b)
                psw = proc.read_psw()

                expected = a ^ b
                self.assertEqual(result, expected,
                    "xor(0x%02x, 0x%02x): result 0x%02x != expected 0x%02x" %
                    (a, b, result, expected))

                if expected == 0:
                    self.assertTrue(psw & Flags.Z,
                        "xor(0x%02x, 0x%02x): Z should be set" % (a, b))
                else:
                    self.assertFalse(psw & Flags.Z,
                        "xor(0x%02x, 0x%02x): Z should be clear" % (a, b))

                # CY and AC must NOT be modified by XOR
                self.assertEqual(psw & Flags.CY, Flags.CY,
                    "xor(0x%02x, 0x%02x): CY was modified" % (a, b))
                self.assertEqual(psw & Flags.AC, Flags.AC,
                    "xor(0x%02x, 0x%02x): AC was modified" % (a, b))


class TestMovRegSideEffects(unittest.TestCase):
    """MOV A,r and MOV r,A: only destination register changes, no flag changes."""

    def _setup_proc(self):
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        # Set distinct values in all registers
        proc.write_gp_reg(Registers.X, 0x11)
        proc.write_gp_reg(Registers.A, 0x22)
        proc.write_gp_reg(Registers.C, 0x33)
        proc.write_gp_reg(Registers.B, 0x44)
        proc.write_gp_reg(Registers.E, 0x55)
        proc.write_gp_reg(Registers.D, 0x66)
        proc.write_gp_reg(Registers.L, 0x77)
        proc.write_gp_reg(Registers.H, 0x88)
        proc.write_psw(Flags.CY | Flags.AC | Flags.Z)
        return proc

    def test_mov_a_r(self):
        """MOV A,r (0x60-0x67 except 0x61): only A changes, no flag changes."""
        reg_opcodes = {
            Registers.X: 0x60, Registers.C: 0x62, Registers.B: 0x63,
            Registers.E: 0x64, Registers.D: 0x65, Registers.L: 0x66,
            Registers.H: 0x67,
        }
        for reg, opcode in reg_opcodes.items():
            proc = self._setup_proc()
            before = _snapshot(proc)
            proc.write_memory_bytes(0, [opcode])
            proc.step()
            after = _snapshot(proc)

            # Only A should change (to the value of the source register)
            self.assertEqual(after['regs'][Registers.A], before['regs'][reg],
                "MOV A,r%d: A should have value from r%d" % (reg, reg))

            # No flag changes at all
            _assert_unchanged(self, before, after,
                              changed_regs={Registers.A},
                              changed_psw_bits=0)

    def test_mov_r_a(self):
        """MOV r,A (0x70-0x77 except 0x71): only target register changes, no flags."""
        reg_opcodes = {
            Registers.X: 0x70, Registers.C: 0x72, Registers.B: 0x73,
            Registers.E: 0x74, Registers.D: 0x75, Registers.L: 0x76,
            Registers.H: 0x77,
        }
        for reg, opcode in reg_opcodes.items():
            proc = self._setup_proc()
            before = _snapshot(proc)
            proc.write_memory_bytes(0, [opcode])
            proc.step()
            after = _snapshot(proc)

            self.assertEqual(after['regs'][reg], before['regs'][Registers.A],
                "MOV r%d,A: r%d should have A's value" % (reg, reg))

            _assert_unchanged(self, before, after,
                              changed_regs={reg},
                              changed_psw_bits=0)


class TestAluImmSideEffects(unittest.TestCase):
    """ALU A,#imm instructions: only A and PSW arithmetic flags change."""

    def _run_alu_imm(self, opcode, imm, changes_a=True):
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_gp_reg(Registers.X, 0x11)
        proc.write_gp_reg(Registers.A, 0x50)
        proc.write_gp_reg(Registers.C, 0x33)
        proc.write_gp_reg(Registers.B, 0x44)
        proc.write_gp_reg(Registers.E, 0x55)
        proc.write_gp_reg(Registers.D, 0x66)
        proc.write_gp_reg(Registers.L, 0x77)
        proc.write_gp_reg(Registers.H, 0x88)
        proc.write_psw(Flags.IE | Flags.ISP)
        proc.write_memory_bytes(0, [opcode, imm])

        before = _snapshot(proc)
        proc.step()
        after = _snapshot(proc)

        changed_regs = {Registers.A} if changes_a else set()
        _assert_unchanged(self, before, after,
                          changed_regs=changed_regs,
                          changed_psw_bits=ARITHMETIC_FLAGS)

    def test_add_a_imm(self):
        self._run_alu_imm(0x0d, 0x30)

    def test_sub_a_imm(self):
        self._run_alu_imm(0x1d, 0x30)

    def test_addc_a_imm(self):
        self._run_alu_imm(0x2d, 0x30)

    def test_subc_a_imm(self):
        self._run_alu_imm(0x3d, 0x30)

    def test_cmp_a_imm(self):
        """CMP does NOT change A, only flags."""
        self._run_alu_imm(0x4d, 0x30, changes_a=False)

    def test_and_a_imm(self):
        self._run_alu_imm(0x5d, 0x30)

    def test_or_a_imm(self):
        self._run_alu_imm(0x6d, 0x30)

    def test_xor_a_imm(self):
        self._run_alu_imm(0x7d, 0x30)


class TestIncDecRegSideEffects(unittest.TestCase):
    """INC/DEC r: only target register and Z/AC change. CY is NOT modified."""

    def test_inc_r_preserves_cy(self):
        """INC r must not modify CY flag."""
        for reg in range(8):
            for init_cy in (0, Flags.CY):
                proc, _ = _make_processor()
                proc.write_sp(0xFE00)
                for r in range(8):
                    proc.write_gp_reg(r, 0x10 + r)
                proc.write_psw(Flags.IE | init_cy)

                opcode = 0x40 + reg  # INC reg
                proc.write_memory_bytes(0, [opcode])

                before = _snapshot(proc)
                proc.step()
                after = _snapshot(proc)

                # CY must be preserved
                self.assertEqual(after['psw'] & Flags.CY, init_cy,
                    "INC r%d: CY was modified (init_cy=%d)" % (reg, init_cy))

                # Only target register and Z/AC should change
                _assert_unchanged(self, before, after,
                                  changed_regs={reg},
                                  changed_psw_bits=Flags.Z | Flags.AC)

    def test_dec_r_preserves_cy(self):
        """DEC r must not modify CY flag."""
        for reg in range(8):
            for init_cy in (0, Flags.CY):
                proc, _ = _make_processor()
                proc.write_sp(0xFE00)
                for r in range(8):
                    proc.write_gp_reg(r, 0x10 + r)
                proc.write_psw(Flags.IE | init_cy)

                opcode = 0x50 + reg  # DEC reg
                proc.write_memory_bytes(0, [opcode])

                before = _snapshot(proc)
                proc.step()
                after = _snapshot(proc)

                # CY must be preserved
                self.assertEqual(after['psw'] & Flags.CY, init_cy,
                    "DEC r%d: CY was modified (init_cy=%d)" % (reg, init_cy))

                _assert_unchanged(self, before, after,
                                  changed_regs={reg},
                                  changed_psw_bits=Flags.Z | Flags.AC)

    def test_inc_all_values_via_instruction(self):
        """Run INC A instruction for all 256 input values."""
        for val in range(256):
            for init_cy in (0, Flags.CY):
                proc, _ = _make_processor()
                proc.write_sp(0xFE00)
                proc.write_gp_reg(Registers.A, val)
                proc.write_psw(init_cy)
                proc.write_memory_bytes(0, [0x41])  # INC A

                proc.step()

                expected = (val + 1) & 0xFF
                self.assertEqual(proc.read_gp_reg(Registers.A), expected)
                self.assertEqual(proc.read_psw() & Flags.CY, init_cy,
                    "INC A: CY modified for input 0x%02x" % val)

    def test_dec_all_values_via_instruction(self):
        """Run DEC A instruction for all 256 input values."""
        for val in range(256):
            for init_cy in (0, Flags.CY):
                proc, _ = _make_processor()
                proc.write_sp(0xFE00)
                proc.write_gp_reg(Registers.A, val)
                proc.write_psw(init_cy)
                proc.write_memory_bytes(0, [0x51])  # DEC A

                proc.step()

                expected = (val - 1) & 0xFF
                self.assertEqual(proc.read_gp_reg(Registers.A), expected)
                self.assertEqual(proc.read_psw() & Flags.CY, init_cy,
                    "DEC A: CY modified for input 0x%02x" % val)


class TestIncwDecwSideEffects(unittest.TestCase):
    """INCW/DECW rp: only target pair changes, NO flag changes at all."""

    def test_incw_no_flag_changes(self):
        """INCW rp must not modify any flags."""
        rp_opcodes = {
            RegisterPairs.AX: 0x80,
            RegisterPairs.BC: 0x82,
            RegisterPairs.DE: 0x84,
            RegisterPairs.HL: 0x86,
        }
        for rp, opcode in rp_opcodes.items():
            for init_psw_val in (0x00, Flags.CY, Flags.Z, Flags.AC, Flags.CY | Flags.Z | Flags.AC):
                proc, _ = _make_processor()
                proc.write_sp(0xFE00)
                proc.write_gp_regpair(RegisterPairs.AX, 0x1122)
                proc.write_gp_regpair(RegisterPairs.BC, 0x3344)
                proc.write_gp_regpair(RegisterPairs.DE, 0x5566)
                proc.write_gp_regpair(RegisterPairs.HL, 0x7788)
                proc.write_psw(init_psw_val)

                proc.write_memory_bytes(0, [opcode])
                before = _snapshot(proc)
                proc.step()
                after = _snapshot(proc)

                # No PSW bits should change at all
                self.assertEqual(before['psw'], after['psw'],
                    "INCW rp%d: PSW changed from 0x%02x to 0x%02x" %
                    (rp, before['psw'], after['psw']))

                # Only target pair registers should change
                changed = {rp * 2, rp * 2 + 1}
                _assert_unchanged(self, before, after,
                                  changed_regs=changed,
                                  changed_psw_bits=0)

    def test_decw_no_flag_changes(self):
        """DECW rp must not modify any flags."""
        rp_opcodes = {
            RegisterPairs.AX: 0x90,
            RegisterPairs.BC: 0x92,
            RegisterPairs.DE: 0x94,
            RegisterPairs.HL: 0x96,
        }
        for rp, opcode in rp_opcodes.items():
            for init_psw_val in (0x00, Flags.CY, Flags.Z, Flags.AC, Flags.CY | Flags.Z | Flags.AC):
                proc, _ = _make_processor()
                proc.write_sp(0xFE00)
                proc.write_gp_regpair(RegisterPairs.AX, 0x1122)
                proc.write_gp_regpair(RegisterPairs.BC, 0x3344)
                proc.write_gp_regpair(RegisterPairs.DE, 0x5566)
                proc.write_gp_regpair(RegisterPairs.HL, 0x7788)
                proc.write_psw(init_psw_val)

                proc.write_memory_bytes(0, [opcode])
                before = _snapshot(proc)
                proc.step()
                after = _snapshot(proc)

                self.assertEqual(before['psw'], after['psw'],
                    "DECW rp%d: PSW changed from 0x%02x to 0x%02x" %
                    (rp, before['psw'], after['psw']))

                changed = {rp * 2, rp * 2 + 1}
                _assert_unchanged(self, before, after,
                                  changed_regs=changed,
                                  changed_psw_bits=0)

    def test_incw_wraps(self):
        """INCW 0xFFFF wraps to 0x0000."""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_gp_regpair(RegisterPairs.AX, 0xFFFF)
        proc.write_memory_bytes(0, [0x80])  # INCW AX
        proc.step()
        self.assertEqual(proc.read_gp_regpair(RegisterPairs.AX), 0x0000)

    def test_decw_wraps(self):
        """DECW 0x0000 wraps to 0xFFFF."""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_gp_regpair(RegisterPairs.AX, 0x0000)
        proc.write_memory_bytes(0, [0x90])  # DECW AX
        proc.step()
        self.assertEqual(proc.read_gp_regpair(RegisterPairs.AX), 0xFFFF)


class TestMovwRpImmSideEffects(unittest.TestCase):
    """MOVW rp,#imm16: only target pair changes, no flag changes."""

    def test_movw_rp_imm(self):
        rp_opcodes = {
            RegisterPairs.AX: 0x10,
            RegisterPairs.BC: 0x12,
            RegisterPairs.DE: 0x14,
            RegisterPairs.HL: 0x16,
        }
        for rp, opcode in rp_opcodes.items():
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_gp_regpair(RegisterPairs.AX, 0x1122)
            proc.write_gp_regpair(RegisterPairs.BC, 0x3344)
            proc.write_gp_regpair(RegisterPairs.DE, 0x5566)
            proc.write_gp_regpair(RegisterPairs.HL, 0x7788)
            proc.write_psw(Flags.CY | Flags.Z | Flags.AC | Flags.IE)

            proc.write_memory_bytes(0, [opcode, 0xCD, 0xAB])  # MOVW rp,#0xABCD
            before = _snapshot(proc)
            proc.step()
            after = _snapshot(proc)

            # No PSW changes
            self.assertEqual(before['psw'], after['psw'])

            # Target pair loaded correctly
            self.assertEqual(proc.read_gp_regpair(rp), 0xABCD)

            changed = {rp * 2, rp * 2 + 1}
            _assert_unchanged(self, before, after,
                              changed_regs=changed,
                              changed_psw_bits=0)


class TestXchSideEffects(unittest.TestCase):
    """XCH A,r: values properly swapped, no flag changes."""

    def test_xch_a_r(self):
        reg_opcodes = {
            Registers.X: 0x30, Registers.C: 0x32, Registers.B: 0x33,
            Registers.E: 0x34, Registers.D: 0x35, Registers.L: 0x36,
            Registers.H: 0x37,
        }
        for reg, opcode in reg_opcodes.items():
            for a_val in (0x00, 0x55, 0xFF):
                for r_val in (0x00, 0xAA, 0xFF):
                    proc, _ = _make_processor()
                    proc.write_sp(0xFE00)
                    proc.write_gp_reg(Registers.A, a_val)
                    proc.write_gp_reg(reg, r_val)
                    proc.write_psw(Flags.CY | Flags.Z | Flags.AC | Flags.IE)

                    proc.write_memory_bytes(0, [opcode])
                    before = _snapshot(proc)
                    proc.step()
                    after = _snapshot(proc)

                    self.assertEqual(after['regs'][Registers.A], r_val)
                    self.assertEqual(after['regs'][reg], a_val)

                    # No PSW changes
                    self.assertEqual(before['psw'], after['psw'])

                    _assert_unchanged(self, before, after,
                                      changed_regs={Registers.A, reg},
                                      changed_psw_bits=0)


class TestCyManipSideEffects(unittest.TestCase):
    """SET1 CY, CLR1 CY, NOT1 CY: only CY flag changes."""

    def test_set1_cy(self):
        for init_psw_val in (0x00, Flags.Z | Flags.AC, Flags.CY | Flags.Z):
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_psw(init_psw_val)
            proc.write_memory_bytes(0, [0x20])  # SET1 CY

            before = _snapshot(proc)
            proc.step()
            after = _snapshot(proc)

            self.assertTrue(after['psw'] & Flags.CY)
            _assert_unchanged(self, before, after,
                              changed_regs=set(),
                              changed_psw_bits=Flags.CY)

    def test_clr1_cy(self):
        for init_psw_val in (0x00, Flags.CY | Flags.Z, Flags.CY | Flags.AC):
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_psw(init_psw_val)
            proc.write_memory_bytes(0, [0x21])  # CLR1 CY

            before = _snapshot(proc)
            proc.step()
            after = _snapshot(proc)

            self.assertFalse(after['psw'] & Flags.CY)
            _assert_unchanged(self, before, after,
                              changed_regs=set(),
                              changed_psw_bits=Flags.CY)

    def test_not1_cy(self):
        for init_cy in (0, Flags.CY):
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_psw(Flags.Z | Flags.AC | init_cy)
            proc.write_memory_bytes(0, [0x01])  # NOT1 CY

            before = _snapshot(proc)
            proc.step()
            after = _snapshot(proc)

            expected_cy = Flags.CY if init_cy == 0 else 0
            self.assertEqual(after['psw'] & Flags.CY, expected_cy)
            _assert_unchanged(self, before, after,
                              changed_regs=set(),
                              changed_psw_bits=Flags.CY)


class TestPushPopSideEffects(unittest.TestCase):
    """PUSH/POP: verify SP changes and memory written/read correctly."""

    def test_push_rp(self):
        """PUSH rp: SP decremented by 2, value written to stack."""
        rp_opcodes = {
            RegisterPairs.AX: 0xB1,
            RegisterPairs.BC: 0xB3,
            RegisterPairs.DE: 0xB5,
            RegisterPairs.HL: 0xB7,
        }
        for rp, opcode in rp_opcodes.items():
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_gp_regpair(RegisterPairs.AX, 0x1122)
            proc.write_gp_regpair(RegisterPairs.BC, 0x3344)
            proc.write_gp_regpair(RegisterPairs.DE, 0x5566)
            proc.write_gp_regpair(RegisterPairs.HL, 0x7788)
            proc.write_psw(Flags.CY | Flags.Z)

            val = proc.read_gp_regpair(rp)
            proc.write_memory_bytes(0, [opcode])
            before = _snapshot(proc)
            proc.step()
            after = _snapshot(proc)

            # SP should decrease by 2
            self.assertEqual(after['sp'], before['sp'] - 2)

            # Value on stack (little-endian)
            self.assertEqual(proc.read_memory(before['sp'] - 2), val & 0xFF)
            self.assertEqual(proc.read_memory(before['sp'] - 1), val >> 8)

            # No register or PSW changes
            _assert_unchanged(self, before, after,
                              changed_regs=set(),
                              changed_sp=True,
                              changed_psw_bits=0)

    def test_pop_rp(self):
        """POP rp: SP incremented by 2, value read from stack."""
        rp_opcodes = {
            RegisterPairs.AX: 0xB0,
            RegisterPairs.BC: 0xB2,
            RegisterPairs.DE: 0xB4,
            RegisterPairs.HL: 0xB6,
        }
        for rp, opcode in rp_opcodes.items():
            proc, _ = _make_processor()
            sp = 0xFDFE
            proc.write_sp(sp)
            # Write known value on stack
            proc.write_memory(sp, 0xCD)      # low byte
            proc.write_memory(sp + 1, 0xAB)  # high byte
            proc.write_gp_regpair(RegisterPairs.AX, 0x0000)
            proc.write_gp_regpair(RegisterPairs.BC, 0x0000)
            proc.write_gp_regpair(RegisterPairs.DE, 0x0000)
            proc.write_gp_regpair(RegisterPairs.HL, 0x0000)
            proc.write_psw(Flags.CY | Flags.Z)

            proc.write_memory_bytes(0, [opcode])
            before = _snapshot(proc)
            proc.step()
            after = _snapshot(proc)

            # SP should increase by 2
            self.assertEqual(after['sp'], before['sp'] + 2)

            # Register pair loaded
            self.assertEqual(proc.read_gp_regpair(rp), 0xABCD)

            changed = {rp * 2, rp * 2 + 1}
            _assert_unchanged(self, before, after,
                              changed_regs=changed,
                              changed_sp=True,
                              changed_psw_bits=0)

    def test_push_psw_pop_psw(self):
        """PUSH PSW / POP PSW round-trip."""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        test_psw = Flags.CY | Flags.Z | Flags.AC | Flags.IE
        proc.write_psw(test_psw)

        # PUSH PSW (0x22)
        proc.write_memory_bytes(0, [0x22])
        proc.step()
        self.assertEqual(proc.read_sp(), 0xFDFF)

        # Corrupt PSW
        proc.write_psw(0x00)

        # POP PSW (0x23)
        proc.write_memory_bytes(1, [0x23])
        proc.step()
        self.assertEqual(proc.read_sp(), 0xFE00)
        self.assertEqual(proc.read_psw(), test_psw & PSW_MASK)


class TestRotateExhaustive(unittest.TestCase):
    """Test all 512 combinations (256 A values x 2 CY states) for each rotate."""

    def test_ror_all_512(self):
        """ROR A,1: bit 0 -> CY, old bit 0 -> bit 7. No through-carry."""
        for a_val in range(256):
            for init_cy in (0, Flags.CY):
                proc, _ = _make_processor()
                proc.write_sp(0xFE00)
                proc.write_gp_reg(Registers.A, a_val)
                proc.write_psw(Flags.IE | Flags.Z | Flags.AC | init_cy)
                proc.write_memory_bytes(0, [0x24])  # ROR A,1

                proc.step()

                bit0 = a_val & 1
                expected = (a_val >> 1) | (bit0 << 7)
                expected_cy = Flags.CY if bit0 else 0

                self.assertEqual(proc.read_gp_reg(Registers.A), expected,
                    "ROR(0x%02x, CY=%d): got 0x%02x expected 0x%02x" %
                    (a_val, init_cy, proc.read_gp_reg(Registers.A), expected))
                self.assertEqual(proc.read_psw() & Flags.CY, expected_cy,
                    "ROR(0x%02x, CY=%d): CY wrong" % (a_val, init_cy))

                # Z and AC must NOT be modified by rotates
                self.assertEqual(proc.read_psw() & Flags.Z, Flags.Z,
                    "ROR(0x%02x, CY=%d): Z was modified" % (a_val, init_cy))
                self.assertEqual(proc.read_psw() & Flags.AC, Flags.AC,
                    "ROR(0x%02x, CY=%d): AC was modified" % (a_val, init_cy))

    def test_rorc_all_512(self):
        """RORC A,1: bit 0 -> CY, old CY -> bit 7. Through-carry."""
        for a_val in range(256):
            for init_cy in (0, Flags.CY):
                proc, _ = _make_processor()
                proc.write_sp(0xFE00)
                proc.write_gp_reg(Registers.A, a_val)
                proc.write_psw(Flags.IE | Flags.Z | Flags.AC | init_cy)
                proc.write_memory_bytes(0, [0x25])  # RORC A,1

                proc.step()

                old_cy = 1 if init_cy else 0
                bit0 = a_val & 1
                expected = (a_val >> 1) | (old_cy << 7)
                expected_cy = Flags.CY if bit0 else 0

                self.assertEqual(proc.read_gp_reg(Registers.A), expected,
                    "RORC(0x%02x, CY=%d): got 0x%02x expected 0x%02x" %
                    (a_val, init_cy, proc.read_gp_reg(Registers.A), expected))
                self.assertEqual(proc.read_psw() & Flags.CY, expected_cy,
                    "RORC(0x%02x, CY=%d): CY wrong" % (a_val, init_cy))

                self.assertEqual(proc.read_psw() & Flags.Z, Flags.Z)
                self.assertEqual(proc.read_psw() & Flags.AC, Flags.AC)

    def test_rol_all_512(self):
        """ROL A,1: bit 7 -> CY, old bit 7 -> bit 0. No through-carry."""
        for a_val in range(256):
            for init_cy in (0, Flags.CY):
                proc, _ = _make_processor()
                proc.write_sp(0xFE00)
                proc.write_gp_reg(Registers.A, a_val)
                proc.write_psw(Flags.IE | Flags.Z | Flags.AC | init_cy)
                proc.write_memory_bytes(0, [0x26])  # ROL A,1

                proc.step()

                bit7 = (a_val >> 7) & 1
                expected = ((a_val << 1) | bit7) & 0xFF
                expected_cy = Flags.CY if bit7 else 0

                self.assertEqual(proc.read_gp_reg(Registers.A), expected,
                    "ROL(0x%02x, CY=%d): got 0x%02x expected 0x%02x" %
                    (a_val, init_cy, proc.read_gp_reg(Registers.A), expected))
                self.assertEqual(proc.read_psw() & Flags.CY, expected_cy,
                    "ROL(0x%02x, CY=%d): CY wrong" % (a_val, init_cy))

                self.assertEqual(proc.read_psw() & Flags.Z, Flags.Z)
                self.assertEqual(proc.read_psw() & Flags.AC, Flags.AC)

    def test_rolc_all_512(self):
        """ROLC A,1: bit 7 -> CY, old CY -> bit 0. Through-carry."""
        for a_val in range(256):
            for init_cy in (0, Flags.CY):
                proc, _ = _make_processor()
                proc.write_sp(0xFE00)
                proc.write_gp_reg(Registers.A, a_val)
                proc.write_psw(Flags.IE | Flags.Z | Flags.AC | init_cy)
                proc.write_memory_bytes(0, [0x27])  # ROLC A,1

                proc.step()

                old_cy = 1 if init_cy else 0
                bit7 = (a_val >> 7) & 1
                expected = ((a_val << 1) | old_cy) & 0xFF
                expected_cy = Flags.CY if bit7 else 0

                self.assertEqual(proc.read_gp_reg(Registers.A), expected,
                    "ROLC(0x%02x, CY=%d): got 0x%02x expected 0x%02x" %
                    (a_val, init_cy, proc.read_gp_reg(Registers.A), expected))
                self.assertEqual(proc.read_psw() & Flags.CY, expected_cy,
                    "ROLC(0x%02x, CY=%d): CY wrong" % (a_val, init_cy))

                self.assertEqual(proc.read_psw() & Flags.Z, Flags.Z)
                self.assertEqual(proc.read_psw() & Flags.AC, Flags.AC)


class TestRotateSideEffects(unittest.TestCase):
    """Verify rotates only modify A and CY, nothing else."""

    def test_ror_side_effects(self):
        for opcode in (0x24, 0x25, 0x26, 0x27):
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_gp_reg(Registers.X, 0x11)
            proc.write_gp_reg(Registers.A, 0x81)
            proc.write_gp_reg(Registers.C, 0x33)
            proc.write_gp_reg(Registers.B, 0x44)
            proc.write_gp_reg(Registers.E, 0x55)
            proc.write_gp_reg(Registers.D, 0x66)
            proc.write_gp_reg(Registers.L, 0x77)
            proc.write_gp_reg(Registers.H, 0x88)
            proc.write_psw(Flags.IE | Flags.ISP | Flags.Z | Flags.AC)

            proc.write_memory_bytes(0, [opcode])
            before = _snapshot(proc)
            proc.step()
            after = _snapshot(proc)

            # Only A and CY should change
            _assert_unchanged(self, before, after,
                              changed_regs={Registers.A},
                              changed_psw_bits=Flags.CY)


class TestFlagPreservation(unittest.TestCase):
    """Verify that instructions preserve flags they should not modify."""

    def test_inc_preserves_cy_all_psw(self):
        """INC r preserves CY regardless of PSW state."""
        # Test with all valid PSW combinations (bit 2 masked out)
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        for psw_val in range(256):
            psw_val &= PSW_MASK
            # Skip RBS bits to avoid register bank switching issues
            if psw_val & (Flags.RBS0 | Flags.RBS1):
                continue
            proc.write_psw(psw_val)
            proc.write_gp_reg(Registers.A, 0x42)
            proc.write_memory_bytes(0, [0x41])  # INC A
            proc.pc = 0
            proc.step()
            self.assertEqual(proc.read_psw() & Flags.CY, psw_val & Flags.CY,
                "INC A with PSW=0x%02x: CY was modified" % psw_val)

    def test_dec_preserves_cy_all_psw(self):
        """DEC r preserves CY regardless of PSW state."""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        for psw_val in range(256):
            psw_val &= PSW_MASK
            if psw_val & (Flags.RBS0 | Flags.RBS1):
                continue
            proc.write_psw(psw_val)
            proc.write_gp_reg(Registers.A, 0x42)
            proc.write_memory_bytes(0, [0x51])  # DEC A
            proc.pc = 0
            proc.step()
            self.assertEqual(proc.read_psw() & Flags.CY, psw_val & Flags.CY,
                "DEC A with PSW=0x%02x: CY was modified" % psw_val)

    def test_or_preserves_cy_ac(self):
        """OR A,#imm preserves CY and AC."""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        for cy in (0, Flags.CY):
            for ac in (0, Flags.AC):
                proc.write_psw(cy | ac)
                proc.write_gp_reg(Registers.A, 0x42)
                proc.write_memory_bytes(0, [0x6d, 0x11])  # OR A,#0x11
                proc.pc = 0
                proc.step()
                self.assertEqual(proc.read_psw() & Flags.CY, cy,
                    "OR A,#imm: CY modified (init CY=%d AC=%d)" % (cy, ac))
                self.assertEqual(proc.read_psw() & Flags.AC, ac,
                    "OR A,#imm: AC modified (init CY=%d AC=%d)" % (cy, ac))

    def test_and_preserves_cy_ac(self):
        """AND A,#imm preserves CY and AC."""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        for cy in (0, Flags.CY):
            for ac in (0, Flags.AC):
                proc.write_psw(cy | ac)
                proc.write_gp_reg(Registers.A, 0xFF)
                proc.write_memory_bytes(0, [0x5d, 0x42])  # AND A,#0x42
                proc.pc = 0
                proc.step()
                self.assertEqual(proc.read_psw() & Flags.CY, cy)
                self.assertEqual(proc.read_psw() & Flags.AC, ac)

    def test_xor_preserves_cy_ac(self):
        """XOR A,#imm preserves CY and AC."""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        for cy in (0, Flags.CY):
            for ac in (0, Flags.AC):
                proc.write_psw(cy | ac)
                proc.write_gp_reg(Registers.A, 0xFF)
                proc.write_memory_bytes(0, [0x7d, 0x42])  # XOR A,#0x42
                proc.pc = 0
                proc.step()
                self.assertEqual(proc.read_psw() & Flags.CY, cy)
                self.assertEqual(proc.read_psw() & Flags.AC, ac)

    def test_mov_preserves_all_flags(self):
        """MOV A,r preserves all PSW flags."""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        for psw_val in range(256):
            psw_val &= PSW_MASK
            if psw_val & (Flags.RBS0 | Flags.RBS1):
                continue
            proc.write_psw(psw_val)
            proc.write_gp_reg(Registers.X, 0x42)
            proc.write_memory_bytes(0, [0x60])  # MOV A,X
            proc.pc = 0
            proc.step()
            self.assertEqual(proc.read_psw(), psw_val,
                "MOV A,X with PSW=0x%02x: PSW changed to 0x%02x" %
                (psw_val, proc.read_psw()))

    def test_movw_preserves_all_flags(self):
        """MOVW rp,#imm preserves all PSW flags."""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        for psw_val in range(256):
            psw_val &= PSW_MASK
            if psw_val & (Flags.RBS0 | Flags.RBS1):
                continue
            proc.write_psw(psw_val)
            proc.write_memory_bytes(0, [0x12, 0xCD, 0xAB])  # MOVW BC,#0xABCD
            proc.pc = 0
            proc.step()
            self.assertEqual(proc.read_psw(), psw_val,
                "MOVW BC,#imm with PSW=0x%02x: PSW changed to 0x%02x" %
                (psw_val, proc.read_psw()))

    def test_xch_preserves_all_flags(self):
        """XCH A,r preserves all PSW flags."""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        for psw_val in range(256):
            psw_val &= PSW_MASK
            if psw_val & (Flags.RBS0 | Flags.RBS1):
                continue
            proc.write_psw(psw_val)
            proc.write_gp_reg(Registers.A, 0x55)
            proc.write_gp_reg(Registers.X, 0xAA)
            proc.write_memory_bytes(0, [0x30])  # XCH A,X
            proc.pc = 0
            proc.step()
            self.assertEqual(proc.read_psw(), psw_val,
                "XCH A,X with PSW=0x%02x: PSW changed to 0x%02x" %
                (psw_val, proc.read_psw()))


class TestBranchInstructions(unittest.TestCase):
    """Test conditional branches with flag set and clear."""

    def test_bc_taken(self):
        """BC branches when CY=1."""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_psw(Flags.CY)
        # BC +5 (displacement 0x05 from PC after consuming the displacement byte)
        proc.write_memory_bytes(0, [0x8d, 0x05])
        proc.step()
        self.assertEqual(proc.pc, 2 + 5)

    def test_bc_not_taken(self):
        """BC does not branch when CY=0."""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_psw(0)
        proc.write_memory_bytes(0, [0x8d, 0x05])
        proc.step()
        self.assertEqual(proc.pc, 2)

    def test_bnc_taken(self):
        """BNC branches when CY=0."""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_psw(0)
        proc.write_memory_bytes(0, [0x9d, 0x05])
        proc.step()
        self.assertEqual(proc.pc, 2 + 5)

    def test_bnc_not_taken(self):
        """BNC does not branch when CY=1."""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_psw(Flags.CY)
        proc.write_memory_bytes(0, [0x9d, 0x05])
        proc.step()
        self.assertEqual(proc.pc, 2)

    def test_bz_taken(self):
        """BZ branches when Z=1."""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_psw(Flags.Z)
        proc.write_memory_bytes(0, [0xad, 0x05])
        proc.step()
        self.assertEqual(proc.pc, 2 + 5)

    def test_bz_not_taken(self):
        """BZ does not branch when Z=0."""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_psw(0)
        proc.write_memory_bytes(0, [0xad, 0x05])
        proc.step()
        self.assertEqual(proc.pc, 2)

    def test_bnz_taken(self):
        """BNZ branches when Z=0."""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_psw(0)
        proc.write_memory_bytes(0, [0xbd, 0x05])
        proc.step()
        self.assertEqual(proc.pc, 2 + 5)

    def test_bnz_not_taken(self):
        """BNZ does not branch when Z=1."""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_psw(Flags.Z)
        proc.write_memory_bytes(0, [0xbd, 0x05])
        proc.step()
        self.assertEqual(proc.pc, 2)

    def test_bc_backward_branch(self):
        """BC with negative displacement."""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_psw(Flags.CY)
        proc.pc = 0x100
        proc.write_memory_bytes(0x100, [0x8d, 0xFC])  # -4 as signed
        proc.step()
        # PC after consuming = 0x102, displacement = -4 -> 0x0FE
        self.assertEqual(proc.pc, 0x102 + (-4) & 0xFFFF)

    def test_bt_saddr_each_bit(self):
        """BT saddr.bit: test each bit position 0-7 with bit set and clear."""
        for bit in range(8):
            opcode = 0x8C + (bit << 4)
            # Bit SET -> branch taken
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_memory(0xFE20, 1 << bit)  # saddr 0x20 -> 0xFE20
            proc.write_memory_bytes(0, [opcode, 0x20, 0x05])
            proc.step()
            self.assertEqual(proc.pc, 3 + 5,
                "BT saddr.%d (bit set): should branch" % bit)

            # Bit CLEAR -> branch not taken
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_memory(0xFE20, (~(1 << bit)) & 0xFF)
            proc.write_memory_bytes(0, [opcode, 0x20, 0x05])
            proc.step()
            self.assertEqual(proc.pc, 3,
                "BT saddr.%d (bit clear): should not branch" % bit)

    def test_bt_a_each_bit(self):
        """BT A.bit: test each bit position 0-7."""
        for bit in range(8):
            opcode2 = 0x0E + (bit << 4)
            # Bit SET -> branch taken
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_gp_reg(Registers.A, 1 << bit)
            proc.write_memory_bytes(0, [0x31, opcode2, 0x05])
            proc.step()
            self.assertEqual(proc.pc, 3 + 5,
                "BT A.%d (bit set): should branch" % bit)

            # Bit CLEAR -> branch not taken
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_gp_reg(Registers.A, (~(1 << bit)) & 0xFF)
            proc.write_memory_bytes(0, [0x31, opcode2, 0x05])
            proc.step()
            self.assertEqual(proc.pc, 3,
                "BT A.%d (bit clear): should not branch" % bit)

    def test_bf_a_each_bit(self):
        """BF A.bit: test each bit position 0-7."""
        for bit in range(8):
            opcode2 = 0x0F + (bit << 4)
            # Bit CLEAR -> branch taken (BF = branch if false/bit clear)
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_gp_reg(Registers.A, (~(1 << bit)) & 0xFF)
            proc.write_memory_bytes(0, [0x31, opcode2, 0x05])
            proc.step()
            self.assertEqual(proc.pc, 3 + 5,
                "BF A.%d (bit clear): should branch" % bit)

            # Bit SET -> branch not taken
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_gp_reg(Registers.A, 1 << bit)
            proc.write_memory_bytes(0, [0x31, opcode2, 0x05])
            proc.step()
            self.assertEqual(proc.pc, 3,
                "BF A.%d (bit set): should not branch" % bit)


class TestSaddrAluInstructions(unittest.TestCase):
    """ADD/SUB/ADDC/SUBC/CMP saddr,#imm: operate on memory, not A."""

    def test_add_saddr_imm(self):
        """ADD saddr,#imm: updates memory, does NOT modify A register."""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        for a_init in (0x00, 0x42, 0xFF):
            for mem_val in (0x00, 0x50, 0xFF):
                for imm in (0x00, 0x01, 0x30, 0xFF):
                    proc.write_gp_reg(Registers.A, a_init)
                    proc.write_memory(0xFE20, mem_val)
                    proc.write_psw(0)
                    # ADD 0xFE20,#imm  -> 0x88 0x20 imm
                    proc.write_memory_bytes(0, [0x88, 0x20, imm])
                    proc.pc = 0
                    proc.step()

                    expected = (mem_val + imm) & 0xFF
                    self.assertEqual(proc.read_memory(0xFE20), expected,
                        "ADD saddr,#0x%02x: mem=0x%02x expected 0x%02x got 0x%02x" %
                        (imm, mem_val, expected, proc.read_memory(0xFE20)))

                    # A must NOT be modified
                    self.assertEqual(proc.read_gp_reg(Registers.A), a_init,
                        "ADD saddr,#imm: A register was modified")

                    # PSW flags correct
                    psw = proc.read_psw()
                    if expected == 0:
                        self.assertTrue(psw & Flags.Z)
                    else:
                        self.assertFalse(psw & Flags.Z)

                    if (mem_val + imm) > 0xFF:
                        self.assertTrue(psw & Flags.CY)
                    else:
                        self.assertFalse(psw & Flags.CY)

    def test_sub_saddr_imm(self):
        """SUB saddr,#imm: updates memory, does NOT modify A register."""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        for a_init in (0x00, 0x42, 0xFF):
            for mem_val in (0x00, 0x50, 0xFF):
                for imm in (0x00, 0x01, 0x30, 0xFF):
                    proc.write_gp_reg(Registers.A, a_init)
                    proc.write_memory(0xFE20, mem_val)
                    proc.write_psw(0)
                    # SUB 0xFE20,#imm -> 0x98 0x20 imm
                    proc.write_memory_bytes(0, [0x98, 0x20, imm])
                    proc.pc = 0
                    proc.step()

                    expected = (mem_val - imm) & 0xFF
                    self.assertEqual(proc.read_memory(0xFE20), expected,
                        "SUB saddr,#0x%02x: mem=0x%02x expected 0x%02x got 0x%02x" %
                        (imm, mem_val, expected, proc.read_memory(0xFE20)))

                    self.assertEqual(proc.read_gp_reg(Registers.A), a_init,
                        "SUB saddr,#imm: A register was modified")

    def test_addc_saddr_imm(self):
        """ADDC saddr,#imm: updates memory, does NOT modify A register."""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        for init_cy in (0, Flags.CY):
            for mem_val in (0x00, 0x50, 0xFF):
                for imm in (0x00, 0x01, 0x30, 0xFF):
                    a_init = 0x42
                    proc.write_gp_reg(Registers.A, a_init)
                    proc.write_memory(0xFE20, mem_val)
                    proc.write_psw(init_cy)
                    # ADDC 0xFE20,#imm -> 0xa8 0x20 imm
                    proc.write_memory_bytes(0, [0xa8, 0x20, imm])
                    proc.pc = 0
                    proc.step()

                    cy = 1 if init_cy else 0
                    expected = (mem_val + imm + cy) & 0xFF
                    self.assertEqual(proc.read_memory(0xFE20), expected)
                    self.assertEqual(proc.read_gp_reg(Registers.A), a_init,
                        "ADDC saddr,#imm: A register was modified")

    def test_subc_saddr_imm(self):
        """SUBC saddr,#imm: updates memory, does NOT modify A register."""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        for init_cy in (0, Flags.CY):
            for mem_val in (0x00, 0x50, 0xFF):
                for imm in (0x00, 0x01, 0x30, 0xFF):
                    a_init = 0x42
                    proc.write_gp_reg(Registers.A, a_init)
                    proc.write_memory(0xFE20, mem_val)
                    proc.write_psw(init_cy)
                    # SUBC 0xFE20,#imm -> 0xb8 0x20 imm
                    proc.write_memory_bytes(0, [0xb8, 0x20, imm])
                    proc.pc = 0
                    proc.step()

                    cy = 1 if init_cy else 0
                    expected = (mem_val - imm - cy) & 0xFF
                    self.assertEqual(proc.read_memory(0xFE20), expected)
                    self.assertEqual(proc.read_gp_reg(Registers.A), a_init,
                        "SUBC saddr,#imm: A register was modified")

    def test_cmp_saddr_imm(self):
        """CMP saddr,#imm: does NOT modify memory or A register."""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        for mem_val in (0x00, 0x50, 0xFF):
            for imm in (0x00, 0x01, 0x30, 0xFF):
                a_init = 0x42
                proc.write_gp_reg(Registers.A, a_init)
                proc.write_memory(0xFE20, mem_val)
                proc.write_psw(0)
                # CMP 0xFE20,#imm -> 0xc8 0x20 imm
                proc.write_memory_bytes(0, [0xc8, 0x20, imm])
                proc.pc = 0
                proc.step()

                # Memory should NOT change (CMP is compare-only)
                self.assertEqual(proc.read_memory(0xFE20), mem_val,
                    "CMP saddr,#imm: memory was modified")
                self.assertEqual(proc.read_gp_reg(Registers.A), a_init,
                    "CMP saddr,#imm: A register was modified")

                # Flags should reflect mem_val - imm
                psw = proc.read_psw()
                diff = mem_val - imm
                expected_result = diff & 0xFF
                if expected_result == 0:
                    self.assertTrue(psw & Flags.Z)
                else:
                    self.assertFalse(psw & Flags.Z)
                if diff < 0:
                    self.assertTrue(psw & Flags.CY)
                else:
                    self.assertFalse(psw & Flags.CY)

    def test_and_saddr_imm(self):
        """AND saddr,#imm: updates memory, does NOT modify A."""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        for mem_val in (0x00, 0x55, 0xFF):
            for imm in (0x00, 0x0F, 0xF0, 0xFF):
                a_init = 0x42
                proc.write_gp_reg(Registers.A, a_init)
                proc.write_memory(0xFE20, mem_val)
                proc.write_psw(Flags.CY | Flags.AC)
                # AND 0xFE20,#imm -> 0xd8 0x20 imm
                proc.write_memory_bytes(0, [0xd8, 0x20, imm])
                proc.pc = 0
                proc.step()

                expected = mem_val & imm
                self.assertEqual(proc.read_memory(0xFE20), expected)
                self.assertEqual(proc.read_gp_reg(Registers.A), a_init,
                    "AND saddr,#imm: A register was modified")

    def test_or_saddr_imm(self):
        """OR saddr,#imm: updates memory, does NOT modify A."""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        for mem_val in (0x00, 0x55, 0xFF):
            for imm in (0x00, 0x0F, 0xF0, 0xFF):
                a_init = 0x42
                proc.write_gp_reg(Registers.A, a_init)
                proc.write_memory(0xFE20, mem_val)
                proc.write_psw(Flags.CY | Flags.AC)
                # OR 0xFE20,#imm -> 0xe8 0x20 imm
                proc.write_memory_bytes(0, [0xe8, 0x20, imm])
                proc.pc = 0
                proc.step()

                expected = mem_val | imm
                self.assertEqual(proc.read_memory(0xFE20), expected)
                self.assertEqual(proc.read_gp_reg(Registers.A), a_init,
                    "OR saddr,#imm: A register was modified")

    def test_xor_saddr_imm(self):
        """XOR saddr,#imm: updates memory, does NOT modify A."""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        for mem_val in (0x00, 0x55, 0xFF):
            for imm in (0x00, 0x0F, 0xF0, 0xFF):
                a_init = 0x42
                proc.write_gp_reg(Registers.A, a_init)
                proc.write_memory(0xFE20, mem_val)
                proc.write_psw(Flags.CY | Flags.AC)
                # XOR 0xFE20,#imm -> 0xf8 0x20 imm
                proc.write_memory_bytes(0, [0xf8, 0x20, imm])
                proc.pc = 0
                proc.step()

                expected = mem_val ^ imm
                self.assertEqual(proc.read_memory(0xFE20), expected)
                self.assertEqual(proc.read_gp_reg(Registers.A), a_init,
                    "XOR saddr,#imm: A register was modified")


class TestRol4Exhaustive(unittest.TestCase):
    """Test ROL4 [HL] for all 256x256 combinations of A and [HL] values.

    ROL4 documentation:
      A[3:0] -> [HL][3:0]
      [HL][7:4] -> A[3:0]
      [HL][3:0] -> [HL][7:4]
      A[7:4] unchanged
    """

    def test_all_256x256(self):
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        hl_addr = 0x1000  # Use a RAM address (not SFR)
        for a_val in range(256):
            for mem_val in range(256):
                proc.write_gp_regpair(RegisterPairs.HL, hl_addr)
                proc.write_gp_reg(Registers.A, a_val)
                proc.write_memory(hl_addr, mem_val)
                proc.write_memory_bytes(0, [0x31, 0x80])  # ROL4 [HL]
                proc.pc = 0
                proc.step()

                a_low = a_val & 0x0F
                a_high = a_val >> 4
                mem_low = mem_val & 0x0F
                mem_high = mem_val >> 4

                expected_a = (a_high << 4) | mem_high
                expected_mem = (mem_low << 4) | a_low

                actual_a = proc.read_gp_reg(Registers.A)
                actual_mem = proc.read_memory(hl_addr)

                self.assertEqual(actual_a, expected_a,
                    "ROL4 A=0x%02x [HL]=0x%02x: A got 0x%02x expected 0x%02x" %
                    (a_val, mem_val, actual_a, expected_a))
                self.assertEqual(actual_mem, expected_mem,
                    "ROL4 A=0x%02x [HL]=0x%02x: [HL] got 0x%02x expected 0x%02x" %
                    (a_val, mem_val, actual_mem, expected_mem))


class TestRor4Exhaustive(unittest.TestCase):
    """Test ROR4 [HL] for all 256x256 combinations of A and [HL] values.

    ROR4 documentation:
      A[3:0] -> [HL][7:4]
      [HL][3:0] -> A[3:0]
      [HL][7:4] -> [HL][3:0]
      A[7:4] unchanged
    """

    def test_all_256x256(self):
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        hl_addr = 0x1000
        for a_val in range(256):
            for mem_val in range(256):
                proc.write_gp_regpair(RegisterPairs.HL, hl_addr)
                proc.write_gp_reg(Registers.A, a_val)
                proc.write_memory(hl_addr, mem_val)
                proc.write_memory_bytes(0, [0x31, 0x90])  # ROR4 [HL]
                proc.pc = 0
                proc.step()

                a_low = a_val & 0x0F
                a_high = a_val >> 4
                mem_low = mem_val & 0x0F
                mem_high = mem_val >> 4

                expected_a = (a_high << 4) | mem_low
                expected_mem = (a_low << 4) | mem_high

                actual_a = proc.read_gp_reg(Registers.A)
                actual_mem = proc.read_memory(hl_addr)

                self.assertEqual(actual_a, expected_a,
                    "ROR4 A=0x%02x [HL]=0x%02x: A got 0x%02x expected 0x%02x" %
                    (a_val, mem_val, actual_a, expected_a))
                self.assertEqual(actual_mem, expected_mem,
                    "ROR4 A=0x%02x [HL]=0x%02x: [HL] got 0x%02x expected 0x%02x" %
                    (a_val, mem_val, actual_mem, expected_mem))


class TestMuluExhaustive(unittest.TestCase):
    """Test MULU X for all 256x256 combinations of A and X."""

    def test_all_256x256(self):
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        for a_val in range(256):
            for x_val in range(256):
                proc.write_gp_reg(Registers.A, a_val)
                proc.write_gp_reg(Registers.X, x_val)
                proc.write_psw(Flags.CY | Flags.Z | Flags.AC | Flags.IE)
                proc.write_memory_bytes(0, [0x31, 0x88])  # MULU X
                proc.pc = 0

                before = _snapshot(proc)
                proc.step()
                after = _snapshot(proc)

                expected = a_val * x_val
                actual = proc.read_gp_regpair(RegisterPairs.AX)

                self.assertEqual(actual, expected,
                    "MULU A=0x%02x X=0x%02x: got 0x%04x expected 0x%04x" %
                    (a_val, x_val, actual, expected))

                # No flag changes
                self.assertEqual(before['psw'], after['psw'],
                    "MULU: PSW changed from 0x%02x to 0x%02x" %
                    (before['psw'], after['psw']))


class TestDivuwExhaustive(unittest.TestCase):
    """Test DIVUW C for significant combinations."""

    def test_nonzero_divisors(self):
        """Test all AX values with representative C values."""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        # Test a range of divisors
        for c_val in range(1, 256):
            # Test a range of dividends
            for ax_val in range(0, 0x10000, 253):  # step by prime for spread
                proc.write_gp_regpair(RegisterPairs.AX, ax_val)
                proc.write_gp_reg(Registers.C, c_val)
                proc.write_psw(Flags.CY | Flags.Z | Flags.AC | Flags.IE)
                proc.write_memory_bytes(0, [0x31, 0x82])  # DIVUW C
                proc.pc = 0

                before_psw = proc.read_psw()
                proc.step()

                expected_q = ax_val // c_val
                expected_r = ax_val % c_val

                actual_ax = proc.read_gp_regpair(RegisterPairs.AX)
                actual_c = proc.read_gp_reg(Registers.C)

                self.assertEqual(actual_ax, expected_q,
                    "DIVUW AX=0x%04x C=0x%02x: quotient got 0x%04x expected 0x%04x" %
                    (ax_val, c_val, actual_ax, expected_q))
                self.assertEqual(actual_c, expected_r,
                    "DIVUW AX=0x%04x C=0x%02x: remainder got 0x%02x expected 0x%02x" %
                    (ax_val, c_val, actual_c, expected_r))

                # No flag changes
                self.assertEqual(proc.read_psw(), before_psw)

    def test_divide_by_zero(self):
        """Division by zero: AX=0xFFFF, C = low byte of original AX."""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        for ax_val in (0x0000, 0x0001, 0x1234, 0xFFFF):
            proc.write_gp_regpair(RegisterPairs.AX, ax_val)
            proc.write_gp_reg(Registers.C, 0)
            proc.write_memory_bytes(0, [0x31, 0x82])  # DIVUW C
            proc.pc = 0
            proc.step()

            self.assertEqual(proc.read_gp_regpair(RegisterPairs.AX), 0xFFFF,
                "DIVUW by 0: AX should be 0xFFFF")
            self.assertEqual(proc.read_gp_reg(Registers.C), ax_val & 0xFF,
                "DIVUW by 0: C should be low byte of original AX")

    def test_all_divisors_with_boundary_dividends(self):
        """All divisors 1-255 with boundary AX values."""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        boundary_ax = [0x0000, 0x0001, 0x00FF, 0x0100, 0x7FFF, 0x8000, 0xFFFE, 0xFFFF]
        for ax_val in boundary_ax:
            for c_val in range(1, 256):
                proc.write_gp_regpair(RegisterPairs.AX, ax_val)
                proc.write_gp_reg(Registers.C, c_val)
                proc.write_memory_bytes(0, [0x31, 0x82])
                proc.pc = 0
                proc.step()

                expected_q = ax_val // c_val
                expected_r = ax_val % c_val

                self.assertEqual(proc.read_gp_regpair(RegisterPairs.AX), expected_q,
                    "DIVUW AX=0x%04x C=0x%02x: quotient wrong" % (ax_val, c_val))
                self.assertEqual(proc.read_gp_reg(Registers.C), expected_r,
                    "DIVUW AX=0x%04x C=0x%02x: remainder wrong" % (ax_val, c_val))


class TestSelRb(unittest.TestCase):
    """SEL RBn: verify only RBS0/RBS1 in PSW change."""

    def test_sel_rb_all_banks(self):
        sel_opcodes = {0: 0xD0, 1: 0xD8, 2: 0xF0, 3: 0xF8}
        for bank, opcode2 in sel_opcodes.items():
            for init_psw_val in (0x00, Flags.CY | Flags.Z | Flags.AC | Flags.IE):
                proc, _ = _make_processor()
                proc.write_sp(0xFE00)
                proc.write_psw(init_psw_val)
                proc.write_memory_bytes(0, [0x61, opcode2])

                before = _snapshot(proc)
                proc.step()
                after = _snapshot(proc)

                # Only RBS0/RBS1 should change
                _assert_unchanged(self, before, after,
                                  changed_regs=set(),
                                  changed_psw_bits=Flags.RBS0 | Flags.RBS1)

                # Verify the bank is correct
                self.assertEqual(proc.read_rb(), bank,
                    "SEL RB%d: read_rb() returned %d" % (bank, proc.read_rb()))

    def test_sel_rb_preserves_other_flags(self):
        """SEL RBn preserves CY, AC, Z, IE, ISP."""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        for psw_val in range(256):
            psw_val &= PSW_MASK
            proc.write_psw(psw_val)
            proc.write_memory_bytes(0, [0x61, 0xD8])  # SEL RB1
            proc.pc = 0
            proc.step()

            after_psw = proc.read_psw()
            # All bits except RBS0/RBS1 must be preserved
            mask = PSW_MASK & ~(Flags.RBS0 | Flags.RBS1)
            self.assertEqual(after_psw & mask, psw_val & mask,
                "SEL RB1 with PSW=0x%02x: non-RBS bits changed to 0x%02x" %
                (psw_val, after_psw))


class TestAddSubImmExhaustive(unittest.TestCase):
    """Test ADD A,#imm and SUB A,#imm for all 256x256 via actual instructions."""

    def test_add_a_imm_all_256x256(self):
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        for a_val in range(256):
            for imm in range(256):
                proc.write_gp_reg(Registers.A, a_val)
                proc.write_psw(Flags.IE | Flags.ISP)
                proc.write_memory_bytes(0, [0x0d, imm])  # ADD A,#imm
                proc.pc = 0
                proc.step()

                expected = (a_val + imm) & 0xFF
                self.assertEqual(proc.read_gp_reg(Registers.A), expected,
                    "ADD A,#0x%02x with A=0x%02x" % (imm, a_val))

                psw = proc.read_psw()
                if expected == 0:
                    self.assertTrue(psw & Flags.Z)
                else:
                    self.assertFalse(psw & Flags.Z)

                if (a_val + imm) > 0xFF:
                    self.assertTrue(psw & Flags.CY)
                else:
                    self.assertFalse(psw & Flags.CY)

                if ((a_val & 0x0F) + (imm & 0x0F)) > 0x0F:
                    self.assertTrue(psw & Flags.AC)
                else:
                    self.assertFalse(psw & Flags.AC)

                # IE, ISP preserved
                self.assertTrue(psw & Flags.IE)
                self.assertTrue(psw & Flags.ISP)

    def test_sub_a_imm_all_256x256(self):
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        for a_val in range(256):
            for imm in range(256):
                proc.write_gp_reg(Registers.A, a_val)
                proc.write_psw(Flags.IE | Flags.ISP)
                proc.write_memory_bytes(0, [0x1d, imm])  # SUB A,#imm
                proc.pc = 0
                proc.step()

                expected = (a_val - imm) & 0xFF
                self.assertEqual(proc.read_gp_reg(Registers.A), expected,
                    "SUB A,#0x%02x with A=0x%02x" % (imm, a_val))

                psw = proc.read_psw()
                if expected == 0:
                    self.assertTrue(psw & Flags.Z)
                else:
                    self.assertFalse(psw & Flags.Z)

                if a_val < imm:
                    self.assertTrue(psw & Flags.CY)
                else:
                    self.assertFalse(psw & Flags.CY)

                if ((a_val & 0x0F) - (imm & 0x0F)) & 0x10:
                    self.assertTrue(psw & Flags.AC)
                else:
                    self.assertFalse(psw & Flags.AC)

                self.assertTrue(psw & Flags.IE)
                self.assertTrue(psw & Flags.ISP)


class TestCmpImmExhaustive(unittest.TestCase):
    """Test CMP A,#imm for all 256x256 via actual instruction.
    Verify A is NOT modified."""

    def test_cmp_a_imm_all_256x256(self):
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        for a_val in range(256):
            for imm in range(256):
                proc.write_gp_reg(Registers.A, a_val)
                proc.write_psw(0)
                proc.write_memory_bytes(0, [0x4d, imm])  # CMP A,#imm
                proc.pc = 0
                proc.step()

                # A must NOT change
                self.assertEqual(proc.read_gp_reg(Registers.A), a_val,
                    "CMP A,#0x%02x: A changed from 0x%02x to 0x%02x" %
                    (imm, a_val, proc.read_gp_reg(Registers.A)))

                # Flags should reflect a_val - imm
                psw = proc.read_psw()
                diff = a_val - imm
                expected = diff & 0xFF

                if expected == 0:
                    self.assertTrue(psw & Flags.Z)
                else:
                    self.assertFalse(psw & Flags.Z)

                if diff < 0:
                    self.assertTrue(psw & Flags.CY)
                else:
                    self.assertFalse(psw & Flags.CY)


class TestNop(unittest.TestCase):
    """NOP: no state changes except PC."""

    def test_nop(self):
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_gp_reg(Registers.A, 0x42)
        proc.write_psw(Flags.CY | Flags.Z | Flags.AC | Flags.IE)
        proc.write_memory_bytes(0, [0x00])

        before = _snapshot(proc)
        proc.step()
        after = _snapshot(proc)

        self.assertEqual(after['pc'], 1)
        _assert_unchanged(self, before, after,
                          changed_regs=set(),
                          changed_psw_bits=0)


class TestAluAddrModes(unittest.TestCase):
    """Test ALU A,!addr16 / A,[HL+byte] / A,saddr / A,[HL] for all 8 ALU ops."""

    def _setup(self):
        proc, mem = _make_processor()
        proc.write_sp(0xFE00)
        return proc, mem

    def _run_alu_addr16(self, opcode, a_val, mem_val, alu_op, changes_a=True):
        """ALU A,!addr16: opcode low high"""
        proc, mem = self._setup()
        proc.write_gp_reg(Registers.A, a_val)
        proc.write_psw(Flags.IE)
        proc.write_memory(0x1234, mem_val)
        proc.write_memory_bytes(0, [opcode, 0x34, 0x12])
        before = _snapshot(proc)
        proc.step()
        after = _snapshot(proc)
        changed = {Registers.A} if changes_a else set()
        _assert_unchanged(self, before, after,
                          changed_regs=changed,
                          changed_psw_bits=ARITHMETIC_FLAGS)
        return proc

    def _run_alu_hl_byte(self, opcode, a_val, mem_val, offset, alu_op, changes_a=True):
        """ALU A,[HL+byte]: opcode offset"""
        proc, mem = self._setup()
        hl_base = 0x1000
        proc.write_gp_regpair(RegisterPairs.HL, hl_base)
        proc.write_gp_reg(Registers.A, a_val)
        proc.write_psw(Flags.IE)
        proc.write_memory(hl_base + offset, mem_val)
        proc.write_memory_bytes(0, [opcode, offset])
        before = _snapshot(proc)
        proc.step()
        after = _snapshot(proc)
        changed = {Registers.A} if changes_a else set()
        _assert_unchanged(self, before, after,
                          changed_regs=changed,
                          changed_psw_bits=ARITHMETIC_FLAGS)
        return proc

    def _run_alu_saddr(self, opcode, a_val, mem_val, alu_op, changes_a=True):
        """ALU A,saddr: opcode saddr_offset (0x20 -> 0xFE20)"""
        proc, mem = self._setup()
        proc.write_gp_reg(Registers.A, a_val)
        proc.write_psw(Flags.IE)
        proc.write_memory(0xFE20, mem_val)
        proc.write_memory_bytes(0, [opcode, 0x20])
        before = _snapshot(proc)
        proc.step()
        after = _snapshot(proc)
        changed = {Registers.A} if changes_a else set()
        _assert_unchanged(self, before, after,
                          changed_regs=changed,
                          changed_psw_bits=ARITHMETIC_FLAGS)
        return proc

    def _run_alu_hl(self, opcode, a_val, mem_val, alu_op, changes_a=True):
        """ALU A,[HL]: opcode"""
        proc, mem = self._setup()
        hl_addr = 0x1000
        proc.write_gp_regpair(RegisterPairs.HL, hl_addr)
        proc.write_gp_reg(Registers.A, a_val)
        proc.write_psw(Flags.IE)
        proc.write_memory(hl_addr, mem_val)
        proc.write_memory_bytes(0, [opcode])
        before = _snapshot(proc)
        proc.step()
        after = _snapshot(proc)
        changed = {Registers.A} if changes_a else set()
        _assert_unchanged(self, before, after,
                          changed_regs=changed,
                          changed_psw_bits=ARITHMETIC_FLAGS)
        return proc

    # ADD addressing modes
    def test_add_a_addr16(self):
        for a_val in (0, 0x50, 0xFF):
            for mem_val in (0, 0x30, 0xFF):
                p = self._run_alu_addr16(0x08, a_val, mem_val, 'add')
                self.assertEqual(p.read_gp_reg(Registers.A), (a_val + mem_val) & 0xFF)

    def test_add_a_hl_byte(self):
        for a_val in (0, 0x50, 0xFF):
            for mem_val in (0, 0x30, 0xFF):
                p = self._run_alu_hl_byte(0x09, a_val, mem_val, 0x10, 'add')
                self.assertEqual(p.read_gp_reg(Registers.A), (a_val + mem_val) & 0xFF)

    def test_add_a_saddr(self):
        for a_val in (0, 0x50, 0xFF):
            for mem_val in (0, 0x30, 0xFF):
                p = self._run_alu_saddr(0x0e, a_val, mem_val, 'add')
                self.assertEqual(p.read_gp_reg(Registers.A), (a_val + mem_val) & 0xFF)

    def test_add_a_hl(self):
        for a_val in (0, 0x50, 0xFF):
            for mem_val in (0, 0x30, 0xFF):
                p = self._run_alu_hl(0x0f, a_val, mem_val, 'add')
                self.assertEqual(p.read_gp_reg(Registers.A), (a_val + mem_val) & 0xFF)

    # SUB addressing modes
    def test_sub_a_addr16(self):
        for a_val in (0, 0x50, 0xFF):
            for mem_val in (0, 0x30, 0xFF):
                p = self._run_alu_addr16(0x18, a_val, mem_val, 'sub')
                self.assertEqual(p.read_gp_reg(Registers.A), (a_val - mem_val) & 0xFF)

    def test_sub_a_hl_byte(self):
        for a_val in (0, 0x50, 0xFF):
            for mem_val in (0, 0x30, 0xFF):
                p = self._run_alu_hl_byte(0x19, a_val, mem_val, 0x10, 'sub')
                self.assertEqual(p.read_gp_reg(Registers.A), (a_val - mem_val) & 0xFF)

    def test_sub_a_saddr(self):
        for a_val in (0, 0x50, 0xFF):
            for mem_val in (0, 0x30, 0xFF):
                p = self._run_alu_saddr(0x1e, a_val, mem_val, 'sub')
                self.assertEqual(p.read_gp_reg(Registers.A), (a_val - mem_val) & 0xFF)

    def test_sub_a_hl(self):
        for a_val in (0, 0x50, 0xFF):
            for mem_val in (0, 0x30, 0xFF):
                p = self._run_alu_hl(0x1f, a_val, mem_val, 'sub')
                self.assertEqual(p.read_gp_reg(Registers.A), (a_val - mem_val) & 0xFF)

    # ADDC addressing modes
    def test_addc_a_addr16(self):
        for a_val in (0, 0x50, 0xFF):
            for mem_val in (0, 0x30, 0xFF):
                p = self._run_alu_addr16(0x28, a_val, mem_val, 'addc')
                self.assertEqual(p.read_gp_reg(Registers.A), (a_val + mem_val) & 0xFF)

    def test_addc_a_hl_byte(self):
        for a_val in (0, 0x50, 0xFF):
            for mem_val in (0, 0x30, 0xFF):
                p = self._run_alu_hl_byte(0x29, a_val, mem_val, 0x10, 'addc')
                self.assertEqual(p.read_gp_reg(Registers.A), (a_val + mem_val) & 0xFF)

    def test_addc_a_saddr(self):
        for a_val in (0, 0x50, 0xFF):
            for mem_val in (0, 0x30, 0xFF):
                p = self._run_alu_saddr(0x2e, a_val, mem_val, 'addc')
                self.assertEqual(p.read_gp_reg(Registers.A), (a_val + mem_val) & 0xFF)

    def test_addc_a_hl(self):
        for a_val in (0, 0x50, 0xFF):
            for mem_val in (0, 0x30, 0xFF):
                p = self._run_alu_hl(0x2f, a_val, mem_val, 'addc')
                self.assertEqual(p.read_gp_reg(Registers.A), (a_val + mem_val) & 0xFF)

    # SUBC addressing modes
    def test_subc_a_addr16(self):
        for a_val in (0, 0x50, 0xFF):
            for mem_val in (0, 0x30, 0xFF):
                p = self._run_alu_addr16(0x38, a_val, mem_val, 'subc')
                self.assertEqual(p.read_gp_reg(Registers.A), (a_val - mem_val) & 0xFF)

    def test_subc_a_hl_byte(self):
        for a_val in (0, 0x50, 0xFF):
            for mem_val in (0, 0x30, 0xFF):
                p = self._run_alu_hl_byte(0x39, a_val, mem_val, 0x10, 'subc')
                self.assertEqual(p.read_gp_reg(Registers.A), (a_val - mem_val) & 0xFF)

    def test_subc_a_saddr(self):
        for a_val in (0, 0x50, 0xFF):
            for mem_val in (0, 0x30, 0xFF):
                p = self._run_alu_saddr(0x3e, a_val, mem_val, 'subc')
                self.assertEqual(p.read_gp_reg(Registers.A), (a_val - mem_val) & 0xFF)

    def test_subc_a_hl(self):
        for a_val in (0, 0x50, 0xFF):
            for mem_val in (0, 0x30, 0xFF):
                p = self._run_alu_hl(0x3f, a_val, mem_val, 'subc')
                self.assertEqual(p.read_gp_reg(Registers.A), (a_val - mem_val) & 0xFF)

    # CMP addressing modes (A not modified)
    def test_cmp_a_addr16(self):
        for a_val in (0, 0x50, 0xFF):
            for mem_val in (0, 0x30, 0xFF):
                p = self._run_alu_addr16(0x48, a_val, mem_val, 'cmp', changes_a=False)
                self.assertEqual(p.read_gp_reg(Registers.A), a_val)

    def test_cmp_a_hl_byte(self):
        for a_val in (0, 0x50, 0xFF):
            for mem_val in (0, 0x30, 0xFF):
                p = self._run_alu_hl_byte(0x49, a_val, mem_val, 0x10, 'cmp', changes_a=False)
                self.assertEqual(p.read_gp_reg(Registers.A), a_val)

    def test_cmp_a_saddr(self):
        for a_val in (0, 0x50, 0xFF):
            for mem_val in (0, 0x30, 0xFF):
                p = self._run_alu_saddr(0x4e, a_val, mem_val, 'cmp', changes_a=False)
                self.assertEqual(p.read_gp_reg(Registers.A), a_val)

    def test_cmp_a_hl(self):
        for a_val in (0, 0x50, 0xFF):
            for mem_val in (0, 0x30, 0xFF):
                p = self._run_alu_hl(0x4f, a_val, mem_val, 'cmp', changes_a=False)
                self.assertEqual(p.read_gp_reg(Registers.A), a_val)

    # AND addressing modes
    def test_and_a_addr16(self):
        for a_val in (0, 0x55, 0xFF):
            for mem_val in (0, 0xAA, 0xFF):
                p = self._run_alu_addr16(0x58, a_val, mem_val, 'and')
                self.assertEqual(p.read_gp_reg(Registers.A), a_val & mem_val)

    def test_and_a_hl_byte(self):
        for a_val in (0, 0x55, 0xFF):
            for mem_val in (0, 0xAA, 0xFF):
                p = self._run_alu_hl_byte(0x59, a_val, mem_val, 0x10, 'and')
                self.assertEqual(p.read_gp_reg(Registers.A), a_val & mem_val)

    def test_and_a_saddr(self):
        for a_val in (0, 0x55, 0xFF):
            for mem_val in (0, 0xAA, 0xFF):
                p = self._run_alu_saddr(0x5e, a_val, mem_val, 'and')
                self.assertEqual(p.read_gp_reg(Registers.A), a_val & mem_val)

    def test_and_a_hl(self):
        for a_val in (0, 0x55, 0xFF):
            for mem_val in (0, 0xAA, 0xFF):
                p = self._run_alu_hl(0x5f, a_val, mem_val, 'and')
                self.assertEqual(p.read_gp_reg(Registers.A), a_val & mem_val)

    # OR addressing modes
    def test_or_a_addr16(self):
        for a_val in (0, 0x55, 0xFF):
            for mem_val in (0, 0xAA, 0xFF):
                p = self._run_alu_addr16(0x68, a_val, mem_val, 'or')
                self.assertEqual(p.read_gp_reg(Registers.A), (a_val | mem_val) & 0xFF)

    def test_or_a_hl_byte(self):
        for a_val in (0, 0x55, 0xFF):
            for mem_val in (0, 0xAA, 0xFF):
                p = self._run_alu_hl_byte(0x69, a_val, mem_val, 0x10, 'or')
                self.assertEqual(p.read_gp_reg(Registers.A), (a_val | mem_val) & 0xFF)

    def test_or_a_saddr(self):
        for a_val in (0, 0x55, 0xFF):
            for mem_val in (0, 0xAA, 0xFF):
                p = self._run_alu_saddr(0x6e, a_val, mem_val, 'or')
                self.assertEqual(p.read_gp_reg(Registers.A), (a_val | mem_val) & 0xFF)

    def test_or_a_hl(self):
        for a_val in (0, 0x55, 0xFF):
            for mem_val in (0, 0xAA, 0xFF):
                p = self._run_alu_hl(0x6f, a_val, mem_val, 'or')
                self.assertEqual(p.read_gp_reg(Registers.A), (a_val | mem_val) & 0xFF)

    # XOR addressing modes
    def test_xor_a_addr16(self):
        for a_val in (0, 0x55, 0xFF):
            for mem_val in (0, 0xAA, 0xFF):
                p = self._run_alu_addr16(0x78, a_val, mem_val, 'xor')
                self.assertEqual(p.read_gp_reg(Registers.A), a_val ^ mem_val)

    def test_xor_a_hl_byte(self):
        for a_val in (0, 0x55, 0xFF):
            for mem_val in (0, 0xAA, 0xFF):
                p = self._run_alu_hl_byte(0x79, a_val, mem_val, 0x10, 'xor')
                self.assertEqual(p.read_gp_reg(Registers.A), a_val ^ mem_val)

    def test_xor_a_saddr(self):
        for a_val in (0, 0x55, 0xFF):
            for mem_val in (0, 0xAA, 0xFF):
                p = self._run_alu_saddr(0x7e, a_val, mem_val, 'xor')
                self.assertEqual(p.read_gp_reg(Registers.A), a_val ^ mem_val)

    def test_xor_a_hl(self):
        for a_val in (0, 0x55, 0xFF):
            for mem_val in (0, 0xAA, 0xFF):
                p = self._run_alu_hl(0x7f, a_val, mem_val, 'xor')
                self.assertEqual(p.read_gp_reg(Registers.A), a_val ^ mem_val)


class TestMovAddrModes(unittest.TestCase):
    """Test all MOV addressing mode variants."""

    def test_mov_saddr_imm(self):
        """MOV saddr,#imm (0x11)"""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        for imm in (0x00, 0x42, 0xFF):
            proc.write_psw(Flags.CY | Flags.Z)
            proc.write_memory_bytes(0, [0x11, 0x20, imm])
            proc.pc = 0
            before = _snapshot(proc)
            proc.step()
            after = _snapshot(proc)
            self.assertEqual(proc.read_memory(0xFE20), imm)
            _assert_unchanged(self, before, after,
                              changed_regs=set(),
                              changed_psw_bits=0)

    def test_mov_sfr_imm(self):
        """MOV sfr,#imm (0x13)"""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        for imm in (0x00, 0x42, 0xFF):
            proc.write_psw(Flags.CY | Flags.Z)
            proc.write_memory_bytes(0, [0x13, 0x80, imm])  # sfr 0xFF80
            proc.pc = 0
            before = _snapshot(proc)
            proc.step()
            after = _snapshot(proc)
            self.assertEqual(proc.read_memory(0xFF80), imm)
            _assert_unchanged(self, before, after,
                              changed_regs=set(),
                              changed_psw_bits=0)

    def test_mov_a_de(self):
        """MOV A,[DE] (0x85)"""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_gp_regpair(RegisterPairs.DE, 0x1000)
        proc.write_memory(0x1000, 0x42)
        proc.write_psw(Flags.CY | Flags.Z)
        proc.write_memory_bytes(0, [0x85])
        before = _snapshot(proc)
        proc.step()
        after = _snapshot(proc)
        self.assertEqual(proc.read_gp_reg(Registers.A), 0x42)
        _assert_unchanged(self, before, after,
                          changed_regs={Registers.A},
                          changed_psw_bits=0)

    def test_mov_a_hl(self):
        """MOV A,[HL] (0x87)"""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_gp_regpair(RegisterPairs.HL, 0x1000)
        proc.write_memory(0x1000, 0x55)
        proc.write_psw(Flags.CY | Flags.Z)
        proc.write_memory_bytes(0, [0x87])
        before = _snapshot(proc)
        proc.step()
        after = _snapshot(proc)
        self.assertEqual(proc.read_gp_reg(Registers.A), 0x55)
        _assert_unchanged(self, before, after,
                          changed_regs={Registers.A},
                          changed_psw_bits=0)

    def test_mov_de_a(self):
        """MOV [DE],A (0x95)"""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_gp_regpair(RegisterPairs.DE, 0x1000)
        proc.write_gp_reg(Registers.A, 0xAB)
        proc.write_psw(Flags.CY | Flags.Z)
        proc.write_memory_bytes(0, [0x95])
        before = _snapshot(proc)
        proc.step()
        after = _snapshot(proc)
        self.assertEqual(proc.read_memory(0x1000), 0xAB)
        _assert_unchanged(self, before, after,
                          changed_regs=set(),
                          changed_psw_bits=0)

    def test_mov_hl_a(self):
        """MOV [HL],A (0x97)"""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_gp_regpair(RegisterPairs.HL, 0x1000)
        proc.write_gp_reg(Registers.A, 0xCD)
        proc.write_psw(Flags.CY | Flags.Z)
        proc.write_memory_bytes(0, [0x97])
        before = _snapshot(proc)
        proc.step()
        after = _snapshot(proc)
        self.assertEqual(proc.read_memory(0x1000), 0xCD)
        _assert_unchanged(self, before, after,
                          changed_regs=set(),
                          changed_psw_bits=0)

    def test_mov_a_hl_byte(self):
        """MOV A,[HL+byte] (0xAE)"""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_gp_regpair(RegisterPairs.HL, 0x1000)
        proc.write_memory(0x1010, 0x77)
        proc.write_psw(Flags.CY | Flags.Z)
        proc.write_memory_bytes(0, [0xAE, 0x10])
        before = _snapshot(proc)
        proc.step()
        after = _snapshot(proc)
        self.assertEqual(proc.read_gp_reg(Registers.A), 0x77)
        _assert_unchanged(self, before, after,
                          changed_regs={Registers.A},
                          changed_psw_bits=0)

    def test_mov_a_hl_c(self):
        """MOV A,[HL+C] (0xAA)"""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_gp_regpair(RegisterPairs.HL, 0x1000)
        proc.write_gp_reg(Registers.C, 0x05)
        proc.write_memory(0x1005, 0x88)
        proc.write_psw(Flags.CY | Flags.Z)
        proc.write_memory_bytes(0, [0xAA])
        before = _snapshot(proc)
        proc.step()
        after = _snapshot(proc)
        self.assertEqual(proc.read_gp_reg(Registers.A), 0x88)
        _assert_unchanged(self, before, after,
                          changed_regs={Registers.A},
                          changed_psw_bits=0)

    def test_mov_a_hl_b(self):
        """MOV A,[HL+B] (0xAB)"""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_gp_regpair(RegisterPairs.HL, 0x1000)
        proc.write_gp_reg(Registers.B, 0x07)
        proc.write_memory(0x1007, 0x99)
        proc.write_psw(Flags.CY | Flags.Z)
        proc.write_memory_bytes(0, [0xAB])
        before = _snapshot(proc)
        proc.step()
        after = _snapshot(proc)
        self.assertEqual(proc.read_gp_reg(Registers.A), 0x99)
        _assert_unchanged(self, before, after,
                          changed_regs={Registers.A},
                          changed_psw_bits=0)

    def test_mov_hl_c_a(self):
        """MOV [HL+C],A (0xBA)"""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_gp_regpair(RegisterPairs.HL, 0x1000)
        proc.write_gp_reg(Registers.C, 0x05)
        proc.write_gp_reg(Registers.A, 0xAA)
        proc.write_psw(Flags.CY | Flags.Z)
        proc.write_memory_bytes(0, [0xBA])
        before = _snapshot(proc)
        proc.step()
        after = _snapshot(proc)
        self.assertEqual(proc.read_memory(0x1005), 0xAA)
        _assert_unchanged(self, before, after,
                          changed_regs=set(),
                          changed_psw_bits=0)

    def test_mov_hl_b_a(self):
        """MOV [HL+B],A (0xBB)"""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_gp_regpair(RegisterPairs.HL, 0x1000)
        proc.write_gp_reg(Registers.B, 0x07)
        proc.write_gp_reg(Registers.A, 0xBB)
        proc.write_psw(Flags.CY | Flags.Z)
        proc.write_memory_bytes(0, [0xBB])
        before = _snapshot(proc)
        proc.step()
        after = _snapshot(proc)
        self.assertEqual(proc.read_memory(0x1007), 0xBB)
        _assert_unchanged(self, before, after,
                          changed_regs=set(),
                          changed_psw_bits=0)

    def test_mov_hl_byte_a(self):
        """MOV [HL+byte],A (0xBE)"""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_gp_regpair(RegisterPairs.HL, 0x1000)
        proc.write_gp_reg(Registers.A, 0xCC)
        proc.write_psw(Flags.CY | Flags.Z)
        proc.write_memory_bytes(0, [0xBE, 0x10])
        before = _snapshot(proc)
        proc.step()
        after = _snapshot(proc)
        self.assertEqual(proc.read_memory(0x1010), 0xCC)
        _assert_unchanged(self, before, after,
                          changed_regs=set(),
                          changed_psw_bits=0)

    def test_mov_a_addr16(self):
        """MOV A,!addr16 (0x8E)"""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_memory(0x1234, 0xDD)
        proc.write_psw(Flags.CY | Flags.Z)
        proc.write_memory_bytes(0, [0x8E, 0x34, 0x12])
        before = _snapshot(proc)
        proc.step()
        after = _snapshot(proc)
        self.assertEqual(proc.read_gp_reg(Registers.A), 0xDD)
        _assert_unchanged(self, before, after,
                          changed_regs={Registers.A},
                          changed_psw_bits=0)

    def test_mov_addr16_a(self):
        """MOV !addr16,A (0x9E)"""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_gp_reg(Registers.A, 0xEE)
        proc.write_psw(Flags.CY | Flags.Z)
        proc.write_memory_bytes(0, [0x9E, 0x34, 0x12])
        before = _snapshot(proc)
        proc.step()
        after = _snapshot(proc)
        self.assertEqual(proc.read_memory(0x1234), 0xEE)
        _assert_unchanged(self, before, after,
                          changed_regs=set(),
                          changed_psw_bits=0)

    def test_mov_a_saddr(self):
        """MOV A,saddr (0xF0)"""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_memory(0xFE20, 0x42)
        proc.write_psw(Flags.CY | Flags.Z)
        proc.write_memory_bytes(0, [0xF0, 0x20])
        before = _snapshot(proc)
        proc.step()
        after = _snapshot(proc)
        self.assertEqual(proc.read_gp_reg(Registers.A), 0x42)
        _assert_unchanged(self, before, after,
                          changed_regs={Registers.A},
                          changed_psw_bits=0)

    def test_mov_saddr_a(self):
        """MOV saddr,A (0xF2)"""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_gp_reg(Registers.A, 0x55)
        proc.write_psw(Flags.CY | Flags.Z)
        proc.write_memory_bytes(0, [0xF2, 0x20])
        before = _snapshot(proc)
        proc.step()
        after = _snapshot(proc)
        self.assertEqual(proc.read_memory(0xFE20), 0x55)
        _assert_unchanged(self, before, after,
                          changed_regs=set(),
                          changed_psw_bits=0)

    def test_mov_a_sfr(self):
        """MOV A,sfr (0xF4)"""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_memory(0xFF80, 0x77)
        proc.write_psw(Flags.CY | Flags.Z)
        proc.write_memory_bytes(0, [0xF4, 0x80])
        before = _snapshot(proc)
        proc.step()
        after = _snapshot(proc)
        self.assertEqual(proc.read_gp_reg(Registers.A), 0x77)
        _assert_unchanged(self, before, after,
                          changed_regs={Registers.A},
                          changed_psw_bits=0)

    def test_mov_sfr_a(self):
        """MOV sfr,A (0xF6)"""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_gp_reg(Registers.A, 0x88)
        proc.write_psw(Flags.CY | Flags.Z)
        proc.write_memory_bytes(0, [0xF6, 0x80])
        before = _snapshot(proc)
        proc.step()
        after = _snapshot(proc)
        self.assertEqual(proc.read_memory(0xFF80), 0x88)
        _assert_unchanged(self, before, after,
                          changed_regs=set(),
                          changed_psw_bits=0)

    def test_mov_r_imm(self):
        """MOV r,#byte (0xA0-0xA7)"""
        for reg in range(8):
            opcode = 0xA0 + reg
            for imm in (0x00, 0x42, 0xFF):
                proc, _ = _make_processor()
                proc.write_sp(0xFE00)
                proc.write_psw(Flags.CY | Flags.Z)
                proc.write_memory_bytes(0, [opcode, imm])
                before = _snapshot(proc)
                proc.step()
                after = _snapshot(proc)
                self.assertEqual(proc.read_gp_reg(reg), imm)
                _assert_unchanged(self, before, after,
                                  changed_regs={reg},
                                  changed_psw_bits=0)


class TestMovwAddrModes(unittest.TestCase):
    """Test all MOVW addressing mode variants."""

    def test_movw_ax_addr16p(self):
        """MOVW AX,!addr16p (0x02)"""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_memory(0x1000, 0xCD)
        proc.write_memory(0x1001, 0xAB)
        proc.write_psw(Flags.CY | Flags.Z)
        proc.write_memory_bytes(0, [0x02, 0x00, 0x10])
        before = _snapshot(proc)
        proc.step()
        after = _snapshot(proc)
        self.assertEqual(proc.read_gp_regpair(RegisterPairs.AX), 0xABCD)
        _assert_unchanged(self, before, after,
                          changed_regs={Registers.X, Registers.A},
                          changed_psw_bits=0)

    def test_movw_addr16p_ax(self):
        """MOVW !addr16p,AX (0x03)"""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_gp_regpair(RegisterPairs.AX, 0xABCD)
        proc.write_psw(Flags.CY | Flags.Z)
        proc.write_memory_bytes(0, [0x03, 0x00, 0x10])
        before = _snapshot(proc)
        proc.step()
        after = _snapshot(proc)
        self.assertEqual(proc.read_memory(0x1000), 0xCD)
        self.assertEqual(proc.read_memory(0x1001), 0xAB)
        _assert_unchanged(self, before, after,
                          changed_regs=set(),
                          changed_psw_bits=0)

    def test_movw_ax_saddrp(self):
        """MOVW AX,saddrp (0x89)"""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_memory(0xFE20, 0xCD)
        proc.write_memory(0xFE21, 0xAB)
        proc.write_psw(Flags.CY | Flags.Z)
        proc.write_memory_bytes(0, [0x89, 0x20])
        before = _snapshot(proc)
        proc.step()
        after = _snapshot(proc)
        self.assertEqual(proc.read_gp_regpair(RegisterPairs.AX), 0xABCD)
        _assert_unchanged(self, before, after,
                          changed_regs={Registers.X, Registers.A},
                          changed_psw_bits=0)

    def test_movw_saddrp_ax(self):
        """MOVW saddrp,AX (0x99)"""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_gp_regpair(RegisterPairs.AX, 0xABCD)
        proc.write_psw(Flags.CY | Flags.Z)
        proc.write_memory_bytes(0, [0x99, 0x20])
        before = _snapshot(proc)
        proc.step()
        after = _snapshot(proc)
        self.assertEqual(proc.read_memory(0xFE20), 0xCD)
        self.assertEqual(proc.read_memory(0xFE21), 0xAB)
        _assert_unchanged(self, before, after,
                          changed_regs=set(),
                          changed_psw_bits=0)

    def test_movw_ax_sfrp(self):
        """MOVW AX,sfrp (0xA9)"""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_memory(0xFF80, 0xCD)
        proc.write_memory(0xFF81, 0xAB)
        proc.write_psw(Flags.CY | Flags.Z)
        proc.write_memory_bytes(0, [0xA9, 0x80])
        before = _snapshot(proc)
        proc.step()
        after = _snapshot(proc)
        self.assertEqual(proc.read_gp_regpair(RegisterPairs.AX), 0xABCD)
        _assert_unchanged(self, before, after,
                          changed_regs={Registers.X, Registers.A},
                          changed_psw_bits=0)

    def test_movw_sfrp_ax(self):
        """MOVW sfrp,AX (0xB9)"""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_gp_regpair(RegisterPairs.AX, 0xABCD)
        proc.write_psw(Flags.CY | Flags.Z)
        proc.write_memory_bytes(0, [0xB9, 0x80])
        before = _snapshot(proc)
        proc.step()
        after = _snapshot(proc)
        self.assertEqual(proc.read_memory(0xFF80), 0xCD)
        self.assertEqual(proc.read_memory(0xFF81), 0xAB)
        _assert_unchanged(self, before, after,
                          changed_regs=set(),
                          changed_psw_bits=0)

    def test_movw_rp_ax(self):
        """MOVW rp,AX (0xD2-0xD6)"""
        rp_opcodes = {RegisterPairs.BC: 0xD2, RegisterPairs.DE: 0xD4, RegisterPairs.HL: 0xD6}
        for rp, opcode in rp_opcodes.items():
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_gp_regpair(RegisterPairs.AX, 0xABCD)
            proc.write_psw(Flags.CY | Flags.Z)
            proc.write_memory_bytes(0, [opcode])
            before = _snapshot(proc)
            proc.step()
            after = _snapshot(proc)
            self.assertEqual(proc.read_gp_regpair(rp), 0xABCD)
            changed = {rp * 2, rp * 2 + 1}
            _assert_unchanged(self, before, after,
                              changed_regs=changed,
                              changed_psw_bits=0)

    def test_movw_ax_rp(self):
        """MOVW AX,rp (0xC2-0xC6)"""
        rp_opcodes = {RegisterPairs.BC: 0xC2, RegisterPairs.DE: 0xC4, RegisterPairs.HL: 0xC6}
        for rp, opcode in rp_opcodes.items():
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_gp_regpair(rp, 0x1234)
            proc.write_psw(Flags.CY | Flags.Z)
            proc.write_memory_bytes(0, [opcode])
            before = _snapshot(proc)
            proc.step()
            after = _snapshot(proc)
            self.assertEqual(proc.read_gp_regpair(RegisterPairs.AX), 0x1234)
            _assert_unchanged(self, before, after,
                              changed_regs={Registers.X, Registers.A},
                              changed_psw_bits=0)

    def test_xchw_ax_rp(self):
        """XCHW AX,rp (0xE2-0xE6)"""
        rp_opcodes = {RegisterPairs.BC: 0xE2, RegisterPairs.DE: 0xE4, RegisterPairs.HL: 0xE6}
        for rp, opcode in rp_opcodes.items():
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_gp_regpair(RegisterPairs.AX, 0x1122)
            proc.write_gp_regpair(rp, 0x3344)
            proc.write_psw(Flags.CY | Flags.Z)
            proc.write_memory_bytes(0, [opcode])
            before = _snapshot(proc)
            proc.step()
            after = _snapshot(proc)
            self.assertEqual(proc.read_gp_regpair(RegisterPairs.AX), 0x3344)
            self.assertEqual(proc.read_gp_regpair(rp), 0x1122)
            changed = {Registers.X, Registers.A, rp * 2, rp * 2 + 1}
            _assert_unchanged(self, before, after,
                              changed_regs=changed,
                              changed_psw_bits=0)

    def test_movw_sp_word(self):
        """MOVW SP,#word (0xEE with saddr offset 0x1C for SP)"""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_psw(Flags.CY | Flags.Z)
        # EE 1C = MOVW [saddr at 0xFF1C],#word -> that is SP
        proc.write_memory_bytes(0, [0xEE, 0x1C, 0x00, 0xFD])
        before = _snapshot(proc)
        proc.step()
        after = _snapshot(proc)
        self.assertEqual(proc.read_sp(), 0xFD00)
        _assert_unchanged(self, before, after,
                          changed_regs=set(),
                          changed_sp=True,
                          changed_psw_bits=0)

    def test_movw_sfrp_word(self):
        """MOVW sfrp,#word (0xFE)"""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_psw(Flags.CY | Flags.Z)
        proc.write_memory_bytes(0, [0xFE, 0x80, 0xCD, 0xAB])  # sfrp 0xFF80
        before = _snapshot(proc)
        proc.step()
        after = _snapshot(proc)
        self.assertEqual(proc.read_memory(0xFF80), 0xCD)
        self.assertEqual(proc.read_memory(0xFF81), 0xAB)
        _assert_unchanged(self, before, after,
                          changed_regs=set(),
                          changed_psw_bits=0)


class TestIncDecSaddr(unittest.TestCase):
    """INC saddr / DEC saddr: memory updated, A NOT modified, CY preserved."""

    def test_inc_saddr(self):
        """INC saddr (0x81)"""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        for mem_val in (0x00, 0x0F, 0x7F, 0xFE, 0xFF):
            for init_cy in (0, Flags.CY):
                a_init = 0x42
                proc.write_gp_reg(Registers.A, a_init)
                proc.write_memory(0xFE20, mem_val)
                proc.write_psw(Flags.IE | init_cy)
                proc.write_memory_bytes(0, [0x81, 0x20])
                proc.pc = 0
                proc.step()
                expected = (mem_val + 1) & 0xFF
                self.assertEqual(proc.read_memory(0xFE20), expected,
                    "INC saddr: mem=0x%02x expected 0x%02x" % (mem_val, expected))
                self.assertEqual(proc.read_gp_reg(Registers.A), a_init,
                    "INC saddr: A was modified")
                self.assertEqual(proc.read_psw() & Flags.CY, init_cy,
                    "INC saddr: CY was modified")

    def test_dec_saddr(self):
        """DEC saddr (0x91)"""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        for mem_val in (0x00, 0x01, 0x10, 0x80, 0xFF):
            for init_cy in (0, Flags.CY):
                a_init = 0x42
                proc.write_gp_reg(Registers.A, a_init)
                proc.write_memory(0xFE20, mem_val)
                proc.write_psw(Flags.IE | init_cy)
                proc.write_memory_bytes(0, [0x91, 0x20])
                proc.pc = 0
                proc.step()
                expected = (mem_val - 1) & 0xFF
                self.assertEqual(proc.read_memory(0xFE20), expected,
                    "DEC saddr: mem=0x%02x expected 0x%02x" % (mem_val, expected))
                self.assertEqual(proc.read_gp_reg(Registers.A), a_init,
                    "DEC saddr: A was modified")
                self.assertEqual(proc.read_psw() & Flags.CY, init_cy,
                    "DEC saddr: CY was modified")


class TestXchAddrModes(unittest.TestCase):
    """XCH A with various addressing modes."""

    def test_xch_a_de(self):
        """XCH A,[DE] (0x05)"""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_gp_regpair(RegisterPairs.DE, 0x1000)
        proc.write_gp_reg(Registers.A, 0x55)
        proc.write_memory(0x1000, 0xAA)
        proc.write_psw(Flags.CY | Flags.Z)
        proc.write_memory_bytes(0, [0x05])
        proc.step()
        self.assertEqual(proc.read_gp_reg(Registers.A), 0xAA)
        self.assertEqual(proc.read_memory(0x1000), 0x55)

    def test_xch_a_hl(self):
        """XCH A,[HL] (0x07)"""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_gp_regpair(RegisterPairs.HL, 0x1000)
        proc.write_gp_reg(Registers.A, 0x11)
        proc.write_memory(0x1000, 0x22)
        proc.write_psw(Flags.CY | Flags.Z)
        proc.write_memory_bytes(0, [0x07])
        proc.step()
        self.assertEqual(proc.read_gp_reg(Registers.A), 0x22)
        self.assertEqual(proc.read_memory(0x1000), 0x11)

    def test_xch_a_saddr(self):
        """XCH A,saddr (0x83)"""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_gp_reg(Registers.A, 0x33)
        proc.write_memory(0xFE20, 0x44)
        proc.write_psw(Flags.CY | Flags.Z)
        proc.write_memory_bytes(0, [0x83, 0x20])
        proc.step()
        self.assertEqual(proc.read_gp_reg(Registers.A), 0x44)
        self.assertEqual(proc.read_memory(0xFE20), 0x33)

    def test_xch_a_sfr(self):
        """XCH A,sfr (0x93)"""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_gp_reg(Registers.A, 0x55)
        proc.write_memory(0xFF80, 0x66)
        proc.write_psw(Flags.CY | Flags.Z)
        proc.write_memory_bytes(0, [0x93, 0x80])
        proc.step()
        self.assertEqual(proc.read_gp_reg(Registers.A), 0x66)
        self.assertEqual(proc.read_memory(0xFF80), 0x55)

    def test_xch_a_addr16(self):
        """XCH A,!addr16 (0xCE)"""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_gp_reg(Registers.A, 0x77)
        proc.write_memory(0x1234, 0x88)
        proc.write_psw(Flags.CY | Flags.Z)
        proc.write_memory_bytes(0, [0xCE, 0x34, 0x12])
        proc.step()
        self.assertEqual(proc.read_gp_reg(Registers.A), 0x88)
        self.assertEqual(proc.read_memory(0x1234), 0x77)

    def test_xch_a_hl_byte(self):
        """XCH A,[HL+byte] (0xDE)"""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_gp_regpair(RegisterPairs.HL, 0x1000)
        proc.write_gp_reg(Registers.A, 0x99)
        proc.write_memory(0x1010, 0xBB)
        proc.write_psw(Flags.CY | Flags.Z)
        proc.write_memory_bytes(0, [0xDE, 0x10])
        proc.step()
        self.assertEqual(proc.read_gp_reg(Registers.A), 0xBB)
        self.assertEqual(proc.read_memory(0x1010), 0x99)


class TestSet1Clr1Saddr(unittest.TestCase):
    """SET1 saddr.bit / CLR1 saddr.bit: all 8 bit positions."""

    def test_set1_saddr_all_bits(self):
        """SET1 saddr.bit (0x0A-0x7A)"""
        for bit in range(8):
            opcode = 0x0A + (bit << 4)
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_memory(0xFE20, 0x00)
            proc.write_psw(Flags.CY | Flags.Z)
            proc.write_memory_bytes(0, [opcode, 0x20])
            before = _snapshot(proc)
            proc.step()
            self.assertEqual(proc.read_memory(0xFE20), 1 << bit,
                "SET1 saddr.%d: expected 0x%02x got 0x%02x" %
                (bit, 1 << bit, proc.read_memory(0xFE20)))
            after = _snapshot(proc)
            _assert_unchanged(self, before, after,
                              changed_regs=set(),
                              changed_psw_bits=0)

    def test_set1_saddr_only_target_bit(self):
        """SET1 saddr.bit: verify only target bit changes."""
        for bit in range(8):
            opcode = 0x0A + (bit << 4)
            init_val = (~(1 << bit)) & 0xFF  # all bits set except target
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_memory(0xFE20, init_val)
            proc.write_memory_bytes(0, [opcode, 0x20])
            proc.step()
            self.assertEqual(proc.read_memory(0xFE20), 0xFF,
                "SET1 saddr.%d: other bits should not change" % bit)

    def test_clr1_saddr_all_bits(self):
        """CLR1 saddr.bit (0x0B-0x7B)"""
        for bit in range(8):
            opcode = 0x0B + (bit << 4)
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_memory(0xFE20, 0xFF)
            proc.write_psw(Flags.CY | Flags.Z)
            proc.write_memory_bytes(0, [opcode, 0x20])
            before = _snapshot(proc)
            proc.step()
            expected = 0xFF & ~(1 << bit)
            self.assertEqual(proc.read_memory(0xFE20), expected,
                "CLR1 saddr.%d: expected 0x%02x got 0x%02x" %
                (bit, expected, proc.read_memory(0xFE20)))
            after = _snapshot(proc)
            _assert_unchanged(self, before, after,
                              changed_regs=set(),
                              changed_psw_bits=0)

    def test_clr1_saddr_only_target_bit(self):
        """CLR1 saddr.bit: verify only target bit changes."""
        for bit in range(8):
            opcode = 0x0B + (bit << 4)
            init_val = 1 << bit  # only target bit set
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_memory(0xFE20, init_val)
            proc.write_memory_bytes(0, [opcode, 0x20])
            proc.step()
            self.assertEqual(proc.read_memory(0xFE20), 0x00,
                "CLR1 saddr.%d: other bits should not change" % bit)


class TestBtSaddrAllBits(unittest.TestCase):
    """BT saddr.bit: all 8 bit positions, taken and not-taken."""

    def test_bt_saddr_all_bits_taken(self):
        for bit in range(8):
            opcode = 0x8C + (bit << 4)
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_memory(0xFE20, 1 << bit)
            proc.write_memory_bytes(0, [opcode, 0x20, 0x05])
            proc.step()
            self.assertEqual(proc.pc, 3 + 5,
                "BT saddr.%d taken: PC should be %d got %d" % (bit, 8, proc.pc))

    def test_bt_saddr_all_bits_not_taken(self):
        for bit in range(8):
            opcode = 0x8C + (bit << 4)
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_memory(0xFE20, (~(1 << bit)) & 0xFF)
            proc.write_memory_bytes(0, [opcode, 0x20, 0x05])
            proc.step()
            self.assertEqual(proc.pc, 3,
                "BT saddr.%d not taken: PC should be 3 got %d" % (bit, proc.pc))


class TestDbnz(unittest.TestCase):
    """DBNZ saddr/$label, DBNZ C/$label, DBNZ B/$label."""

    def test_dbnz_saddr_taken(self):
        """DBNZ saddr,$label (0x04): count > 1, should branch."""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_memory(0xFE20, 5)  # count = 5
        proc.write_memory_bytes(0, [0x04, 0x20, 0x05])
        proc.step()
        self.assertEqual(proc.read_memory(0xFE20), 4)
        self.assertEqual(proc.pc, 3 + 5)

    def test_dbnz_saddr_not_taken(self):
        """DBNZ saddr,$label (0x04): count = 1, should NOT branch."""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_memory(0xFE20, 1)  # count = 1
        proc.write_memory_bytes(0, [0x04, 0x20, 0x05])
        proc.step()
        self.assertEqual(proc.read_memory(0xFE20), 0)
        self.assertEqual(proc.pc, 3)

    def test_dbnz_c_taken(self):
        """DBNZ C,$label (0x8A): count > 1, should branch."""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_gp_reg(Registers.C, 3)
        proc.write_memory_bytes(0, [0x8A, 0x05])
        proc.step()
        self.assertEqual(proc.read_gp_reg(Registers.C), 2)
        self.assertEqual(proc.pc, 2 + 5)

    def test_dbnz_c_not_taken(self):
        """DBNZ C,$label (0x8A): count = 1, should NOT branch."""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_gp_reg(Registers.C, 1)
        proc.write_memory_bytes(0, [0x8A, 0x05])
        proc.step()
        self.assertEqual(proc.read_gp_reg(Registers.C), 0)
        self.assertEqual(proc.pc, 2)

    def test_dbnz_b_taken(self):
        """DBNZ B,$label (0x8B): count > 1, should branch."""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_gp_reg(Registers.B, 10)
        proc.write_memory_bytes(0, [0x8B, 0x05])
        proc.step()
        self.assertEqual(proc.read_gp_reg(Registers.B), 9)
        self.assertEqual(proc.pc, 2 + 5)

    def test_dbnz_b_not_taken(self):
        """DBNZ B,$label (0x8B): count = 1, should NOT branch."""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_gp_reg(Registers.B, 1)
        proc.write_memory_bytes(0, [0x8B, 0x05])
        proc.step()
        self.assertEqual(proc.read_gp_reg(Registers.B), 0)
        self.assertEqual(proc.pc, 2)

    def test_dbnz_saddr_wrap(self):
        """DBNZ saddr with count=0 wraps to 0xFF, branches."""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_memory(0xFE20, 0)
        proc.write_memory_bytes(0, [0x04, 0x20, 0x05])
        proc.step()
        self.assertEqual(proc.read_memory(0xFE20), 0xFF)
        self.assertEqual(proc.pc, 3 + 5)


class TestCallRetInstructions(unittest.TestCase):
    """CALL, CALLF, CALLT, RET, RETI, RETB, BRK."""

    def test_call_addr16(self):
        """CALL !addr16 (0x9A): pushes return address, jumps to target."""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_memory_bytes(0, [0x9A, 0x00, 0x50])  # CALL !0x5000
        proc.step()
        self.assertEqual(proc.pc, 0x5000)
        self.assertEqual(proc.read_sp(), 0xFE00 - 2)
        # Return address on stack (after the 3-byte instruction)
        self.assertEqual(proc.read_memory(0xFDFE), 0x03)  # low byte of return addr
        self.assertEqual(proc.read_memory(0xFDFF), 0x00)  # high byte

    def test_callf(self):
        """CALLF (0x0C-0x7C): call from table."""
        # 0x0C -> base 0x0800, 0x1C -> 0x0900, etc.
        for i in range(8):
            opcode = 0x0C + (i << 4)
            base = 0x0800 + (i << 8)
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_memory_bytes(0, [opcode, 0x42])  # CALLF base+0x42
            proc.step()
            self.assertEqual(proc.pc, base + 0x42,
                "CALLF opcode 0x%02x: expected PC=0x%04x got 0x%04x" %
                (opcode, base + 0x42, proc.pc))
            self.assertEqual(proc.read_sp(), 0xFE00 - 2)

    def test_callt(self):
        """CALLT (0xC1-0xFF odd): call from table at 0x40-0x7E."""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        # Set up vector at 0x40: target = 0x1234
        proc.write_memory(0x40, 0x34)
        proc.write_memory(0x41, 0x12)
        proc.write_memory_bytes(0, [0xC1])  # CALLT [0040h]
        proc.step()
        self.assertEqual(proc.pc, 0x1234)
        self.assertEqual(proc.read_sp(), 0xFE00 - 2)

    def test_callt_various(self):
        """CALLT multiple entries."""
        for idx, opcode in enumerate(range(0xC1, 0x100, 2)):
            offset = ((opcode & 0b00111110) >> 1)
            vector_addr = 0x40 + (offset * 2)
            target = 0x2000 + idx
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_memory(vector_addr, target & 0xFF)
            proc.write_memory(vector_addr + 1, target >> 8)
            proc.write_memory_bytes(0, [opcode])
            proc.step()
            self.assertEqual(proc.pc, target,
                "CALLT 0x%02x: expected 0x%04x got 0x%04x" % (opcode, target, proc.pc))

    def test_ret(self):
        """RET (0xAF): pops return address."""
        proc, _ = _make_processor()
        sp = 0xFDFE
        proc.write_sp(sp)
        proc.write_memory(sp, 0x34)      # low byte of return address
        proc.write_memory(sp + 1, 0x12)  # high byte
        proc.write_memory_bytes(0, [0xAF])
        proc.step()
        self.assertEqual(proc.pc, 0x1234)
        self.assertEqual(proc.read_sp(), sp + 2)

    def test_reti(self):
        """RETI (0x8F): pops return address AND PSW."""
        proc, _ = _make_processor()
        sp = 0xFDFD
        proc.write_sp(sp)
        # Stack: PC low, PC high, PSW
        proc.write_memory(sp, 0x34)      # PC low
        proc.write_memory(sp + 1, 0x12)  # PC high
        proc.write_memory(sp + 2, Flags.CY | Flags.Z | Flags.IE)  # PSW
        proc.write_psw(0)
        proc.write_memory_bytes(0, [0x8F])
        proc.step()
        self.assertEqual(proc.pc, 0x1234)
        self.assertEqual(proc.read_sp(), sp + 3)
        self.assertEqual(proc.read_psw(), (Flags.CY | Flags.Z | Flags.IE) & PSW_MASK)

    def test_retb(self):
        """RETB (0x9F): pops return address AND PSW."""
        proc, _ = _make_processor()
        sp = 0xFDFD
        proc.write_sp(sp)
        proc.write_memory(sp, 0x78)      # PC low
        proc.write_memory(sp + 1, 0x56)  # PC high
        proc.write_memory(sp + 2, Flags.CY | Flags.AC)  # PSW
        proc.write_psw(0)
        proc.write_memory_bytes(0, [0x9F])
        proc.step()
        self.assertEqual(proc.pc, 0x5678)
        self.assertEqual(proc.read_sp(), sp + 3)
        self.assertEqual(proc.read_psw(), (Flags.CY | Flags.AC) & PSW_MASK)

    def test_brk(self):
        """BRK (0xBF): pushes PSW and PC, jumps to BRK vector."""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_psw(Flags.CY | Flags.Z | Flags.IE)
        # BRK vector at 0x003E-0x003F (BRK_VECTOR_ADDRESS = 0x003E)
        proc.write_memory(0x003E, 0x00)  # vector low
        proc.write_memory(0x003F, 0x80)  # vector high
        proc.write_memory_bytes(0, [0xBF])
        proc.step()
        self.assertEqual(proc.pc, 0x8000)
        # PSW pushed, then PC pushed
        # SP decremented by 3 (1 byte PSW + 2 bytes PC)
        self.assertEqual(proc.read_sp(), 0xFE00 - 3)
        # IE should be cleared in current PSW
        self.assertFalse(proc.read_psw() & Flags.IE)


class TestBrInstructions(unittest.TestCase):
    """BR $label and BR !addr16."""

    def test_br_relative(self):
        """BR $label (0xFA): relative branch."""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_memory_bytes(0, [0xFA, 0x05])
        proc.step()
        self.assertEqual(proc.pc, 2 + 5)

    def test_br_relative_backward(self):
        """BR $label backward."""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.pc = 0x100
        proc.write_memory_bytes(0x100, [0xFA, 0xFC])  # -4
        proc.step()
        self.assertEqual(proc.pc, (0x102 - 4) & 0xFFFF)

    def test_br_addr16(self):
        """BR !addr16 (0x9B): absolute branch."""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_memory_bytes(0, [0x9B, 0x00, 0x50])
        proc.step()
        self.assertEqual(proc.pc, 0x5000)


class TestAddwSubwCmpwInstruction(unittest.TestCase):
    """ADDW/SUBW/CMPW AX,#word via actual instruction execution."""

    def test_addw_ax_word(self):
        """ADDW AX,#word (0xCA): test boundary and representative values."""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        test_pairs = []
        for a_high in (0x00, 0x01, 0x7F, 0x80, 0xFE, 0xFF):
            for a_low in (0x00, 0x01, 0x7F, 0x80, 0xFE, 0xFF):
                for b_high in (0x00, 0x01, 0x7F, 0x80, 0xFE, 0xFF):
                    for b_low in (0x00, 0x01, 0x7F, 0x80, 0xFE, 0xFF):
                        test_pairs.append(((a_high << 8) | a_low, (b_high << 8) | b_low))
        for ax_val, imm in test_pairs:
            proc.write_gp_regpair(RegisterPairs.AX, ax_val)
            proc.write_psw(Flags.IE)
            proc.write_memory_bytes(0, [0xCA, imm & 0xFF, imm >> 8])
            proc.pc = 0
            proc.step()
            expected = (ax_val + imm) & 0xFFFF
            self.assertEqual(proc.read_gp_regpair(RegisterPairs.AX), expected,
                "ADDW AX=0x%04x + 0x%04x" % (ax_val, imm))
            psw = proc.read_psw()
            if expected == 0:
                self.assertTrue(psw & Flags.Z)
            else:
                self.assertFalse(psw & Flags.Z)
            if (ax_val + imm) > 0xFFFF:
                self.assertTrue(psw & Flags.CY)
            else:
                self.assertFalse(psw & Flags.CY)

    def test_subw_ax_word(self):
        """SUBW AX,#word (0xDA): test boundary values."""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        boundaries = [0x0000, 0x0001, 0x00FF, 0x0100, 0x7FFF, 0x8000, 0xFFFE, 0xFFFF]
        for ax_val in boundaries:
            for imm in boundaries:
                proc.write_gp_regpair(RegisterPairs.AX, ax_val)
                proc.write_psw(Flags.IE)
                proc.write_memory_bytes(0, [0xDA, imm & 0xFF, imm >> 8])
                proc.pc = 0
                proc.step()
                expected = (ax_val - imm) & 0xFFFF
                self.assertEqual(proc.read_gp_regpair(RegisterPairs.AX), expected,
                    "SUBW AX=0x%04x - 0x%04x" % (ax_val, imm))
                psw = proc.read_psw()
                if expected == 0:
                    self.assertTrue(psw & Flags.Z)
                else:
                    self.assertFalse(psw & Flags.Z)
                if ax_val < imm:
                    self.assertTrue(psw & Flags.CY)
                else:
                    self.assertFalse(psw & Flags.CY)

    def test_cmpw_ax_word(self):
        """CMPW AX,#word (0xEA): like SUBW but AX not modified."""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        boundaries = [0x0000, 0x0001, 0x00FF, 0x0100, 0x7FFF, 0x8000, 0xFFFE, 0xFFFF]
        for ax_val in boundaries:
            for imm in boundaries:
                proc.write_gp_regpair(RegisterPairs.AX, ax_val)
                proc.write_psw(Flags.IE)
                proc.write_memory_bytes(0, [0xEA, imm & 0xFF, imm >> 8])
                proc.pc = 0
                proc.step()
                # AX must NOT change
                self.assertEqual(proc.read_gp_regpair(RegisterPairs.AX), ax_val,
                    "CMPW AX=0x%04x, 0x%04x: AX was modified" % (ax_val, imm))
                psw = proc.read_psw()
                diff = ax_val - imm
                if diff & 0xFFFF == 0:
                    self.assertTrue(psw & Flags.Z)
                else:
                    self.assertFalse(psw & Flags.Z)
                if diff < 0:
                    self.assertTrue(psw & Flags.CY)
                else:
                    self.assertFalse(psw & Flags.CY)


class TestPrefix31AluHlCB(unittest.TestCase):
    """ALU A,[HL+C] and A,[HL+B] for all 8 ALU ops, plus XCH and BR AX."""

    def _setup_hl_c(self, proc, c_val, mem_val):
        proc.write_gp_regpair(RegisterPairs.HL, 0x1000)
        proc.write_gp_reg(Registers.C, c_val)
        proc.write_memory(0x1000 + c_val, mem_val)

    def _setup_hl_b(self, proc, b_val, mem_val):
        proc.write_gp_regpair(RegisterPairs.HL, 0x1000)
        proc.write_gp_reg(Registers.B, b_val)
        proc.write_memory(0x1000 + b_val, mem_val)

    def test_add_a_hl_c(self):
        """ADD A,[HL+C] (0x31 0x0A)"""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        for a_val in (0, 0x50, 0xFF):
            for mem_val in (0, 0x30, 0xFF):
                self._setup_hl_c(proc, 0x05, mem_val)
                proc.write_gp_reg(Registers.A, a_val)
                proc.write_psw(Flags.IE)
                proc.write_memory_bytes(0, [0x31, 0x0A])
                proc.pc = 0
                proc.step()
                self.assertEqual(proc.read_gp_reg(Registers.A), (a_val + mem_val) & 0xFF)

    def test_add_a_hl_b(self):
        """ADD A,[HL+B] (0x31 0x0B)"""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        for a_val in (0, 0x50, 0xFF):
            for mem_val in (0, 0x30, 0xFF):
                self._setup_hl_b(proc, 0x07, mem_val)
                proc.write_gp_reg(Registers.A, a_val)
                proc.write_psw(Flags.IE)
                proc.write_memory_bytes(0, [0x31, 0x0B])
                proc.pc = 0
                proc.step()
                self.assertEqual(proc.read_gp_reg(Registers.A), (a_val + mem_val) & 0xFF)

    def test_sub_a_hl_c(self):
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        for a_val in (0, 0x50, 0xFF):
            for mem_val in (0, 0x30, 0xFF):
                self._setup_hl_c(proc, 0x05, mem_val)
                proc.write_gp_reg(Registers.A, a_val)
                proc.write_psw(Flags.IE)
                proc.write_memory_bytes(0, [0x31, 0x1A])
                proc.pc = 0
                proc.step()
                self.assertEqual(proc.read_gp_reg(Registers.A), (a_val - mem_val) & 0xFF)

    def test_sub_a_hl_b(self):
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        for a_val in (0, 0x50, 0xFF):
            for mem_val in (0, 0x30, 0xFF):
                self._setup_hl_b(proc, 0x07, mem_val)
                proc.write_gp_reg(Registers.A, a_val)
                proc.write_psw(Flags.IE)
                proc.write_memory_bytes(0, [0x31, 0x1B])
                proc.pc = 0
                proc.step()
                self.assertEqual(proc.read_gp_reg(Registers.A), (a_val - mem_val) & 0xFF)

    def test_addc_a_hl_c(self):
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        self._setup_hl_c(proc, 0x05, 0x30)
        proc.write_gp_reg(Registers.A, 0x50)
        proc.write_psw(Flags.IE)
        proc.write_memory_bytes(0, [0x31, 0x2A])
        proc.pc = 0
        proc.step()
        self.assertEqual(proc.read_gp_reg(Registers.A), 0x80)

    def test_addc_a_hl_b(self):
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        self._setup_hl_b(proc, 0x07, 0x30)
        proc.write_gp_reg(Registers.A, 0x50)
        proc.write_psw(Flags.IE)
        proc.write_memory_bytes(0, [0x31, 0x2B])
        proc.pc = 0
        proc.step()
        self.assertEqual(proc.read_gp_reg(Registers.A), 0x80)

    def test_subc_a_hl_c(self):
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        self._setup_hl_c(proc, 0x05, 0x30)
        proc.write_gp_reg(Registers.A, 0x50)
        proc.write_psw(Flags.IE)
        proc.write_memory_bytes(0, [0x31, 0x3A])
        proc.pc = 0
        proc.step()
        self.assertEqual(proc.read_gp_reg(Registers.A), 0x20)

    def test_subc_a_hl_b(self):
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        self._setup_hl_b(proc, 0x07, 0x30)
        proc.write_gp_reg(Registers.A, 0x50)
        proc.write_psw(Flags.IE)
        proc.write_memory_bytes(0, [0x31, 0x3B])
        proc.pc = 0
        proc.step()
        self.assertEqual(proc.read_gp_reg(Registers.A), 0x20)

    def test_cmp_a_hl_c(self):
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        self._setup_hl_c(proc, 0x05, 0x50)
        proc.write_gp_reg(Registers.A, 0x50)
        proc.write_psw(Flags.IE)
        proc.write_memory_bytes(0, [0x31, 0x4A])
        proc.pc = 0
        proc.step()
        self.assertEqual(proc.read_gp_reg(Registers.A), 0x50)  # not modified
        self.assertTrue(proc.read_psw() & Flags.Z)

    def test_cmp_a_hl_b(self):
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        self._setup_hl_b(proc, 0x07, 0x50)
        proc.write_gp_reg(Registers.A, 0x50)
        proc.write_psw(Flags.IE)
        proc.write_memory_bytes(0, [0x31, 0x4B])
        proc.pc = 0
        proc.step()
        self.assertEqual(proc.read_gp_reg(Registers.A), 0x50)
        self.assertTrue(proc.read_psw() & Flags.Z)

    def test_and_a_hl_c(self):
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        self._setup_hl_c(proc, 0x05, 0x0F)
        proc.write_gp_reg(Registers.A, 0xF0)
        proc.write_psw(Flags.IE)
        proc.write_memory_bytes(0, [0x31, 0x5A])
        proc.pc = 0
        proc.step()
        self.assertEqual(proc.read_gp_reg(Registers.A), 0x00)

    def test_and_a_hl_b(self):
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        self._setup_hl_b(proc, 0x07, 0x0F)
        proc.write_gp_reg(Registers.A, 0xFF)
        proc.write_psw(Flags.IE)
        proc.write_memory_bytes(0, [0x31, 0x5B])
        proc.pc = 0
        proc.step()
        self.assertEqual(proc.read_gp_reg(Registers.A), 0x0F)

    def test_or_a_hl_c(self):
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        self._setup_hl_c(proc, 0x05, 0x0F)
        proc.write_gp_reg(Registers.A, 0xF0)
        proc.write_psw(Flags.IE)
        proc.write_memory_bytes(0, [0x31, 0x6A])
        proc.pc = 0
        proc.step()
        self.assertEqual(proc.read_gp_reg(Registers.A), 0xFF)

    def test_or_a_hl_b(self):
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        self._setup_hl_b(proc, 0x07, 0x0F)
        proc.write_gp_reg(Registers.A, 0xF0)
        proc.write_psw(Flags.IE)
        proc.write_memory_bytes(0, [0x31, 0x6B])
        proc.pc = 0
        proc.step()
        self.assertEqual(proc.read_gp_reg(Registers.A), 0xFF)

    def test_xor_a_hl_c(self):
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        self._setup_hl_c(proc, 0x05, 0xFF)
        proc.write_gp_reg(Registers.A, 0xFF)
        proc.write_psw(Flags.IE)
        proc.write_memory_bytes(0, [0x31, 0x7A])
        proc.pc = 0
        proc.step()
        self.assertEqual(proc.read_gp_reg(Registers.A), 0x00)

    def test_xor_a_hl_b(self):
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        self._setup_hl_b(proc, 0x07, 0x55)
        proc.write_gp_reg(Registers.A, 0xAA)
        proc.write_psw(Flags.IE)
        proc.write_memory_bytes(0, [0x31, 0x7B])
        proc.pc = 0
        proc.step()
        self.assertEqual(proc.read_gp_reg(Registers.A), 0xFF)

    def test_xch_a_hl_c(self):
        """XCH A,[HL+C] (0x31 0x8A)"""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_gp_regpair(RegisterPairs.HL, 0x1000)
        proc.write_gp_reg(Registers.C, 0x05)
        proc.write_gp_reg(Registers.A, 0x11)
        proc.write_memory(0x1005, 0x22)
        proc.write_memory_bytes(0, [0x31, 0x8A])
        proc.step()
        self.assertEqual(proc.read_gp_reg(Registers.A), 0x22)
        self.assertEqual(proc.read_memory(0x1005), 0x11)

    def test_xch_a_hl_b(self):
        """XCH A,[HL+B] (0x31 0x8B)"""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_gp_regpair(RegisterPairs.HL, 0x1000)
        proc.write_gp_reg(Registers.B, 0x07)
        proc.write_gp_reg(Registers.A, 0x33)
        proc.write_memory(0x1007, 0x44)
        proc.write_memory_bytes(0, [0x31, 0x8B])
        proc.step()
        self.assertEqual(proc.read_gp_reg(Registers.A), 0x44)
        self.assertEqual(proc.read_memory(0x1007), 0x33)

    def test_br_ax(self):
        """BR AX (0x31 0x98): jumps to address in AX."""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_gp_regpair(RegisterPairs.AX, 0x5678)
        proc.write_memory_bytes(0, [0x31, 0x98])
        proc.step()
        self.assertEqual(proc.pc, 0x5678)


class TestPrefix31BitBranch(unittest.TestCase):
    """BT/BF/BTCLR for A, sfr, [HL], saddr via prefix 0x31."""

    def test_bt_a_all_bits(self):
        """BT A.bit,$label (0x31 0x0E-0x7E)"""
        for bit in range(8):
            opcode2 = 0x0E + (bit << 4)
            # taken
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_gp_reg(Registers.A, 1 << bit)
            proc.write_memory_bytes(0, [0x31, opcode2, 0x05])
            proc.step()
            self.assertEqual(proc.pc, 3 + 5)
            # not taken
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_gp_reg(Registers.A, (~(1 << bit)) & 0xFF)
            proc.write_memory_bytes(0, [0x31, opcode2, 0x05])
            proc.step()
            self.assertEqual(proc.pc, 3)

    def test_bf_a_all_bits(self):
        """BF A.bit,$label (0x31 0x0F-0x7F)"""
        for bit in range(8):
            opcode2 = 0x0F + (bit << 4)
            # taken (bit clear)
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_gp_reg(Registers.A, (~(1 << bit)) & 0xFF)
            proc.write_memory_bytes(0, [0x31, opcode2, 0x05])
            proc.step()
            self.assertEqual(proc.pc, 3 + 5)
            # not taken (bit set)
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_gp_reg(Registers.A, 1 << bit)
            proc.write_memory_bytes(0, [0x31, opcode2, 0x05])
            proc.step()
            self.assertEqual(proc.pc, 3)

    def test_btclr_a_all_bits(self):
        """BTCLR A.bit,$label (0x31 0x0D-0x7D)"""
        for bit in range(8):
            opcode2 = 0x0D + (bit << 4)
            # bit set -> branch taken, bit cleared after
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_gp_reg(Registers.A, 0xFF)
            proc.write_memory_bytes(0, [0x31, opcode2, 0x05])
            proc.step()
            self.assertEqual(proc.pc, 3 + 5)
            self.assertFalse(proc.read_gp_reg(Registers.A) & (1 << bit),
                "BTCLR A.%d: bit should be cleared" % bit)
            # bit clear -> branch not taken, bit stays clear
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_gp_reg(Registers.A, (~(1 << bit)) & 0xFF)
            proc.write_memory_bytes(0, [0x31, opcode2, 0x05])
            proc.step()
            self.assertEqual(proc.pc, 3)

    def test_bt_sfr_all_bits(self):
        """BT sfr.bit,$label (0x31 0x06-0x76)"""
        for bit in range(8):
            opcode2 = 0x06 + (bit << 4)
            # taken
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_memory(0xFF80, 1 << bit)
            proc.write_memory_bytes(0, [0x31, opcode2, 0x80, 0x05])
            proc.step()
            self.assertEqual(proc.pc, 4 + 5,
                "BT sfr.%d taken" % bit)
            # not taken
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_memory(0xFF80, (~(1 << bit)) & 0xFF)
            proc.write_memory_bytes(0, [0x31, opcode2, 0x80, 0x05])
            proc.step()
            self.assertEqual(proc.pc, 4,
                "BT sfr.%d not taken" % bit)

    def test_bf_sfr_all_bits(self):
        """BF sfr.bit,$label (0x31 0x07-0x77)"""
        for bit in range(8):
            opcode2 = 0x07 + (bit << 4)
            # taken (bit clear)
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_memory(0xFF80, (~(1 << bit)) & 0xFF)
            proc.write_memory_bytes(0, [0x31, opcode2, 0x80, 0x05])
            proc.step()
            self.assertEqual(proc.pc, 4 + 5)
            # not taken (bit set)
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_memory(0xFF80, 1 << bit)
            proc.write_memory_bytes(0, [0x31, opcode2, 0x80, 0x05])
            proc.step()
            self.assertEqual(proc.pc, 4)

    def test_btclr_sfr_all_bits(self):
        """BTCLR sfr.bit,$label (0x31 0x05-0x75)"""
        for bit in range(8):
            opcode2 = 0x05 + (bit << 4)
            # bit set -> branch, bit cleared
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_memory(0xFF80, 0xFF)
            proc.write_memory_bytes(0, [0x31, opcode2, 0x80, 0x05])
            proc.step()
            self.assertEqual(proc.pc, 4 + 5)
            self.assertFalse(proc.read_memory(0xFF80) & (1 << bit))
            # bit clear -> no branch
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_memory(0xFF80, (~(1 << bit)) & 0xFF)
            proc.write_memory_bytes(0, [0x31, opcode2, 0x80, 0x05])
            proc.step()
            self.assertEqual(proc.pc, 4)

    def test_bt_hl_all_bits(self):
        """BT [HL].bit,$label (0x31 0x86-0xF6)"""
        for bit in range(8):
            opcode2 = 0x86 + (bit << 4)
            # taken
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_gp_regpair(RegisterPairs.HL, 0x1000)
            proc.write_memory(0x1000, 1 << bit)
            proc.write_memory_bytes(0, [0x31, opcode2, 0x05])
            proc.step()
            self.assertEqual(proc.pc, 3 + 5)
            # not taken
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_gp_regpair(RegisterPairs.HL, 0x1000)
            proc.write_memory(0x1000, (~(1 << bit)) & 0xFF)
            proc.write_memory_bytes(0, [0x31, opcode2, 0x05])
            proc.step()
            self.assertEqual(proc.pc, 3)

    def test_bf_hl_all_bits(self):
        """BF [HL].bit,$label (0x31 0x87-0xF7)"""
        for bit in range(8):
            opcode2 = 0x87 + (bit << 4)
            # taken (bit clear)
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_gp_regpair(RegisterPairs.HL, 0x1000)
            proc.write_memory(0x1000, (~(1 << bit)) & 0xFF)
            proc.write_memory_bytes(0, [0x31, opcode2, 0x05])
            proc.step()
            self.assertEqual(proc.pc, 3 + 5)
            # not taken
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_gp_regpair(RegisterPairs.HL, 0x1000)
            proc.write_memory(0x1000, 1 << bit)
            proc.write_memory_bytes(0, [0x31, opcode2, 0x05])
            proc.step()
            self.assertEqual(proc.pc, 3)

    def test_btclr_hl_all_bits(self):
        """BTCLR [HL].bit,$label (0x31 0x85-0xF5)"""
        for bit in range(8):
            opcode2 = 0x85 + (bit << 4)
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_gp_regpair(RegisterPairs.HL, 0x1000)
            proc.write_memory(0x1000, 0xFF)
            proc.write_memory_bytes(0, [0x31, opcode2, 0x05])
            proc.step()
            self.assertEqual(proc.pc, 3 + 5)
            self.assertFalse(proc.read_memory(0x1000) & (1 << bit))

    def test_bf_saddr_all_bits(self):
        """BF saddr.bit,$label (0x31 0x03-0x73)"""
        for bit in range(8):
            opcode2 = 0x03 + (bit << 4)
            # taken (bit clear)
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_memory(0xFE20, (~(1 << bit)) & 0xFF)
            proc.write_memory_bytes(0, [0x31, opcode2, 0x20, 0x05])
            proc.step()
            self.assertEqual(proc.pc, 4 + 5)
            # not taken
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_memory(0xFE20, 1 << bit)
            proc.write_memory_bytes(0, [0x31, opcode2, 0x20, 0x05])
            proc.step()
            self.assertEqual(proc.pc, 4)

    def test_btclr_saddr_all_bits(self):
        """BTCLR saddr.bit,$label (0x31 0x01-0x71)"""
        for bit in range(8):
            opcode2 = 0x01 + (bit << 4)
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_memory(0xFE20, 0xFF)
            proc.write_memory_bytes(0, [0x31, opcode2, 0x20, 0x05])
            proc.step()
            self.assertEqual(proc.pc, 4 + 5)
            self.assertFalse(proc.read_memory(0xFE20) & (1 << bit))


class TestPrefix61RegRegAlu(unittest.TestCase):
    """Register-to-register ALU ops via prefix 0x61."""

    def test_add_r_a_exhaustive(self):
        """ADD r,A (0x61 0x00-0x07): exhaustive 256x256 for r=X (reg 0)."""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        for a_val in range(256):
            for r_val in range(256):
                proc.write_gp_reg(Registers.A, a_val)
                proc.write_gp_reg(Registers.X, r_val)
                proc.write_psw(Flags.IE)
                proc.write_memory_bytes(0, [0x61, 0x00])  # ADD X,A
                proc.pc = 0
                proc.step()
                expected = (a_val + r_val) & 0xFF
                self.assertEqual(proc.read_gp_reg(Registers.X), expected,
                    "ADD X,A: A=0x%02x X=0x%02x" % (a_val, r_val))
                # A should NOT be modified
                self.assertEqual(proc.read_gp_reg(Registers.A), a_val)

    def test_add_r_a_all_regs(self):
        """ADD r,A for all registers: verify correct destination.
        Note: handler reads A as one operand, reg as the other, writes to reg.
        When reg=A, both operands are A's value (0x05), so result = 0x05+0x05."""
        for reg in range(8):
            opcode2 = 0x00 + reg
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            for r in range(8):
                proc.write_gp_reg(r, 0x10 + r)
            proc.write_gp_reg(Registers.A, 0x05)
            if reg != Registers.A:
                proc.write_gp_reg(reg, 0x10)
            proc.write_psw(Flags.IE)
            proc.write_memory_bytes(0, [0x61, opcode2])
            before = _snapshot(proc)
            proc.step()
            after = _snapshot(proc)
            if reg == Registers.A:
                # ADD A,A: both operands are A=0x05
                self.assertEqual(proc.read_gp_reg(reg), (0x05 + 0x05) & 0xFF)
            else:
                self.assertEqual(proc.read_gp_reg(reg), (0x10 + 0x05) & 0xFF)
            _assert_unchanged(self, before, after,
                              changed_regs={reg},
                              changed_psw_bits=ARITHMETIC_FLAGS)

    def test_add_a_r_all_regs(self):
        """ADD A,r for registers except A (0x61 0x08-0x0F, skip 0x09=A)."""
        for reg in (Registers.X, Registers.C, Registers.B, Registers.E,
                    Registers.D, Registers.L, Registers.H):
            opcode2 = 0x08 + reg
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_gp_reg(Registers.A, 0x10)
            proc.write_gp_reg(reg, 0x20)
            proc.write_psw(Flags.IE)
            proc.write_memory_bytes(0, [0x61, opcode2])
            proc.step()
            self.assertEqual(proc.read_gp_reg(Registers.A), 0x30)

    def test_sub_a_r_exhaustive(self):
        """SUB A,r (0x61 0x18-0x1F): exhaustive 256x256 for r=X."""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        for a_val in range(256):
            for r_val in range(256):
                proc.write_gp_reg(Registers.A, a_val)
                proc.write_gp_reg(Registers.X, r_val)
                proc.write_psw(Flags.IE)
                proc.write_memory_bytes(0, [0x61, 0x18])  # SUB A,X
                proc.pc = 0
                proc.step()
                expected = (a_val - r_val) & 0xFF
                self.assertEqual(proc.read_gp_reg(Registers.A), expected,
                    "SUB A,X: A=0x%02x X=0x%02x" % (a_val, r_val))

    def test_sub_r_a_all_regs(self):
        """SUB r,A (0x61 0x10-0x17) for all registers.
        Handler: a=read_gp_reg(reg), b=read_gp_reg(A), result=sub(a,b), write reg."""
        for reg in range(8):
            opcode2 = 0x10 + reg
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_gp_reg(Registers.A, 0x05)
            if reg != Registers.A:
                proc.write_gp_reg(reg, 0x10)
            proc.write_psw(Flags.IE)
            proc.write_memory_bytes(0, [0x61, opcode2])
            proc.step()
            if reg == Registers.A:
                self.assertEqual(proc.read_gp_reg(reg), 0x00)  # A - A = 0
            else:
                self.assertEqual(proc.read_gp_reg(reg), (0x10 - 0x05) & 0xFF)

    def test_addc_r_a_all_regs(self):
        """ADDC r,A (0x61 0x20-0x27) for all registers."""
        for reg in range(8):
            opcode2 = 0x20 + reg
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_gp_reg(Registers.A, 0x05)
            if reg != Registers.A:
                proc.write_gp_reg(reg, 0x10)
            proc.write_psw(Flags.IE)  # CY=0
            proc.write_memory_bytes(0, [0x61, opcode2])
            proc.step()
            if reg == Registers.A:
                self.assertEqual(proc.read_gp_reg(reg), 0x0A)  # A+A+0
            else:
                self.assertEqual(proc.read_gp_reg(reg), 0x15)

    def test_addc_a_r_all_regs(self):
        """ADDC A,r (0x61 0x28-0x2F) for registers except A."""
        for reg in (Registers.X, Registers.C, Registers.B, Registers.E,
                    Registers.D, Registers.L, Registers.H):
            opcode2 = 0x28 + reg
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_gp_reg(Registers.A, 0x10)
            proc.write_gp_reg(reg, 0x20)
            proc.write_psw(Flags.IE | Flags.CY)  # CY=1
            proc.write_memory_bytes(0, [0x61, opcode2])
            proc.step()
            self.assertEqual(proc.read_gp_reg(Registers.A), 0x31)

    def test_subc_r_a_all_regs(self):
        """SUBC r,A (0x61 0x30-0x37) for all registers."""
        for reg in range(8):
            opcode2 = 0x30 + reg
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_gp_reg(Registers.A, 0x05)
            if reg != Registers.A:
                proc.write_gp_reg(reg, 0x10)
            proc.write_psw(Flags.IE)  # CY=0
            proc.write_memory_bytes(0, [0x61, opcode2])
            proc.step()
            if reg == Registers.A:
                self.assertEqual(proc.read_gp_reg(reg), 0x00)  # A-A-0
            else:
                self.assertEqual(proc.read_gp_reg(reg), 0x0B)

    def test_subc_a_r_all_regs(self):
        """SUBC A,r (0x61 0x38-0x3F) for registers except A."""
        for reg in (Registers.X, Registers.C, Registers.B, Registers.E,
                    Registers.D, Registers.L, Registers.H):
            opcode2 = 0x38 + reg
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_gp_reg(Registers.A, 0x20)
            proc.write_gp_reg(reg, 0x10)
            proc.write_psw(Flags.IE)  # CY=0
            proc.write_memory_bytes(0, [0x61, opcode2])
            proc.step()
            self.assertEqual(proc.read_gp_reg(Registers.A), 0x10)

    def test_cmp_r_a_all_regs(self):
        """CMP r,A (0x61 0x40-0x47) for all registers."""
        for reg in range(8):
            opcode2 = 0x40 + reg
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_gp_reg(Registers.A, 0x10)
            proc.write_gp_reg(reg, 0x10)
            proc.write_psw(Flags.IE)
            proc.write_memory_bytes(0, [0x61, opcode2])
            before = _snapshot(proc)
            proc.step()
            # Neither register should change
            self.assertEqual(proc.read_gp_reg(reg), 0x10)
            self.assertTrue(proc.read_psw() & Flags.Z)

    def test_cmp_a_r_all_regs(self):
        """CMP A,r (0x61 0x48-0x4F) for registers except A."""
        for reg in (Registers.X, Registers.C, Registers.B, Registers.E,
                    Registers.D, Registers.L, Registers.H):
            opcode2 = 0x48 + reg
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_gp_reg(Registers.A, 0x20)
            proc.write_gp_reg(reg, 0x10)
            proc.write_psw(Flags.IE)
            proc.write_memory_bytes(0, [0x61, opcode2])
            proc.step()
            self.assertEqual(proc.read_gp_reg(Registers.A), 0x20)
            self.assertFalse(proc.read_psw() & Flags.Z)
            self.assertFalse(proc.read_psw() & Flags.CY)

    def test_and_r_a_all_regs(self):
        """AND r,A (0x61 0x50-0x57) for all registers.
        Handler: a=read_gp_reg(A), b=read_gp_reg(reg), result=and(a,b), write reg."""
        for reg in range(8):
            opcode2 = 0x50 + reg
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_gp_reg(Registers.A, 0x0F)
            if reg != Registers.A:
                proc.write_gp_reg(reg, 0xFF)
            proc.write_psw(Flags.IE)
            proc.write_memory_bytes(0, [0x61, opcode2])
            proc.step()
            if reg == Registers.A:
                self.assertEqual(proc.read_gp_reg(reg), 0x0F)  # A AND A
            else:
                self.assertEqual(proc.read_gp_reg(reg), 0x0F)

    def test_and_a_r_all_regs(self):
        """AND A,r (0x61 0x58-0x5F) for registers except A."""
        for reg in (Registers.X, Registers.C, Registers.B, Registers.E,
                    Registers.D, Registers.L, Registers.H):
            opcode2 = 0x58 + reg
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_gp_reg(Registers.A, 0xFF)
            proc.write_gp_reg(reg, 0xF0)
            proc.write_psw(Flags.IE)
            proc.write_memory_bytes(0, [0x61, opcode2])
            proc.step()
            self.assertEqual(proc.read_gp_reg(Registers.A), 0xF0)

    def test_or_r_a_all_regs(self):
        """OR r,A (0x61 0x60-0x67) for all registers."""
        for reg in range(8):
            opcode2 = 0x60 + reg
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_gp_reg(Registers.A, 0x0F)
            if reg != Registers.A:
                proc.write_gp_reg(reg, 0xF0)
            proc.write_psw(Flags.IE)
            proc.write_memory_bytes(0, [0x61, opcode2])
            proc.step()
            if reg == Registers.A:
                self.assertEqual(proc.read_gp_reg(reg), 0x0F)  # A OR A
            else:
                self.assertEqual(proc.read_gp_reg(reg), 0xFF)

    def test_or_a_r_all_regs(self):
        """OR A,r (0x61 0x68-0x6F) for registers except A."""
        for reg in (Registers.X, Registers.C, Registers.B, Registers.E,
                    Registers.D, Registers.L, Registers.H):
            opcode2 = 0x68 + reg
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_gp_reg(Registers.A, 0x0F)
            proc.write_gp_reg(reg, 0xF0)
            proc.write_psw(Flags.IE)
            proc.write_memory_bytes(0, [0x61, opcode2])
            proc.step()
            self.assertEqual(proc.read_gp_reg(Registers.A), 0xFF)

    def test_xor_r_a_all_regs(self):
        """XOR r,A (0x61 0x70-0x77) for all registers."""
        for reg in range(8):
            opcode2 = 0x70 + reg
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_gp_reg(Registers.A, 0xFF)
            proc.write_gp_reg(reg, 0xFF)
            proc.write_psw(Flags.IE)
            proc.write_memory_bytes(0, [0x61, opcode2])
            proc.step()
            self.assertEqual(proc.read_gp_reg(reg), 0x00)

    def test_xor_a_r_all_regs(self):
        """XOR A,r (0x61 0x78-0x7F) for registers except A."""
        for reg in (Registers.X, Registers.C, Registers.B, Registers.E,
                    Registers.D, Registers.L, Registers.H):
            opcode2 = 0x78 + reg
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_gp_reg(Registers.A, 0x55)
            proc.write_gp_reg(reg, 0xAA)
            proc.write_psw(Flags.IE)
            proc.write_memory_bytes(0, [0x61, opcode2])
            proc.step()
            self.assertEqual(proc.read_gp_reg(Registers.A), 0xFF)


class TestPrefix61BitOpsA(unittest.TestCase):
    """SET1/CLR1/MOV1/AND1/OR1/XOR1 on A bits via prefix 0x61."""

    def test_set1_a_all_bits(self):
        """SET1 A.bit (0x61 0x8A-0xFA)"""
        for bit in range(8):
            opcode2 = 0x8A + (bit << 4)
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_gp_reg(Registers.A, 0x00)
            proc.write_memory_bytes(0, [0x61, opcode2])
            proc.step()
            self.assertEqual(proc.read_gp_reg(Registers.A), 1 << bit)

    def test_clr1_a_all_bits(self):
        """CLR1 A.bit (0x61 0x8B-0xFB)"""
        for bit in range(8):
            opcode2 = 0x8B + (bit << 4)
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_gp_reg(Registers.A, 0xFF)
            proc.write_memory_bytes(0, [0x61, opcode2])
            proc.step()
            self.assertEqual(proc.read_gp_reg(Registers.A), 0xFF & ~(1 << bit))

    def test_mov1_cy_a_bit(self):
        """MOV1 CY,A.bit (0x61 0x8C-0xFC)"""
        for bit in range(8):
            opcode2 = 0x8C + (bit << 4)
            # bit set -> CY=1
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_gp_reg(Registers.A, 1 << bit)
            proc.write_psw(0)
            proc.write_memory_bytes(0, [0x61, opcode2])
            proc.step()
            self.assertTrue(proc.read_psw() & Flags.CY,
                "MOV1 CY,A.%d: CY should be set" % bit)
            # bit clear -> CY=0
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_gp_reg(Registers.A, (~(1 << bit)) & 0xFF)
            proc.write_psw(Flags.CY)
            proc.write_memory_bytes(0, [0x61, opcode2])
            proc.step()
            self.assertFalse(proc.read_psw() & Flags.CY,
                "MOV1 CY,A.%d: CY should be clear" % bit)

    def test_mov1_a_bit_cy(self):
        """MOV1 A.bit,CY (0x61 0x89-0xF9)"""
        for bit in range(8):
            opcode2 = 0x89 + (bit << 4)
            # CY=1 -> bit set
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_gp_reg(Registers.A, 0x00)
            proc.write_psw(Flags.CY)
            proc.write_memory_bytes(0, [0x61, opcode2])
            proc.step()
            self.assertTrue(proc.read_gp_reg(Registers.A) & (1 << bit),
                "MOV1 A.%d,CY=1: bit should be set" % bit)
            # CY=0 -> bit clear
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_gp_reg(Registers.A, 0xFF)
            proc.write_psw(0)
            proc.write_memory_bytes(0, [0x61, opcode2])
            proc.step()
            self.assertFalse(proc.read_gp_reg(Registers.A) & (1 << bit),
                "MOV1 A.%d,CY=0: bit should be clear" % bit)

    def test_and1_cy_a_bit(self):
        """AND1 CY,A.bit (0x61 0x8D-0xFD)"""
        for bit in range(8):
            opcode2 = 0x8D + (bit << 4)
            # CY=1, A.bit=1 -> CY=1
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_gp_reg(Registers.A, 1 << bit)
            proc.write_psw(Flags.CY)
            proc.write_memory_bytes(0, [0x61, opcode2])
            proc.step()
            self.assertTrue(proc.read_psw() & Flags.CY)
            # CY=1, A.bit=0 -> CY=0
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_gp_reg(Registers.A, (~(1 << bit)) & 0xFF)
            proc.write_psw(Flags.CY)
            proc.write_memory_bytes(0, [0x61, opcode2])
            proc.step()
            self.assertFalse(proc.read_psw() & Flags.CY)

    def test_or1_cy_a_bit(self):
        """OR1 CY,A.bit (0x61 0x8E-0xFE)"""
        for bit in range(8):
            opcode2 = 0x8E + (bit << 4)
            # CY=0, A.bit=1 -> CY=1
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_gp_reg(Registers.A, 1 << bit)
            proc.write_psw(0)
            proc.write_memory_bytes(0, [0x61, opcode2])
            proc.step()
            self.assertTrue(proc.read_psw() & Flags.CY)
            # CY=0, A.bit=0 -> CY=0
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_gp_reg(Registers.A, (~(1 << bit)) & 0xFF)
            proc.write_psw(0)
            proc.write_memory_bytes(0, [0x61, opcode2])
            proc.step()
            self.assertFalse(proc.read_psw() & Flags.CY)

    def test_xor1_cy_a_bit(self):
        """XOR1 CY,A.bit (0x61 0x8F-0xFF)"""
        for bit in range(8):
            opcode2 = 0x8F + (bit << 4)
            # CY=0, A.bit=1 -> CY=1
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_gp_reg(Registers.A, 1 << bit)
            proc.write_psw(0)
            proc.write_memory_bytes(0, [0x61, opcode2])
            proc.step()
            self.assertTrue(proc.read_psw() & Flags.CY)
            # CY=1, A.bit=1 -> CY=0
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_gp_reg(Registers.A, 1 << bit)
            proc.write_psw(Flags.CY)
            proc.write_memory_bytes(0, [0x61, opcode2])
            proc.step()
            self.assertFalse(proc.read_psw() & Flags.CY)


class TestAdjba(unittest.TestCase):
    """ADJBA (0x61 0x80): representative truth table cases."""

    def _run_adjba(self, a_val, cy, ac):
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_gp_reg(Registers.A, a_val)
        psw = 0
        if cy:
            psw |= Flags.CY
        if ac:
            psw |= Flags.AC
        proc.write_psw(psw)
        proc.write_memory_bytes(0, [0x61, 0x80])
        proc.step()
        return proc.read_gp_reg(Registers.A), proc.read_psw()

    def test_adjba_no_adjust(self):
        """0x12 with CY=0, AC=0 -> 0x12"""
        a, psw = self._run_adjba(0x12, 0, 0)
        self.assertEqual(a, 0x12)
        self.assertFalse(psw & Flags.CY)

    def test_adjba_low_nibble_adjust(self):
        """0x1A with CY=0, AC=0 -> 0x20 (low nibble > 9)"""
        a, psw = self._run_adjba(0x1A, 0, 0)
        self.assertEqual(a, 0x20)

    def test_adjba_high_nibble_adjust(self):
        """0xA0 with CY=0, AC=0 -> 0x00 with CY=1 (high nibble >= 10)"""
        a, psw = self._run_adjba(0xA0, 0, 0)
        self.assertEqual(a, 0x00)
        self.assertTrue(psw & Flags.CY)

    def test_adjba_both_adjust(self):
        """0xAB with CY=0, AC=0 -> 0x11 with CY=1"""
        a, psw = self._run_adjba(0xAB, 0, 0)
        self.assertEqual(a, 0x11)
        self.assertTrue(psw & Flags.CY)

    def test_adjba_with_cy(self):
        """0x05 with CY=1, AC=0 -> 0x65"""
        a, psw = self._run_adjba(0x05, 1, 0)
        self.assertEqual(a, 0x65)
        self.assertTrue(psw & Flags.CY)

    def test_adjba_with_ac(self):
        """0x10 with CY=0, AC=1 -> 0x16"""
        a, psw = self._run_adjba(0x10, 0, 1)
        self.assertEqual(a, 0x16)

    def test_adjba_zero_result(self):
        """0x9A with CY=0, AC=0 -> 0x00 with Z=1"""
        a, psw = self._run_adjba(0x9A, 0, 0)
        self.assertEqual(a, 0x00)
        self.assertTrue(psw & Flags.Z)


class TestAdjbs(unittest.TestCase):
    """ADJBS (0x61 0x90): representative truth table cases."""

    def _run_adjbs(self, a_val, cy, ac):
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_gp_reg(Registers.A, a_val)
        psw = 0
        if cy:
            psw |= Flags.CY
        if ac:
            psw |= Flags.AC
        proc.write_psw(psw)
        proc.write_memory_bytes(0, [0x61, 0x90])
        proc.step()
        return proc.read_gp_reg(Registers.A), proc.read_psw()

    def test_adjbs_no_adjust(self):
        """0x12 with CY=0, AC=0 -> 0x12"""
        a, psw = self._run_adjbs(0x12, 0, 0)
        self.assertEqual(a, 0x12)

    def test_adjbs_cy_adjust(self):
        """0xA0 with CY=1, AC=0 -> 0x40 with CY=1"""
        a, psw = self._run_adjbs(0xA0, 1, 0)
        self.assertEqual(a, 0x40)
        self.assertTrue(psw & Flags.CY)

    def test_adjbs_ac_adjust(self):
        """0x06 with CY=0, AC=1 -> 0x00 with Z=1"""
        a, psw = self._run_adjbs(0x06, 0, 1)
        self.assertEqual(a, 0x00)
        self.assertTrue(psw & Flags.Z)

    def test_adjbs_both_adjust(self):
        """0x66 with CY=1, AC=1 -> 0x00 with CY=1, Z=1"""
        a, psw = self._run_adjbs(0x66, 1, 1)
        self.assertEqual(a, 0x00)
        self.assertTrue(psw & Flags.CY)
        self.assertTrue(psw & Flags.Z)


class TestPrefix71BitOps(unittest.TestCase):
    """SET1/CLR1/MOV1/AND1/OR1/XOR1 on SFR and [HL] bits via prefix 0x71."""

    def test_set1_sfr_all_bits(self):
        """SET1 sfr.bit (0x71 0x0A-0x7A)"""
        for bit in range(8):
            opcode2 = 0x0A + (bit << 4)
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_memory(0xFF80, 0x00)
            proc.write_memory_bytes(0, [0x71, opcode2, 0x80])
            proc.step()
            self.assertEqual(proc.read_memory(0xFF80), 1 << bit)

    def test_clr1_sfr_all_bits(self):
        """CLR1 sfr.bit (0x71 0x0B-0x7B)"""
        for bit in range(8):
            opcode2 = 0x0B + (bit << 4)
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_memory(0xFF80, 0xFF)
            proc.write_memory_bytes(0, [0x71, opcode2, 0x80])
            proc.step()
            self.assertEqual(proc.read_memory(0xFF80), 0xFF & ~(1 << bit))

    def test_set1_hl_all_bits(self):
        """SET1 [HL].bit (0x71 0x82-0xF2)"""
        for bit in range(8):
            opcode2 = 0x82 + (bit << 4)
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_gp_regpair(RegisterPairs.HL, 0x1000)
            proc.write_memory(0x1000, 0x00)
            proc.write_memory_bytes(0, [0x71, opcode2])
            proc.step()
            self.assertEqual(proc.read_memory(0x1000), 1 << bit)

    def test_clr1_hl_all_bits(self):
        """CLR1 [HL].bit (0x71 0x83-0xF3)"""
        for bit in range(8):
            opcode2 = 0x83 + (bit << 4)
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_gp_regpair(RegisterPairs.HL, 0x1000)
            proc.write_memory(0x1000, 0xFF)
            proc.write_memory_bytes(0, [0x71, opcode2])
            proc.step()
            self.assertEqual(proc.read_memory(0x1000), 0xFF & ~(1 << bit))

    def test_mov1_saddr_bit_cy(self):
        """MOV1 saddr.bit,CY (0x71 0x01-0x71)"""
        for bit in range(8):
            opcode2 = 0x01 + (bit << 4)
            for cy in (0, Flags.CY):
                proc, _ = _make_processor()
                proc.write_sp(0xFE00)
                proc.write_memory(0xFE20, 0x00 if cy else 0xFF)
                proc.write_psw(cy)
                proc.write_memory_bytes(0, [0x71, opcode2, 0x20])
                proc.step()
                if cy:
                    self.assertTrue(proc.read_memory(0xFE20) & (1 << bit))
                else:
                    self.assertFalse(proc.read_memory(0xFE20) & (1 << bit))

    def test_mov1_cy_sfr_bit(self):
        """MOV1 CY,sfr.bit (0x71 0x0C-0x7C)"""
        for bit in range(8):
            opcode2 = 0x0C + (bit << 4)
            # bit set -> CY=1
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_memory(0xFF80, 1 << bit)
            proc.write_psw(0)
            proc.write_memory_bytes(0, [0x71, opcode2, 0x80])
            proc.step()
            self.assertTrue(proc.read_psw() & Flags.CY)
            # bit clear -> CY=0
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_memory(0xFF80, (~(1 << bit)) & 0xFF)
            proc.write_psw(Flags.CY)
            proc.write_memory_bytes(0, [0x71, opcode2, 0x80])
            proc.step()
            self.assertFalse(proc.read_psw() & Flags.CY)

    def test_mov1_sfr_bit_cy(self):
        """MOV1 sfr.bit,CY (0x71 0x09-0x79)"""
        for bit in range(8):
            opcode2 = 0x09 + (bit << 4)
            for cy in (0, Flags.CY):
                proc, _ = _make_processor()
                proc.write_sp(0xFE00)
                proc.write_memory(0xFF80, 0x00 if cy else 0xFF)
                proc.write_psw(cy)
                proc.write_memory_bytes(0, [0x71, opcode2, 0x80])
                proc.step()
                if cy:
                    self.assertTrue(proc.read_memory(0xFF80) & (1 << bit))
                else:
                    self.assertFalse(proc.read_memory(0xFF80) & (1 << bit))

    def test_mov1_cy_saddr_bit(self):
        """MOV1 CY,saddr.bit (0x71 0x04-0x74)"""
        for bit in range(8):
            opcode2 = 0x04 + (bit << 4)
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_memory(0xFE20, 1 << bit)
            proc.write_psw(0)
            proc.write_memory_bytes(0, [0x71, opcode2, 0x20])
            proc.step()
            self.assertTrue(proc.read_psw() & Flags.CY)

    def test_mov1_cy_hl_bit(self):
        """MOV1 CY,[HL].bit (0x71 0x84-0xF4)"""
        for bit in range(8):
            opcode2 = 0x84 + (bit << 4)
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_gp_regpair(RegisterPairs.HL, 0x1000)
            proc.write_memory(0x1000, 1 << bit)
            proc.write_psw(0)
            proc.write_memory_bytes(0, [0x71, opcode2])
            proc.step()
            self.assertTrue(proc.read_psw() & Flags.CY)

    def test_mov1_hl_bit_cy(self):
        """MOV1 [HL].bit,CY (0x71 0x81-0xF1)"""
        for bit in range(8):
            opcode2 = 0x81 + (bit << 4)
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_gp_regpair(RegisterPairs.HL, 0x1000)
            proc.write_memory(0x1000, 0x00)
            proc.write_psw(Flags.CY)
            proc.write_memory_bytes(0, [0x71, opcode2])
            proc.step()
            self.assertTrue(proc.read_memory(0x1000) & (1 << bit))

    def test_and1_cy_hl_bit(self):
        """AND1 CY,[HL].bit (0x71 0x85-0xF5)"""
        for bit in range(8):
            opcode2 = 0x85 + (bit << 4)
            # CY=1, bit=1 -> CY=1
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_gp_regpair(RegisterPairs.HL, 0x1000)
            proc.write_memory(0x1000, 1 << bit)
            proc.write_psw(Flags.CY)
            proc.write_memory_bytes(0, [0x71, opcode2])
            proc.step()
            self.assertTrue(proc.read_psw() & Flags.CY)
            # CY=1, bit=0 -> CY=0
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_gp_regpair(RegisterPairs.HL, 0x1000)
            proc.write_memory(0x1000, 0)
            proc.write_psw(Flags.CY)
            proc.write_memory_bytes(0, [0x71, opcode2])
            proc.step()
            self.assertFalse(proc.read_psw() & Flags.CY)

    def test_and1_cy_sfr_bit(self):
        """AND1 CY,sfr.bit (0x71 0x0D-0x7D)"""
        for bit in range(8):
            opcode2 = 0x0D + (bit << 4)
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_memory(0xFF80, 1 << bit)
            proc.write_psw(Flags.CY)
            proc.write_memory_bytes(0, [0x71, opcode2, 0x80])
            proc.step()
            self.assertTrue(proc.read_psw() & Flags.CY)

    def test_and1_cy_saddr_bit(self):
        """AND1 CY,saddr.bit (0x71 0x05-0x75)"""
        for bit in range(8):
            opcode2 = 0x05 + (bit << 4)
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_memory(0xFE20, 1 << bit)
            proc.write_psw(Flags.CY)
            proc.write_memory_bytes(0, [0x71, opcode2, 0x20])
            proc.step()
            self.assertTrue(proc.read_psw() & Flags.CY)

    def test_or1_cy_hl_bit(self):
        """OR1 CY,[HL].bit (0x71 0x86-0xF6)"""
        for bit in range(8):
            opcode2 = 0x86 + (bit << 4)
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_gp_regpair(RegisterPairs.HL, 0x1000)
            proc.write_memory(0x1000, 1 << bit)
            proc.write_psw(0)
            proc.write_memory_bytes(0, [0x71, opcode2])
            proc.step()
            self.assertTrue(proc.read_psw() & Flags.CY)

    def test_or1_cy_sfr_bit(self):
        """OR1 CY,sfr.bit (0x71 0x0E-0x7E)"""
        for bit in range(8):
            opcode2 = 0x0E + (bit << 4)
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_memory(0xFF80, 1 << bit)
            proc.write_psw(0)
            proc.write_memory_bytes(0, [0x71, opcode2, 0x80])
            proc.step()
            self.assertTrue(proc.read_psw() & Flags.CY)

    def test_or1_cy_saddr_bit(self):
        """OR1 CY,saddr.bit (0x71 0x06-0x76)"""
        for bit in range(8):
            opcode2 = 0x06 + (bit << 4)
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_memory(0xFE20, 1 << bit)
            proc.write_psw(0)
            proc.write_memory_bytes(0, [0x71, opcode2, 0x20])
            proc.step()
            self.assertTrue(proc.read_psw() & Flags.CY)

    def test_xor1_cy_hl_bit(self):
        """XOR1 CY,[HL].bit (0x71 0x87-0xF7)"""
        for bit in range(8):
            opcode2 = 0x87 + (bit << 4)
            # CY=0 XOR bit=1 -> CY=1
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_gp_regpair(RegisterPairs.HL, 0x1000)
            proc.write_memory(0x1000, 1 << bit)
            proc.write_psw(0)
            proc.write_memory_bytes(0, [0x71, opcode2])
            proc.step()
            self.assertTrue(proc.read_psw() & Flags.CY)
            # CY=1 XOR bit=1 -> CY=0
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_gp_regpair(RegisterPairs.HL, 0x1000)
            proc.write_memory(0x1000, 1 << bit)
            proc.write_psw(Flags.CY)
            proc.write_memory_bytes(0, [0x71, opcode2])
            proc.step()
            self.assertFalse(proc.read_psw() & Flags.CY)

    def test_xor1_cy_sfr_bit(self):
        """XOR1 CY,sfr.bit (0x71 0x0F-0x7F)"""
        for bit in range(8):
            opcode2 = 0x0F + (bit << 4)
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_memory(0xFF80, 1 << bit)
            proc.write_psw(0)
            proc.write_memory_bytes(0, [0x71, opcode2, 0x80])
            proc.step()
            self.assertTrue(proc.read_psw() & Flags.CY)

    def test_xor1_cy_saddr_bit(self):
        """XOR1 CY,saddr.bit (0x71 0x07-0x77)"""
        for bit in range(8):
            opcode2 = 0x07 + (bit << 4)
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            proc.write_memory(0xFE20, 1 << bit)
            proc.write_psw(0)
            proc.write_memory_bytes(0, [0x71, opcode2, 0x20])
            proc.step()
            self.assertTrue(proc.read_psw() & Flags.CY)


class TestHalt(unittest.TestCase):
    """HALT: verify PC re-execution behavior."""

    def test_halt_reexecutes(self):
        """HALT with no pending interrupt: PC backs up to re-execute."""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_memory_bytes(0, [0x71, 0x10])
        proc.step()
        # Should re-execute: PC backs up by 2
        self.assertEqual(proc.pc, 0)


class TestAddcImmExhaustive(unittest.TestCase):
    def test_addc_a_imm_all_256x256_cy0(self):
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        for a_val in range(256):
            for imm in range(256):
                proc.write_gp_reg(Registers.A, a_val)
                proc.write_psw(Flags.IE | Flags.ISP)  # CY=0
                proc.write_memory_bytes(0, [0x2d, imm])
                proc.pc = 0
                proc.step()
                expected = (a_val + imm) & 0xFF
                self.assertEqual(proc.read_gp_reg(Registers.A), expected,
                    "ADDC(CY=0) A=0x%02x,#0x%02x" % (a_val, imm))
                psw = proc.read_psw()
                if expected == 0:
                    self.assertTrue(psw & Flags.Z)
                else:
                    self.assertFalse(psw & Flags.Z)
                if (a_val + imm) > 0xFF:
                    self.assertTrue(psw & Flags.CY)
                else:
                    self.assertFalse(psw & Flags.CY)

    def test_addc_a_imm_all_256x256_cy1(self):
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        for a_val in range(256):
            for imm in range(256):
                proc.write_gp_reg(Registers.A, a_val)
                proc.write_psw(Flags.IE | Flags.ISP | Flags.CY)
                proc.write_memory_bytes(0, [0x2d, imm])
                proc.pc = 0
                proc.step()
                expected = (a_val + imm + 1) & 0xFF
                self.assertEqual(proc.read_gp_reg(Registers.A), expected,
                    "ADDC(CY=1) A=0x%02x,#0x%02x" % (a_val, imm))
                psw = proc.read_psw()
                if expected == 0:
                    self.assertTrue(psw & Flags.Z)
                else:
                    self.assertFalse(psw & Flags.Z)
                if (a_val + imm + 1) > 0xFF:
                    self.assertTrue(psw & Flags.CY)
                else:
                    self.assertFalse(psw & Flags.CY)


class TestSubcImmExhaustive(unittest.TestCase):
    def test_subc_a_imm_all_256x256_cy0(self):
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        for a_val in range(256):
            for imm in range(256):
                proc.write_gp_reg(Registers.A, a_val)
                proc.write_psw(Flags.IE | Flags.ISP)  # CY=0
                proc.write_memory_bytes(0, [0x3d, imm])
                proc.pc = 0
                proc.step()
                expected = (a_val - imm) & 0xFF
                self.assertEqual(proc.read_gp_reg(Registers.A), expected,
                    "SUBC(CY=0) A=0x%02x,#0x%02x" % (a_val, imm))
                psw = proc.read_psw()
                if expected == 0:
                    self.assertTrue(psw & Flags.Z)
                else:
                    self.assertFalse(psw & Flags.Z)
                if a_val < imm:
                    self.assertTrue(psw & Flags.CY)
                else:
                    self.assertFalse(psw & Flags.CY)

    def test_subc_a_imm_all_256x256_cy1(self):
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        for a_val in range(256):
            for imm in range(256):
                proc.write_gp_reg(Registers.A, a_val)
                proc.write_psw(Flags.IE | Flags.ISP | Flags.CY)
                proc.write_memory_bytes(0, [0x3d, imm])
                proc.pc = 0
                proc.step()
                expected = (a_val - imm - 1) & 0xFF
                self.assertEqual(proc.read_gp_reg(Registers.A), expected,
                    "SUBC(CY=1) A=0x%02x,#0x%02x" % (a_val, imm))
                psw = proc.read_psw()
                if expected == 0:
                    self.assertTrue(psw & Flags.Z)
                else:
                    self.assertFalse(psw & Flags.Z)
                if (a_val - imm - 1) < 0:
                    self.assertTrue(psw & Flags.CY)
                else:
                    self.assertFalse(psw & Flags.CY)


class TestAndImmExhaustive(unittest.TestCase):
    def test_and_a_imm_all_256x256(self):
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        for a_val in range(256):
            for imm in range(256):
                proc.write_gp_reg(Registers.A, a_val)
                proc.write_psw(Flags.IE | Flags.ISP | Flags.CY | Flags.AC)
                proc.write_memory_bytes(0, [0x5d, imm])
                proc.pc = 0
                proc.step()
                expected = a_val & imm
                self.assertEqual(proc.read_gp_reg(Registers.A), expected,
                    "AND A=0x%02x,#0x%02x" % (a_val, imm))
                psw = proc.read_psw()
                if expected == 0:
                    self.assertTrue(psw & Flags.Z)
                else:
                    self.assertFalse(psw & Flags.Z)
                self.assertTrue(psw & Flags.CY)
                self.assertTrue(psw & Flags.AC)


class TestOrImmExhaustive(unittest.TestCase):
    def test_or_a_imm_all_256x256(self):
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        for a_val in range(256):
            for imm in range(256):
                proc.write_gp_reg(Registers.A, a_val)
                proc.write_psw(Flags.IE | Flags.ISP | Flags.CY | Flags.AC)
                proc.write_memory_bytes(0, [0x6d, imm])
                proc.pc = 0
                proc.step()
                expected = a_val | imm
                self.assertEqual(proc.read_gp_reg(Registers.A), expected,
                    "OR A=0x%02x,#0x%02x" % (a_val, imm))
                psw = proc.read_psw()
                if expected == 0:
                    self.assertTrue(psw & Flags.Z)
                else:
                    self.assertFalse(psw & Flags.Z)
                self.assertTrue(psw & Flags.CY)
                self.assertTrue(psw & Flags.AC)


class TestXorImmExhaustive(unittest.TestCase):
    def test_xor_a_imm_all_256x256(self):
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        for a_val in range(256):
            for imm in range(256):
                proc.write_gp_reg(Registers.A, a_val)
                proc.write_psw(Flags.IE | Flags.ISP | Flags.CY | Flags.AC)
                proc.write_memory_bytes(0, [0x7d, imm])
                proc.pc = 0
                proc.step()
                expected = a_val ^ imm
                self.assertEqual(proc.read_gp_reg(Registers.A), expected,
                    "XOR A=0x%02x,#0x%02x" % (a_val, imm))
                psw = proc.read_psw()
                if expected == 0:
                    self.assertTrue(psw & Flags.Z)
                else:
                    self.assertFalse(psw & Flags.Z)
                self.assertTrue(psw & Flags.CY)
                self.assertTrue(psw & Flags.AC)


class TestAluAddrModeResults(unittest.TestCase):
    """For each ALU op x each addressing mode, verify the actual result
    in A (or flags for CMP), using distinct values that would fail if
    the wrong register or address were used."""

    def _test_alu_addr16(self, opcode, a_val, mem_val, expected_a, verify_a=True):
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_gp_reg(Registers.A, a_val)
        addr = 0x1000
        proc.write_memory(addr, mem_val)
        proc.write_memory_bytes(0, [opcode, addr & 0xFF, addr >> 8])
        proc.write_psw(0)
        proc.step()
        if verify_a:
            self.assertEqual(proc.read_gp_reg(Registers.A), expected_a,
                "opcode 0x%02x: A=0x%02x, [0x%04x]=0x%02x -> expected 0x%02x got 0x%02x" %
                (opcode, a_val, addr, mem_val, expected_a, proc.read_gp_reg(Registers.A)))

    def _test_alu_hl_imm(self, opcode, a_val, mem_val, offset, expected_a, verify_a=True):
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_gp_reg(Registers.A, a_val)
        base = 0x1000
        proc.write_gp_regpair(RegisterPairs.HL, base)
        proc.write_memory(base + offset, mem_val)
        proc.write_memory_bytes(0, [opcode, offset])
        proc.write_psw(0)
        proc.step()
        if verify_a:
            self.assertEqual(proc.read_gp_reg(Registers.A), expected_a)

    def _test_alu_saddr(self, opcode, a_val, mem_val, expected_a, verify_a=True):
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_gp_reg(Registers.A, a_val)
        saddr = 0xFE30  # operand byte = 0x30
        proc.write_memory(saddr, mem_val)
        proc.write_memory_bytes(0, [opcode, 0x30])
        proc.write_psw(0)
        proc.step()
        if verify_a:
            self.assertEqual(proc.read_gp_reg(Registers.A), expected_a,
                "opcode 0x%02x saddr: A=0x%02x, [0x%04x]=0x%02x -> expected 0x%02x got 0x%02x" %
                (opcode, a_val, saddr, mem_val, expected_a, proc.read_gp_reg(Registers.A)))

    def _test_alu_hl(self, opcode, a_val, mem_val, expected_a, verify_a=True):
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_gp_reg(Registers.A, a_val)
        addr = 0x1000
        proc.write_gp_regpair(RegisterPairs.HL, addr)
        proc.write_memory(addr, mem_val)
        proc.write_memory_bytes(0, [opcode])
        proc.write_psw(0)
        proc.step()
        if verify_a:
            self.assertEqual(proc.read_gp_reg(Registers.A), expected_a)

    # ADD A,<addr> — all 4 modes
    def test_add_addr16_result(self):
        self._test_alu_addr16(0x08, 0x30, 0x15, 0x45)

    def test_add_hl_imm_result(self):
        self._test_alu_hl_imm(0x09, 0x30, 0x15, 0x20, 0x45)

    def test_add_saddr_result(self):
        self._test_alu_saddr(0x0e, 0x30, 0x15, 0x45)

    def test_add_hl_result(self):
        self._test_alu_hl(0x0f, 0x30, 0x15, 0x45)

    # SUB A,<addr>
    def test_sub_addr16_result(self):
        self._test_alu_addr16(0x18, 0x50, 0x15, 0x3B)

    def test_sub_hl_imm_result(self):
        self._test_alu_hl_imm(0x19, 0x50, 0x15, 0x20, 0x3B)

    def test_sub_saddr_result(self):
        self._test_alu_saddr(0x1e, 0x50, 0x15, 0x3B)

    def test_sub_hl_result(self):
        self._test_alu_hl(0x1f, 0x50, 0x15, 0x3B)

    # ADDC A,<addr>
    def test_addc_addr16_result(self):
        self._test_alu_addr16(0x28, 0x30, 0x15, 0x45)

    def test_addc_hl_imm_result(self):
        self._test_alu_hl_imm(0x29, 0x30, 0x15, 0x20, 0x45)

    def test_addc_saddr_result(self):
        self._test_alu_saddr(0x2e, 0x30, 0x15, 0x45)

    def test_addc_hl_result(self):
        self._test_alu_hl(0x2f, 0x30, 0x15, 0x45)

    # SUBC A,<addr>
    def test_subc_addr16_result(self):
        self._test_alu_addr16(0x38, 0x50, 0x15, 0x3B)

    def test_subc_hl_imm_result(self):
        self._test_alu_hl_imm(0x39, 0x50, 0x15, 0x20, 0x3B)

    def test_subc_saddr_result(self):
        self._test_alu_saddr(0x3e, 0x50, 0x15, 0x3B)

    def test_subc_hl_result(self):
        self._test_alu_hl(0x3f, 0x50, 0x15, 0x3B)

    # CMP A,<addr> — A must NOT change
    def test_cmp_addr16_a_preserved(self):
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_gp_reg(Registers.A, 0x50)
        proc.write_memory(0x1000, 0x15)
        proc.write_memory_bytes(0, [0x48, 0x00, 0x10])
        proc.write_psw(0)
        proc.step()
        self.assertEqual(proc.read_gp_reg(Registers.A), 0x50)

    def test_cmp_hl_imm_a_preserved(self):
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_gp_reg(Registers.A, 0x50)
        proc.write_gp_regpair(RegisterPairs.HL, 0x1000)
        proc.write_memory(0x1020, 0x15)
        proc.write_memory_bytes(0, [0x49, 0x20])
        proc.write_psw(0)
        proc.step()
        self.assertEqual(proc.read_gp_reg(Registers.A), 0x50)

    def test_cmp_saddr_a_preserved(self):
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_gp_reg(Registers.A, 0x50)
        proc.write_memory(0xFE30, 0x15)
        proc.write_memory_bytes(0, [0x4e, 0x30])
        proc.write_psw(0)
        proc.step()
        self.assertEqual(proc.read_gp_reg(Registers.A), 0x50)

    def test_cmp_hl_a_preserved(self):
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_gp_reg(Registers.A, 0x50)
        proc.write_gp_regpair(RegisterPairs.HL, 0x1000)
        proc.write_memory(0x1000, 0x15)
        proc.write_memory_bytes(0, [0x4f])
        proc.write_psw(0)
        proc.step()
        self.assertEqual(proc.read_gp_reg(Registers.A), 0x50)

    # AND A,<addr>
    def test_and_addr16_result(self):
        self._test_alu_addr16(0x58, 0xF3, 0x3C, 0x30)

    def test_and_hl_imm_result(self):
        self._test_alu_hl_imm(0x59, 0xF3, 0x3C, 0x20, 0x30)

    def test_and_saddr_result(self):
        self._test_alu_saddr(0x5e, 0xF3, 0x3C, 0x30)

    def test_and_hl_result(self):
        self._test_alu_hl(0x5f, 0xF3, 0x3C, 0x30)

    # OR A,<addr>
    def test_or_addr16_result(self):
        self._test_alu_addr16(0x68, 0xF0, 0x0C, 0xFC)

    def test_or_hl_imm_result(self):
        self._test_alu_hl_imm(0x69, 0xF0, 0x0C, 0x20, 0xFC)

    def test_or_saddr_result(self):
        self._test_alu_saddr(0x6e, 0xF0, 0x0C, 0xFC)

    def test_or_hl_result(self):
        self._test_alu_hl(0x6f, 0xF0, 0x0C, 0xFC)

    # XOR A,<addr>
    def test_xor_addr16_result(self):
        self._test_alu_addr16(0x78, 0xFF, 0x0F, 0xF0)

    def test_xor_hl_imm_result(self):
        self._test_alu_hl_imm(0x79, 0xFF, 0x0F, 0x20, 0xF0)

    def test_xor_saddr_result(self):
        self._test_alu_saddr(0x7e, 0xFF, 0x0F, 0xF0)

    def test_xor_hl_result(self):
        self._test_alu_hl(0x7f, 0xFF, 0x0F, 0xF0)


class TestSaddrAluResults(unittest.TestCase):
    """ADD/SUB/ADDC/SUBC/AND/OR/XOR saddr,#imm — verify the actual
    value written to the saddr location."""

    def _test_saddr_alu(self, opcode, init_mem, imm, expected_mem):
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        saddr = 0xFE30
        proc.write_memory(saddr, init_mem)
        proc.write_gp_reg(Registers.A, 0xAA)  # distinct value to ensure A not clobbered
        proc.write_memory_bytes(0, [opcode, 0x30, imm])
        proc.write_psw(0)
        proc.step()
        self.assertEqual(proc.read_memory(saddr), expected_mem,
            "opcode 0x%02x: [saddr]=0x%02x, #0x%02x -> expected 0x%02x got 0x%02x" %
            (opcode, init_mem, imm, expected_mem, proc.read_memory(saddr)))
        self.assertEqual(proc.read_gp_reg(Registers.A), 0xAA,
            "opcode 0x%02x: A was clobbered" % opcode)

    def test_add_saddr_result(self):
        self._test_saddr_alu(0x88, 0x30, 0x15, 0x45)

    def test_sub_saddr_result(self):
        self._test_saddr_alu(0x98, 0x50, 0x15, 0x3B)

    def test_addc_saddr_result(self):
        self._test_saddr_alu(0xa8, 0x30, 0x15, 0x45)

    def test_subc_saddr_result(self):
        self._test_saddr_alu(0xb8, 0x50, 0x15, 0x3B)

    def test_cmp_saddr_mem_unchanged(self):
        """CMP saddr,#imm must NOT modify the saddr value."""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        saddr = 0xFE30
        proc.write_memory(saddr, 0x50)
        proc.write_memory_bytes(0, [0xc8, 0x30, 0x15])
        proc.write_psw(0)
        proc.step()
        self.assertEqual(proc.read_memory(saddr), 0x50)

    def test_and_saddr_result(self):
        self._test_saddr_alu(0xd8, 0xF3, 0x3C, 0x30)

    def test_or_saddr_result(self):
        self._test_saddr_alu(0xe8, 0xF0, 0x0C, 0xFC)

    def test_xor_saddr_result(self):
        self._test_saddr_alu(0xf8, 0xFF, 0x0F, 0xF0)


class TestPrefix31AluResults(unittest.TestCase):
    """Verify prefix 0x31 ALU ops read from the correct [HL+C] or [HL+B]
    address and write the correct result to A."""

    def _test_hl_c(self, op_byte, a_val, mem_val, expected_a, verify_a=True):
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_gp_reg(Registers.A, a_val)
        proc.write_gp_regpair(RegisterPairs.HL, 0x1000)
        proc.write_gp_reg(Registers.C, 0x20)
        proc.write_memory(0x1020, mem_val)
        proc.write_memory_bytes(0, [0x31, op_byte])
        proc.write_psw(0)
        proc.step()
        if verify_a:
            self.assertEqual(proc.read_gp_reg(Registers.A), expected_a,
                "0x31 0x%02x [HL+C]: expected A=0x%02x got 0x%02x" %
                (op_byte, expected_a, proc.read_gp_reg(Registers.A)))

    def _test_hl_b(self, op_byte, a_val, mem_val, expected_a, verify_a=True):
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_gp_reg(Registers.A, a_val)
        proc.write_gp_regpair(RegisterPairs.HL, 0x1000)
        proc.write_gp_reg(Registers.B, 0x30)
        proc.write_memory(0x1030, mem_val)
        proc.write_memory_bytes(0, [0x31, op_byte])
        proc.write_psw(0)
        proc.step()
        if verify_a:
            self.assertEqual(proc.read_gp_reg(Registers.A), expected_a,
                "0x31 0x%02x [HL+B]: expected A=0x%02x got 0x%02x" %
                (op_byte, expected_a, proc.read_gp_reg(Registers.A)))

    def test_add_hl_c_result(self):
        self._test_hl_c(0x0a, 0x30, 0x15, 0x45)

    def test_add_hl_b_result(self):
        self._test_hl_b(0x0b, 0x30, 0x15, 0x45)

    def test_sub_hl_c_result(self):
        self._test_hl_c(0x1a, 0x50, 0x15, 0x3B)

    def test_sub_hl_b_result(self):
        self._test_hl_b(0x1b, 0x50, 0x15, 0x3B)

    def test_addc_hl_c_result(self):
        self._test_hl_c(0x2a, 0x30, 0x15, 0x45)

    def test_addc_hl_b_result(self):
        self._test_hl_b(0x2b, 0x30, 0x15, 0x45)

    def test_subc_hl_c_result(self):
        self._test_hl_c(0x3a, 0x50, 0x15, 0x3B)

    def test_subc_hl_b_result(self):
        self._test_hl_b(0x3b, 0x50, 0x15, 0x3B)

    def test_cmp_hl_c_a_preserved(self):
        self._test_hl_c(0x4a, 0x50, 0x15, 0x50, verify_a=True)
        # CMP doesn't change A

    def test_cmp_hl_b_a_preserved(self):
        self._test_hl_b(0x4b, 0x50, 0x15, 0x50, verify_a=True)

    def test_and_hl_c_result(self):
        self._test_hl_c(0x5a, 0xF3, 0x3C, 0x30)

    def test_and_hl_b_result(self):
        self._test_hl_b(0x5b, 0xF3, 0x3C, 0x30)

    def test_or_hl_c_result(self):
        self._test_hl_c(0x6a, 0xF0, 0x0C, 0xFC)

    def test_or_hl_b_result(self):
        self._test_hl_b(0x6b, 0xF0, 0x0C, 0xFC)

    def test_xor_hl_c_result(self):
        self._test_hl_c(0x7a, 0xFF, 0x0F, 0xF0)

    def test_xor_hl_b_result(self):
        self._test_hl_b(0x7b, 0xFF, 0x0F, 0xF0)


class TestPrefix61AluResults(unittest.TestCase):
    """For prefix 0x61 register ALU ops, verify the correct register
    is used as the source and the result is written to the correct
    destination. Uses distinct register values to catch wrong-register bugs."""

    def _setup_distinct_regs(self, proc):
        """Set all registers to distinct values so wrong-register reads are caught."""
        proc.write_gp_reg(Registers.X, 0x11)
        proc.write_gp_reg(Registers.A, 0x22)
        proc.write_gp_reg(Registers.C, 0x33)
        proc.write_gp_reg(Registers.B, 0x44)
        proc.write_gp_reg(Registers.E, 0x55)
        proc.write_gp_reg(Registers.D, 0x66)
        proc.write_gp_reg(Registers.L, 0x77)
        proc.write_gp_reg(Registers.H, 0x88)

    def test_add_r_a_all_regs(self):
        """ADD r,A (0x61 0x00-0x07): result stored in r, A unchanged."""
        reg_vals = {0: 0x11, 1: 0x22, 2: 0x33, 3: 0x44, 4: 0x55, 5: 0x66, 6: 0x77, 7: 0x88}
        a_val = 0x22
        for r in range(8):
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            self._setup_distinct_regs(proc)
            proc.write_psw(0)
            proc.write_memory_bytes(0, [0x61, r])
            proc.step()
            expected = (reg_vals[r] + a_val) & 0xFF
            self.assertEqual(proc.read_gp_reg(r), expected,
                "ADD r%d,A: expected 0x%02x got 0x%02x" % (r, expected, proc.read_gp_reg(r)))

    def test_add_a_r_all_regs(self):
        """ADD A,r (0x61 0x08-0x0F): result stored in A."""
        reg_vals = {0: 0x11, 2: 0x33, 3: 0x44, 4: 0x55, 5: 0x66, 6: 0x77, 7: 0x88}
        a_val = 0x22
        for r, val in reg_vals.items():
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            self._setup_distinct_regs(proc)
            proc.write_psw(0)
            proc.write_memory_bytes(0, [0x61, 0x08 + r])
            proc.step()
            expected = (a_val + val) & 0xFF
            self.assertEqual(proc.read_gp_reg(Registers.A), expected,
                "ADD A,r%d: expected 0x%02x got 0x%02x" % (r, expected, proc.read_gp_reg(Registers.A)))

    def test_sub_r_a_all_regs(self):
        """SUB r,A (0x61 0x10-0x17): result stored in r."""
        reg_vals = {0: 0x11, 1: 0x22, 2: 0x33, 3: 0x44, 4: 0x55, 5: 0x66, 6: 0x77, 7: 0x88}
        a_val = 0x22
        for r in range(8):
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            self._setup_distinct_regs(proc)
            proc.write_psw(0)
            proc.write_memory_bytes(0, [0x61, 0x10 + r])
            proc.step()
            expected = (reg_vals[r] - a_val) & 0xFF
            self.assertEqual(proc.read_gp_reg(r), expected,
                "SUB r%d,A: expected 0x%02x got 0x%02x" % (r, expected, proc.read_gp_reg(r)))

    def test_sub_a_r_all_regs(self):
        """SUB A,r (0x61 0x18-0x1F): result stored in A."""
        reg_vals = {0: 0x11, 2: 0x33, 3: 0x44, 4: 0x55, 5: 0x66, 6: 0x77, 7: 0x88}
        a_val = 0x22
        for r, val in reg_vals.items():
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            self._setup_distinct_regs(proc)
            proc.write_psw(0)
            proc.write_memory_bytes(0, [0x61, 0x18 + r])
            proc.step()
            expected = (a_val - val) & 0xFF
            self.assertEqual(proc.read_gp_reg(Registers.A), expected,
                "SUB A,r%d: expected 0x%02x got 0x%02x" % (r, expected, proc.read_gp_reg(Registers.A)))

    def test_cmp_r_a_all_regs(self):
        """CMP r,A (0x61 0x40-0x47): r unchanged, flags reflect r - A."""
        reg_vals = {0: 0x11, 1: 0x22, 2: 0x33, 3: 0x44, 4: 0x55, 5: 0x66, 6: 0x77, 7: 0x88}
        a_val = 0x22
        for r in range(8):
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            self._setup_distinct_regs(proc)
            proc.write_psw(0)
            proc.write_memory_bytes(0, [0x61, 0x40 + r])
            proc.step()
            self.assertEqual(proc.read_gp_reg(r), reg_vals[r],
                "CMP r%d,A: r%d was modified" % (r, r))
            diff = reg_vals[r] - a_val
            psw = proc.read_psw()
            if (diff & 0xFF) == 0:
                self.assertTrue(psw & Flags.Z, "CMP r%d,A: Z wrong" % r)
            else:
                self.assertFalse(psw & Flags.Z, "CMP r%d,A: Z wrong" % r)

    def test_and_or_xor_a_r_result(self):
        """AND/OR/XOR A,r: verify result using distinct register values."""
        ops = {
            0x58: lambda a, b: a & b,   # AND A,r
            0x68: lambda a, b: a | b,   # OR A,r
            0x78: lambda a, b: a ^ b,   # XOR A,r
        }
        reg_vals = {0: 0x11, 2: 0x33, 3: 0x44, 4: 0x55, 5: 0x66, 6: 0x77, 7: 0x88}
        for base_op, fn in ops.items():
            for r, val in reg_vals.items():
                proc, _ = _make_processor()
                proc.write_sp(0xFE00)
                self._setup_distinct_regs(proc)
                proc.write_psw(0)
                proc.write_memory_bytes(0, [0x61, base_op + r])
                proc.step()
                expected = fn(0x22, val) & 0xFF  # A=0x22
                self.assertEqual(proc.read_gp_reg(Registers.A), expected,
                    "0x61 0x%02x: expected A=0x%02x got 0x%02x" %
                    (base_op + r, expected, proc.read_gp_reg(Registers.A)))

    def test_and_or_xor_r_a_result(self):
        """AND/OR/XOR r,A: verify result using distinct register values."""
        ops = {
            0x50: lambda a, b: a & b,   # AND r,A
            0x60: lambda a, b: a | b,   # OR r,A
            0x70: lambda a, b: a ^ b,   # XOR r,A
        }
        reg_vals = {0: 0x11, 1: 0x22, 2: 0x33, 3: 0x44, 4: 0x55, 5: 0x66, 6: 0x77, 7: 0x88}
        for base_op, fn in ops.items():
            for r in range(8):
                proc, _ = _make_processor()
                proc.write_sp(0xFE00)
                self._setup_distinct_regs(proc)
                proc.write_psw(0)
                proc.write_memory_bytes(0, [0x61, base_op + r])
                proc.step()
                expected = fn(reg_vals[r], 0x22) & 0xFF  # A=0x22
                self.assertEqual(proc.read_gp_reg(r), expected,
                    "0x61 0x%02x: expected r%d=0x%02x got 0x%02x" %
                    (base_op + r, r, expected, proc.read_gp_reg(r)))


class TestInterruptDelay(unittest.TestCase):
    """Verify _interrupt_delayed is set by instructions that require it.

    The flag is set by the instruction handler, then consumed by step()
    after the handler returns. We check it between handler execution and
    the interrupt check by inspecting the flag inside a custom step."""

    def _run_and_check_delayed(self, proc, code):
        """Run instruction and return True if it set _interrupt_delayed."""
        proc.write_memory_bytes(0, code)
        proc.pc = 0
        proc._inst_cycles = 0
        opcode = proc._consume_byte()
        handler = proc._opcodes_unprefixed[opcode]
        handler(opcode)
        return proc._interrupt_delayed

    def test_reti_sets_interrupt_delayed(self):
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_memory(0xFDFD, 0x00)
        proc.write_memory(0xFDFE, 0x10)
        proc.write_memory(0xFDFF, 0x00)
        proc.write_sp(0xFDFD)
        self.assertTrue(self._run_and_check_delayed(proc, [0x8F]))

    def test_retb_sets_interrupt_delayed(self):
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_memory(0xFDFD, 0x00)
        proc.write_memory(0xFDFE, 0x10)
        proc.write_memory(0xFDFF, 0x00)
        proc.write_sp(0xFDFD)
        self.assertTrue(self._run_and_check_delayed(proc, [0x9F]))

    def test_pop_psw_sets_interrupt_delayed(self):
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_memory(0xFDFF, 0x00)
        proc.write_sp(0xFDFF)
        self.assertTrue(self._run_and_check_delayed(proc, [0x23]))

    def test_mov_psw_a_sets_interrupt_delayed(self):
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_gp_reg(Registers.A, 0x00)
        self.assertTrue(self._run_and_check_delayed(proc, [0xF2, 0x1E]))

    def test_mov_psw_imm_sets_interrupt_delayed(self):
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        self.assertTrue(self._run_and_check_delayed(proc, [0x11, 0x1E, 0x00]))

    def test_mov_saddr_a_does_not_set_interrupt_delayed(self):
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_gp_reg(Registers.A, 0x42)
        self.assertFalse(self._run_and_check_delayed(proc, [0xF2, 0x30]))

    def test_mov_saddr_imm_does_not_set_interrupt_delayed(self):
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        self.assertFalse(self._run_and_check_delayed(proc, [0x11, 0x30, 0x42]))

    def test_ei_sets_interrupt_delayed(self):
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        self.assertTrue(self._run_and_check_delayed(proc, [0x7A, 0x1E]))

    def test_set1_non_psw_does_not_set_interrupt_delayed(self):
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        self.assertFalse(self._run_and_check_delayed(proc, [0x7A, 0x30]))

    def test_push_psw_sets_interrupt_delayed(self):
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        self.assertTrue(self._run_and_check_delayed(proc, [0x22]))

    def test_di_sets_interrupt_delayed(self):
        """DI (CLR1 PSW.7) should set interrupt delayed."""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        self.assertTrue(self._run_and_check_delayed(proc, [0x7B, 0x1E]))

    def test_mov_a_psw_sets_interrupt_delayed(self):
        """MOV A,PSW (read from PSW) should set interrupt delayed."""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        self.assertTrue(self._run_and_check_delayed(proc, [0xF0, 0x1E]))

    def test_set1_psw_any_bit_sets_interrupt_delayed(self):
        """SET1 PSW.0 (not just PSW.7) should set interrupt delayed."""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        self.assertTrue(self._run_and_check_delayed(proc, [0x0A, 0x1E]))

    def test_clr1_saddr_non_psw_no_delay(self):
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        self.assertFalse(self._run_and_check_delayed(proc, [0x0B, 0x30]))

    def test_mov_sfr_touching_mk0l_sets_interrupt_delayed(self):
        """MOV sfr,A where sfr=MK0L (0xFFE4) should set interrupt delayed."""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_gp_reg(Registers.A, 0xFF)
        # sfr operand byte 0xE4 -> address 0xFFE4 = MK0L
        self.assertTrue(self._run_and_check_delayed(proc, [0xF6, 0xE4]))

    def test_mov_sfr_touching_pr0l_sets_interrupt_delayed(self):
        """MOV A,sfr where sfr=PR0L (0xFFE8) should set interrupt delayed."""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        # sfr operand byte 0xE8 -> address 0xFFE8 = PR0L
        self.assertTrue(self._run_and_check_delayed(proc, [0xF4, 0xE8]))

    def test_mov_sfr_non_interrupt_reg_no_delay(self):
        """MOV sfr,A where sfr is not PSW/IF/MK/PR should NOT set delay."""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_gp_reg(Registers.A, 0x00)
        # sfr operand byte 0x80 -> address 0xFF80 (not an interrupt reg)
        self.assertFalse(self._run_and_check_delayed(proc, [0xF6, 0x80]))

    def test_set1_sfr_touching_if0l_sets_interrupt_delayed(self):
        """SET1 sfr.bit where sfr=IF0L (0xFFE0) should set interrupt delayed."""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        # 0x71 0x0A sfr_byte: SET1 sfr.0, sfr byte 0xE0 -> 0xFFE0 = IF0L
        self.assertTrue(self._run_and_check_delayed(proc, [0x71, 0x0A, 0xE0]))

    def test_nop_does_not_set_interrupt_delayed(self):
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        self.assertFalse(self._run_and_check_delayed(proc, [0x00]))


class TestEdgeCases(unittest.TestCase):
    def test_pc_wraps_at_0xffff(self):
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_memory(0xFFFF, 0x00)  # NOP at last address
        proc.pc = 0xFFFF
        proc.step()
        self.assertEqual(proc.pc, 0x0000)

    def test_sp_wraps_on_push(self):
        proc, _ = _make_processor()
        proc.write_sp(0x0001)
        proc.write_memory_bytes(0, [0x22])  # PUSH PSW
        proc.step()
        self.assertEqual(proc.read_sp(), 0x0000)

    def test_hl_byte_address_wraps(self):
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_gp_regpair(RegisterPairs.HL, 0xFFFF)
        proc.write_memory(0x0009, 0x42)  # 0xFFFF + 0x0A = 0x10009 & 0xFFFF = 0x0009
        proc.write_memory_bytes(0, [0xAE, 0x0A])  # MOV A,[HL+0AH]
        proc.step()
        self.assertEqual(proc.read_gp_reg(Registers.A), 0x42)

    def test_hl_b_address_wraps(self):
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_gp_regpair(RegisterPairs.HL, 0xFFF0)
        proc.write_gp_reg(Registers.B, 0x20)
        proc.write_memory(0x0010, 0x55)  # 0xFFF0 + 0x20 = 0x10010 & 0xFFFF = 0x0010
        proc.write_memory_bytes(0, [0xAB])  # MOV A,[HL+B]
        proc.step()
        self.assertEqual(proc.read_gp_reg(Registers.A), 0x55)

    def test_hl_c_address_wraps(self):
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_gp_regpair(RegisterPairs.HL, 0xFFF0)
        proc.write_gp_reg(Registers.C, 0x20)
        proc.write_memory(0x0010, 0x66)
        proc.write_memory_bytes(0, [0xAA])  # MOV A,[HL+C]
        proc.step()
        self.assertEqual(proc.read_gp_reg(Registers.A), 0x66)

    def test_add_0xff_plus_1(self):
        """All three flags simultaneously: Z=1, CY=1, AC=1."""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_gp_reg(Registers.A, 0xFF)
        proc.write_memory_bytes(0, [0x0D, 0x01])
        proc.step()
        self.assertEqual(proc.read_gp_reg(Registers.A), 0x00)
        psw = proc.read_psw()
        self.assertTrue(psw & Flags.Z)
        self.assertTrue(psw & Flags.CY)
        self.assertTrue(psw & Flags.AC)

    def test_sub_0_minus_1(self):
        """Borrow and half-borrow simultaneously."""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_gp_reg(Registers.A, 0x00)
        proc.write_memory_bytes(0, [0x1D, 0x01])
        proc.step()
        self.assertEqual(proc.read_gp_reg(Registers.A), 0xFF)
        psw = proc.read_psw()
        self.assertTrue(psw & Flags.CY)
        self.assertTrue(psw & Flags.AC)

    def test_addw_0xffff_plus_1(self):
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_gp_regpair(RegisterPairs.AX, 0xFFFF)
        proc.write_memory_bytes(0, [0xCA, 0x01, 0x00])
        proc.step()
        self.assertEqual(proc.read_gp_regpair(RegisterPairs.AX), 0x0000)
        psw = proc.read_psw()
        self.assertTrue(psw & Flags.Z)
        self.assertTrue(psw & Flags.CY)

    def test_branch_max_forward(self):
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_psw(Flags.CY)
        proc.write_memory_bytes(0x100, [0x8D, 0x7F])  # BC $+127
        proc.pc = 0x100
        proc.step()
        self.assertEqual(proc.pc, 0x102 + 0x7F)

    def test_branch_max_backward(self):
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_psw(Flags.CY)
        proc.write_memory_bytes(0x200, [0x8D, 0x80])  # BC $-128
        proc.pc = 0x200
        proc.step()
        self.assertEqual(proc.pc, 0x202 - 128)

    def test_branch_zero_displacement(self):
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_psw(Flags.CY)
        proc.write_memory_bytes(0x100, [0x8D, 0x00])  # BC $+0
        proc.pc = 0x100
        proc.step()
        self.assertEqual(proc.pc, 0x102)

    def test_psw_bit2_always_zero(self):
        proc, _ = _make_processor()
        proc.write_psw(0xFF)
        self.assertEqual(proc.read_psw() & 0x04, 0)

    def test_reset_sets_psw_to_02(self):
        proc, _ = _make_processor()
        proc.write_memory(0x0000, 0x00)
        proc.write_memory(0x0001, 0x01)
        proc.reset()
        self.assertEqual(proc.read_psw(), 0x02)
        self.assertEqual(proc.pc, 0x0100)


class TestCallfAllPages(unittest.TestCase):
    def test_callf_all_8_pages(self):
        for page in range(8):
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            opcode = 0x0C | (page << 4)
            proc.write_memory_bytes(0, [opcode, 0xFF])
            proc.step()
            expected = 0x0800 | (page << 8) | 0xFF
            self.assertEqual(proc.pc, expected,
                "CALLF page %d: expected 0x%04x got 0x%04x" % (page, expected, proc.pc))
            # Verify return address pushed
            ret_lo = proc.read_memory(proc.read_sp())
            ret_hi = proc.read_memory(proc.read_sp() + 1)
            self.assertEqual((ret_hi << 8) | ret_lo, 0x0002)

    def test_callf_all_8_pages_low_offset(self):
        for page in range(8):
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            opcode = 0x0C | (page << 4)
            proc.write_memory_bytes(0, [opcode, 0x00])
            proc.step()
            expected = 0x0800 | (page << 8)
            self.assertEqual(proc.pc, expected)


class TestCaltAllEntries(unittest.TestCase):
    def test_callt_all_32_entries(self):
        for ta in range(32):
            proc, _ = _make_processor()
            proc.write_sp(0xFE00)
            table_addr = 0x0040 + ta * 2
            proc.write_memory(table_addr, ta & 0xFF)
            proc.write_memory(table_addr + 1, 0x10)
            opcode = 0xC1 | (ta << 1)
            proc.write_memory_bytes(0, [opcode])
            proc.step()
            expected = 0x1000 | ta
            self.assertEqual(proc.pc, expected,
                "CALLT [%04XH]: expected 0x%04x got 0x%04x" % (table_addr, expected, proc.pc))
            ret_lo = proc.read_memory(proc.read_sp())
            ret_hi = proc.read_memory(proc.read_sp() + 1)
            self.assertEqual((ret_hi << 8) | ret_lo, 0x0001)


class TestNibbleRotateRoundtrip(unittest.TestCase):
    def test_ror4_then_rol4_restores(self):
        """ROR4 followed by ROL4 should restore original values."""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_gp_regpair(RegisterPairs.HL, 0x1000)
        for a_val in range(256):
            for mem_val in range(256):
                proc.write_gp_reg(Registers.A, a_val)
                proc.write_memory(0x1000, mem_val)
                proc.write_memory_bytes(0, [0x31, 0x90, 0x31, 0x80])  # ROR4, ROL4
                proc.pc = 0
                proc.step()
                proc.step()
                self.assertEqual(proc.read_gp_reg(Registers.A), a_val,
                    "ROR4+ROL4 A: start=0x%02x mem=0x%02x" % (a_val, mem_val))
                self.assertEqual(proc.read_memory(0x1000), mem_val,
                    "ROR4+ROL4 mem: A=0x%02x start=0x%02x" % (a_val, mem_val))

    def test_rol4_then_ror4_restores(self):
        """ROL4 followed by ROR4 should restore original values."""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_gp_regpair(RegisterPairs.HL, 0x1000)
        for a_val in range(256):
            for mem_val in range(256):
                proc.write_gp_reg(Registers.A, a_val)
                proc.write_memory(0x1000, mem_val)
                proc.write_memory_bytes(0, [0x31, 0x80, 0x31, 0x90])  # ROL4, ROR4
                proc.pc = 0
                proc.step()
                proc.step()
                self.assertEqual(proc.read_gp_reg(Registers.A), a_val)
                self.assertEqual(proc.read_memory(0x1000), mem_val)


class TestDbnzFullLoop(unittest.TestCase):
    def test_dbnz_b_counts_to_zero(self):
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_gp_reg(Registers.B, 5)
        proc.write_memory_bytes(0x100, [0x8B, 0xFE])  # DBNZ B, $-2 (loop back)
        proc.pc = 0x100
        for _ in range(10):
            proc.step()
            if proc.read_gp_reg(Registers.B) == 0:
                break
        self.assertEqual(proc.read_gp_reg(Registers.B), 0)
        self.assertEqual(proc.pc, 0x102)  # fell through

    def test_dbnz_c_counts_to_zero(self):
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_gp_reg(Registers.C, 3)
        proc.write_memory_bytes(0x100, [0x8A, 0xFE])
        proc.pc = 0x100
        for _ in range(10):
            proc.step()
            if proc.read_gp_reg(Registers.C) == 0:
                break
        self.assertEqual(proc.read_gp_reg(Registers.C), 0)
        self.assertEqual(proc.pc, 0x102)

    def test_dbnz_saddr_counts_to_zero(self):
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_memory(0xFE30, 4)  # saddr offset 0x30 -> address 0xFE30
        proc.write_memory_bytes(0x100, [0x04, 0x30, 0xFD])  # DBNZ saddr, $-3
        proc.pc = 0x100
        for _ in range(10):
            proc.step()
            if proc.read_memory(0xFE30) == 0:
                break
        self.assertEqual(proc.read_memory(0xFE30), 0)
        self.assertEqual(proc.pc, 0x103)


class TestIntegration(unittest.TestCase):
    def test_loop_sum_1_to_5(self):
        """Sum numbers 1 to 5 using DBNZ loop."""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        code = [
            0xA1, 0x00,       # MOV A, #00H    ; sum = 0
            0xA3, 0x05,       # MOV B, #05H    ; counter = 5
            # loop (offset 4):
            0x61, 0x0B,       # ADD A, B       ; sum += counter
            0x8B, 0xFC,       # DBNZ B, loop   ; counter--; if != 0 goto loop
            0x00,             # NOP
        ]
        proc.write_memory_bytes(0x100, code)
        proc.pc = 0x100
        for _ in range(20):
            proc.step()
            if proc.pc == 0x108:
                break
        self.assertEqual(proc.read_gp_reg(Registers.A), 15)  # 1+2+3+4+5

    def test_memory_copy_with_de_hl(self):
        """Copy 4 bytes from src to dst using [DE] and [HL]."""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        src = 0x1000
        dst = 0x2000
        for i in range(4):
            proc.write_memory(src + i, 0x10 * (i + 1))
        code = [
            0x16, dst & 0xFF, dst >> 8,   # MOVW HL, #dst
            0x14, src & 0xFF, src >> 8,   # MOVW DE, #src
            0xA3, 0x04,                    # MOV B, #04H
            # loop (offset 8):
            0x85,                          # MOV A, [DE]
            0x97,                          # MOV [HL], A
            0x84,                          # INCW DE
            0x86,                          # INCW HL
            0x8B, 0xFA,                    # DBNZ B, loop
            0x00,                          # NOP
        ]
        proc.write_memory_bytes(0x100, code)
        proc.pc = 0x100
        for _ in range(50):
            proc.step()
            if proc.pc >= 0x10D:
                break
        for i in range(4):
            self.assertEqual(proc.read_memory(dst + i), 0x10 * (i + 1),
                "byte %d: expected 0x%02x" % (i, 0x10 * (i + 1)))

    def test_subroutine_with_bank_switch(self):
        """Call a subroutine that uses a different register bank."""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_rb(0)
        code_main = [
            0xA1, 0xAA,       # MOV A, #AAH (in bank 0)
            0x9A, 0x00, 0x02, # CALL !0200H
            0x00,             # NOP (A should still be AA)
        ]
        code_sub = [
            0x61, 0xD8,       # SEL RB1
            0xA1, 0xBB,       # MOV A, #BBH (in bank 1)
            0x61, 0xD0,       # SEL RB0
            0xAF,             # RET
        ]
        proc.write_memory_bytes(0x100, code_main)
        proc.write_memory_bytes(0x200, code_sub)
        proc.pc = 0x100
        for _ in range(10):
            proc.step()
            if proc.pc == 0x105:
                break
        self.assertEqual(proc.read_gp_reg(Registers.A), 0xAA)
        self.assertEqual(proc.read_rb(), 0)
        proc.write_rb(1)
        self.assertEqual(proc.read_gp_reg(Registers.A), 0xBB)

    def test_multiply_divide_roundtrip(self):
        """Multiply then divide should get back original values."""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_gp_reg(Registers.A, 0x07)
        proc.write_gp_reg(Registers.X, 0x0B)
        proc.write_memory_bytes(0, [0x31, 0x88])  # MULU X
        proc.step()
        self.assertEqual(proc.read_gp_regpair(RegisterPairs.AX), 0x004D)  # 7*11=77
        proc.write_gp_reg(Registers.C, 0x0B)
        proc.write_memory_bytes(2, [0x31, 0x82])  # DIVUW C
        proc.step()
        self.assertEqual(proc.read_gp_regpair(RegisterPairs.AX), 0x0007)
        self.assertEqual(proc.read_gp_reg(Registers.C), 0x00)

    def test_16bit_addition(self):
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_gp_regpair(RegisterPairs.AX, 0x1234)
        proc.write_memory_bytes(0, [0xCA, 0x78, 0x56])  # ADDW AX, #5678H
        proc.step()
        self.assertEqual(proc.read_gp_regpair(RegisterPairs.AX), 0x68AC)


class TestBCDAdjustIntegration(unittest.TestCase):
    def test_bcd_add_25_plus_37(self):
        """25 + 37 = 62 in BCD."""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_gp_reg(Registers.A, 0x25)
        proc.write_psw(0)
        proc.write_memory_bytes(0, [0x0D, 0x37, 0x61, 0x80])  # ADD A,#37; ADJBA
        proc.pc = 0
        proc.step()
        proc.step()
        self.assertEqual(proc.read_gp_reg(Registers.A), 0x62)
        self.assertFalse(proc.read_psw() & Flags.CY)

    def test_bcd_add_99_plus_01(self):
        """99 + 01 = 100 in BCD -> A=00, CY=1."""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_gp_reg(Registers.A, 0x99)
        proc.write_psw(0)
        proc.write_memory_bytes(0, [0x0D, 0x01, 0x61, 0x80])
        proc.pc = 0
        proc.step()
        proc.step()
        self.assertEqual(proc.read_gp_reg(Registers.A), 0x00)
        self.assertTrue(proc.read_psw() & Flags.CY)

    def test_bcd_sub_62_minus_37(self):
        """62 - 37 = 25 in BCD."""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_gp_reg(Registers.A, 0x62)
        proc.write_psw(0)
        proc.write_memory_bytes(0, [0x1D, 0x37, 0x61, 0x90])  # SUB A,#37; ADJBS
        proc.pc = 0
        proc.step()
        proc.step()
        self.assertEqual(proc.read_gp_reg(Registers.A), 0x25)
        self.assertFalse(proc.read_psw() & Flags.CY)

    def test_bcd_sub_00_minus_01(self):
        """00 - 01 = 99 with borrow in BCD."""
        proc, _ = _make_processor()
        proc.write_sp(0xFE00)
        proc.write_gp_reg(Registers.A, 0x00)
        proc.write_psw(0)
        proc.write_memory_bytes(0, [0x1D, 0x01, 0x61, 0x90])
        proc.pc = 0
        proc.step()
        proc.step()
        self.assertEqual(proc.read_gp_reg(Registers.A), 0x99)
        self.assertTrue(proc.read_psw() & Flags.CY)


if __name__ == '__main__':
    unittest.main()


