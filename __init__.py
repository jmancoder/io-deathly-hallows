import bpy
from bpy.props import StringProperty, PointerProperty
from bpy_extras.io_utils import ImportHelper


class IODH_Settings(bpy.types.PropertyGroup):
    manifest_path: StringProperty(
        name="Manifest Path",
        description="Path to the manifest.json file in the extracted .bin.gz archive",
        subtype="FILE_PATH",
    )


class IODH_OT_import_msh(bpy.types.Operator, ImportHelper):
    bl_idname = "import_scene.iodh_msh"
    bl_label = "Import MSH"
    filename_ext = ""

    filter_glob: StringProperty(
        default="*",
        options={"HIDDEN"},
        maxlen=255,
    )

    def execute(self, context):
        with open(self.filepath, "rb") as f:
            magic = f.read(4)
        if magic != b"THNG":
            self.report({"ERROR"}, "Not a valid file")
            return {"CANCELLED"}
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
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.Scene.iodh_settings = PointerProperty(type=IODH_Settings)


def unregister():
    del bpy.types.Scene.iodh_settings
    for c in reversed(classes):
        bpy.utils.unregister_class(c)
