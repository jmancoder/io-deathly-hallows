import json
import logging
from pathlib import Path

import bpy
from bpy.props import StringProperty, PointerProperty
from bpy_extras.io_utils import ImportHelper

from .asset_reader import AssetReader
from . import asset_importer

logger = logging.getLogger(__name__)


class IODH_Settings(bpy.types.PropertyGroup):
    manifest_path: StringProperty(
        name="Manifest Path",
        description="Path to the manifest.json file in the extracted .bin.gz archive",
        subtype="FILE_PATH",
    )


def _create_asset_reader(context: bpy.types.Context) -> AssetReader:
    settings = context.scene.iodh_settings
    manifest_path = Path(bpy.path.abspath(settings.manifest_path))
    with open(manifest_path, "rt") as f:
        manifest = json.load(f)
    return AssetReader(manifest_path.parent, manifest)


class IODH_OT_import_msh(bpy.types.Operator, ImportHelper):
    """Import shapes, materials, and textures from an MSH file and its dependencies."""

    bl_idname = "import_scene.iodh_msh"
    bl_label = "Import MSH"
    filename_ext = "MSH"

    filter_glob: StringProperty(
        default="*.MSH",
        options={"HIDDEN"},
        maxlen=255,
    )

    def execute(self, context):
        reader = _create_asset_reader(context)
        shapes = reader.read_msh(Path(self.filepath))
        for shape in shapes:
            asset_importer.import_shape(context, shape, None, None)
        return {"FINISHED"}


class IODH_OT_import_skl(bpy.types.Operator, ImportHelper):
    """Import bones from an SKL file and then import the adjacent MSH file."""

    bl_idname = "import_scene.iodh_skl"
    bl_label = "Import SKL"
    filename_ext = "SKL"

    filter_glob: StringProperty(
        default="*.SKL",
        options={"HIDDEN"},
        maxlen=255,
    )

    def execute(self, context):
        reader = _create_asset_reader(context)
        skl_path = Path(self.filepath)
        skeleton = reader.read_skl(skl_path)
        armature_obj = asset_importer.import_skl(context, skeleton)
        bone_names = [bone.name for bone in skeleton.bones]

        msh_path = skl_path.parent / f"{skl_path.stem}.MSH"
        if msh_path.is_file():
            shapes = reader.read_msh(msh_path)
            for shape in shapes:
                asset_importer.import_shape(context, shape, armature_obj, bone_names)
        else:
            logger.error('Failed to locate mesh at "%s"', msh_path)
        return {"FINISHED"}


class IODH_PT_main(bpy.types.Panel):
    bl_idname = "IODH_PT_main"
    bl_label = "Deathly Hallows IO"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Deathly Hallows"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        settings = context.scene.iodh_settings
        layout.prop(settings, "manifest_path")
        layout.operator("import_scene.iodh_skl", icon="IMPORT")
        layout.operator("import_scene.iodh_msh", icon="IMPORT")


classes = (IODH_Settings, IODH_OT_import_msh, IODH_OT_import_skl, IODH_PT_main)


def register():
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    logger.addHandler(ch)

    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.Scene.iodh_settings = PointerProperty(type=IODH_Settings)


def unregister():
    for h in list(logger.handlers):
        logger.removeHandler(h)
        h.close()

    del bpy.types.Scene.iodh_settings
    for c in reversed(classes):
        bpy.utils.unregister_class(c)
