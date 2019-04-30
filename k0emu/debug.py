import os
import sys
import serial # pyserial
from k0emu.processor import Processor


class BaseDebugger(object):
    '''Methods a debugger must implement'''
    def read(self, address, length):
        '''Read <length> bytes from memory starting at <address>.'''
        raise NotImplementedError

    def write(self, address, data):
        '''Write <data> bytes to memory starting at <address>.'''
        raise NotImplementedError

    def call(self, address, data):
        '''Call <address> in memory.  The code must return (0xAF RET).'''
        raise NotImplementedError


class EmulatorDebugger(BaseDebugger):
    '''Debugger for the k0emu software emulator'''
    def __init__(self, processor):
        self.proc = processor
        self.proc.write_sp(0xfe1d)  # for consistency with serial debugger firmware

    def read(self, address, length):
        data = bytearray()
        for i in range(length):
            data.append(self.proc.read_memory(address + i))
        return data

    def write(self, address, data):
        for addr, d in enumerate(data, address):
            self.proc.write_memory(addr, d)

    def call(self, address):
        self.proc.pc = address
        while self.proc.read_memory(self.proc.pc) != 0xaf:  # ret
            self.proc.step()


class SerialDebugger(BaseDebugger):
    '''Serial interface to a real uPD78F0831Y running the debugger firmware'''
    def __init__(self, serial):
        self.ser = serial
        self.find_prompt()

    def find_prompt(self):
        self.ser.flushOutput()
        self.ser.write(b'\n')
        while True:
            data = self.ser.read(1)
            if data == b'>':
                return

    def read(self, address, length):
        low, high = self._split_word(address)
        self.ser.write(bytearray([ord(b'R'), low, high, length]))
        response_length = 2 + length
        data = bytearray(self.ser.read(response_length))
        if len(data) != response_length:
            raise Exception("too short")
        if data[0] != ord('r'):
            raise Exception("unexpected response: %r" % data[0])
        if data[-1] != ord('>'):
            raise Exception("no prompt")
        data.pop(0) # remove first byte of packet ('r' response)
        data.pop()  # remove last byte of packet ('>' prompt)
        return data

    def write(self, address, data):
        low, high = self._split_word(address)
        packet = bytearray([ord(b'W'), low, high, len(data)])
        for d in data:
            packet.append(d)
        self.ser.write(packet)
        response_length = 2
        data = self.ser.read(response_length)
        if len(data) != response_length:
            raise Exception("too short: %r" % data)
        if data[0] != ord('w'):
            raise Exception("unexpected response: %r" % data[0])
        if data[1] != ord('>'):
            raise Exception("no prompt")

    def call(self, address):
        low, high = self._split_word(address)
        self.ser.write(bytearray([ord(b'B'), low, high]))
        data = self.ser.read(2)
        if len(data) != 2:
            raise Exception("too short: %r" % data)
        if data[0] != ord('b'):
            raise Exception("unexpected response: %r" % data[0])
        if data[1] != ord('>'):
            raise Exception("no prompt")

    def _split_word(self, word):
        low = word & 0xFF
        high = word >> 8
        return low, high


def make_serial():
    name = os.environ.get('FTDI_DEVICE')
    if name is None:
        from serial.tools.list_ports import comports
        candidates = [ x.device for x in comports() if 'Bluetooth' not in x.device ]
        if not candidates:
            raise Exception("No serial port found")
        name = candidates[0]
    return serial.Serial(port=name, baudrate=38400, timeout=2)

def make_serial_debugger(ser=None):
    if ser is None:
        ser = make_serial()
    debug = SerialDebugger(ser)
    return debug

def make_emulator_debugger(proc=None):
    if proc is None:
        proc = Processor()
    debug = EmulatorDebugger(proc)
    return debug

def make_debugger_from_argv(argv=None):
    if argv is None:
        argv = sys.argv
    if 'emulator' in argv:
        factory = make_emulator_debugger
    else:
        factory = make_serial_debugger
    return factory()
