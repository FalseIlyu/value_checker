# coding=utf-8

from glob import glob
from io import BufferedReader

if __name__ != "__main__":
    from .file_definition_utilities import *
else:
    from file_definition_utilities import *


class AlFile:

    def __init__(self, reader: BufferedReader) -> None:
        if reader:
            self.header = AlHeader(reader)
            self.skeleton = Skeleton(
                reader, self.header.animationMetadataOffset
                )
            self.animationMetadataArray = [
                AnimationMetadata(reader)
                for i in range(self.header.animationCount)
                ]
            size = [
                self.animationMetadataArray[i+1].animationOffset
                for i in range(self.header.animationCount - 1)
                ]
            size.append(self.header.size + 0x60)
            size = [
                size[i] - self.animationMetadataArray[i].animationOffset
                for i in range(len(size))
                ]
            self.animationDataArray = [
                AnimationData(reader, size[i])
                for i in range(self.header.animationCount)
                ]
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
            self.animationCount = read_int32(reader)
            self.unknowns2 = [read_float(reader) for i in range(2)]
            return
        else:
            raise ValueError("Need a valid BufferedReader")


class Skeleton:
    def __init__(self, reader: BufferedReader, sectionEnd: int) -> None:
        if reader:
            self.boneCount = read_int32(reader)
            self.unknown = read_int32(reader)
            self.bones = [AlBone(reader) for i in range(self.boneCount)]
            bufferSize = sectionEnd - (8 + (self.boneCount * 0x24))
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
            return
        else:
            raise ValueError("Need a valid BufferedReader")


class AnimationMetadata:
    """
    Maybe metadata of an animation
    Size : 0x94
    """
    def __init__(self, reader: BufferedReader) -> None:
        if reader:
            self.unknowns1 = [read_int32(reader) for i in range(2)]
            self.name = reader.read(0x40).decode("utf-8").replace("\0", "")
            self.unknowns2 = [read_int32(reader) for i in range(6)]
            self.boneCount = read_int32(reader)
            self.frameCount = read_int32(reader)
            self.samplingRate = read_float(reader)
            self.duration = read_float(reader)
            self.unknown2 = read_int32(reader)
            self.unknown3 = read_int32(reader)
            self.unknowns5 = [read_float(reader) for i in range(6)]
            self.animationOffset = read_int32(reader)
            return
        else:
            raise ValueError("Need a valid BufferedReader")


class AnimationData:
    """
    Maybe binary data of an animation
    Size : 0x90 + ???
    """
    def __init__(self, reader: BufferedReader, size: int) -> None:
        if reader:
            self.unknowns1 = [read_int32(reader) for i in range(2)]
            self.name = reader.read(0x40).decode("utf-8").replace("\0", "")
            # self.unknown1 = read_int32(reader)
            self.unknowns2 = [read_int32(reader) for i in range(6)]
            self.boneCount = read_int32(reader)
            self.frameCount = read_int32(reader)
            self.samplingRate = read_float(reader)
            self.duration = read_float(reader)
            self.unknown2 = read_int32(reader)
            self.unknown3 = read_int32(reader)
            self.unknowns5 = [read_float(reader) for i in range(6)]
            self.size = size - 0x90
            self.unknownsData = reader.read(self.size)
            return
        else:
            raise ValueError("Need a valid BufferedReader")


def main():
    for filepath in glob(
        "G:\\Lionhead Studios\\Black & White 2\\Data\\Art\\**\\catapult.al"
    ):
        with open(filepath, "rb") as alTest:
            file = AlFile(alTest)
            continue
    return


if __name__ == "__main__":
    main()
