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

bl_info = {
           'name': 'Item Panel & Batch Naming',
           'author': 'proxe',
           'version': (0, 7, 0),
           'blender': (2, 66, 0),
           'location': '3D View > Properties Panel',
           'warning': 'Work in Progress',
           #'wiki_url': '',
           #'tracker_url': '',
           'description': "An improved item panel for the 3D View with include"
                          "d batch naming tools.",
           'category': '3D View'
          }

import bpy

# ##### BEGIN INFO BLOCK #####
#
#    Author: Trentin Frederick (a.k.a, proxe)
#    Contact: trentin.frederick@gmail.com, proxe.err0r@gmail.com
#    Version: 0.7.0
#
# ##### END INFO BLOCK #####

# ##### BEGIN VERSION BLOCK #####
#
#    0.7
#    - Restored ability to pupulate panel for the active objects/bones
#    constraints, modifiers, bone constraints.
#    - Create target menu allowing user to rename specific types of objects,
#    constraints, modifiers, object data and bone constraints.
#    0.6
#    - Removed ability to populate the item panel with all selected objects,
#    objects constraints, modifiers, object's data, bones and bone constraints.
#    - Removed visibility and selectability options from the left and right of
#    active bone name input field in favor of the default item panel's format.
#    - Code cleanup
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
#    0.8
#    - Add ability to populate the panel with active objects materials, and
#    their textures if applicable.
#    - Add ability to populate the panel with the active objects particle
#    systems.
#    - Account for batch naming materials, textures and particle systems in
#    the batch naming functions
#    - Include the materials, textures and particle systems in the batch
#    naming operator.
#    0.9
#    - See if there is something I can do to make the menus for types a bit
#    more easily readable, i.e. recreate the same menu that operator_menu_enum
#    of object.add_modifier would create.
#    - If everything is working well, remove some of the props default values
#    so that the value is stored for the next time it is called.
#    - Unregister blenders default item panel when this addon is active
#    1.0
#    - Add ability to display vertex groups and shapekeys in item panel, vertex
#    groups should have a quick select and deselect option, shapekeys ideally
#    would have the slider available but just where it should be placed is
#    unclear.
#    - Create batch naming functionality for vertex groups & shapekeys, ideally
#    this would be accessed from within a menu rather then as part of the
#    'target row', may as whell include options for uv maps and vertex colors.
#    - Actually fill out the docstrings.
#    - Commit addon
#
# ##### END VERSION BLOCK #####

# PEP8 Compliant

###############
## FUNCTIONS ##
###############
  # Imports
import re


  # Rename
def rename(self, data_path, batch_name, find, replace, prefix, suffix,
           trim_start, trim_end):
    """docstring"""
    if not batch_name:
        target = data_path.name[trim_start:]
    else:
        target = batch_name
        target = target[trim_start:]
    if trim_end > 0:
        target = target[:-trim_end]
    target = re.sub(find, replace, target)  # re will send an error if using
                                            # toolshelf in the find field while
                                            # typing out the expression.
    target = prefix + target + suffix
    if data_path in {'con', 'mod'}:
        data_path.name = target
    else:
        data_path.name = target[:]


  # Batch Rename
def batch_rename(self, context, batch_name, find, replace, prefix, suffix,
                 trim_start, trim_end, batch_objects, batch_object_constraints,
                 batch_modifiers, batch_objects_data, batch_bones,
                 batch_bone_constraints, object_type, constraint_type,
                 modifier_type):
    """docstring"""
  # Objects
    if batch_objects:
        for object in context.selected_objects:
            if object_type in 'ALL':
                data_path = object
                rename(self, data_path, batch_name, find, replace, prefix,
                       suffix, trim_start, trim_end)
            else:
                if object_type in object.type:
                    data_path = object
                    rename(self, data_path, batch_name, find, replace, prefix,
                           suffix, trim_start, trim_end)
                else:
                    pass
    else:
        pass
  # Object Constraints
    if batch_object_constraints:
        for object in context.selected_objects:
            for constraint in object.constraints[:]:
                if constraint_type in 'ALL':
                    data_path = constraint
                    rename(self, data_path, batch_name, find, replace, prefix,
                           suffix, trim_start, trim_end)
                else:
                    if constraint_type in constraint.type:
                        data_path = constraint
                        rename(self, data_path, batch_name, find, replace,
                               prefix, suffix, trim_start, trim_end)
                    else:
                        pass
    else:
        pass
  # Object Modifiers
    if batch_modifiers:
        for object in context.selected_objects:
            for modifier in object.modifiers[:]:
                if modifier_type in 'ALL':
                    data_path = modifier
                    rename(self, data_path, batch_name, find, replace, prefix,
                           suffix, trim_start, trim_end)
                else:
                    if modifier_type in modifier.type:
                        data_path = modifier
                        rename(self, data_path, batch_name, find, replace,
                               prefix, suffix, trim_start, trim_end)
                    else:
                        pass
    else:
        pass
  # Objects Data
    if batch_objects_data:
        for object in context.selected_objects:
            if object_type in 'ALL':
                data_path = object.data
                rename(self, data_path, batch_name, find, replace, prefix,
                       suffix, trim_start, trim_end)
            else:
                if object_type in object.type:
                    data_path = object.data
                    rename(self, data_path, batch_name, find, replace,
                           prefix, suffix, trim_start, trim_end)
                else:
                    pass
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
            for constraint in bone.constraints[:]:
                if constraint_type in 'ALL':
                    data_path = constraint
                    rename(self, data_path, batch_name, find, replace, prefix,
                           suffix, trim_start, trim_end)
                else:
                    if constraint_type in contraint.type:
                        data_path = constraint
                        rename(self, data_path, batch_name, find, replace,
                               prefix, suffix, trim_start, trim_end)
                    else:
                        pass
    else:
        pass

###############
## OPERATORS ##
###############
  # Imports
from bpy.props import *
from bpy.types import Operator


  # View 3D Batch Naming (OT)
class VIEW3D_OT_batch_naming(Operator):
    """Invoke the batch naming operator."""
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
                             "g of the names by this amount.",
                             min=0, max=50, default=0)
    trim_end = IntProperty(name='Trim End', description="Trim the ending of th"
                           "e names by this amount.",
                           min=0, max=50, default=0)
    batch_objects = BoolProperty(name='Objects', description="Apply batch nami"
                                 "ng to the selected objects.",
                                 default=False)
    batch_object_constraints = BoolProperty(name='Object Constraints',
                                            description="Apply batch naming to"
                                            " the constraints of the selected "
                                            "objects.",
                                            default=False)
    batch_modifiers = BoolProperty(name='Modifiers', description="Apply batch "
                                   "naming to the modifiers of the selected ob"
                                   "jects.",
                                   default=False)
    batch_objects_data = BoolProperty(name='Object Data', description="Apply b"
                                      "atch naming to the object data of the s"
                                      "elected objects.",
                                      default=False)
    batch_bones = BoolProperty(name='Bones', description="Apply batch naming t"
                               "o the selected bones.",
                               default=False)
    batch_bone_constraints = BoolProperty(name='Bone Constraints',
                                          description="Apply batch naming to t"
                                          "he constraints of the selected bone"
                                          "s.",
                                          default=False)
    object_type = EnumProperty(name='Type', description="The type of object th"
                               "at the batch naming operations will be perform"
                               "ed on.",
                               items=[
                                     ('LAMP', 'Lamp', ""),
                                     ('CAMERA', 'Camera', ""),
                                     ('SPEAKER', 'Speaker', ""),
                                     ('EMPTY', 'Empty', ""),
                                     ('LATTICE', 'Lattice', ""),
                                     ('ARMATURE', 'Armature', ""),
                                     ('FONT', 'Font', ""),
                                     ('META', 'Meta', ""),
                                     ('SURFACE', 'Surface', ""),
                                     ('CURVE', 'Curve', ""),
                                     ('MESH', 'Mesh', ""),
                                     ('ALL', 'All Objects', ""),
                                     ], default='ALL')
    constraint_type = EnumProperty(name='Type', description="The type of const"
                                   "raint that the batch naming operations wil"
                                   "l be performed on.",
                                   items=[
                                  ('SHRINKWRAP', 'Shrinkwrap', ""),
                                  ('SCRIPT', 'Script', ""),
                                  ('RIGID_BODY_JOINT', 'Rigid Body Joint', ""),
                                  ('PIVOT', 'Pivot', ""),
                                  ('FOLLOW_PATH', 'Follow Path', ""),
                                  ('FLOOR', 'Floor', ""),
                                  ('CHILD_OF', 'ChildOf', ""),
                                  ('ACTION', 'Action', ""),
                                  ('TRACK_TO', 'TrackTo', ""),
                                  ('STRETCH_TO', 'Stretch To', ""),
                                  ('SPLINE_IK', 'Spline IK', ""),
                                  ('LOCKED_TRACK', 'Locked Track', ""),
                                  ('IK', 'IK', ""),
                                  ('DAMPED_TRACK', 'Damped Track', ""),
                                  ('CLAMP_TO', 'Clamp To', ""),
                                  ('TRANSFORM', 'Transformation', ""),
                                  ('MAINTAIN_VOLUME', 'Maintain Volume', ""),
                                  ('LIMIT_SCALE', 'Limit Scale', ""),
                                  ('LIMIT_ROTATION', 'Limit Rotation', ""),
                                  ('LIMIT_LOCATION', 'Limit Location', ""),
                                  ('LIMIT_DISTANCE', 'Limit Distance', ""),
                                  ('COPY_TRANSFORMS', 'Copy Transforms', ""),
                                  ('COPY_SCALE', 'Copy Scale', ""),
                                  ('COPY_ROTATION', 'Copy Rotation', ""),
                                  ('COPY_LOCATION', 'Copy Location', ""),
                                  ('FOLLOW_TRACK', 'Follow Track', ""),
                                  ('OBJECT_SOLVER', 'Object Solver', ""),
                                  ('CAMERA_SOLVER', 'Camera Solver', ""),
                                  ('ALL', 'All Constraints', ""),
                                   ], default='ALL')
    modifier_type = EnumProperty(name='Type', description="The type of modifie"
                                 "r that the batch naming operations will be p"
                                 "erformed on.",
                                 items=[
                    ('SOFT_BODY', 'Soft Body', ""),
                    ('SMOKE', 'Smoke', ""),
                    ('PARTICLE_SYSTEM', 'Particle System', ""),
                    ('PARTICLE_INSTANCE', 'Particle Instance', ""),
                    ('OCEAN', 'Ocean', ""),
                    ('FLUID_SIMULATION', 'Fluid Simulation', ""),
                    ('EXPLODE', 'Explode', ""),
                    ('DYNAMIC_PAINT', 'Dynamic Paint', ""),
                    ('COLLISION', 'Collision', ""),
                    ('CLOTH', 'Cloth', ""),
                    ('WAVE', 'Wave', ""),
                    ('WARP', 'Warp', ""),
                    ('SMOOTH', 'Smooth', ""),
                    ('SIMPLE_DEFORM', 'Simple Deform', ""),
                    ('SHRINKWRAP', 'Shrinkwrap', ""),
                    ('MESH_DEFORM', 'Mesh Deform', ""),
                    ('LATTICE', 'Lattice', ""),
                    ('LAPLACIANSMOOTH', 'Laplacian Smooth', ""),
                    ('HOOK', 'Hook', ""),
                    ('DISPLACE', 'Displace', ""),
                    ('CURVE', 'Curve', ""),
                    ('CAST', 'Cast', ""),
                    ('ARMATURE', 'Armature', ""),
                    ('TRIANGULATE', 'Triangulate', ""),
                    ('SUBSURF', 'Subdivision Surface', ""),
                    ('SOLIDIFY', 'Solidify', ""),
                    ('SKIN', 'Skin', ""),
                    ('SCREW', 'Screw', ""),
                    ('REMESH', 'Remesh', ""),
                    ('MULTIRES', 'Multiresolution', ""),
                    ('MIRROR', 'Mirror', ""),
                    ('MASK', 'Mask', ""),
                    ('EDGE_SPLIT', 'Edge Split', ""),
                    ('DECIMATE', 'Decimate', ""),
                    ('BUILD', 'Build', ""),
                    ('BOOLEAN', 'Boolean', ""),
                    ('BEVEL', 'Bevel', ""),
                    ('ARRAY', 'Array', ""),
                    ('VERTEX_WEIGHT_PROXIMITY', 'Vertex Weight Proximity', ""),
                    ('VERTEX_WEIGHT_EDIT', 'Vertex Weight Edit', ""),
                    ('UV_WARP', 'UV Warp', ""),
                    ('UV_PROJECT', 'UV Project', ""),
                    ('MESH_CACHE', 'Mesh Cache', ""),
                    ('ALL', 'All Modifiers', ""),
                    ], default='ALL')

    @classmethod
    def poll(cls, context):
        """docstring"""
        return context.space_data.type in 'VIEW_3D'

    def draw(self, context):
        """docstring"""
        layout = self.layout
        col = layout.column()
        props = self.properties

        row = col.row(align=True)  # Bug? icon_only doesn't appear to work.
                                   # using empty text parameter instead.
  # Target Row
        split = col.split(align=True)
        split.prop(props, 'batch_objects', text="", icon='OBJECT_DATA')
        split.prop(props, 'batch_object_constraints', text="",
                   icon='CONSTRAINT')
        split.prop(props, 'batch_modifiers', text="", icon='MODIFIER')
        split.prop(props, 'batch_objects_data', text="", icon='MESH_DATA')
        if context.object.mode in {'POSE', 'EDIT_ARMATURE'}:
            split.prop(props, 'batch_bones', text="", icon='BONE_DATA')
            if context.selected_pose_bones:
                split.prop(props, 'batch_bone_constraints', text="",
                           icon='CONSTRAINT_BONE')
            else:
                pass
        else:
            pass
  # Target Types
        col.prop(props, 'object_type', text="", icon='OBJECT_DATA')
        col.prop(props, 'constraint_type', text="", icon='CONSTRAINT')
        col.prop(props, 'modifier_type', text="", icon='MODIFIER')
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

    def execute(self, context):
        """docstring"""
        batch_rename(self, context, self.batch_name, self.find, self.replace,
                     self.prefix, self.suffix, self.trim_start, self.trim_end,
                     self.batch_objects, self.batch_object_constraints,
                     self.batch_modifiers, self.batch_objects_data,
                     self.batch_bones, self.batch_bone_constraints,
                     self.object_type, self.constraint_type,
                     self.modifier_type)
        return {'FINISHED'}

    def invoke(self, context, event):
        """docstring"""
        wm = context.window_manager
        wm.invoke_props_dialog(self, width=225)

        return {'RUNNING_MODAL'}

###############
## INTERFACE ##
###############
  # Imports
from bpy.types import Panel, PropertyGroup


  # Item Panel Property Group
class Item(PropertyGroup):
    """Property group for item panel."""
  # TODO: item panel property values
    view_options = BoolProperty(name='Show/hide view options',
                                description="Toggle view options for this pane"
                                "l, the state that they are in is uneffected b"
                                "y this action.", default=False)
    view_constraints = BoolProperty(name='View object constraints',
                                    description="Display the object constraint"
                                    "s of the active object.", default=False)
    view_modifiers = BoolProperty(name='View object modifiers', description="D"
                                  "isplay the object modifiers of the active o"
                                  "bject.", default=False)
    view_bone_constraints = BoolProperty(name='View bone constraints',
                                         description="Display the bone constra"
                                         "ints of the active pose bone.",
                                         default=False)


  # View 3D Item (PT)
class VIEW3D_PT_item(Panel):
    """docstring"""
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = 'Item'

    def draw_header(self, context):
        """docstring"""
        layout = self.layout
        wm_props = context.window_manager.item

        layout.prop(wm_props, 'view_options', text="")

    def draw(self, context):
        """docstring"""
        layout = self.layout
        col = layout.column()
        wm_props = context.window_manager.item
  # View options row
        split = col.split(align=True)
        if wm_props.view_options:
            split.prop(wm_props, 'view_constraints', text="",
                       icon='CONSTRAINT')
            split.prop(wm_props, 'view_modifiers', text="", icon='MODIFIER')
            if context.object.mode in 'POSE':
                split.prop(wm_props, 'view_bone_constraints', text="",
                           icon='CONSTRAINT_BONE')
            else:
                pass
        else:
            pass
  # Data block list
        row = col.row(align=True)
        row.template_ID(context.scene.objects, 'active')
        row.operator('view3d.batch_naming', text="", icon='AUTO')
        if wm_props.view_constraints:
            for con in context.active_object.constraints:
                row = col.row(align=True)
                sub = row.row()
                sub.scale_x = 1.6
                sub.label(text="", icon='DOT')
                if con.mute:
                    ico = 'RESTRICT_VIEW_ON'
                else:
                    ico = 'RESTRICT_VIEW_OFF'
                row.prop(con, 'mute', text="", icon=ico)
                row.prop(con, 'name', text="")
        else:
            pass
        if wm_props.view_modifiers:
            for mod in context.active_object.modifiers:
                row = col.row(align=True)
                sub = row.row()
                sub.scale_x = 1.6
                sub.label(text="", icon='DOT')
                if mod.show_viewport:
                    ico = 'RESTRICT_VIEW_OFF'
                else:
                    ico = 'RESTRICT_VIEW_ON'
                row.prop(mod, 'show_viewport', text="", icon=ico)
                row.prop(mod, 'name', text="")
        else:
            pass
        if context.object.type in 'EMPTY':
            if context.object.empty_draw_type in 'IMAGE':
                row = col.row(align=True)
                row.template_ID(context.active_object, 'data',
                                open='image.open', unlink='image.unlink')
            else:
                pass
        else:
            row = col.row(align=True)
            row.template_ID(context.active_object, 'data')
        if context.active_bone:
            row = col.row(align=True)
            sub = row.row()
            sub.scale_x = 1.6
            sub.label(text="", icon='BONE_DATA')
            row.prop(context.active_bone, 'name', text="")
            if context.object.mode in 'POSE':
                if wm_props.view_bone_constraints:
                    for con in context.active_pose_bone.constraints:
                        row = col.row(align=True)
                        sub = row.row()
                        sub.scale_x = 1.6
                        sub.label(text="", icon='DOT')
                        if con.mute:
                            ico = 'RESTRICT_VIEW_ON'
                        else:
                            ico = 'RESTRICT_VIEW_OFF'
                        row.prop(con, 'mute', text="", icon=ico)
                        row.prop(con, 'name', text="")
                else:
                    pass
            else:
                pass
        else:
            pass

##############
## REGISTER ##
##############


def register():
    """Register"""
    wm = bpy.types.WindowManager
    bpy.utils.register_module(__name__)
    wm.item = bpy.props.PointerProperty(type=Item)
    bpy.context.window_manager.item.name = 'Item Panel Properties'


def unregister():
    """Unregister"""
    wm = bpy.types.WindowManager
    bpy.utils.unregister_module(__name__)
    try:
        del wm.item
    except:
        pass

if __name__ in '__main__':
    register()
