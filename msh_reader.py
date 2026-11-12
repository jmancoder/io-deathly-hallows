from dataclasses import dataclass
import logging
from pathlib import Path
from typing import Any

import numpy as np
import numpy.typing as npt

from .binary_reader import BinaryReader

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class Texture:
    file_id: int
    data_id: int
    name: str
    data_path: Path
    width: int
    height: int
    size: int


@dataclass(slots=True)
class MaterialProperty:
    name: str
    unk_0: int
    unk_1: int


@dataclass(slots=True)
class Material:
    name: str
    template_name: str
    texture_map: dict[str, Texture]
    properties: list[MaterialProperty]


@dataclass(slots=True)
class Shape:
    file_id: int
    name: str
    vertices: npt.NDArray
    face_indices: npt.NDArray
    materials: list[Material]


class MSHReader:
    def __init__(self, root_path: Path, manifest: dict) -> None:
        self.root_path = root_path
        self.manifest = manifest
        self.asset_pool: dict[int, Any] = {}

    def get_string(self, string_id: int) -> str:
        return self.manifest["strings"][str(string_id)]

    def get_path(self, asset_id: int) -> Path:
        name = self.get_string(asset_id)
        if ":" in name:
            category, path = name.split(":")
        else:
            path = name
        return self.root_path / path

    def create_reader(self, path: Path) -> BinaryReader:
        with open(path, "rb") as f:
            return BinaryReader(f.read())

    def read_tex(self, tex_id: int) -> Texture:
        tex_path = self.get_path(tex_id)
        logger.info('Reading TEX file "%s"', tex_path)
        bs = self.create_reader(tex_path)

        bs.read_int32()
        bs.read_int32()
        bs.read_int32()
        bs.read_int32()
        width = bs.read_uint32()
        height = bs.read_uint32()
        bs.read_int32()
        size = bs.read_uint32()
        bs.read_int32()
        data_id = bs.read_uint32()
        data_path = self.get_path(data_id)
        return Texture(tex_id, data_id, tex_path.stem, data_path, width, height, size)

    def read_material(self, bs: BinaryReader) -> Material:
        mat_start = bs.tell()
        template_name = self.get_string(bs.read_uint32())
        bs.read_uint32()
        mat_name = bs.read_string(24)

        # Read textures
        tex_map: dict[str, Texture] = {}
        for _ in range(16):
            bs.seek(32, 1)
            tex_type = self.get_string(bs.read_uint32())
            tex_id = bs.read_uint32()
            if tex_id not in self.asset_pool:
                texture = self.read_tex(tex_id)
                self.asset_pool[tex_id] = texture
            else:
                texture = self.asset_pool[tex_id]
            tex_map[tex_type] = texture
            bs.seek(32, 1)

        # Read properties
        bs.seek(mat_start + 0x4C0)
        prop_count = bs.read_uint32()
        bs.seek(mat_start + 0x500)
        props: list[MaterialProperty] = []
        for _ in range(prop_count):
            prop_name = self.get_string(bs.read_uint32())
            unk_0 = bs.read_int32()
            bs.read_int32()
            unk_1 = bs.read_int32()
            bs.read_int32()
            bs.read_int32()
            bs.read_int32()
            props.append(MaterialProperty(prop_name, unk_0, unk_1))

        bs.seek(mat_start + 0x900)
        return Material(mat_name, template_name, tex_map, props)

    def _get_vertex_dtype(self, dtype_index: int) -> npt.DTypeLike:
        match dtype_index:
            case 0:
                return np.dtype(
                    [
                        ("position", "<f4", 3),
                        ("normal", "<u1", 4),
                        ("uv_0", "<f2", 2),
                        ("uv_1", "<f2", 2),
                        ("color", "<u1", 4),
                    ]
                )
            case 1:
                return np.dtype(
                    [
                        ("position", "<f4", 3),
                        ("normal", "<u1", 4),
                        ("uv_0", "<f2", 2),
                        ("uv_1", "<f2", 2),
                        ("weights", "<u1", 4),
                        ("indices", "<u1", 4),
                        ("color", "<u1", 4),
                    ]
                )
            case 2:
                return np.dtype([("position", "<f4", 3)])
            case 3:
                return np.dtype(
                    [
                        ("position", "<f4", 3),
                        ("color", "<u1", 4),
                    ]
                )
            case 4:
                return np.dtype(
                    [
                        ("position", "<f4", 3),
                        ("color", "<u1", 4),
                        ("uv_0", "<f4", 2),
                    ]
                )
            case 5:
                return np.dtype(
                    [
                        ("position", "<f4", 3),
                        ("normal", "<f4", 3),
                    ]
                )
            case 6:
                return np.dtype(
                    [
                        ("position", "<f4", 3),
                        ("normal", "<f4", 3),
                        ("color", "<u1", 4),
                        ("uv_0", "<f4", 2),
                    ]
                )
            case 7:
                return np.dtype(
                    [
                        ("position", "<f4", 3),
                        ("normal", "<f4", 3),
                        ("uv_0", "<f4", 2),
                        ("weights", "<u1", 4),
                        ("indices", "<u1", 4),
                    ]
                )
            case 8:
                return np.dtype(
                    [
                        ("position", "<f4", 3),
                        ("normal", "<u1", 4),
                        ("uv_0", "<f2", 2),
                        ("uv_1", "<f2", 2),
                        ("uv_2", "<f2", 2),
                        ("color", "<u1", 4),
                    ]
                )
            case 9:
                return np.dtype(
                    [
                        ("position", "<f4", 3),
                        ("color", "<u1", 4),
                        ("uv_0", "<f2", 4),
                        ("uv_1", "<f4", 2),
                    ]
                )
            case 10:
                return np.dtype(
                    [
                        ("position", "<f4", 3),
                        ("normal", "<f4", 3),
                        ("binormal", "<f4", 3),
                        ("uv_0", "<f2", 4),
                        ("color", "<u1", 4),
                        ("uv_1", "<f4", 2),
                    ]
                )
            case 11:
                return np.dtype(
                    [
                        ("position", "<f4", 3),
                        ("normal", "<u1", 4),
                        ("uv_0", "<f2", 2),
                        ("uv_1", "<f2", 2),
                        ("uv_2", "<f4", 3),
                        ("color", "<u1", 4),
                    ]
                )
            case 12:
                return np.dtype(
                    [
                        ("position", "<f4", 3),
                        ("normal", "<u1", 4),
                        ("uv_0", "<f4", 2),
                        ("uv_1", "<f4", 2),
                        ("weights", "<u1", 4),
                        ("indices", "<u1", 4),
                        ("uv_2", "<f4", 3),
                        ("color", "<u1", 4),
                    ]
                )
            case 13:
                return np.dtype(
                    [
                        ("position", "<f4", 3),
                        ("uv_0", "<f2", 2),
                        ("color", "<u1", 4),
                    ]
                )
            case 14:
                return np.dtype(
                    [
                        ("position", "<f4", 3),
                        ("normal", "<u1", 4),
                        ("uv_0", "<f2", 2),
                        ("color", "<u1", 4),
                    ]
                )
            case 15:
                return np.dtype(
                    [
                        ("position", "<f4", 3),
                        ("normal", "<u1", 4),
                        ("uv_0", "<f2", 2),
                        ("weights", "<u1", 4),
                        ("indices", "<u1", 4),
                        ("color", "<u1", 4),
                    ]
                )
            case _:
                raise ValueError(f"Unknown vertex type {dtype_index}")

    def read_shape(self, shape_id: int) -> Shape:
        shape_path = self.get_path(shape_id)
        logger.info('Reading shape file "%s"', shape_path)
        bs = self.create_reader(shape_path)

        shape_name = self.get_string(bs.read_uint32())
        bs.read_vec3f()
        bs.read_int32()
        bs.read_vec3f()
        bs.read_int32()
        bs.read_vec3f()
        bs.read_int32()
        bs.read_vec3f()
        bs.read_int32()
        bs.read_vec3f()
        bs.read_int32()
        bs.read_vec3f()
        bs.read_int32()
        bs.read_vec3f()
        bs.read_int32()
        vertex_count = bs.read_uint32()
        face_idx_count = bs.read_uint32()
        bs.read_int32()
        material_count = bs.read_int32()
        vertex_type_id = bs.read_uint32()
        face_type_id = bs.read_uint32()
        bs.read_int32()
        vertex_buf_id = bs.read_uint32()
        vertex_buf_size = bs.read_uint32()
        bs.read_int32()
        bs.read_int32()
        bs.seek(48, 1)
        face_buf_id = bs.read_uint32()
        face_buf_size = bs.read_uint32()
        bs.read_int32()
        bs.read_int32()
        bs.read_int32()
        bs.read_int32()
        bs.read_int32()
        bs.read_int32()
        bs.read_matrix_4x4()
        unk_id_0 = bs.read_uint32()
        material_group_id = bs.read_uint32()
        unk_id_1 = bs.read_uint32()
        bs.read_int32()
        bs.read_int32()
        bs.read_int32()
        bs.read_int32()
        bs.read_int32()
        unk_size = bs.read_uint32()
        unk_id_2 = bs.read_uint32()
        bs.read_int32()
        bs.read_int32()

        # Read vertices
        if vertex_count > 0:
            vertex_dtype = self._get_vertex_dtype(vertex_type_id)
            stride = vertex_buf_size // vertex_count
            if stride != vertex_dtype.itemsize:
                raise ValueError(
                    f"Stored vertex stride is {stride}, "
                    f"but NumPy stride is {vertex_dtype.itemsize}"
                )
            vertices = np.fromfile(
                self.get_path(vertex_buf_id),
                vertex_dtype,
                vertex_count,
            )
        else:
            vertices = np.array([])

        # Read face indices
        if face_idx_count > 0:
            if face_type_id == 0:
                face_indices = np.fromfile(
                    self.get_path(face_buf_id), "<u2", face_idx_count
                )
            elif face_type_id == 1:
                face_indices = np.fromfile(
                    self.get_path(face_buf_id), "<u4", face_idx_count
                )
            else:
                raise NotImplementedError(f"Unimplemented face type {face_type_id}")
        else:
            face_indices = np.array([])

        # Read material group
        if material_group_id not in self.asset_pool:
            material_group_path = self.get_path(material_group_id)
            logger.info('Reading material group file "%s"', material_group_path)
            bs = self.create_reader(material_group_path)
            materials = [self.read_material(bs) for _ in range(material_count)]
            self.asset_pool[material_group_id] = materials
        else:
            materials = self.asset_pool[material_group_id]
        return Shape(shape_id, shape_name, vertices, face_indices, materials)

    def read_msh(self, msh_path: Path) -> list[Shape]:
        logger.info('Reading msh file "%s"', msh_path)
        bs = self.create_reader(msh_path)

        assert bs.read_uint32() == 0
        assert bs.read_uint32() == 0
        shape_count = bs.read_uint32()
        shape_table_id = bs.read_uint32()
        node_count = bs.read_uint32()
        node_table_id = bs.read_uint32()

        # Read shape ID table
        shape_table_path = self.get_path(shape_table_id)
        logger.info('Reading shape table file "%s"', shape_table_path)
        bs = self.create_reader(shape_table_path)
        shape_id_table = [bs.read_uint32() for _ in range(shape_count)]

        # Read shapes
        shapes: list[Shape] = []
        for shape_id in shape_id_table:
            if shape_id not in self.asset_pool:
                shape = self.read_shape(shape_id)
                shapes.append(shape)
                self.asset_pool[shape_id] = shape
            else:
                shape = self.asset_pool[shape_id]
        return shapes
