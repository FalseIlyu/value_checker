# coding=utf-8

from glob import glob
from io import BufferedReader
import os

from numpy import byte

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
                for _ in range(self.header.animationCount)
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
                AnimationData(
                    reader,
                    self.animationMetadataArray[i].animationOffset,
                    size[i]
                    )
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
            self.name = read_str(reader, 0x40)
            self.animationMetadataOffset = read_int32(reader)
            self.size = read_int32(reader)
            self.animationDataOffset = read_int32(reader)
            self.animationCount = read_int32(reader)
            self.unknowns2 = read_vector(reader, 2, read_float)
            return
        else:
            raise ValueError("Need a valid BufferedReader")


class Skeleton:
    def __init__(self, reader: BufferedReader, sectionEnd: int) -> None:
        if reader:
            self.boneCount = read_int32(reader)
            self.unknown = read_int32(reader)
            self.bones = [AlBone(reader) for i in range(self.boneCount)]
            bufferSize = int((sectionEnd - (8 + (self.boneCount * 0x24))) / 4)
            self.buffer = read_vector(reader, bufferSize * 2, read_int16)
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
            self.name = read_str(reader, 0x20)
            self.parent = read_int32(reader, signed=True)
            return
        else:
            raise ValueError("Need a valid BufferedReader")


class AnimationHeader:
    """
    Header of animation data
    Size : 0x90
    """
    def __init__(self, reader: BufferedReader) -> None:
        if reader:
            self.magicNumber = read_int32(reader)
            self.versionNumber = read_int32(reader)
            self.name = read_str(reader, 0x40)
            self.animationType = read_int32(reader)
            self.animationEventStringSize = read_int32(reader)
            self.unknowns1 = read_vector(reader, 3, read_int32)
            self.animationEventCount = read_int32(reader)
            self.boneCount = read_int32(reader)
            self.frameCount = read_int32(reader)
            self.samplingRate = read_float(reader)
            self.duration = read_float(reader)
            self.distance = read_float(reader)
            self.isCyclic = read_bool(reader)
            self.isHierarchical = read_bool(reader)
            self.flags = read_int16(reader)
            self.unknowns2a = read_vector(reader, 2, read_int32)
            self.unknown3 = read_int32(reader)
            self.unknowns2b = read_vector(reader, 2, read_int32)
            self.unknown4 = read_int32(reader)
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
            self.animationInfo = AnimationHeader(reader)
            self.animationOffset = read_int32(reader)
            return
        else:
            raise ValueError("Need a valid BufferedReader")


class AnimationEvent:
    """
    ???
    Size : 0x48
    """
    def __init__(self, reader: BufferedReader, offset: int) -> None:
        self.boneOffset = read_int32(reader)
        self.nameOffset = read_int32(reader)
        self.transitionMatrix = [
            read_vector(reader, 4, read_float),
            read_vector(reader, 4, read_float),
            read_vector(reader, 4, read_float),
            read_vector(reader, 4, read_float)
        ]

        currentPos = reader.tell()
        reader.seek(self.boneOffset + offset, os.SEEK_SET)
        self.bone = bytearray()
        c = reader.read(1)
        while c != b'\x00':
            self.bone.append(int.from_bytes(c, 'little'))
            c = reader.read(1)
        self.bone = self.bone.decode("utf-8")

        reader.seek(self.nameOffset + offset, os.SEEK_SET)
        self.name = bytearray()
        c = reader.read(1)
        while c != b'\x00':
            self.name.append(int.from_bytes(c, 'little'))
            c = reader.read(1)
        self.name = self.name.decode("utf-8")

        reader.seek(currentPos)
        return


class AnimationKeyFrame:
    def __init__(self, reader: BufferedReader, numBones: int) -> None:
        self.timestamp = read_int32(reader)
        self.transorm = [
            {
                "Rotation": [read_int32(reader) for _ in range(4)],
                "Transform": [read_int32(reader) for _ in range(3)]
            }
            for _ in range(numBones)
        ]
        pass


class AnimationData:
    """
    Maybe binary data of an animation
    Size : 0x90 + ???
    """
    def __init__(self, reader: BufferedReader, offset: int, size: int) -> None:
        if reader:
            reader.seek(offset)
            self.animationInfo = AnimationHeader(reader)
            animEventCount = self.animationInfo.animationEventCount
            animEventStringSize = self.animationInfo.animationEventStringSize
            self.animationEvents = [
                AnimationEvent(reader, offset) for _ in range(animEventCount)
            ]

            self.size = size - 0x90 - (0x48 * animEventCount)\
                - animEventStringSize - self.animationInfo.unknowns1[0] - 4
            offset = reader.tell()\
                + animEventStringSize  # + self.animationInfo.unknowns1[0]

            reader.seek(offset)
            self.unknown = read_int32(reader)
            self.unknownData = read_vector(
                reader,
                int((self.animationInfo.unknowns1[0] + self.unknown)/4),
                read_int32
            )

            self.size -= self.unknown
            self.unknownData1 = read_vector(
                reader,
                int(self.size/4),
                read_float
            )
            return
        else:
            raise ValueError("Need a valid BufferedReader")


def main():
    for filepath in glob(
        "G:\\Lionhead Studios\\Black & White 2\\Data\\Art\\**\\**.al"
    ):
        test = True
        with open(filepath, "rb") as alTest:
            file = AlFile(alTest)
            continue
    return


if __name__ == "__main__":
    main()
