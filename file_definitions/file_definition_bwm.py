# coding=utf-8
""" Reader for a .bwm file """
from io import BufferedReader, BufferedWriter
from typing import List
from glob import glob
import struct

from numpy import mat

from file_definition_utilities import (
    read_float,
    read_int16,
    read_int32,
    write_float,
    write_int16,
    write_int32,
    write_str,
    write_vector
)

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
            collisionPoint(reader)
            for i in range(self.modelHeader.collisionPointCount)
        ]
        self.strides = [Stride(reader) for i in range(self.modelHeader.strideCount)]
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
        size += (self.modelHeader.unknownCount1 + self.modelHeader.collisionPointCount) * 0xC
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

    def write(self, filepath:str):
        writer = open(filepath,"xb")
        self.fileHeader.size = self.size()
        self.fileHeader.metadataSize = self.metadataSize()
        self.fileHeader.write(writer)
        self.modelHeader.write(writer)
        for materialDefinition in self.materialDefinitions:
            materialDefinition.write(writer)
        materialRefs = []
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
        for (stride, data) in zip(self.strides[1:],self.data):
            stride.write_data(writer, data)
        #for data in self.data:
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
            self.fileIdentifier = (reader.read(40)).decode("utf-8").replace("\0","")  # 0x00
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

    def write(self, writer:BufferedWriter = None):
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
            self.radius = read_float(reader)  # Snappin related value (maybe distance)
            self.unknown2 = read_float(reader)
            self.volume = read_float(reader)

            self.materialDefinitionCount = read_int32(reader)  # 0x7C
            self.meshDescriptionCount = read_int32(reader)  # 0X80
            self.boneCount = read_int32(reader)  # 0x84
            self.entityCount = read_int32(reader)  # 0x88
            self.unknownCount1 = read_int32(reader)  # 0x8C
            self.collisionPointCount = read_int32(reader)  # 0x90

            self.unknowns2 = tuple(read_float(reader) for i in range(5))

            self.vertexCount = read_int32(reader)  # 0xA8
            self.strideCount = read_int32(reader)  # 0xAC
            self.type = read_int32(reader)  # 0xB0 Three for skins and two for the rest
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
            self.unknown2 = 0.0
            self.volume = 0.0

            self.materialDefinitionCount = 1
            self.meshDescriptionCount = 1
            self.boneCount = 0
            self.entityCount = 0
            self.unknownCount1 = 0
            self.collisionPointCount = 0
            
            self.unknowns2 = tuple(0.0 for i in range(5))

            self.vertexCount = 0
            self.strideCount = 1
            self.type = 2
            self.indexCount = 0
            self.modelCleaveCount = 0
    
    def write(self, writer:BufferedWriter):
        write_float(writer, self.unknown1)
        write_vector(writer, self.pnt, write_float)
        write_vector(writer, self.box1, write_float)
        write_vector(writer, self.box2, write_float)
        write_vector(writer, self.cent, write_float)
        write_float(writer, self.height)
        write_float(writer, self.radius)
        write_float(writer, self.unknown2)
        write_float(writer, self.volume)

        write_int32(writer, self.materialDefinitionCount)
        write_int32(writer, self.meshDescriptionCount)
        write_int32(writer, self.boneCount)
        write_int32(writer, self.entityCount)
        write_int32(writer, self.unknownCount1)
        write_int32(writer, self.collisionPointCount)

        write_vector(writer, self.unknowns2, write_float)
        write_int32(writer, self.vertexCount)
        write_int32(writer, self.strideCount)
        write_int32(writer, self.type)
        write_int32(writer, self.indexCount)

class MaterialDefinition:
    """
    '  Size    :   0x1C0
    """

    def __init__(self, reader: BufferedReader = None):
        if reader:
            self.diffuseMap = reader.read(64).decode("utf-8").replace("\0","")
            self.lightMap = reader.read(64).decode("utf-8").replace("\0","")
            self.growthMap = reader.read(64).decode("utf-8").replace("\0","")
            self.specularMap = reader.read(64).decode("utf-8").replace("\0","")
            self.animatedTexture = reader.read(64).decode("utf-8").replace("\0","")
            self.normalMap = reader.read(64).decode("utf-8").replace("\0","")
            self.type = reader.read(64).decode("utf-8").replace("\0","")
            return
        else:
            self.diffuseMap = ""
            self.lightMap = ""
            self.growthMap = ""
            self.specularMap = ""
            self.animatedTexture = ""
            self.normalMap = ""
            self.type = ""

    def write(self, writer:BufferedWriter):
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

            self.axis1 = struct.unpack("<fff", reader.read(12))
            self.axis2 = struct.unpack("<fff", reader.read(12))
            self.axis3 = struct.unpack("<fff", reader.read(12))
            self.position = struct.unpack("<fff", reader.read(12))
            
            self.unknowns1 = [read_float(reader) for i in range(4)]
            self.box1 = [read_float(reader) for i in range(3)]
            self.box2 = [read_float(reader) for i in range(3)]
            self.unknowns2 = [read_float(reader) for i in range(5) ]
            self.unknown_int = read_int32(reader)
            self.bbox_volume = read_float(reader)
            self.materialRefsCount = read_int32(reader)
            self.u2 = read_int32(reader)
            self.id = read_int32(reader)
            self.name = reader.read(64).decode("utf-8").replace("\0","")
            self.unknowns3 = [read_float(reader) for i in range(2)]
            self.materialRefs: List[MaterialRef] = []

            return
        else:
            self.facesCount = 0
            self.indiciesOffset = 0
            self.indiciesSize = 0
            self.vertexOffset = 0
            self.vertexSize = 0

            self.axis1 = (0.0, 0.0, 0.0)
            self.axis2 = (0.0, 0.0, 0.0)
            self.axis3 = (0.0, 0.0, 0.0)
            self.position = [0.0 for i in range(3)]
            
            self.unknowns1 = [0.0 for i in range(4)]
            self.box1 = [0.0 for i in range(3)]
            self.box2 = [0.0 for i in range(3)]
            self.unknowns2 = [0.0 for i in range(5) ]
            self.unknown_int = 0
            self.bbox_volume = 0.0
            self.materialRefsCount = 1
            self.u2 = 0
            self.id = 1
            self.name = ''
            self.unknowns3 = [0.0 for i in range(2)]
            self.materialRefs: List[MaterialRef] = []

    def write(self, writer:BufferedWriter = None):
        write_int32(writer, self.facesCount)
        write_int32(writer, self.indiciesOffset)
        write_int32(writer, self.indiciesSize)
        write_int32(writer, self.vertexOffset)
        write_int32(writer, self.vertexSize)

        write_vector(writer, self.axis1, write_float)
        write_vector(writer, self.axis2, write_float)
        write_vector(writer, self.axis3, write_float)
        write_vector(writer, self.position, write_float)

        write_vector(writer, self.unknowns1, write_float)
        write_vector(writer, self.box1, write_float)
        write_vector(writer, self.box2, write_float)
        write_vector(writer, self.unknowns2, write_float)
        write_int32(writer, self.unknown_int)
        write_float(writer, self.bbox_volume)
        write_int32(writer, self.materialRefsCount)
        write_int32(writer, self.u2)
        write_int32(writer, self.id)
        write_str(writer, self.name, 64)
        write_vector(writer, self.unknowns3, write_float)

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

    def write(self, writer:BufferedWriter = None):
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
            self.axis1 = (read_float(reader), read_float(reader), read_float(reader))
            self.axis2 = (read_float(reader), read_float(reader), read_float(reader))
            self.axis3 = (read_float(reader), read_float(reader), read_float(reader))
            self.position = (read_float(reader), read_float(reader), read_float(reader))
            return

    def write(self, writer:BufferedWriter = None):
        write_vector(writer, self.axis1, write_float)
        write_vector(writer, self.axis2, write_float)
        write_vector(writer, self.axis3, write_float)
        write_vector(writer, self.position, write_float)

class Entity:
    """
    '  Size    :   0x130
    """

    def __init__(self, reader: BufferedReader = None):
        if reader:
            self.axis1 = (read_float(reader), read_float(reader), read_float(reader))
            self.axis2 = (read_float(reader), read_float(reader), read_float(reader))
            self.axis3 = (read_float(reader), read_float(reader), read_float(reader))
            self.position = (read_float(reader), read_float(reader), read_float(reader))
            self.name = reader.read(256).decode("utf-8").replace("\0","")
            return
        else:
            self.axis1 = (0.0, 0.0, 0.0)
            self.axis2 = (0.0, 0.0, 0.0)
            self.axis3 = (0.0, 0.0, 0.0)
            self.position = (0.0, 0.0, 0.0)
            self.name = ""

    def write(self, writer:BufferedWriter = None):
        write_vector(writer, self.axis1, write_float)
        write_vector(writer, self.axis2, write_float)
        write_vector(writer, self.axis3, write_float)
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

    def write(self, writer:BufferedWriter = None):
        write_vector(writer, self.unknown, write_float)

class collisionPoint:
    """
    '  Size    :   0x0C
    """

    def __init__(self, reader: BufferedReader = None):
        if reader:
            self.unknown = struct.unpack("<fff", reader.read(12))
            return
        else:
            self.unknown = (0.0, 0.0, 0.0)

    def write(self, writer:BufferedWriter = None):
        write_vector(writer, self.unknown, write_float)

class Stride:
    """
    '  Size    :   0x88
    """

    def __init__(self, reader: BufferedReader = None):
        stride_format = [4, 8, 12, 4, 1]
        size = 0x88
        if reader:
            self.count = read_int32(reader)
            self.idSizes = [
                (read_int32(reader), read_int32(reader)) for i in range(self.count)
            ]
            self.stride = 0
            for (_, ssize) in self.idSizes:
                self.stride = self.stride + stride_format[ssize]
            size = 0x88 - 4 - (8 * self.count)
            self.unknown = reader.read(size)
            return
        else:
            self.count = 0
            self.idSizes = []
            self.stride = 0
            self.size = 0x88 - 4
            self.unknown = bytes([0 for i in range(size)])

    def read_data(self, reader: BufferedReader):
        stride_format = [4, 8, 12, 4, 1]
        data = []
        for (_, sSize) in self.idSizes:
            if sSize == 3 or sSize == 4:
                data.append(int.from_bytes(reader.read(stride_format[sSize]), byteorder="little"))
            elif sSize == 0:
                data.append(read_float(reader))
            else:
                vector_size = int(stride_format[sSize]/3)
                data.append([read_int32(reader) for i in range(vector_size)])
        return data

    def write(self, writer: BufferedWriter):
        write_int32(writer, self.count)
        for idSize in self.idSizes:
            write_vector(writer, idSize, write_int32)
        writer.write(self.unknown)

    def write_data(self, writer: BufferedWriter, data: List[List]):
        stride_format = [4, 8, 12, 4, 1]
        for stride_data in data:
            i = 0
            for (_, sSize) in self.idSizes:
                if sSize  == 4:
                    writer.write(
                        stride_data[i].to_bytes(
                            1, 
                            byteorder="little", 
                            signed = False)
                        )
                elif sSize == 3:
                    write_int32(writer, stride_data[i])
                elif sSize == 0:
                    write_float(writer, stride_data[i])
                else:
                    write_vector(writer, stride_data[i], write_int32)
                i += 1

class Vertex:
    """
    '  Size    :   0x20
    """

    def __init__(self, stride: Stride, reader: BufferedReader = None):
        if reader:
            self.uvs = []
            for (strideId, _) in stride.idSizes:
                if strideId == 0:
                    self.position = (
                        read_float(reader),
                        read_float(reader),
                        read_float(reader),
                    )
                if strideId == 1:
                    self.normal = (
                        read_float(reader),
                        read_float(reader),
                        read_float(reader),
                    )
                if strideId == 2:
                    self.uvs.append((read_float(reader), read_float(reader)))
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
    for filepath in glob("G:\\Lionhead Studios\\Black & White 2\\Data\\Art\\skins\\s_dove.bwm"):
        with open(filepath, "rb") as testBWM:
            file = BWMFile(testBWM)
            file.write("./s_dove.bwm")
    return

if __name__ == "__main__":

    # test call
    main()