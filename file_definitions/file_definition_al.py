# coding=utf-8

from glob import glob
from io import BufferedReader

from numpy import single
from file_definition_utilities import (
    read_float,
    read_int16,
    read_int32
)

class AlFile:

    def __init__(self, reader: BufferedReader) -> None:
        if reader:
            self.header = AlHeader(reader)
            self.bones = [AlBone(reader) for i in range(self.header.boneCount)]
            reader.read((self.header.animstart + 0x5C)- (0x68 + (self.header.boneCount * 0x24)))
            self.animation = [Animation(reader) for i in range(self.header.animationCount+1)]
            return
        else:
            raise ValueError("Need a valid BufferedReader")

class AlHeader:
    """
    Header for binary animation files (.al)
    Size : 0x68
    """
    def __init__(self, reader: BufferedReader) -> None:
        if reader:
            self.magicnumber1 = read_int32(reader)
            self.magicnumber2 = read_int32(reader)
            self.name = reader.read(0x40).decode("utf-8").replace("\0", "")
            self.animstart = read_int32(reader)
            self.size = read_int32(reader)
            self.unknown2 = read_int32(reader)
            self.animationCount = read_int32(reader)
            self.unknowns2 = [read_int32(reader) for i in range(2)]
            self.boneCount = read_int32(reader)
            self.buffer = read_int32(reader)
            return
        else:
            raise ValueError("Need a valid BufferedReader")

class AlBone:
    """
    Information on the bone of a skeleton
    Size : 0x24
    """
    def __init__(self, reader: BufferedReader) -> None:
        if reader:
            self.name = reader.read(0x20).decode("utf-8").replace("\0", "")
            self.parent = read_int32(reader, signed=True)
        else:
            raise ValueError("Need a valid BufferedReader")

class Animation:
    """
    Maybe metadata on an animation
    Size : 0x94
    """
    def __init__(self, reader: BufferedReader) -> None:
        if reader:
            self.unknown1 = read_int32(reader, signed=True)
            self.unknowns1 = [read_int32(reader) for i in range(2)]
            self.name = reader.read(0x40).decode("utf-8").replace("\0", "")
            self.unknowns2 = [read_int32(reader,signed=True) for i in range(18)]
        else:
            raise ValueError("Need a valid BufferedReader")
        pass

def main():
    for filepath in glob("G:\\Lionhead Studios\\Black & White 2\\Data\\Art\\**\\**.al"):
        with open(filepath, "rb") as alTest:
            file = AlFile(alTest)
            continue
    return

if __name__ == "__main__":

    main()