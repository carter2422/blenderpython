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
    'name': 'edge_fillet',
    'author': '',
    'version': (0, 3, 7),
    'blender': (2, 6, 5),
    'api': 53207,
    'location': 'View3D > Tool Shelf',
    'description': '',
    'warning': '',
    'wiki_url': '',
    'tracker_url': '',
    'category': 'Mesh' }

# ------ ------
import bpy
import bmesh
from bpy.props import FloatProperty, IntProperty, BoolProperty
from mathutils import Matrix
from math import cos, pi, degrees, sin, tan, radians

# ------ ------
def edit_mode_out():
    bpy.ops.object.mode_set(mode = 'OBJECT')

def edit_mode_in():
    bpy.ops.object.mode_set(mode = 'EDIT')

def get_adj_v_(list_):
        tmp = {}
        for i in list_:
                try:             tmp[i[0]].append(i[1])
                except KeyError: tmp[i[0]] = [i[1]]
                try:             tmp[i[1]].append(i[0])
                except KeyError: tmp[i[1]] = [i[0]]
        return tmp

def a_rot(ang, rp, axis, q):
    mtrx = Matrix.Rotation(ang, 3, axis)
    tmp = q - rp
    tmp1 = mtrx * tmp
    tmp2 = tmp1 + rp
    return tmp2

# ------ ------
class f_buf():
    an = 0

# ------ ------
def f_(bme, list_0, adj, n, radius, out, flip):

    dict_0 = get_adj_v_(list_0)
    list_1 = [[dict_0[i][0], i, dict_0[i][1]] for i in dict_0 if (len(dict_0[i]) == 2)][0]

    list_del = [bme.verts[list_1[1]]]
    list_2 = []

    p = (bme.verts[list_1[1]].co).copy()
    p1 = (bme.verts[list_1[0]].co).copy()
    p2 = (bme.verts[list_1[2]].co).copy()

    vec1 = p - p1
    vec2 = p - p2

    ang = vec1.angle(vec2, any)
    f_buf.an = round(degrees(ang))

    if f_buf.an == 180 or f_buf.an == 0.0:
        pass
    else:
        opp = adj
        if radius == False:
            h = adj * (1 / cos(ang * 0.5))
            d = adj
        elif radius == True:
            h = opp / sin(ang * 0.5)
            d = opp / tan(ang * 0.5)

        p3 = p - (vec1.normalized() * d)
        p4 = p - (vec2.normalized() * d)

        no = (vec1.cross(vec2)).normalized()
        rp = a_rot(radians(90), p, (p3 - p4), (p - (no * h)))

        vec3 = rp - p3
        vec4 = rp - p4

        axis = vec1.cross(vec2)

        if out == False:
            if flip == False:
                rot_ang = vec3.angle(vec4)
            elif flip == True:
                rot_ang = vec1.angle(vec2)
        elif out == True:
            rot_ang = (2 * pi) - vec1.angle(vec2)

        for j in range(n + 1):
            if out == False:
                if flip == False:
                    tmp2 = a_rot(rot_ang * j / n, rp, axis, p4)
                elif flip == True:
                    tmp2 = a_rot(rot_ang * j / n, p, axis, p - (vec1.normalized() * opp))
            elif out == True:
                tmp2 = a_rot(rot_ang * j / n, p, axis, p - (vec2.normalized() * opp))

            bme.verts.new(tmp2)
            bme.verts.index_update()
            list_2.append(bme.verts[-1].index)

        if flip == True:
            list_1[1:2] = list_2
        else:
            list_2.reverse()
            list_1[1:2] = list_2
        list_2[:] = []

        n1 = len(list_1)
        for t in range(n1 - 1):
            bme.edges.new([bme.verts[list_1[t]], bme.verts[list_1[(t + 1) % n1]]])
            bme.edges.index_update()

    if not f_buf.an == 180 or f_buf.an == 0.0:
        bme.verts.remove(list_del[0])
        bme.verts.index_update()

# ------ panel 0 ------
class f_p0(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    #bl_idname = 'f_p0_id'                                                
    bl_label = 'Edge Fillet'
    bl_context = 'mesh_edit'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        layout.operator('f.op0_id', text = 'Fillet')

# ------ operator 0 ------
class f_op0(bpy.types.Operator):
    bl_idname = 'f.op0_id'
    bl_label = 'Edge Fillet'
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    adj = FloatProperty( name = '', default = 0.1, min = 0.00001, max = 100.0, step = 1, precision = 3 )
    n = IntProperty( name = '', default = 3, min = 1, max = 100, step = 1 )
    out = BoolProperty( name = 'Outside', default = False )
    flip = BoolProperty( name = 'Flip', default = False )
    radius = BoolProperty( name = 'Radius', default = False )
    
    @classmethod
    def poll(cls, context):
        return (context.active_object and context.active_object.type == 'MESH' and context.mode == 'EDIT_MESH')

    def draw(self, context):
        layout = self.layout
        if f_buf.an == 180 or f_buf.an == 0.0:
            box = layout.box()
            box.label('Info:')
            box.label('Angle equal to 0 or 180,')
            box.label('unable to fillet.')
        else:
            box = layout.box()
            box.prop(self, 'radius')
            row = box.split(0.35, align = True)

            if self.radius == True:
                row.label('Radius:')
            elif self.radius == False:
                row.label('Distance:')
            row.prop(self, 'adj')
            row1 = box.split(0.55, align = True)
            row1.label('Number of sides:')
            row1.prop(self, 'n', slider = True)

            if self.n > 1:
                row2 = box.split(0.50, align = True)
                row2.prop(self, 'out')
                if self.out == False:
                    row2.prop(self, 'flip')

    def execute(self, context):
        adj = self.adj
        n = self.n
        out = self.out
        flip = self.flip
        radius = self.radius

        edit_mode_out()
        ob_act = context.active_object
        bme = bmesh.new()
        bme.from_mesh(ob_act.data)

        list_0 = [[v.index for v in e.verts] for e in bme.edges if e.select and e.is_valid]

        if len(list_0) != 2:
            self.report({'INFO'}, 'Two adjacent edges must be selected.')
            edit_mode_in()
            return {'CANCELLED'}
        else:
            if out == True:
                flip = False
            f_(bme, list_0, adj, n, radius, out, flip)

        bme.to_mesh(ob_act.data)
        edit_mode_in()
        bpy.ops.mesh.select_all(action = 'DESELECT')
        return {'FINISHED'}

# ------ ------
class_list = [ f_op0, f_p0 ]

# ------ register ------
def register():
    for c in class_list:
        bpy.utils.register_class(c)

# ------ unregister ------
def unregister():
    for c in class_list:
        bpy.utils.unregister_class(c)

# ------ ------
if __name__ == "__main__":
    register()