import json
import logging
from pathlib import Path

import bpy
from bpy.props import CollectionProperty, EnumProperty, StringProperty, PointerProperty
from bpy_extras.io_utils import ImportHelper

from .asset_reader import AssetReader
from . import asset_importer

logger = logging.getLogger(__package__)


class IODH_Settings(bpy.types.PropertyGroup):
    source_game: EnumProperty(
        name="Game",
        description="The title of the game you are importing from",
        items=[
            (
                "DH1",
                "Deathly Hallows - Part 1",
                "Harry Potter and the Deathly Hallows - Part 1",
            ),
            (
                "DH2",
                "Deathly Hallows - Part 2",
                "Harry Potter and the Deathly Hallows - Part 2",
            ),
        ],
        default="DH1",
    )
    manifest_path: StringProperty(
        name="Manifest Path",
        description="A path to the manifest.json file in the extracted .bin.gz archive",
        subtype="FILE_PATH",
    )
    delta_manifest_path: StringProperty(
        name="Delta Manifest Path",
        description="An optional path to the manifest.json "
        "file in the extracted delta-global.bin.gz archive",
        subtype="FILE_PATH",
    )


def _create_asset_reader(context: bpy.types.Context) -> AssetReader:
    settings = context.scene.iodh_settings

    if settings.delta_manifest_path:
        delta_manifest_path = Path(bpy.path.abspath(settings.delta_manifest_path))
        with open(delta_manifest_path, "rt") as f:
            delta_manifest = json.load(f)
        delta_reader = AssetReader(
            delta_manifest_path.parent, delta_manifest, settings.source_game
        )
    else:
        delta_reader = None

    if not settings.manifest_path:
        raise ValueError("Manifest path cannot be empty")
    manifest_path = Path(bpy.path.abspath(settings.manifest_path))
    with open(manifest_path, "rt") as f:
        manifest = json.load(f)
    return AssetReader(
        manifest_path.parent, manifest, settings.source_game, delta_reader
    )


class IODH_OT_import_skl(bpy.types.Operator, ImportHelper):
    """Import bones from an SKL file, then import the adjacent MSH file"""

    bl_idname = "import_scene.iodh_skl"
    bl_label = "Import SKL"
    filename_ext = ".SKL"

    filter_glob: StringProperty(
        default="*.SKL",
        options={"HIDDEN"},
        maxlen=255,
    )
    directory: StringProperty(
        subtype="DIR_PATH",
        options={"SKIP_SAVE", "HIDDEN"},
    )
    files: CollectionProperty(
        type=bpy.types.OperatorFileListElement,
        options={"SKIP_SAVE", "HIDDEN"},
    )

    def execute(self, context: bpy.types.Context) -> set[str]:
        reader = _create_asset_reader(context)
        for file_elem in self.files:
            skl_path = Path(self.directory) / str(file_elem.name)
            skeleton = reader.read_skl(skl_path)
            armature_obj = asset_importer.import_skl(context, skeleton)
            bone_names = [bone.name for bone in skeleton.bones]

            msh_path = skl_path.with_suffix(".MSH")
            if msh_path.is_file():
                shapes = reader.read_msh(msh_path)
                for shape in shapes:
                    asset_importer.import_shape(
                        context, shape, armature_obj, bone_names
                    )
            else:
                logger.error('Failed to locate mesh at "%s"', msh_path)
        return {"FINISHED"}


class IODH_OT_import_msh(bpy.types.Operator, ImportHelper):
    """Import shapes, materials, and textures from an MSH file and its dependencies"""

    bl_idname = "import_scene.iodh_msh"
    bl_label = "Import MSH"
    filename_ext = ".MSH"

    filter_glob: StringProperty(
        default="*.MSH",
        options={"HIDDEN"},
        maxlen=255,
    )
    directory: StringProperty(
        subtype="DIR_PATH",
        options={"SKIP_SAVE", "HIDDEN"},
    )
    files: CollectionProperty(
        type=bpy.types.OperatorFileListElement,
        options={"SKIP_SAVE", "HIDDEN"},
    )

    def execute(self, context: bpy.types.Context) -> set[str]:
        reader = _create_asset_reader(context)
        for file_elem in self.files:
            msh_path = Path(self.directory) / str(file_elem.name)
            shapes = reader.read_msh(msh_path)
            for shape in shapes:
                asset_importer.import_shape(context, shape, None, None)
        return {"FINISHED"}


class IODH_OT_import_tex(bpy.types.Operator, ImportHelper):
    """Import a TEX file as a Blender image"""

    bl_idname = "import_scene.iodh_tex"
    bl_label = "Import TEX"
    filename_ext = ".TEX"

    filter_glob: StringProperty(
        default="*.TEX",
        options={"HIDDEN"},
        maxlen=255,
    )
    directory: StringProperty(
        subtype="DIR_PATH",
        options={"SKIP_SAVE", "HIDDEN"},
    )
    files: CollectionProperty(
        type=bpy.types.OperatorFileListElement,
        options={"SKIP_SAVE", "HIDDEN"},
    )

    def execute(self, context: bpy.types.Context) -> set[str]:
        reader = _create_asset_reader(context)
        for file_elem in self.files:
            tex_path = Path(self.directory) / str(file_elem.name)
            tex_data = reader.read_tex(tex_path)
            img = asset_importer.import_tex(tex_data)
            img.use_fake_user = True
        return {"FINISHED"}


class IODH_PT_main(bpy.types.Panel):
    bl_idname = "IODH_PT_main"
    bl_label = "Deathly Hallows IO"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Deathly Hallows"

    def draw(self, context: bpy.types.Context) -> None:
        settings = context.scene.iodh_settings
        layout = self.layout

        layout.prop(settings, "source_game")

        row = layout.split(factor=0.35, align=True)
        row.label(text="Manifest Path")
        row.prop(settings, "manifest_path", text="")

        row = layout.split(factor=0.5, align=True)
        row.label(text="Delta Manifest Path")
        row.prop(settings, "delta_manifest_path", text="")

        layout.operator("import_scene.iodh_skl", icon="IMPORT")
        layout.operator("import_scene.iodh_msh", icon="IMPORT")
        layout.operator("import_scene.iodh_tex", icon="IMPORT")


classes = (
    IODH_Settings,
    IODH_OT_import_msh,
    IODH_OT_import_skl,
    IODH_OT_import_tex,
    IODH_PT_main,
)


def register() -> None:
    logger.setLevel(logging.WARNING)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    logger.addHandler(handler)

    for target_class in classes:
        bpy.utils.register_class(target_class)
    bpy.types.Scene.iodh_settings = PointerProperty(type=IODH_Settings)


def unregister() -> None:
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()

    del bpy.types.Scene.iodh_settings
    for target_class in reversed(classes):
        bpy.utils.unregister_class(target_class)
