# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or modify it
#  under the terms of the GNU General Public License as published by the Free
#  Software Foundation; either version 2 of the License, or (at your option)
#  any later version.
#
#  This program is distributed in the hope that it will be useful, but WITHOUT
#  ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
#  FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
#  more details.
#
#  You should have received a copy of the GNU General Public License along with
#  this program; if not, write to the Free Software Foundation, Inc.,
#  51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {'name': 'Item Panel & Batch Naming',
           'author': 'proxe',
           'version': (0, 6),
           'blender': (2, 66, 0),
           'location': '3D View > Properties Panel',
           'warning': "Work in Progress",
          #'wiki_url': '',
          #'tracker_url': '',
           'description': "An improved item panel for the 3D View with include"
                          "d batch naming tools.",
           'category': '3D View'}

import bpy

# ##### BEGIN INFO BLOCK #####
#
#    Author: Trentin Frederick (a.k.a, proxe)
#    Contact: trentin.frederick@gmail.com, proxe.err0r@gmail.com
#    Version: 0.6
#    Naming Conventions: API friendly
#    PEP8 Compliance: Partial
#
# ##### END INFO BLOCK #####

# ##### BEGIN VERSION INFO BLOCK #####
#
#    HISTORY:
#    0.6
#    - Removed ability to populate the item panel with all selected objects,
#    objects constraints, modifiers, object's data, bones and bone constraints.
#    0.5
#    - Optimized code, followed many PEP8 guidelines.
#    - Altered batch naming functions and operators to account for all selected
#    object's constraints's and modifiers, and to account for all selected bone
#    constraints.
#    0.4
#    - Created batch naming functions and operator, added ui prop to access
#    this located next to active object input field.
#    - Added visibility and selectability options for active bone, located to
#    the left and right of the name input field for active bone.
#    0.3
#    - Added item panel property group, used to control visibiliy options of
#    selected objects/bones, by allowing them to pupulate the panel when
#    selected.
#    - Made the item panel display all selected objects, object constraints,
#    modifiers, object data, bones and bone constraints
#    - Added visibility controls for displayed constraints and modifiers
#    0.2
#    - Replaced the item panel's input field for object and active object with
#    the template_ID used in properties window for both items.
#    - Added a blank Icon for active_bone, for visual seperation.
#    0.1
#    - Created the item panel addon.
#    - Added object data naming field to item panel.
#
#    TODO:
#    0.7
#    - Restore ability to pupulate panel for the active objects/bones
#    constraints, modifiers, bone constraints.
#    - Add ability to populate the panel with active objects materials, and
#    their textures if applicable.
#    - Add ability to populate the panel with the active objects particle
#    systems.
#    0.8
#    - Account for batch naming materials, textures and particle systems in
#    the batch naming functions
#    - Include the materials, textures and particle systems in the batch
#    naming operator.
#    0.9
#    - Unregister blenders default item panel when this addon is active
#    1.0
#    - Commit addon
#
# ##### END VERSION INFO BLOCK #####

###############
## FUNCTIONS ##
###############
  # Imports
import re
import fnmatch

  # Rename
def rename(self, data_path, batch_name, find, replace, prefix, suffix,
           trim_start, trim_end):
    "docstring"
    if not self.batch_name:
        target = data_path.name[trim_start:]

    else:
        target = self.batch_name
        target = target[trim_start:]

    if trim_end > 0:
        target = target[:-trim_end]

    target = re.sub(find, replace, target)

    target = prefix + target + suffix

    if data_path in {'con', 'mod'}:
        data_path.name = target

    else:
        data_path.name = target[:]

  # Batch Rename
def batch_rename(self, context, batch_name, find, replace, prefix, suffix,
                 trim_start, trim_end, batch_objects, batch_object_constraints,
                 batch_modifiers, batch_objects_data, batch_bones,
                 batch_bone_constraints):
    "docstring"
  # Objects
    if self.batch_objects:
        for ob in context.selected_objects:
            data_path = ob
            rename(self, data_path, batch_name, find, replace, prefix, suffix,
                   trim_start, trim_end)
    else:
        pass

  # Object Constraints
    if self.batch_object_constraints:
        for ob in context.selected_objects:
            for con in ob.constraints[:]:
                data_path = con
                rename(self, data_path, batch_name, find, replace, prefix,
                       suffix, trim_start, trim_end)
    else:
        pass

  # Object Modifiers
    if self.batch_modifiers:
        for ob in context.selected_objects:
            for mod in ob.modifiers[:]:
                data_path = mod
                rename(self, data_path, batch_name, find, replace, prefix,
                       suffix, trim_start, trim_end)
    else:
        pass

  # Objects Data
    if batch_objects_data:
        for ob in context.selected_objects:
            if ob.data.users == 1:  # TODO: ob.data.users > 1
                data_path = ob.data
                rename(self, data_path, batch_name, find, replace, prefix,
                       suffix, trim_start, trim_end)
    else:
        pass

  # Bones
    if batch_bones:
        if context.selected_editable_bones:
            for bone in context.selected_editable_bones:
                data_path = bone
                rename(self, data_path, batch_name, find, replace, prefix,
                       suffix, trim_start, trim_end)
        elif context.selected_pose_bones:
            for bone in context.selected_pose_bones:
                data_path = bone
                rename(self, data_path, batch_name, find, replace, prefix,
                       suffix, trim_start, trim_end)
        else:
            pass
    else:
        pass

  # Bone Constraints
    if batch_bone_constraints:
        for bone in context.selected_pose_bones:
            for con in bone.constraints[:]:
                data_path = con
                rename(self, data_path, batch_name, find, replace, prefix,
                        suffix, trim_start, trim_end)



###############
## OPERATORS ##
###############
  # Imports
from bpy.props import *
from bpy.types import Operator

  # View 3D Batch Naming (OT)
class VIEW3D_OT_batch_naming(Operator):
    "Invoke the batch naming operator."
    bl_idname = 'view3d.batch_naming'
    bl_label = 'Batch Naming'
    bl_options = {'REGISTER', 'UNDO'}

    batch_name = StringProperty(name='Name', description="Designate a new name"
                                ", if blank, the current names are effected by"
                                " any changes to the parameters below.")

    find = StringProperty(name='Find', description="Find this text and remove "
                          "it from the names.")

    replace = StringProperty(name='Replace', description="Replace found text w"
                             "ithin the names with the text entered here.")

    prefix = StringProperty(name='Prefix', description="Designate a prefix to "
                            "use for the names.")

    suffix = StringProperty(name='Suffix', description="Designate a suffix to "
                            "use for the names")

    trim_start = IntProperty(name='Trim Start', description="Trim the beginnin"
                             "g of the names by this amount.", min=0, max=50,
                             default=0)

    trim_end = IntProperty(name='Trim End', description="Trim the ending of th"
                           "e names by this amount.", min=0, max=50, default=0)

    batch_objects = BoolProperty(name='Objects', description="Apply batch nami"
                                 "ng to the selected objects.",
                                 default=False)

    batch_object_constraints = BoolProperty(name='Object Constraints',
                                            description="Apply batch naming to"
                                            " the constraints of the selected "
                                            "objects.", default=False)

    batch_modifiers = BoolProperty(name='Modifiers', description="Apply batch "
                                   "naming to the modifiers of the selected ob"
                                   "jects.",
                                   default=False)

    batch_object_data = BoolProperty(name='Object Data', description="Apply ba"
                                     "tch naming to the object data of the sel"
                                     "ected objects.", default=False)

    batch_bones = BoolProperty(name='Bones', description="Apply batch naming t"
                               "o the selected bones.", default=False)

    batch_bone_constraints = BoolProperty(name='Bone Constraints',
                                          description="Apply batch naming to t"
                                          "he constraints of the selected bone"
                                          "s.", default=False)

    dialog_width = 200  # Controls width of batch rename operator dialogue.

    def draw(self, context):
        "docstring"
        layout = self.layout
        col = layout.column()
        props = self.properties

        row = col.row(align=True)  # Bug? icon_only doesn't appear to work.
                                   # using empty text perameter instead.
  # Target Row
        split = col.split(align=True)
        split.prop(props, 'batch_objects', text="", icon='OBJECT_DATA')
        split.prop(props, 'batch_object_constraints', text="",
                   icon='CONSTRAINT')
        split.prop(props, 'batch_modifiers', text="", icon='MODIFIER')
        split.prop(props, 'batch_object_data', text="", icon='MESH_DATA')
        if context.object.mode in {'POSE', 'EDIT_ARMATURE'}:
            split.prop(props, 'batch_bones', text="", icon='BONE_DATA')
            if context.selected_pose_bones:
                split.prop(props, 'batch_bone_constraints', text="",
                           icon='CONSTRAINT_BONE')
  # Input Fields
        col.separator()
        col.prop(props, 'batch_name')
        col.separator()
        col.prop(props, 'find', icon='VIEWZOOM')
        col.separator()
        col.prop(props, 'replace', icon='FILE_REFRESH')
        col.separator()
        col.prop(props, 'prefix', icon='LOOP_BACK')
        col.separator()
        col.prop(props, 'suffix', icon='LOOP_FORWARDS')
        col.separator()
        row = col.row()
        row.label(text="Trim Start:")
        row.prop(props, 'trim_start', text="")
        row = col.row()
        row.label(text="Trim End:")
        row.prop(props, 'trim_end', text="")

    @classmethod
    def poll(cls, context):
        "docstring"
        return context.space_data.type in 'VIEW_3D'

    def execute(self, context):
        "docstring"
        batch_rename(self, context, self.batch_name, self.find, self.replace,
                     self.prefix, self.suffix, self.trim_start, self.trim_end,
                     self.batch_objects, self.batch_object_constraints,
                     self.batch_modifiers, self.batch_object_data,
                     self.batch_bones, self.batch_bone_constraints)

        return {'FINISHED'}

    def invoke(self, context, event):
        "docstring"
        wm = context.window_manager
        wm.invoke_props_dialog(self, self.dialog_width)

        return {'RUNNING_MODAL'}

###############
## INTERFACE ##
###############
  # Imports
from bpy.types import Panel

  # Item Panel Property Group
class ItemPanel(bpy.types.PropertyGroup):
    "Property group for item panel."
  # TODO: item panel property values
    view_options = BoolProperty(name='Hide view options',
                                description="Toggle view options for this pane"
                                "l, the state that they are in is uneffected b"
                                "y this action.", default=False)

    view_objects = BoolProperty(name='View selected objects', description="Dis"
                                "play all selected objects in a list below the"
                                " active object name input field.",
                                default=False)

    view_constraints = BoolProperty(name='View selected object\'s constraints',
                                    description="Display the object constraint"
                                    "s in a list for all selected objects unde"
                                    "rneath each of the selected objects name "
                                    "input fields.", default=False)

    view_modifiers = BoolProperty(name='View selected object\'s modifiers',
                                  description="Display the object modifiers in"
                                  " a list for all selected objects underneath"
                                  " each of the selected objects name input fi"
                                  "elds.", default=False)

    view_object_data = BoolProperty(name='View selected object\'s data',
                                    description="Display the object data in a "
                                    "list below the object data name input fie"
                                    "ld for all selected objects.",
                                    default=False)

    view_bones = BoolProperty(name='View selected bones', description="Display"
                              " all selected bones in a list below the active "
                              "bone name input field.", default=False)

    view_bone_constraints = BoolProperty(name='View selected bone\'s constrain'
                                         'ts', description="Display the bone c"
                                         "onstraints for each of the selected "
                                         "pose bones.", default=False)

  # View 3D Item (PT)
class VIEW3D_PT_item_panel(Panel):
    "docstring"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = 'Item'
  # TODO: restore draw header property
    #def draw_header(self, context):
        #"docstring"
        #layout = self.layout
        #wm_props = context.window_manager.itempanel

        #layout.prop(wm_props, 'view_options', text="")

    def draw(self, context):
        "docstring"
        layout = self.layout
        col = layout.column()
        #wm_props = context.window_manager.itempanel
  # TODO: draw item panel properties
  # View options row
        #split = col.split(align=True)
        #if wm_prop.view_options:
            #split.prop(wm_props, 'view_objects', text="", icon='OBJECT_DATA')
            #split.prop(wm_props, 'view_constraints', text="",
                       #icon='CONSTRAINT')
            #split.prop(wm_props, 'view_modifiers', text="", icon='MODIFIER')
            #split.prop(wm_props, 'view_object_data', text="", icon='DATA_MESH')
            #if context.selected_bone:
                #split.prop(wm_props, 'view_bones', text="", icon='BONE_DATA')
            #if context.selected_pose_bone:
                #split.prop(wm_props, 'view_bone_constraints', text="",
                           #icon='CONSTRAINT_BONE')

  # Data name input props
        row = col.row(align=True)
        row.template_ID(context.scene.objects, 'active')
        row.operator('view3d.batch_naming', text="", icon='AUTO')

        if context.object.type in 'EMPTY':
            if context.object.empty_draw_type in 'IMAGE':
                row = col.row(align=True)
                row.template_ID(context.active_object, 'data',
                                open='image.open', unlink='image.unlink')

        else:
            row = col.row(align=True)
            row.template_ID(context.active_object, 'data')

        if context.active_bone:
            row = col.row(align=True)
            sub = row.row()
            sub.scale_x = 1.6
            if context.active_bone.hide:
                ico = 'RESTRICT_VIEW_ON'
            else:
                ico = 'RESTRICT_VIEW_OFF'
            sub.prop(context.active_bone, 'hide', text="", icon=ico)
            row.prop(context.active_bone, 'name', text="")
            if context.active_bone.hide_select:
                ico = 'RESTRICT_SELECT_ON'
            else:
                ico = 'RESTRICT_SELECT_OFF'
            row.prop(context.active_bone, 'hide_select', text="", icon=ico)

##############
## REGISTER ##
##############

def register():
    "Register"
    #wm = bpy.types.WindowManager
    bpy.utils.register_module(__name__)
    # TODO: register item panel props
    # wm.itempanel = bpy.props.PointerProperty(type=ItemPanel)

def unregister():
    "Unregister"
    wm = bpy.types.WindowManager
    bpy.utils.unregister_module(__name__)
    try:
        del wm.itempanel
    except:
        pass

if __name__ in '__main__':
    register()
