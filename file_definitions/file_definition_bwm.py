# <pep8-80 compliant>
# coding=utf-8
""" Structures of a .bwm with associated IO """
from io import BufferedReader, BufferedWriter
from colorama import Fore, Style
from typing import List
from glob import glob
from enum import Enum
import struct

if __name__ != "__main__":
    from .file_definition_utilities import *
else:
    from file_definition_utilities import *
    import filecmp
    import json
    import os


# Section for enumated type
class FileType(Enum):
    MODEL = 2
    SKIN = 3


class StrideSize(Enum):
    FLOAT = 0
    TUPLE = 1
    POINT_3D = 2
    INT = 3
    BYTE = 4


class StrideType(Enum):
    POINT = 0
    NORMAL = 1
    UV_MAP = 2
    BONE_INDEX = 6
    BONE_WEIGHT = 7


class UVType(Enum):
    UV_TEXTURE = 0
    UV_LIGTHMAP = 1
    UV_ANIMATION = 2


# Section for BWM file structure
class BWMFile:

    """
    '  Initialisize the data of a BWMFile
    """

    def __init__(self, reader: BufferedReader = None):
        self.fileHeader = BWMHeader(reader)
        self.modelHeader = LionheadModelHeader(reader)
        self.materialDefinitions = [
            MaterialDefinition(reader)
            for i in range(self.modelHeader.materialDefinitionCount)
        ]
        self.meshDescriptions = [
            MeshDescription(reader)
            for i in range(self.modelHeader.meshDescriptionCount)
        ]
        for mesh in self.meshDescriptions:
            mesh.materialRefs = [
                MaterialRef(reader) for i in range(mesh.materialRefsCount)
            ]
        self.bones = [Bone(reader) for i in range(self.modelHeader.boneCount)]
        self.entities = [
            Entity(reader) for i in range(self.modelHeader.entityCount)
        ]
        self.unknowns1 = [
            Unknown1(reader) for i in range(self.modelHeader.unknownCount1)
        ]
        self.collisionPoints = [
            CollisionPoint(reader)
            for i in range(self.modelHeader.collisionPointCount)
        ]
        self.strides = [Stride(reader)
                        for i in range(self.modelHeader.strideCount)]
        self.vertices = [
            Vertex(self.strides[0], reader)
            for vertex in range(self.modelHeader.vertexCount)
        ]
        self.data = [
            [
                stride.read_data(reader)
                for vertex in range(self.modelHeader.vertexCount)
            ]
            for stride in self.strides[1:]
        ]
        self.indexes = [
            read_int16(reader) for i in range(self.modelHeader.indexCount)
        ]
        if self.fileHeader.version > 5:
            self.modelHeader.modelCleaveCount = read_int32(reader)
            self.modelCleaves = [
                (read_float(reader), read_float(reader), read_float(reader))
                for i in range(self.modelHeader.modelCleaveCount)
            ]

        return

    def metadataSize(self):
        size = 0x80
        size += self.modelHeader.materialDefinitionCount * 0x1C0
        size += self.modelHeader.meshDescriptionCount * 0xDC
        for mesh_description in self.meshDescriptions:
            size += mesh_description.materialRefsCount * 0x20
        size += self.modelHeader.boneCount * 0x30
        size += self.modelHeader.entityCount * 0x130
        size += (self.modelHeader.unknownCount1 +
                 self.modelHeader.collisionPointCount) * 0xC
        size += self.modelHeader.strideCount * 0x88

        return size

    def size(self):
        size = self.metadataSize() + 0xC
        for i in range(self.modelHeader.strideCount):
            size += self.strides[i].stride * self.modelHeader.vertexCount
        size += 2 * self.modelHeader.indexCount
        if self.fileHeader.version > 5:
            size += (0xC * self.modelHeader.modelCleaveCount) + 4

        return size

    def write(self, filepath: str):
        writer = open(filepath, "xb")
        self.fileHeader.size = self.size()
        self.fileHeader.metadataSize = self.metadataSize()
        self.fileHeader.write(writer)
        self.modelHeader.write(writer)
        for materialDefinition in self.materialDefinitions:
            materialDefinition.write(writer)
        materialRefs = []
        # self.meshDescriptions.sort(key = lambda x: x.id)
        for meshDescription in self.meshDescriptions:
            meshDescription.write(writer)
            materialRefs.extend(meshDescription.materialRefs)
        for materialRef in materialRefs:
            materialRef.write(writer)
        for bone in self.bones:
            bone.write(writer)
        for entity in self.entities:
            entity.write(writer)
        for unknown1 in self.unknowns1:
            unknown1.write(writer)
        for collisionPoint in self.collisionPoints:
            collisionPoint.write(writer)
        for stride in self.strides:
            stride.write(writer)
        for vertex in self.vertices:
            vertex.write(writer)
        for (stride, data) in zip(self.strides[1:], self.data):
            stride.write_data(writer, data)
        # for data in self.data:
        #    writer.write(data)
        for indice in self.indexes:
            write_int16(writer, indice)
        if self.fileHeader.version > 5:
            write_int32(writer, self.modelHeader.modelCleaveCount)
            for modelCleave in self.modelCleaves:
                write_vector(writer, modelCleave, write_float)


class BWMHeader:
    """
    '  Header for BWM files, contains identifier for the format
    '  and information on format version and file size
    '  Size :   0x38
    """

    def __init__(self, reader: BufferedReader = None):
        if reader:
            self.fileIdentifier = (reader.read(40)).decode(
                ).replace("\0", "")  # 0x00
            if "LiOnHeAdMODEL" not in self.fileIdentifier:
                raise ValueError(
                    "This is not a valid .bwm file (magic string mismatch)."
                )
            self.size = read_int32(reader)  # 0x28
            self.numberIdentifier = read_int32(reader)  # 0x2C
            if self.numberIdentifier != 0x2B00B1E5:
                raise ValueError(
                    "This is not a valid .bwm file (magic number mismatch)."
                )
            self.version = read_int32(reader)  # 0x30
            if self.version < 5:
                raise ValueError("Unsupported version of the format")
            self.metadataSize = read_int32(reader)  # 0x34
            # 0x38 + metadataSize = vertexPointer
            return
        else:
            self.fileIdentifier = "LiOnHeAdMODEL"
            self.size = 0
            self.numberIdentifier = 0x2B00B1E5
            self.version = 5
            self.metadataSize = 0

    def write(self, writer: BufferedWriter = None):
        if writer:
            write_str(writer, self.fileIdentifier, 40)
            write_int32(writer, self.size)
            write_int32(writer, 0x2B00B1E5)
            write_int32(writer, self.version)
            write_int32(writer, self.metadataSize)


class LionheadModelHeader:
    """
    '  Part of the Header summarizing information about the model
    '  described by the file
    '  Size :   0x80
    """

    def __init__(self, reader: BufferedReader = None):
        if reader:
            self.unknown1 = read_float(reader)
            self.pnt = tuple(read_float(reader) for i in range(3))
            self.box1 = tuple(read_float(reader) for i in range(3))
            self.box2 = tuple(read_float(reader) for i in range(3))
            self.cent = tuple(read_float(reader) for i in range(3))
            self.height = read_float(reader)
            # Snappin related value (maybe distance)
            self.radius = read_float(reader)
            self.unknown2 = read_int32(reader)
            self.volume = read_float(reader)

            self.materialDefinitionCount = read_int32(reader)  # 0x7C
            self.meshDescriptionCount = read_int32(reader)  # 0X80
            self.boneCount = read_int32(reader)  # 0x84
            self.entityCount = read_int32(reader)  # 0x88
            self.unknownCount1 = read_int32(reader)  # 0x8C
            self.collisionPointCount = read_int32(reader)  # 0x90

            self.unknown3 = read_float(reader)
            self.unknowns2 = tuple(read_float(reader) for i in range(3))
            self.unknown4 = read_float(reader)

            self.vertexCount = read_int32(reader)  # 0xA8
            self.strideCount = read_int32(reader)  # 0xAC
            # 0xB0 Three for skins and two for the rest
            self.type = FileType(read_int32(reader))
            self.indexCount = read_int32(reader)  # 0xB4
            self.modelCleaveCount = 0
            return
        else:
            self.unknown1 = 0.0
            self.pnt = tuple(0.0 for i in range(3))
            self.box1 = tuple(0.0 for i in range(3))
            self.box2 = tuple(0.0 for i in range(3))
            self.cent = tuple(0.0 for i in range(3))
            self.height = 0.0
            self.radius = 0.0
            self.unknown2 = 0
            self.volume = 0.0

            self.materialDefinitionCount = 1
            self.meshDescriptionCount = 1
            self.boneCount = 0
            self.entityCount = 0
            self.unknownCount1 = 0
            self.collisionPointCount = 0

            self.unknown3 = 0.0
            self.unknowns2 = tuple(0.0 for i in range(3))
            self.unknown4 = 0.0

            self.vertexCount = 0
            self.strideCount = 1
            self.type = FileType.MODEL
            self.indexCount = 0
            self.modelCleaveCount = 0

    def write(self, writer: BufferedWriter):
        write_float(writer, self.unknown1)
        write_vector(writer, self.pnt, write_float)
        write_vector(writer, self.box1, write_float)
        write_vector(writer, self.box2, write_float)
        write_vector(writer, self.cent, write_float)
        write_float(writer, self.height)
        write_float(writer, self.radius)
        write_int32(writer, self.unknown2)
        write_float(writer, self.volume)

        write_int32(writer, self.materialDefinitionCount)
        write_int32(writer, self.meshDescriptionCount)
        write_int32(writer, self.boneCount)
        write_int32(writer, self.entityCount)
        write_int32(writer, self.unknownCount1)
        write_int32(writer, self.collisionPointCount)

        write_float(writer, self.unknown3)
        write_vector(writer, self.unknowns2, write_float)
        write_float(writer, self.unknown4)

        write_int32(writer, self.vertexCount)
        write_int32(writer, self.strideCount)
        write_int32(writer, self.type.value)
        write_int32(writer, self.indexCount)


class MaterialDefinition:
    """
    '  Size    :   0x1C0
    """

    def __init__(self, reader: BufferedReader = None):
        if reader:
            self.diffuseMap = reader.read(64).decode().replace("\0", "")
            self.lightMap = reader.read(64).decode().replace("\0", "")
            self.growthMap = reader.read(64).decode().replace("\0", "")
            self.specularMap = reader.read(64).decode().replace("\0", "")
            self.animatedTexture = reader.read(64).decode().replace("\0", "")
            self.normalMap = reader.read(64).decode().replace("\0", "")
            self.type = reader.read(64).decode().replace("\0", "")
            return
        else:
            self.diffuseMap = ""
            self.lightMap = ""
            self.growthMap = ""
            self.specularMap = ""
            self.animatedTexture = ""
            self.normalMap = ""
            self.type = ""

    def write(self, writer: BufferedWriter):
        write_str(writer, self.diffuseMap, 64)
        write_str(writer, self.lightMap, 64)
        write_str(writer, self.growthMap, 64)
        write_str(writer, self.specularMap, 64)
        write_str(writer, self.animatedTexture, 64)
        write_str(writer, self.normalMap, 64)
        write_str(writer, self.type, 64)


class MeshDescription:
    """
    '  Size    :   0xDC
    """

    def __init__(self, reader: BufferedReader = None):
        if reader:
            self.facesCount = read_int32(reader)
            self.indiciesOffset = read_int32(reader)
            self.indiciesSize = read_int32(reader)
            self.vertexOffset = read_int32(reader)
            self.vertexSize = read_int32(reader)

            self.zaxis = struct.unpack("<fff", reader.read(12))
            self.xaxis = struct.unpack("<fff", reader.read(12))
            self.yaxis = struct.unpack("<fff", reader.read(12))
            self.position = struct.unpack("<fff", reader.read(12))

            self.cent = [read_float(reader) for i in range(3)]
            self.radius = read_float(reader)
            self.box1 = [read_float(reader) for i in range(3)]
            self.box2 = [read_float(reader) for i in range(3)]
            self.unknowns1 = [read_float(reader) for i in range(3)]
            self.height = read_float(reader)
            self.unknown1 = read_float(reader)
            self.unknown_int = read_int32(reader)
            self.bbox_volume = read_float(reader)
            self.materialRefsCount = read_int32(reader)
            self.u2 = read_int32(reader)
            self.lod_level = read_int32(reader)
            self.name = reader.read(64).decode().replace("\0", "")
            self.unknowns3 = [read_int32(reader) for i in range(2)]
            self.materialRefs: List[MaterialRef] = []

            return
        else:
            self.facesCount = 0
            self.indiciesOffset = 0
            self.indiciesSize = 0
            self.vertexOffset = 0
            self.vertexSize = 0

            self.zaxis = (0.0, 0.0, 0.0)
            self.xaxis = (0.0, 0.0, 0.0)
            self.yaxis = (0.0, 0.0, 0.0)
            self.position = [0.0 for i in range(3)]

            self.cent = [0.0 for i in range(3)]
            self.radius = 0.0
            self.box1 = [0.0 for i in range(3)]
            self.box2 = [0.0 for i in range(3)]
            self.unknowns1 = [0.0 for i in range(3)]
            self.height = 0.0
            self.unknown1 = 0.0
            self.unknown_int = 0
            self.bbox_volume = 0.0
            self.materialRefsCount = 1
            self.u2 = 0
            self.lod_level = 1
            self.name = ''
            self.unknowns3 = [0 for i in range(2)]
            self.materialRefs: List[MaterialRef] = []

    def write(self, writer: BufferedWriter = None):
        write_int32(writer, self.facesCount)
        write_int32(writer, self.indiciesOffset)
        write_int32(writer, self.indiciesSize)
        write_int32(writer, self.vertexOffset)
        write_int32(writer, self.vertexSize)

        write_vector(writer, self.zaxis, write_float)
        write_vector(writer, self.xaxis, write_float)
        write_vector(writer, self.yaxis, write_float)
        write_vector(writer, self.position, write_float)

        write_vector(writer, self.cent, write_float)
        write_float(writer, self.radius)
        write_vector(writer, self.box1, write_float)
        write_vector(writer, self.box2, write_float)
        write_vector(writer, self.unknowns1, write_float)
        write_float(writer, self.height)
        write_float(writer, self.unknown1)
        write_int32(writer, self.unknown_int)
        write_float(writer, self.bbox_volume)
        write_int32(writer, self.materialRefsCount)
        write_int32(writer, self.u2)
        write_int32(writer, self.lod_level)
        write_str(writer, self.name, 64)
        write_vector(writer, self.unknowns3, write_int32)


class MaterialRef:
    """
    '  Size    :   0x20
    """

    def __init__(self, reader: BufferedReader = None):
        if reader:
            self.materialDefinition = read_int32(reader)
            self.indiciesOffset = read_int32(reader)
            self.indiciesSize = read_int32(reader)
            self.vertexOffset = read_int32(reader)
            self.vertexSize = read_int32(reader)
            self.facesOffset = read_int32(reader)
            self.facesSize = read_int32(reader)
            self.unknown = read_float(reader)
            return
        else:
            self.materialDefinition = 0
            self.indiciesOffset = 0
            self.indiciesSize = 0
            self.vertexOffset = 0
            self.vertexSize = 0
            self.facesOffset = 0
            self.facesSize = 0
            self.unknown = 0.0

    def write(self, writer: BufferedWriter = None):
        write_int32(writer, self.materialDefinition)
        write_int32(writer, self.indiciesOffset)
        write_int32(writer, self.indiciesSize)
        write_int32(writer, self.vertexOffset)
        write_int32(writer, self.vertexSize)
        write_int32(writer, self.facesOffset)
        write_int32(writer, self.facesSize)
        write_float(writer, self.unknown)


class Bone:
    """
    '  Size    :   0x30
    """

    def __init__(self, reader: BufferedReader = None):
        if reader:
            self.zaxis = (
                read_float(reader),
                read_float(reader),
                read_float(reader))
            self.xaxis = (
                read_float(reader),
                read_float(reader),
                read_float(reader))
            self.yaxis = (
                read_float(reader),
                read_float(reader),
                read_float(reader))
            self.position = (
                read_float(reader),
                read_float(reader),
                read_float(reader))
            return

    def write(self, writer: BufferedWriter = None):
        write_vector(writer, self.zaxis, write_float)
        write_vector(writer, self.xaxis, write_float)
        write_vector(writer, self.yaxis, write_float)
        write_vector(writer, self.position, write_float)


class Entity:
    """
    '  Size    :   0x130
    """

    def __init__(self, reader: BufferedReader = None):
        if reader:
            self.zaxis = (
                read_float(reader),
                read_float(reader),
                read_float(reader))
            self.xaxis = (
                read_float(reader),
                read_float(reader),
                read_float(reader))
            self.yaxis = (
                read_float(reader),
                read_float(reader),
                read_float(reader))
            self.position = (
                read_float(reader),
                read_float(reader),
                read_float(reader))
            self.name = reader.read(256).decode().replace("\0", "")
            return
        else:
            self.zaxis = (0.0, 0.0, 0.0)
            self.xaxis = (0.0, 0.0, 0.0)
            self.yaxis = (0.0, 0.0, 0.0)
            self.position = (0.0, 0.0, 0.0)
            self.name = ""

    def write(self, writer: BufferedWriter = None):
        write_vector(writer, self.zaxis, write_float)
        write_vector(writer, self.xaxis, write_float)
        write_vector(writer, self.yaxis, write_float)
        write_vector(writer, self.position, write_float)
        write_str(writer, self.name, 256)


class Unknown1:
    """
    '  Size    :   0x0C
    """

    def __init__(self, reader: BufferedReader = None):
        if reader:
            self.unknown = struct.unpack("<fff", reader.read(12))
            return
        else:
            self.unknown = (0.0, 0.0, 0.0)

    def write(self, writer: BufferedWriter = None):
        write_vector(writer, self.unknown, write_float)


class CollisionPoint:
    """
    '  Size    :   0x0C
    """

    def __init__(self, reader: BufferedReader = None):
        if reader:
            self.position = struct.unpack("<fff", reader.read(12))
            return
        else:
            self.position = (0.0, 0.0, 0.0)

    def write(self, writer: BufferedWriter = None):
        write_vector(writer, self.position, write_float)


class Stride:
    """
    '  Size    :   0x88
    """
    strideFormat = [4, 8, 12, 4, 1]

    def __init__(self, reader: BufferedReader = None):
        if reader:
            self.count = read_int32(reader)
            self.idSizes = [
                (
                    StrideType(read_int32(reader)),
                    StrideSize(read_int32(reader))
                ) for i in range(self.count)
            ]
            self.stride = 0
            for (_, ssize) in self.idSizes:
                self.stride = self.stride + Stride.strideFormat[ssize.value]
            size = 0x88 - 4 - (8 * self.count)
            self.unknown = reader.read(size)
            return
        else:
            self.count = 0
            self.idSizes = []
            self.stride = 0
            self.size = 0x88 - 4
            self.unknown = bytes([0 for i in range(self.size)])

    def read_data(self, reader: BufferedReader):
        data = []
        for (_, sSize) in self.idSizes:
            if sSize == StrideSize.INT or sSize == StrideSize.BYTE:
                data.append(int.from_bytes(reader.read(
                    Stride.strideFormat[sSize.value]), byteorder="little"))
            elif sSize == StrideSize.FLOAT:
                data.append(read_float(reader))
            elif sSize == StrideSize.POINT_3D or sSize == StrideSize.TUPLE:
                vector_size = int(Stride.strideFormat[sSize.value]/4)
                data.append([read_float(reader) for i in range(vector_size)])
            else:
                raise ValueError("This isn't a supported stride Datatype")

        if len(data) > 1:
            return data[0]
        return data

    def write(self, writer: BufferedWriter):
        write_int32(writer, self.count)
        for sId, sSize in self.idSizes:
            write_int32(writer, sId.value)
            write_int32(writer, sSize.value)
        writer.write(self.unknown)

    def write_data(self, writer: BufferedWriter, data: List[List]):
        for stride_data in data:
            for i, (_, sSize) in enumerate(self.idSizes):
                if sSize == StrideSize.BYTE:
                    writer.write(
                        stride_data[i].to_bytes(
                            1,
                            byteorder="little",
                            signed=False)
                    )
                elif sSize == StrideSize.INT:
                    write_int32(writer, stride_data[i])
                elif sSize == StrideSize.FLOAT:
                    write_float(writer, stride_data[i])
                elif sSize == StrideSize.VECTOR or sSize == StrideSize.TUPLE:
                    write_vector(writer, stride_data[i], write_int32)
                else:
                    raise ValueError("Not a supported stride Datatype")


class Vertex:
    """
    '  Size    :   0x20
    """

    def __init__(self, stride: Stride, reader: BufferedReader = None):
        if reader:
            self.uvs = []
            for (strideId, _) in stride.idSizes:
                if strideId == StrideType.POINT:
                    self.position = (
                        read_float(reader),
                        read_float(reader),
                        read_float(reader),
                    )
                elif strideId == StrideType.NORMAL:
                    self.normal = (
                        read_float(reader),
                        read_float(reader),
                        read_float(reader),
                    )
                elif strideId == StrideType.UV_MAP:
                    self.uvs.append((read_float(reader), read_float(reader)))
                else:
                    raise ValueError(
                        f"This type is not usable for a Vertex {strideId.name}"
                        )
            return
        else:
            self.uvs = []
            self.position = (0.0, 0.0, 0.0)
            self.normal = (0.0, 0.0, 0.0)

    def write(self, writer: BufferedWriter):
        write_vector(writer, self.position, write_float)
        write_vector(writer, self.normal, write_float)
        for uv in self.uvs:
            write_vector(writer, uv, write_float)


def main():
    localPath = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(localPath, "deftests_config.json")) as cfgFile:
        config = json.load(cfgFile)
    resultPath = os.path.join(localPath, "WriteBWM")

    def clean_up():
        for filePath in glob(f"{resultPath}\\**"):
            os.remove(filePath)
        os.rmdir(resultPath)
    if os.path.exists(resultPath):
        clean_up()
    try:
        os.mkdir(resultPath)
        allSame = True

        for filePath in glob(f"{config['gamePath']}\\{config['bwmsPath']}"):
            with open(filePath, "rb") as testBWM:
                fileName = os.path.basename(filePath)
                try:
                    file = BWMFile(testBWM)
                except ValueError:
                    print(f"{Fore.RED}Couldn't read{Style.RESET_ALL}"
                          f" {fileName}")
                    continue

                resultFile = os.path.join(resultPath, fileName)
                file.write(resultFile)
                if not filecmp.cmp(filePath, resultFile):
                    print(f"{Fore.YELLOW}Writing"
                          f"{Style.RESET_ALL} {fileName} {Fore.YELLOW}"
                          f"back don't yield an exact copy{Style.RESET_ALL}")
                    allSame = False
                os.remove(resultFile)

        if allSame:
            print(f"{Fore.GREEN}All files written are exact copies of their"
                  f" original{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}Some written files aren't exact copie of their"
                  f" original{Style.RESET_ALL}")

        os.rmdir(resultPath)
    except (KeyboardInterrupt, FileExistsError) as e:
        clean_up()
        print(e)

    return


if __name__ == "__main__":

    # test call
    main()
