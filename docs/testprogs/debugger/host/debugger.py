#!/usr/bin/env python3 -u
import sys
if sys.version_info.major < 3:
    raise Exception("Python 2 is not supported")

import serial # pyserial

class Debugger(object):
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

    def read_memory(self, address):
        low = address & 0xFF
        high = address >> 8
        self.ser.write(bytearray([ord(b'R'), low, high]))
        data = self.ser.read(3)
        if len(data) != 3:
            raise Exception("too short")
        if data[0] != ord('r'):
            raise Exception("unexpected response: %r" % data[0])
        if data[2] != ord('>'):
            raise Exception("no prompt")
        return data[1]

    def write_memory(self, address, value):
        low = address & 0xFF
        high = address >> 8
        self.ser.write(bytearray([ord(b'W'), low, high, value]))
        data = self.ser.read(2)
        if len(data) != 2:
            raise Exception("too short: %r" % data)
        if data[0] != ord('w'):
            raise Exception("unexpected response: %r" % data[0])
        if data[1] != ord('>'):
            raise Exception("no prompt")

    def branch(self, address):
        low = address & 0xFF
        high = address >> 8
        self.ser.write(bytearray([ord(b'B'), low, high]))
        data = self.ser.read(2)
        if len(data) != 2:
            raise Exception("too short: %r" % data)
        if data[0] != ord('b'):
            raise Exception("unexpected response: %r" % data[0])
        if data[1] != ord('>'):
            raise Exception("no prompt")

def make_serial():
    from serial.tools.list_ports import comports
    names = [ x.device for x in comports() if 'Bluetooth' not in x.device ]
    if not names:
        raise Exception("No serial port found")
    return serial.Serial(port=names[0], baudrate=38400, timeout=2)

def make_debugger(ser=None):
    if ser is None:
        ser = make_serial()
    debug = Debugger(ser)
    return debug
