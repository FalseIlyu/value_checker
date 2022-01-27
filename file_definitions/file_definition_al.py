# coding=utf-8

from asyncore import read
from glob import glob
from io import BufferedReader
from matplotlib.pyplot import bone

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
            self.skeleton = Skeleton(reader, self.header.animationMetadataOffset)
            self.animation = [AnimationMetadata(reader) for i in range(self.header.animationMetadataCount)]
            return
        else:
            raise ValueError("Need a valid BufferedReader")

class AlHeader:
    """
    Header for binary animation files (.al)
    Size : 0x60
    """
    def __init__(self, reader: BufferedReader) -> None:
        if reader:
            self.magicnumber1 = read_int32(reader)
            self.magicnumber2 = read_int32(reader)
            self.name = reader.read(0x40).decode("utf-8").replace("\0", "")
            self.animationMetadataOffset = read_int32(reader)
            self.size = read_int32(reader)
            self.animationDataOffset = read_int32(reader)
            self.animationMetadataCount = read_int32(reader)
            self.unknowns2 = [read_int32(reader) for i in range(2)]
            return
        else:
            raise ValueError("Need a valid BufferedReader")

class Skeleton:
    def __init__(self, reader: BufferedReader, sectionEnd: int) -> None:
        if reader:
            self.boneCount = read_int32(reader)
            self.unknown = read_int32(reader)
            self.bones = [AlBone(reader) for i in range(self.boneCount)]
            bufferSize =  sectionEnd - (8 + (self.boneCount * 0x24))
            self.buffer = reader.read(bufferSize)
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

class AnimationMetadata:
    """
    Maybe metadata on an animation
    Size : 0x94
    """
    def __init__(self, reader: BufferedReader) -> None:
        if reader:
            self.unknowns1 = [read_int32(reader) for i in range(2)]
            self.name = reader.read(0x40).decode("utf-8").replace("\0", "")
            self.unknowns2 = [read_int32(reader) for i in range(7)]
            self.unknowns3 = [read_int32(reader) for i in range(11)]
            self.animationOffset = read_int32(reader)
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