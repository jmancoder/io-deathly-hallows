import bpy
from bpy.types import Image
import numpy as np
import numpy.typing as npt

from .msh_reader import Shape


def convert_normals(theta_b: npt.NDArray[np.uint8], phi_b: npt.NDArray[np.uint8]):
    t = theta_b.astype(np.float32) * (2 * np.pi / 256)
    f = phi_b.astype(np.float32) * (2 * np.pi / 256)
    return -np.stack([np.sin(t) * np.cos(f), np.cos(t), np.sin(t) * np.sin(f)], axis=-1)


def import_shape(context: bpy.types.Context, shape: Shape) -> None:
    # Import positions
    mesh = bpy.data.meshes.new(str(shape.file_id))
    mesh.vertices.add(len(shape.vertices))
    mesh.vertices.foreach_set("co", shape.vertices["position"].ravel())

    # Import triangles
    indices = shape.face_indices
    n_triangles = len(indices) // 3
    mesh.loops.add(len(indices))
    mesh.loops.foreach_set("vertex_index", indices)
    mesh.polygons.add(n_triangles)
    mesh.polygons.foreach_set("loop_start", np.arange(n_triangles, dtype=np.int32) * 3)
    mesh.polygons.foreach_set("loop_total", np.full(n_triangles, 3, dtype=np.int32))
    mesh.update(calc_edges=True)

    # Import UVs
    for i in range(2):
        attr_name = f"uv_{i}"
        if attr_name not in shape.vertices.dtype.names:
            continue
        uvs = shape.vertices[attr_name]
        uvs[:, 1] = 1.0 - uvs[:, 1]
        uvs = uvs[shape.face_indices]
        uv_layer = mesh.uv_layers.new(name=f"UVMap{i}")
        uv_layer.data.foreach_set("uv", uvs.ravel())

    # Unpack and import spherical normals
    raw_normals = shape.vertices["normal"]
    normals = convert_normals(raw_normals[:, 3], raw_normals[:, 2])
    mesh.normals_split_custom_set_from_vertices(normals)

    # Create mesh object with stored name
    mesh_name = "Mesh"
    for name in shape.name.split("|")[2:]:
        if name == "EXPORT":
            break
        mesh_name = name
    mesh_obj = bpy.data.objects.new(mesh_name, mesh)
    context.collection.objects.link(mesh_obj)

    # Import images
    image_map: dict[int, Image] = {}
    for mat_data in shape.materials:
        for tex_type, texture in mat_data.texture_map.items():
            if texture.name in bpy.data.images:
                continue
            image = image_map[texture.file_id] = bpy.data.images.load(
                str(texture.data_path)
            )
            image.name = texture.name
