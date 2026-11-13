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


class IODH_OT_import_msh(bpy.types.Operator, ImportHelper):
    bl_idname = "import_scene.iodh_msh"
    bl_label = "Import MSH"
    filename_ext = "MSH"

    filter_glob: StringProperty(
        default="*.MSH",
        options={"HIDDEN"},
        maxlen=255,
    )

    def execute(self, context):
        settings = context.scene.iodh_settings
        with open(settings.manifest_path, "rt") as f:
            manifest = json.load(f)

        reader = AssetReader(Path(settings.manifest_path).parent, manifest)
        shapes = reader.read_msh(Path(self.filepath))
        for shape in shapes:
            asset_importer.import_shape(context, shape)
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
        layout.operator("import_scene.iodh_msh", icon="IMPORT")


classes = (IODH_Settings, IODH_OT_import_msh, IODH_PT_main)


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
