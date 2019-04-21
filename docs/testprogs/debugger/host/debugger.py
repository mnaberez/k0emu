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

    def branch(self, address):
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
