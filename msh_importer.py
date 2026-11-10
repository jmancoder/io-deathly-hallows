import bpy
import numpy as np

from .msh_reader import Shape


def import_shape(context: bpy.types.Context, shape: Shape) -> None:
    mesh_name = "Mesh"
    for name in shape.delimited_name.split("|")[2:]:
        if name == "EXPORT":
            break
        mesh_name = name

    mesh = bpy.data.meshes.new(mesh_name)
    mesh.vertices.add(len(shape.vertices))
    mesh.vertices.foreach_set("co", shape.vertices["position"].ravel())

    # Import triangles
    mesh.loops.add(len(shape.face_indices))
    mesh.loops.foreach_set("vertex_index", shape.face_indices)
    mesh.polygons.add(len(shape.face_indices) // 3)
    mesh.polygons.foreach_set(
        "loop_start", np.arange(0, len(shape.face_indices), 3, dtype="<i4")
    )
    mesh.polygons.foreach_set(
        "loop_total", np.full(len(shape.face_indices), 3, dtype="<i4")
    )
    mesh.update(calc_edges=True)

    # Create mesh object
    mesh_obj = bpy.data.objects.new(mesh_name, mesh)
    context.collection.objects.link(mesh_obj)
