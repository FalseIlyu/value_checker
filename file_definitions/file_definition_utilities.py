# <pep8-80 compliant>
# coding=utf-8
"""Module containing function generally usefull to parsing binary files"""
from io import BufferedReader, BufferedWriter
from typing import Iterable
import struct


def read_float(reader: BufferedReader) -> float:
    """Return the 4 next bytes in a file as a float"""
    return struct.unpack("<f", reader.read(4))[0]


def read_int16(reader: BufferedReader, signed: bool = False) -> int:
    """Return the 2 next bytes in a file as an int"""
    return int.from_bytes(reader.read(2), byteorder="little", signed=signed)


def read_int32(reader: BufferedReader, signed: bool = False) -> int:
    """Return the 4 next bytes in a file as an int"""
    return int.from_bytes(reader.read(4), byteorder="little", signed=signed)


def write_float(writer: BufferedWriter, float: float) -> None:
    """Return the 4 next bytes in a file as a float"""
    writer.write(struct.pack("<f", float))


def write_int16(writer: BufferedWriter, int: int, signed: bool = False) -> None:
    writer.write(int.to_bytes(2, byteorder="little", signed=signed))


def write_int32(writer: BufferedWriter, int: int, signed: bool = False) -> None:
    writer.write(int.to_bytes(4, byteorder="little", signed=signed))


def write_vector(writer: BufferedWriter, vector: Iterable, type_fun) -> None:
    for value in vector:
        type_fun(writer, value)


def write_str(writer: BufferedWriter, string: str, size: int) -> None:
    writer.write(string.encode("utf-8"))
    writer.write(bytes([0 for i in range(size - len(string))]))
