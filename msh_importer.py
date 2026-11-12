import bpy
import numpy as np
import numpy.typing as npt

from . import msh_reader


def convert_normals(theta_b: npt.NDArray[np.uint8], phi_b: npt.NDArray[np.uint8]):
    t = theta_b.astype(np.float32) * (2 * np.pi / 256)
    f = phi_b.astype(np.float32) * (2 * np.pi / 256)
    return -np.stack([np.sin(t) * np.cos(f), np.cos(t), np.sin(t) * np.sin(f)], axis=-1)


def import_material(material_data: msh_reader.Material) -> bpy.types.Material:
    mat = bpy.data.materials.new(material_data.name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    bsdf = nodes.get("Principled BSDF")
    links = mat.node_tree.links

    # Import textures/images
    for tex_type, tex_data in material_data.texture_map.items():
        if tex_data.name in bpy.data.images:
            image = bpy.data.images.get(tex_data.name)
        else:
            image = bpy.data.images.load(str(tex_data.data_path))
            image.name = tex_data.name

        img_node = nodes.new("ShaderNodeTexImage")
        img_node.image = image

        if tex_type == "sp:t_colour":
            image.colorspace_settings.name = "sRGB"
            img_node.location = (-1000.0, 250.0)
            links.new(img_node.outputs["Color"], bsdf.inputs["Base Color"])

        elif tex_type == "sp:t_normal":
            image.colorspace_settings.name = "Non-Color"
            img_node.location = (-1000.0, -250.0)

            norm_map_node = nodes.new("ShaderNodeNormalMap")
            norm_map_node.convention = "DIRECTX"
            norm_map_node.location = (-500.0, -250.0)

            links.new(img_node.outputs["Color"], norm_map_node.inputs["Color"])
            links.new(norm_map_node.outputs["Normal"], bsdf.inputs["Normal"])

        elif tex_type == "sp:t_spec":
            image.colorspace_settings.name = "Non-Color"
            img_node.location = (-1000.0, 0.0)

            sep_node = nodes.new("ShaderNodeSeparateColor")
            sep_node.location = (-600.0, 0.0)

            one_minus_node = nodes.new("ShaderNodeMath")
            one_minus_node.operation = "SUBTRACT"
            one_minus_node.inputs[0].default_value = 1.0
            one_minus_node.location = (-400.0, 0.0)

            links.new(img_node.outputs["Color"], sep_node.inputs["Color"])
            links.new(sep_node.outputs["Red"], one_minus_node.inputs[1])
            links.new(one_minus_node.outputs["Value"], bsdf.inputs["Roughness"])

        # TODO: Link secondary textures
    return mat


def import_shape(context: bpy.types.Context, shape: msh_reader.Shape) -> None:
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

    # Import UVs
    for i in range(4):
        attr_name = f"uv_{i}"
        if attr_name not in shape.vertices.dtype.names:
            continue
        uvs = shape.vertices[attr_name]
        uvs[:, 1] = 1.0 - uvs[:, 1]
        uvs = uvs[shape.face_indices]
        uv_layer = mesh.uv_layers.new(name=f"UVMap{i}")
        uv_layer.data.foreach_set("uv", uvs.ravel())

    # Import normals
    if "normal" in shape.vertices.dtype.names:
        raw_normals = shape.vertices["normal"]
        if raw_normals.itemsize == 1:
            # Unpack 8-bit spherical normals
            normals = convert_normals(raw_normals[:, 3], raw_normals[:, 2])
        else:
            normals = raw_normals
        mesh.normals_split_custom_set_from_vertices(normals)

    # Import materials
    for mat_data in shape.materials:
        if mat_data.name in bpy.data.materials:
            mesh.materials.append(bpy.data.materials.get(mat_data.name))
        else:
            mesh.materials.append(import_material(mat_data))

    # Assign materials
    corner_starts = np.array(
        [slot.start_corner for slot in shape.slots], dtype=np.int64
    )
    material_indices = np.array(
        [slot.material_index for slot in shape.slots], dtype=np.int32
    )
    loop_starts = np.empty(len(mesh.polygons), dtype=np.int32)
    mesh.polygons.foreach_get("loop_start", loop_starts)
    poly_mat_indices = material_indices[
        np.searchsorted(corner_starts, loop_starts, side="right") - 1
    ]
    mesh.polygons.foreach_set("material_index", poly_mat_indices)
    mesh.update(calc_edges=True)

    # Create mesh object with stored name
    mesh_name = "Mesh"
    for name in shape.name.split("|")[2:]:
        if name == "EXPORT":
            break
        mesh_name = name
    mesh_obj = bpy.data.objects.new(mesh_name, mesh)
    context.collection.objects.link(mesh_obj)
