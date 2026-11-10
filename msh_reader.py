from dataclasses import dataclass
import logging
from pathlib import Path

import numpy as np
import numpy.typing as npt

from .binary_reader import BinaryReader

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class Shape:
    properties: str
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
        logger.info("Reading shape %s", shape_path)
        bs = self.create_reader(shape_path)
        properties = self.get_string(bs.read_uint32())
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
        unk_attr_size = vertex_buf_size // vertex_count - 12
        vertex_dtype = np.dtype(
            [("position", "<f4", 3), ("unknown", "<u1", unk_attr_size)]
        )
        vertices = np.fromfile(
            self.get_path(vertex_buf_id), vertex_dtype, vertex_count
        )

        # Read face indices
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
        return Shape(properties, vertices, face_indices)

    def read_msh(self, msh_path: Path) -> None:
        bs = self.create_reader(msh_path)
        assert bs.read_uint32() == 0
        assert bs.read_uint32() == 0
        shape_count = bs.read_uint32()
        shape_table_id = bs.read_uint32()
        node_count = bs.read_uint32()
        node_table_id = bs.read_uint32()

        shape_table_path = self.get_path(shape_table_id)
        logger.info("Reading shape table %s", shape_table_path)
        bs = self.create_reader(shape_table_path)
        shape_id_table = [bs.read_uint32() for _ in range(shape_count)]
        shapes = [self.read_shape(shape_id) for shape_id in shape_id_table]
