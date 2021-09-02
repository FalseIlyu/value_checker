# coding=utf-8
"""Module containing function generally usefull to parsing binary files"""
from io import BufferedReader
import struct


def read_float(reader: BufferedReader) -> float:
    """Return the 4 next bytes in a file as a float"""
    return struct.unpack("f", reader.read(4))[0]


def read_int16(reader: BufferedReader) -> int:
    """Return the 2 next bytes in a file as an int"""
    return int.from_bytes(reader.read(2), byteorder="little")


def read_int32(reader: BufferedReader) -> int:
    """Return the 4 next bytes in a file as an int"""
    return int.from_bytes(reader.read(4), byteorder="little")
