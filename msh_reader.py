from dataclasses import dataclass
import logging
from pathlib import Path

import numpy as np
import numpy.typing as npt

from .binary_reader import BinaryReader

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class Shape:
    file_id: int
    name: str
    vertices: npt.NDArray
    face_indices: npt.NDArray


class MSHReader:
    def __init__(self, root_path: Path, manifest: dict) -> None:
        self.root_path = root_path
        self.manifest = manifest

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
        bs.read_int32()
        bs.read_int32()
        bs.read_matrix_4x4()
        bs.read_int32()
        unk_id_0 = bs.read_uint32()
        unk_id_1 = bs.read_uint32()
        unk_id_2 = bs.read_uint32()
        bs.read_int32()
        bs.read_int32()
        bs.read_int32()
        bs.read_int32()
        bs.read_int32()
        unk_size = bs.read_uint32()
        unk_id_3 = bs.read_uint32()
        bs.read_int32()
        bs.read_int32()

        # Read vertices
        if vertex_count > 0:
            vertex_stride = vertex_buf_size // vertex_count
            vertex_fields = [("position", "<f4", 3)]
            if vertex_stride >= 16:
                vertex_fields.append(("normal", "<u1", 4))
            if vertex_stride >= 20:
                vertex_fields.append(("uv_1", "<f2", 2))
            if vertex_stride >= 24:
                vertex_fields.append(("uv_0", "<f2", 2))
            if vertex_stride >= 28:
                vertex_fields.append(("uv_2", "<f2", 2))
            if vertex_stride >= 32:
                vertex_fields.append(("color", "u1", 4))
            if vertex_stride > 32:
                vertex_fields.append(("unk", "u1", vertex_stride - 32))
            vertices = np.fromfile(
                self.get_path(vertex_buf_id), np.dtype(vertex_fields), vertex_count
            )
        else:
            vertices = np.array([])

        # Read face indices
        if face_idx_count > 0:
            face_idx_stride = face_buf_size // face_idx_count
            if face_idx_stride == 2:
                face_indices = np.fromfile(
                    self.get_path(face_buf_id), "<u2", face_idx_count
                )
            elif face_idx_stride == 4:
                face_indices = np.fromfile(
                    self.get_path(face_buf_id), "<u4", face_idx_count
                )
            else:
                raise ValueError(f"Unexpected face index stride {face_idx_stride}")
        else:
            face_indices = np.array([])
        return Shape(shape_id, shape_name, vertices, face_indices)

    def read_msh(self, msh_path: Path) -> list[Shape]:
        logger.info('Reading msh file "%s"', msh_path)
        bs = self.create_reader(msh_path)
        assert bs.read_uint32() == 0
        assert bs.read_uint32() == 0
        shape_count = bs.read_uint32()
        shape_table_id = bs.read_uint32()
        node_count = bs.read_uint32()
        node_table_id = bs.read_uint32()

        shape_table_path = self.get_path(shape_table_id)
        logger.info('Reading shape table file "%s"', shape_table_path)
        bs = self.create_reader(shape_table_path)
        shape_id_table = [bs.read_uint32() for _ in range(shape_count)]
        shapes = [self.read_shape(shape_id) for shape_id in shape_id_table]
        return shapes
