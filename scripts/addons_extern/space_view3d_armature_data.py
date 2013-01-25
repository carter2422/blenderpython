# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
    "name": "Armature Data Panel",
    "author": "Trentin Frederick (proxe)",
    "blender": (2, 6, 2),
    "location": "Tool Shelf",
    "description": "Edit Armature & Bone Data in Properties panel & align Custom Shapes.",
    "category": "Rigging"}

import bpy
from rna_prop_ui import PropertyPanel
from mathutils import Matrix

###############
## FUNCTIONS ##
###############

def object2bone():
    '''aligns custom_shape to active_bone or custom_shape_transform'''
    obj = bpy.context.active_object
    bone = bpy.context.active_bone
    ob = obj.pose.bones[bone.name].custom_shape
    tbone = obj.pose.bones[bone.name].custom_shape_transform

    if obj.pose.bones[bone.name].custom_shape_transform != None:

        mat = obj.matrix_world * tbone.matrix

    else:

        mat = obj.matrix_world * bone.matrix_local

    ob.location = mat.to_translation()
    ob.rotation_mode = 'XYZ'
    ob.rotation_euler = mat.to_euler()

    scl = mat.to_scale()
    scl_avg = (scl[0] + scl[1] + scl[2]) / 3
    ob.scale = (bone.length * scl_avg), (bone.length * scl_avg), (bone.length * scl_avg)


###############
## OPERATORS ##
###############

class shape2bone(bpy.types.Operator):
    '''Places an Object at the loc/rot/scale of the given Bone'''
    bl_idname = "posebone.custom_shape_shape2bone"
    bl_label = "Align Object to Bone"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.active_bone)

    def execute(self, context):
        use_global_undo = context.user_preferences.edit.use_global_undo
        context.user_preferences.edit.use_global_undo = False

        try:
            object2bone()

        finally:
            context.user_preferences.edit.use_global_undo = use_global_undo

        return {'FINISHED'}

###############
## INTERFACE ##
###############

class rig_data_ui(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Armature Data"
    bl_idname = "_PT_armature_data"

    @classmethod
    def poll(self, context):
        try:
            return (context.active_bone)

        except (AttributeError, KeyError, TypeError):
            return False

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True) # looks better

        obj = context.active_object
        ob = obj.data
        bone = context.active_bone

        #################
        ## OBJECT MODE ##
        #################

        if context.mode == 'OBJECT':

            row = col.row()
            row.prop(ob, "pose_position", text="")

            col = layout.column(align=True)
            col.prop(ob, "layers", text="")
            #col.prop(ob, "layers_protected", text="") # here if you need it

            row = col.row()
            row.separator()

            row = col.row()
            row.label(text="", icon="BLANK1")
            row.prop(ob, "draw_type", text="")

            row = col.row()
            row.prop(ob, "show_names", text="Names", toggle=True)
            row.prop(ob, "show_group_colors", text="Colors", toggle=True)

            row = col.row()
            row.prop(ob, "show_axes", text="Axes", toggle=True)
            row.prop(obj, "show_x_ray", text="X-Ray", toggle=True)

            row = col.row()
            row.prop(ob, "show_bone_custom_shapes", text="Shapes", toggle=True)

            row = col.row()
            row.prop(ob, "use_deform_delay", text="Delay Refresh", toggle=True)

            col = layout.column(align=True)

            row = col.row()
            row.label(text="", icon="BLANK1")
            row.prop(obj.pose.bones[bone.name], "custom_shape", text="")

            row = col.row()
            row.prop_search(obj.pose.bones[bone.name], "custom_shape_transform", obj.pose, "bones", text="")

            row = col.row()
            row.prop(bone, "show_wire", toggle=True)
            row.prop(bone, "hide", toggle=True)

            row = col.row()
            row.operator("posebone.custom_shape_shape2bone", text="Shape to Bone")

        ###############
        ## POSE MODE ##
        ###############

        elif context.mode == 'POSE':

            row = col.row()
            row.prop(ob, "pose_position", text="")

            col = layout.column(align=True)
            col.prop(ob, "layers", text="")
            #col.prop(ob, "layers_protected", text="") # here if you need it

            row = col.row()
            row.separator()

            row = col.row()
            row.label(text="", icon="BLANK1")
            row.prop(ob, "draw_type", text="")

            row = col.row()
            row.prop(ob, "show_names", text="Names", toggle=True)
            row.prop(ob, "show_group_colors", text="Colors", toggle=True)

            row = col.row()
            row.prop(ob, "show_axes", text="Axes", toggle=True)
            row.prop(obj, "show_x_ray", text="X-Ray", toggle=True)

            row = col.row()
            row.prop(ob, "show_bone_custom_shapes", text="Shapes", toggle=True)

            row = col.row()
            row.prop(ob, "use_deform_delay", text="Delay Refresh", toggle=True)

            col = layout.column(align=True)

            row = col.row()
            row.label(text="", icon="BLANK1")
            row.prop_search(bone, "parent", ob, "edit_bones", text="")

            row = col.row()
            row.prop_search(obj.pose.bones[bone.name], "bone_group", obj.pose, "bone_groups", text="")

            col = layout.column(align=True)

            if bone.use_deform == True:

                row = col.row()
                row.label(icon="BLANK1")
                row.prop(bone, "use_deform", text="Deform:", toggle=True)

                row = col.row()
                row.prop(bone, "use_envelope_multiply", text="Multiply", toggle=True)

                row = col.row()
                row.prop(bone, "envelope_weight", text="Weight")

                row = col.row()
                row.prop(bone, "bbone_segments", text="Segments")

                row = col.row()
                row.prop(bone, "bbone_in", text="Ease In")

                row = col.row()
                row.prop(bone, "bbone_out", text="Ease Out")

                row = col.row()
                row.prop(bone, "use_cyclic_offset", toggle=True)

            else:

                row = col.row()
                row.label(icon="BLANK1")
                row.prop(bone, "use_deform", text="Deform", toggle=True)

            col = layout.column(align=True)

            row = col.row()
            row.label(text="", icon="BLANK1")
            row.prop(obj.pose.bones[bone.name], "custom_shape", text="")

            row = col.row()
            row.prop_search(obj.pose.bones[bone.name], "custom_shape_transform", obj.pose, "bones", text="")

            row = col.row()
            row.prop(bone, "show_wire", toggle=True)
            row.prop(bone, "hide", toggle=True)

            row = col.row()
            row.operator("posebone.custom_shape_shape2bone", text="Shape to Bone")

        ###############
        ## EDIT MODE ##
        ###############

        else:

            col.prop(ob, "layers", text="")
            #col.prop(ob, "layers_protected", text="") # here if you need it

            row = col.row()
            row.separator()

            row = col.row()
            row.label(text="", icon="BLANK1")
            row.prop(ob, "draw_type", text="")

            row = col.row()
            row.prop(ob, "show_names", text="Names", toggle=True)
            row.prop(ob, "show_group_colors", text="Colors", toggle=True)

            row = col.row()
            row.prop(ob, "show_axes", text="Axes", toggle=True)
            row.prop(obj, "show_x_ray", text="X-Ray", toggle=True)

            col = layout.column(align=True)
            col.prop(bone, "layers", text="")

            row = col.row()
            row.separator()

            row = col.row()
            row.label(text="", icon="BLANK1")
            row.prop_search(bone, "parent", ob, "edit_bones", text="")

            row = col.row()
            row.prop(bone, "use_connect", toggle=True)

            row = col.row()
            row.prop(bone, "use_local_location", text="Loc", toggle=True)
            row.prop(bone, "use_inherit_rotation", text="Rot", toggle=True)
            row.prop(bone, "use_inherit_scale", text="Scale", toggle=True)

            col = layout.column(align=True)

            if bone.use_deform == True:

                row = col.row()
                row.label(icon="BLANK1")
                row.prop(bone, "use_deform", text="Deform:", toggle=True)

                row = col.row()
                row.prop(bone, "use_envelope_multiply", text="Multiply", toggle=True)

                row = col.row()
                row.prop(bone, "envelope_weight", text="Weight")

                row = col.row()
                row.prop(bone, "bbone_segments", text="Segments")

                row = col.row()
                row.prop(bone, "bbone_in", text="Ease In")

                row = col.row()
                row.prop(bone, "bbone_out", text="Ease Out")

                row = col.row()
                row.prop(bone, "use_cyclic_offset", toggle=True)

            else:

                row = col.row()
                row.label(icon="BLANK1")
                row.prop(bone, "use_deform", text="Deform", toggle=True)

##############
## REGISTER ##
##############

def register():
    bpy.utils.register_module(__name__)


def unregister():
    bpy.utils.unregister_module(__name__)


if __name__ == "__main__":
    register()