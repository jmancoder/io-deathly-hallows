from __future__ import annotations
from dataclasses import dataclass
import logging
from pathlib import Path
from typing import Any, Literal

import numpy as np
import numpy.typing as npt
from mathutils import Matrix

from .binary_reader import BinaryReader

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class Texture:
    data_id: int
    name: str
    data_path: Path | None
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
    shader_name: str
    texture_map: dict[str, Texture]
    properties: list[MaterialProperty]


@dataclass(slots=True)
class Batch:
    face_start_index: int
    face_index_count: int
    material_index: int
    bone_pal_start_idx: int
    bone_pal_len: int
    flags: int


@dataclass(slots=True)
class Shape:
    file_id: int
    name: str
    vertices: npt.NDArray
    face_indices: npt.NDArray
    batches: list[Batch]
    materials: list[Material]
    bone_palette: npt.NDArray


@dataclass(slots=True)
class Bone:
    name: str
    transform: Matrix
    inverse_transform: Matrix
    unk_vec_a: tuple[float, float, float, float]
    unk_vec_b: tuple[float, float, float, float]
    parent_index: int
    sibling_index: int
    child_index: int
    self_index: int


@dataclass(slots=True)
class Skeleton:
    name: str
    bone_group_id: int
    bones: list[Bone]


class AssetReader:
    def __init__(
        self,
        root_path: Path,
        manifest: dict,
        source_game: Literal["DH1", "DH2"],
        delta_reader: AssetReader | None = None,
    ) -> None:
        self.root_path = root_path
        self.manifest = manifest
        self.source_game = source_game
        self.delta_reader = delta_reader

        self.archive_name: str = root_path.name
        self.asset_pool: dict[int, Any] = {}

    def get_string(self, string_id: int) -> str:
        return self.manifest["strings"][str(string_id)]

    def get_path(self, asset_id: int, use_delta_root=False) -> Path:
        name = self.get_string(asset_id)
        if ":" in name:
            category, path = name.split(":")
            if category != self.archive_name:
                path += "." + category
        else:
            path = name
        if use_delta_root and self.delta_reader is not None:
            return self.delta_reader.root_path / path
        return self.root_path / path

    def read_tex(self, tex_path: Path) -> Texture:
        logger.info('Reading TEX file "%s"', tex_path)
        bs = BinaryReader(tex_path.read_bytes())

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
        logger.info('Caching TEX data path "%s"', data_path)
        return Texture(data_id, tex_path.stem, data_path, width, height, size)

    def read_face_batch(self, bs: BinaryReader) -> Batch:
        bs.read_int32()
        face_idx_start = bs.read_uint32()
        face_idx_count = bs.read_uint32()
        material_idx = bs.read_int32()
        bs.read_int32()
        bs.read_int32()
        bone_pal_start_idx = bs.read_uint32()
        bone_pal_len = bs.read_uint32()
        flags = bs.read_uint32()

        return Batch(
            face_idx_start,
            face_idx_count,
            material_idx,
            bone_pal_start_idx,
            bone_pal_len,
            flags,
        )

    def read_material(self, bs: BinaryReader) -> Material:
        mat_start = bs.tell()
        shader_name = self.get_string(bs.read_uint32())
        shader_name = shader_name.split(":")[-1]
        bs.read_uint32()
        mat_name = bs.read_string(24)

        # Read textures
        tex_map: dict[str, Texture] = {}
        for _ in range(16):
            bs.seek(32, 1)
            tex_type = self.get_string(bs.read_uint32())
            tex_id = bs.read_uint32()
            if tex_id not in self.asset_pool:
                tex_path = self.get_path(tex_id)
                if tex_path.is_file():
                    texture = self.read_tex(tex_path)
                else:
                    # Load texture from global delta archive, if present
                    if self.delta_reader is not None:
                        texture = self.delta_reader.read_tex(
                            self.get_path(tex_id, use_delta_root=True)
                        )
                    else:
                        logger.error('Failed to load TEX file at "%s"', tex_path)
                        texture = Texture(tex_id, tex_path.stem, None, 1, 1, 0)
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
        return Material(mat_name, shader_name, tex_map, props)

    def _get_vertex_dtype_dh1(self, dtype_index: int) -> npt.DTypeLike:
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
                        ("uv_0", "<f2", 2),
                        ("uv_1", "<f4", 2),
                        ("uv_2", "<f4", 2),
                    ]
                )
            case 10:
                return np.dtype(
                    [
                        ("position", "<f4", 3),
                        ("normal", "<f4", 3),
                        ("binormal", "<f4", 3),
                        ("uv_0", "<f2", 2),
                        ("uv_1", "<f2", 2),
                        ("color", "<u1", 4),
                        ("uv_2", "<f4", 2),
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

    def _get_vertex_dtype_dh2(self, dtype_index: int) -> npt.DTypeLike:
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
            case 9:
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
            case _:
                raise ValueError(f"Unknown vertex type {dtype_index}")

    def read_shape(self, shape_id: int) -> Shape:
        shape_path = self.get_path(shape_id)
        logger.info('Reading shape file "%s"', shape_path)
        bs = BinaryReader(shape_path.read_bytes())

        shape_name = self.get_string(bs.read_uint32())
        for _ in range(7):
            bs.read_vec3f()
            bs.read_int32()
        vertex_count = bs.read_uint32()
        face_idx_count = bs.read_uint32()
        batch_count = bs.read_uint32()
        material_count = bs.read_int32()
        vertex_type_id = bs.read_uint32()
        face_type_id = bs.read_uint32()
        bs.read_int32()
        if self.source_game == "DH2":
            bs.read_int32()
            bs.read_int32()
            bs.read_int32()
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
        bs.read_matrix_4x4()
        bs.read_int32()
        shape_batch_group_id = bs.read_uint32()
        material_group_id = bs.read_uint32()
        material_prop_group_id = bs.read_uint32()
        bs.read_int32()
        bone_pal_id = bs.read_uint32()
        bone_pal_idx_count = bs.read_uint32()
        if self.source_game == "DH2":
            bs.read_int32()
            bs.read_int32()
            bs.read_int32()
        bs.read_int32()
        bs.read_int32()
        bs.read_uint32()
        unk_id = bs.read_uint32()
        unk_count = bs.read_uint32()

        # Read vertices
        if vertex_count > 0:
            if self.source_game == "DH1":
                vertex_dtype = self._get_vertex_dtype_dh1(vertex_type_id)
            else:
                vertex_dtype = self._get_vertex_dtype_dh2(vertex_type_id)
            stride = vertex_buf_size // vertex_count
            if stride != vertex_dtype.itemsize:
                raise ValueError(
                    f"Stored vertex stride is {stride}, "
                    f"but NumPy stride is {vertex_dtype.itemsize}"
                )
            vertex_buf_path = self.get_path(vertex_buf_id)
            logger.info('Reading vertex buffer file "%s"', vertex_buf_path)
            vertices = np.fromfile(
                vertex_buf_path,
                vertex_dtype,
                vertex_count,
            )
        else:
            vertices = np.empty(0)

        # Read face indices
        if face_idx_count > 0:
            face_buf_path = self.get_path(face_buf_id)
            logger.info('Reading face index buffer file "%s"', face_buf_path)
            face_idx_stride = face_buf_size // face_idx_count
            if face_idx_stride == 2:
                face_indices = np.fromfile(face_buf_path, "<u2", face_idx_count)
            elif face_idx_stride == 4:
                face_indices = np.fromfile(face_buf_path, "<u4", face_idx_count)
            else:
                raise NotImplementedError(f"Unimplemented face type {face_type_id}")
        else:
            face_indices = np.empty(0, "<u2")

        # Read shape batch group
        shape_batch_group_path = self.get_path(shape_batch_group_id)
        logger.info('Reading shape batch group file "%s"', shape_batch_group_path)
        bs = BinaryReader(shape_batch_group_path.read_bytes())
        batches = [self.read_face_batch(bs) for _ in range(batch_count)]

        # Read material group
        if material_group_id not in self.asset_pool:
            material_group_path = self.get_path(material_group_id)
            logger.info('Reading material group file "%s"', material_group_path)
            bs = BinaryReader(material_group_path.read_bytes())
            materials = [self.read_material(bs) for _ in range(material_count)]
            self.asset_pool[material_group_id] = materials
        else:
            materials = self.asset_pool[material_group_id]

        # Read bone palette indices
        if bone_pal_idx_count > 0:
            bone_pal_path = self.get_path(bone_pal_id)
            logger.info('Reading bone palette file "%s"', bone_pal_path)
            bone_palette = np.fromfile(bone_pal_path, "<u2", bone_pal_idx_count)
        else:
            bone_palette = np.empty(0, "<u2")

        return Shape(
            shape_id,
            shape_name,
            vertices,
            face_indices,
            batches,
            materials,
            bone_palette,
        )

    def read_msh(self, msh_path: Path) -> list[Shape]:
        logger.info('Reading MSH file "%s"', msh_path)
        bs = BinaryReader(msh_path.read_bytes())

        bs.read_int32()
        bs.read_int32()
        shape_count = bs.read_uint32()
        shape_table_id = bs.read_uint32()
        node_count = bs.read_uint32()
        node_table_id = bs.read_uint32()

        # Read shape ID table
        shape_table_path = self.get_path(shape_table_id)
        logger.info('Reading shape table file "%s"', shape_table_path)
        bs = BinaryReader(shape_table_path.read_bytes())
        shape_id_table = [bs.read_uint32() for _ in range(shape_count)]

        # Read shapes
        shapes: list[Shape] = []
        for shape_id in shape_id_table:
            if shape_id not in self.asset_pool:
                shape = self.read_shape(shape_id)
                self.asset_pool[shape_id] = shape
            else:
                shape = self.asset_pool[shape_id]
            shapes.append(shape)
        return shapes

    def read_bone(self, bs: BinaryReader) -> Bone:
        if self.source_game == "DH1":
            name = bs.read_string(64)
        transform_a = bs.read_matrix_4x4()
        transform_b = bs.read_matrix_4x4()
        unk_vec_a = bs.read_vec4f()
        unk_vec_b = bs.read_vec4f()
        if self.source_game == "DH2":
            name = bs.read_string(64)
        parent_idx = bs.read_int32()
        sibling_idx = bs.read_int32()
        child_idx = bs.read_int32()
        self_idx = bs.read_int32()
        return Bone(
            name,
            transform_a,
            transform_b,
            unk_vec_a,
            unk_vec_b,
            parent_idx,
            sibling_idx,
            child_idx,
            self_idx,
        )

    def read_skl(self, skl_path: Path) -> Skeleton:
        logger.info('Reading SKL file "%s"', skl_path)
        bs = BinaryReader(skl_path.read_bytes())

        bone_count = bs.read_uint32()
        bone_group_id = bs.read_uint32()
        bs.read_int32()
        unk_id = bs.read_uint32()
        bs.read_float()
        bs.read_int32()
        bs.read_int32()
        bs.read_int32()

        bone_group_path = self.get_path(bone_group_id)
        logger.info('Reading bone group file "%s"', bone_group_path)
        bs = BinaryReader(bone_group_path.read_bytes())
        bones = [self.read_bone(bs) for _ in range(bone_count)]
        return Skeleton(skl_path.stem, bone_group_id, bones)
