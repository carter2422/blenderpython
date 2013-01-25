# -*- coding: utf-8 -*-

# ***** BEGIN GPL LICENSE BLOCK *****
#
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ***** END GPL LICENCE BLOCK *****

# ------ ------
bl_info = {
    'name': 'edge_extend',
    'author': '',
    'version': (0, 1, 1),
    'blender': (2, 6, 5),
    'api': 53207,
    'location': '',
    'description': '',
    'warning': '',
    'wiki_url': '',
    'tracker_url': '',
    'category': 'Mesh' }

# ------ ------
import bpy
import bmesh
from bpy.props import BoolProperty, EnumProperty, PointerProperty, FloatProperty
from mathutils import Vector
from mathutils.geometry import intersect_line_plane

# ------ ------
def edit_mode_out():
    bpy.ops.object.mode_set(mode = 'OBJECT')

def edit_mode_in():
    bpy.ops.object.mode_set(mode = 'EDIT')

# ------ ------
class eex_p_group0(bpy.types.PropertyGroup):
    en0 = EnumProperty( items =( ('opt0', 'X', ''), ('opt1', 'Y', ''), ('opt2', 'Z', ''), ('opt3', 'Custom', '')  ), name = '', default = 'opt3' )

# ------ ------
class eex_buf():
    list_fi = []

# ------ panel 0 ------
class eex_p0(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    #bl_idname = 'eex_p0_id'
    bl_label = 'Edge Extend'
    bl_context = 'mesh_edit'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        en0 = context.scene.eex_custom_props.en0
        layout = self.layout
        row = layout.split(0.70, align = True)
        row.prop(context.scene.eex_custom_props, 'en0', expand = False, text = 'Plane')
        if en0 == 'opt3':
            row.operator('eex.op0_id', text = 'Store')
        layout.operator('eex.op1_id', text = 'Extend')

# ------ operator 0 ------ get axis
class eex_op0(bpy.types.Operator):
    bl_idname = 'eex.op0_id'
    bl_label = '....'
    bl_options = {'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return (context.active_object and context.active_object.type == 'MESH' and context.mode == 'EDIT_MESH')

    def execute(self, context):
        edit_mode_out()
        ob_act = context.active_object
        bme = bmesh.new()
        bme.from_mesh(ob_act.data)
        eex_buf.list_fi[:] = []
        for f in bme.faces:
            if f.select and f.is_valid:
                eex_buf.list_fi.append(f.index)
                f.select_set(0)
        bme.to_mesh(ob_act.data)
        edit_mode_in()
        return {'FINISHED'}

# ------ operator 1 ------
class eex_op1(bpy.types.Operator):
    bl_idname = 'eex.op1_id'
    bl_label = 'Edge Extend'
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    b = BoolProperty( name = '', default = False )
    d = FloatProperty(name = '', default = 0.0, min = -100.0, max = 100.0, step = 1, precision = 3)
    
    @classmethod
    def poll(cls, context):
        return (context.active_object and context.active_object.type == 'MESH' and context.mode == 'EDIT_MESH')

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.prop(self, 'b', text = 'Intersection point', toggle = False)
        row = box.split(0.40, align = True)
        row.label(text = 'Distance:')
        row.prop(self, 'd', text = '', slider = False)
    
    def execute(self, context):
        en0 = context.scene.eex_custom_props.en0
        d = self.d
        b = self.b

        edit_mode_out()
        ob_act = context.active_object
        bme = bmesh.new()
        bme.from_mesh(ob_act.data)

        list_0 = [ [v.index for v in e.verts] for e in bme.edges if e.select and e.is_valid ]

        pp = None
        pn = None

        # -- -- -- -- check for selected edges
        if len(list_0) == 0:
            self.report({'INFO'}, 'No edges selected unable to continue.')
            edit_mode_in()
            return {'CANCELLED'}

        if en0 == 'opt3':      # <----- custom
            if len(eex_buf.list_fi) == 0:
                self.report({'INFO'}, 'No face stored in memory unable to continue.')
                edit_mode_in()
                return {'CANCELLED'}
            else:
                f = bme.faces[eex_buf.list_fi[0]]
                f.normal_update()
                pn = (f.normal).copy()
                pp = (bme.verts[[v.index for v in f.verts][0]].co).copy() + (pn * d)

        elif en0 == 'opt0':      # <----- x
            pn = Vector((0.0, 1.0, 0.0))
            pp = Vector((0.0, 0.0, 1.0)) + (pn * d)

        elif en0 == 'opt1':      # <----- y
            pn = Vector((1.0, 0.0, 0.0))
            pp = Vector((0.0, 0.0, 1.0)) + (pn * d)

        elif en0 == 'opt2':      # <----- z
            pn = Vector((0.0, 0.0, 1.0))
            pp = Vector((1.0, 0.0, 0.0)) + (pn * d)

        # -- -- -- --
        for ek in list_0:
            lp1 = (bme.verts[ek[0]].co).copy()
            lp2 = (bme.verts[ek[1]].co).copy()
            ip = intersect_line_plane(lp1, lp2, pp, pn)      # <----- ip
            if ip == None:
                self.report({'INFO'}, 'One of selected edges is parallel to the plane no intersection possible unable to continue.')
                edit_mode_in()
                return {'CANCELLED'}
            elif ip != None:
                list_tmp = []
                if b == False:
                    vec1_l = (lp1 - ip).length
                    vec2_l = (lp2 - ip).length
                    if vec1_l < vec2_l:
                        bme.verts[ek[0]].co = ip
                    elif vec2_l < vec1_l:
                        bme.verts[ek[1]].co = ip
                elif b == True:
                   bme.verts.new(ip)
                   bme.verts.index_update()

        uns = [e.select_set(0) for e in bme.edges if e.select]
        del uns

        bme.to_mesh(ob_act.data)
        edit_mode_in()
        return {'FINISHED'}

# ------ ------
class_list = [ eex_op0, eex_op1, eex_p0, eex_p_group0 ]

# ------ register ------
def register():
    for c in class_list:
        bpy.utils.register_class(c)
    bpy.types.Scene.eex_custom_props = PointerProperty(type = eex_p_group0)

# ------ unregister ------
def unregister():
    for c in class_list:
        bpy.utils.unregister_class(c)

    if 'eex_custom_props' in bpy.context.scene:
        del bpy.context.scene['eex_custom_props']

# ------ ------
if __name__ == "__main__":
    register()