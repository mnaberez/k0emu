#!/usr/bin/env python3 -u
import sys
import serial # pyserial

def make_serial():
    from serial.tools.list_ports import comports
    names = [ x.device for x in comports() if 'Bluetooth' not in x.device ]
    if not names:
        raise Exception("No serial port found")
    return serial.Serial(port=names[0], baudrate=38400, timeout=2)

class Debugger(object):
    def __init__(self, serial):
        self.ser = serial

    def find_prompt(self):
        self.ser.flushOutput()
        self.ser.write(b'\n')
        while True:
            data = self.ser.read(1)
            if data == b'>':
                return

    def read_memory(self, address):
        self.find_prompt()
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
        self.find_prompt()
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
        self.find_prompt()
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


def main():
    ser = make_serial()
    debug = Debugger(ser)

    while True:
        for x in range(256):
            # 0020 A1 2A         [ 4]   31     mov a,#42
            # 0022 9E 00 FE      [ 9]   32     mov 0xfe01,a
            # af                                ret
            code = [0xa1, x, 0x9e, 0x07, 0xfe, 0xaf]
            for address, value in enumerate(code, 0xf000):
                debug.write_memory(address, value) # ret
                if debug.read_memory(address) != value:
                    raise Exception("write failed")
            debug.branch(0xf000)
            sys.stdout.write("%02x " % debug.read_memory(0xfe07))
            sys.stdout.flush()

if __name__ == '__main__':
    main()
