# <pep8-80 compliant>
# coding=utf-8
"""Module containing function generally usefull to parsing binary files"""
from io import BufferedReader, BufferedWriter
from typing import Iterable
import struct


def read_bool(reader: BufferedReader) -> bool:
    """ Return the nex byte in a file in a boolean"""
    return bool(int.from_bytes(reader.read(1), 'little'))


def read_float(reader: BufferedReader) -> float:
    """Return the 4 next bytes in a file as a float"""
    return struct.unpack("<f", reader.read(4))[0]


def read_int16(reader: BufferedReader, signed: bool = False) -> int:
    """Return the 2 next bytes in a file as an int"""
    return int.from_bytes(reader.read(2), byteorder="little", signed=signed)


def read_int32(reader: BufferedReader, signed: bool = False) -> int:
    """Return the 4 next bytes in a file as an int"""
    return int.from_bytes(reader.read(4), byteorder="little", signed=signed)


def read_vector(reader: BufferedReader, size: int, type_fun) -> Iterable:
    return [type_fun(reader) for _ in range(size)]


def read_str(reader: BufferedReader, size: int) -> str:
    return reader.read(size).decode("utf-8").replace("\0", "")


def write_bool(writer: BufferedWriter, bool: bool) -> None:
    """ Return the nex byte in a file in a boolean"""
    writer.write(bool.to_bytes(1, byteorder="little", signed=False))


def write_float(writer: BufferedWriter, float: float) -> None:
    """Return the 4 next bytes in a file as a float"""
    writer.write(struct.pack("<f", float))


def write_int16(
    writer: BufferedWriter,
    int: int,
    signed: bool = False
) -> None:
    writer.write(int.to_bytes(2, byteorder="little", signed=signed))


def write_int32(
    writer: BufferedWriter,
    int: int,
    signed: bool = False
) -> None:
    writer.write(int.to_bytes(4, byteorder="little", signed=signed))


def write_vector(writer: BufferedWriter, vector: Iterable, type_fun) -> None:
    for value in vector:
        type_fun(writer, value)


def write_str(writer: BufferedWriter, string: str, size: int) -> None:
    writer.write(string.encode("utf-8"))
    writer.write(bytes([0 for _ in range(size - len(string))]))
