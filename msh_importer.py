import logging

import bpy
import numpy as np
import numpy.typing as npt

from . import msh_reader

logger = logging.getLogger(__name__)


def create_gfx_world_group() -> bpy.types.ShaderNodeTree:
    group = bpy.data.node_groups.new(name="gfx_world", type="ShaderNodeTree")
    group.interface.new_socket(
        name="t_colour", in_out="INPUT", socket_type="NodeSocketColor"
    )
    socket = group.interface.new_socket(
        name="t_colour_alpha", in_out="INPUT", socket_type="NodeSocketFloat"
    )
    socket.default_value = 1.0
    socket.min_value = 0.0
    socket.max_value = 1.0
    group.interface.new_socket(
        name="t_normal", in_out="INPUT", socket_type="NodeSocketColor"
    )
    group.interface.new_socket(
        name="t_spec", in_out="INPUT", socket_type="NodeSocketColor"
    )
    group.interface.new_socket(
        name="t_detail", in_out="INPUT", socket_type="NodeSocketColor"
    )
    group.interface.new_socket(
        name="t_mask", in_out="INPUT", socket_type="NodeSocketColor"
    )
    group.interface.new_socket(
        name="BSDF", in_out="OUTPUT", socket_type="NodeSocketShader"
    )

    nodes = group.nodes
    links = group.links

    input_node = nodes.new(type="NodeGroupInput")
    input_node.location = (-1000.0, 0.0)

    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (0.0, 0.0)
    links.new(input_node.outputs["t_colour"], bsdf.inputs["Base Color"])
    links.new(input_node.outputs["t_colour_alpha"], bsdf.inputs["Alpha"])

    sep_color_node = nodes.new("ShaderNodeSeparateColor")
    sep_color_node.location = (-650.0, -250.0)
    one_minus_node = nodes.new("ShaderNodeMath")
    one_minus_node.operation = "SUBTRACT"
    one_minus_node.inputs[0].default_value = 1.0
    one_minus_node.location = (-350.0, -250.0)
    links.new(input_node.outputs["t_spec"], sep_color_node.inputs["Color"])
    links.new(sep_color_node.outputs["Green"], one_minus_node.inputs[1])
    links.new(one_minus_node.outputs["Value"], bsdf.inputs["Roughness"])

    norm_map_node = nodes.new("ShaderNodeNormalMap")
    norm_map_node.convention = "DIRECTX"
    norm_map_node.location = (-500.0, -500.0)
    links.new(input_node.outputs["t_normal"], norm_map_node.inputs["Color"])
    links.new(norm_map_node.outputs["Normal"], bsdf.inputs["Normal"])

    output_node = nodes.new(type="NodeGroupOutput")
    output_node.location = (1000.0, 0.0)
    links.new(bsdf.outputs["BSDF"], output_node.inputs["BSDF"])
    return group


def create_gfx_layered_group() -> bpy.types.ShaderNodeTree:
    group = bpy.data.node_groups.new(name="gfx_layered", type="ShaderNodeTree")
    group.interface.new_socket(
        name="t_colour", in_out="INPUT", socket_type="NodeSocketColor"
    )
    socket = group.interface.new_socket(
        name="t_colour_alpha", in_out="INPUT", socket_type="NodeSocketFloat"
    )
    socket.default_value = 1.0
    socket.min_value = 0.0
    socket.max_value = 1.0
    group.interface.new_socket(
        name="t_normal", in_out="INPUT", socket_type="NodeSocketColor"
    )
    group.interface.new_socket(
        name="t_spec", in_out="INPUT", socket_type="NodeSocketColor"
    )
    group.interface.new_socket(
        name="t_colour2", in_out="INPUT", socket_type="NodeSocketColor"
    )
    socket = group.interface.new_socket(
        name="t_colour2_alpha", in_out="INPUT", socket_type="NodeSocketFloat"
    )
    socket.default_value = 1.0
    socket.min_value = 0.0
    socket.max_value = 1.0
    group.interface.new_socket(
        name="t_normal2", in_out="INPUT", socket_type="NodeSocketColor"
    )
    group.interface.new_socket(
        name="t_spec2", in_out="INPUT", socket_type="NodeSocketColor"
    )
    group.interface.new_socket(
        name="t_detail", in_out="INPUT", socket_type="NodeSocketColor"
    )
    group.interface.new_socket(
        name="t_mask", in_out="INPUT", socket_type="NodeSocketColor"
    )
    group.interface.new_socket(
        name="BSDF", in_out="OUTPUT", socket_type="NodeSocketShader"
    )

    nodes = group.nodes
    links = group.links

    input_node = nodes.new(type="NodeGroupInput")
    input_node.location = (-1000.0, 0.0)

    # Add layer 1
    bsdf_0 = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf_0.location = (0.0, 0.0)
    links.new(input_node.outputs["t_colour"], bsdf_0.inputs["Base Color"])
    links.new(input_node.outputs["t_colour_alpha"], bsdf_0.inputs["Alpha"])

    sep_color_node = nodes.new("ShaderNodeSeparateColor")
    sep_color_node.location = (-650.0, -250.0)
    one_minus_node = nodes.new("ShaderNodeMath")
    one_minus_node.operation = "SUBTRACT"
    one_minus_node.inputs[0].default_value = 1.0
    one_minus_node.location = (-350.0, -250.0)
    links.new(input_node.outputs["t_spec"], sep_color_node.inputs["Color"])
    links.new(sep_color_node.outputs["Green"], one_minus_node.inputs[1])
    links.new(one_minus_node.outputs["Value"], bsdf_0.inputs["Roughness"])

    norm_map_node = nodes.new("ShaderNodeNormalMap")
    norm_map_node.convention = "DIRECTX"
    norm_map_node.location = (-500.0, -500.0)
    links.new(input_node.outputs["t_normal"], norm_map_node.inputs["Color"])
    links.new(norm_map_node.outputs["Normal"], bsdf_0.inputs["Normal"])

    # Add layer 2
    bsdf_1 = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf_1.location = (0.0, -1000.0)
    links.new(input_node.outputs["t_colour2"], bsdf_1.inputs["Base Color"])
    links.new(input_node.outputs["t_colour2_alpha"], bsdf_1.inputs["Alpha"])

    sep_color_node = nodes.new("ShaderNodeSeparateColor")
    sep_color_node.location = (-650.0, -1250.0)
    one_minus_node = nodes.new("ShaderNodeMath")
    one_minus_node.operation = "SUBTRACT"
    one_minus_node.inputs[0].default_value = 1.0
    one_minus_node.location = (-350.0, -1250.0)
    links.new(input_node.outputs["t_spec2"], sep_color_node.inputs["Color"])
    links.new(sep_color_node.outputs["Green"], one_minus_node.inputs[1])
    links.new(one_minus_node.outputs["Value"], bsdf_1.inputs["Roughness"])

    norm_map_node = nodes.new("ShaderNodeNormalMap")
    norm_map_node.convention = "DIRECTX"
    norm_map_node.location = (-500.0, -1500.0)
    links.new(input_node.outputs["t_normal2"], norm_map_node.inputs["Color"])
    links.new(norm_map_node.outputs["Normal"], bsdf_1.inputs["Normal"])

    # Mix layers using detail texture
    mix_shader_node = nodes.new("ShaderNodeMixShader")
    mix_shader_node.location = (500.0, 0.0)
    output_node = nodes.new(type="NodeGroupOutput")
    output_node.location = (1000.0, 0.0)
    links.new(input_node.outputs["t_detail"], mix_shader_node.inputs[0])
    links.new(bsdf_0.outputs["BSDF"], mix_shader_node.inputs[1])
    links.new(bsdf_1.outputs["BSDF"], mix_shader_node.inputs[2])
    links.new(mix_shader_node.outputs[0], output_node.inputs["BSDF"])
    return group


def import_material(material_data: msh_reader.Material) -> bpy.types.Material:
    # Import images
    img_map: dict[str, bpy.types.Image] = {}
    for tex_type, tex_data in material_data.texture_map.items():
        img = bpy.data.images.get(tex_data.name)
        if img is None:
            img = bpy.data.images.load(str(tex_data.data_path))
            img.name = tex_data.name
        category, prop_type = tex_type.split(":")
        if category == "sp":
            img_map[prop_type] = img

    # Create empty material
    material = bpy.data.materials.new(material_data.name)
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    links.clear()

    # Create node group if necessary
    match material_data.shader_name:
        case "gfx_layered":
            group_tree = bpy.data.node_groups.get("gfx_layered")
            if group_tree is None:
                group_tree = create_gfx_layered_group()
        case "gfx_world":
            group_tree = bpy.data.node_groups.get("gfx_world")
            if group_tree is None:
                group_tree = create_gfx_world_group()
        case _:
            group_tree = bpy.data.node_groups.get(material_data.shader_name)
            if group_tree is None:
                group_tree = create_gfx_world_group()
                group_tree.name = material_data.shader_name

    # Add group and output nodes
    group_node = nodes.new(type="ShaderNodeGroup")
    group_node.node_tree = group_tree
    group_node.location = (-300.0, 0.0)
    output_node = nodes.new("ShaderNodeOutputMaterial")
    links.new(group_node.outputs["BSDF"], output_node.inputs["Surface"])

    # Add image and UV nodes
    x_off = -900.0
    y_off = 0.0
    for img_type, img in img_map.items():
        match img_type:
            case "t_colour":
                img.colorspace_settings.name = "sRGB"
                img_node = nodes.new("ShaderNodeTexImage")
                img_node.image = img
                img_node.location = (x_off, y_off)
                links.new(img_node.outputs["Color"], group_node.inputs["t_colour"])
                links.new(
                    img_node.outputs["Alpha"], group_node.inputs["t_colour_alpha"]
                )

            case "t_normal":
                img.colorspace_settings.name = "Non-Color"
                img_node = nodes.new("ShaderNodeTexImage")
                img_node.image = img
                img_node.location = (x_off, y_off)
                links.new(img_node.outputs["Color"], group_node.inputs["t_normal"])

            case "t_spec":
                img.colorspace_settings.name = "Non-Color"
                img_node = nodes.new("ShaderNodeTexImage")
                img_node.image = img
                img_node.location = (x_off, y_off)
                links.new(img_node.outputs["Color"], group_node.inputs["t_spec"])

            case "t_colour2":
                img.colorspace_settings.name = "sRGB"
                img_node = nodes.new("ShaderNodeTexImage")
                img_node.image = img
                img_node.location = (x_off, y_off)
                links.new(img_node.outputs["Color"], group_node.inputs["t_colour2"])
                links.new(
                    img_node.outputs["Alpha"], group_node.inputs["t_colour2_alpha"]
                )

            case "t_normal2":
                img.colorspace_settings.name = "Non-Color"
                img_node = nodes.new("ShaderNodeTexImage")
                img_node.image = img
                img_node.location = (x_off, y_off)
                links.new(img_node.outputs["Color"], group_node.inputs["t_normal2"])

            case "t_spec2":
                img.colorspace_settings.name = "Non-Color"
                img_node = nodes.new("ShaderNodeTexImage")
                img_node.image = img
                img_node.location = (x_off, y_off)
                links.new(img_node.outputs["Color"], group_node.inputs["t_spec2"])

            case "t_detail":
                img.colorspace_settings.name = "Non-Color"
                img_node = nodes.new("ShaderNodeTexImage")
                img_node.image = img
                img_node.location = (x_off, y_off)
                links.new(img_node.outputs["Color"], group_node.inputs["t_detail"])

            case "t_mask":
                uv_node = nodes.new("ShaderNodeUVMap")
                uv_node.uv_map = "UVMap1"
                uv_node.location = (x_off - 300.0, y_off)
                img.colorspace_settings.name = "Non-Color"
                img_node = nodes.new("ShaderNodeTexImage")
                img_node.image = img
                img_node.location = (x_off, y_off)
                links.new(uv_node.outputs["UV"], img_node.inputs["Vector"])
                links.new(img_node.outputs["Color"], group_node.inputs["t_mask"])

            case _:
                logger.warning(
                    "%s uses image of unimplemented type %s", material.name, img_type
                )
                img.colorspace_settings.name = "Non-Color"
                img_node = nodes.new("ShaderNodeTexImage")
                img_node.image = img
                img_node.location = (x_off, y_off)
        y_off -= 300.0
    return material


def _convert_normals(theta_b: npt.NDArray[np.uint8], phi_b: npt.NDArray[np.uint8]):
    t = theta_b.astype(np.float32) * (2 * np.pi / 256)
    f = phi_b.astype(np.float32) * (2 * np.pi / 256)
    return -np.stack([np.sin(t) * np.cos(f), np.cos(t), np.sin(t) * np.sin(f)], axis=-1)


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
            normals = _convert_normals(raw_normals[:, 3], raw_normals[:, 2])
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
