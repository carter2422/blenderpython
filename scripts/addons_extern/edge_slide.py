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
    'name': 'edge_slide',
    'author': '',
    'version': (0, 2, 0),
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
from bpy.props import FloatProperty, BoolProperty
from math import sin, cos, pi

# ------ ------
def edit_mode_out():
    bpy.ops.object.mode_set(mode = 'OBJECT')

def edit_mode_in():
    bpy.ops.object.mode_set(mode = 'EDIT')

def get_k0n_(ek, f_edge_keys):
    tmp = [i for i in f_edge_keys if ek[0] in i]
    if ek in tmp:
        tmp.remove(ek)
    tmp_ek = list(tmp[0])
    if ek[0] in tmp_ek:
        tmp_ek.remove(ek[0])
    return tmp_ek[0]

def get_k1n_(ek, f_edge_keys):
    tmp = [i for i in f_edge_keys if ek[1] in i]
    if ek in tmp:
        tmp.remove(ek)
    tmp_ek = list(tmp[0])
    if ek[1] in tmp_ek:
        tmp_ek.remove(ek[1])
    return tmp_ek[0]

def get_d1_(ev0_ang, h_pi, d):
    d1 = 0
    if ev0_ang == h_pi:
        d1 = d
    elif ev0_ang != h_pi:
        if ev0_ang < h_pi:
            d1 = d / sin(ev0_ang)
        elif ev0_ang > h_pi:
            d1 = d / cos(ev0_ang - h_pi)
    return d1

def get_d2_(ev1_ang, h_pi, d):
    d2 = 0
    if ev1_ang == h_pi:
        d2 = d
    elif ev1_ang != h_pi:
        if ev1_ang < h_pi:
            d2 = d / sin(ev1_ang)
        elif ev1_ang > h_pi:
            d2 = d / cos(ev1_ang - h_pi)
    return d2

# ------ ------
def f_(bme, e, list_1, n_, d, prc, b0, b1):

    ev0_tmp = None
    ev1_tmp = None

    if n_ == 1:
        f = bme.faces[list_1[0]]
        ek = tuple([v.index for v in e.verts])
        f_edge_keys = [ tuple([v.index for v in e.verts]) for e in f.edges ]

        ev0 = (bme.verts[ek[0]].co).copy()
        ev1 = (bme.verts[ek[1]].co).copy()

        ev0n0 = (bme.verts[get_k0n_(ek, f_edge_keys)].co).copy()
        ev1n0 = (bme.verts[get_k1n_(ek, f_edge_keys)].co).copy()

        vec0 = (ev0n0 - ev0)
        vec1 = (ev1n0 - ev1)

        ev0_ang = round((vec0.angle((ev1 - ev0), any)), 6)
        ev1_ang = round((vec1.angle((ev0 - ev1), any)), 6)

        d1 = get_d1_(ev0_ang, (round(pi * 0.5, 6)), d)
        d2 = get_d2_(ev1_ang, (round(pi * 0.5, 6)), d)

        if b0 == True:
            ev0_tmp = ev0 + (vec0 * (prc / 100))
            ev1_tmp = ev1 + (vec1 * (prc / 100))
        elif b0 == False:
            ev0_tmp = ev0 + (vec0.normalized() * d1)
            ev1_tmp = ev1 + (vec1.normalized() * d2)

    elif n_ == 2:
        if b0 == True:
            val = prc
        elif b0 == False:
            val = d

        ek = tuple([v.index for v in e.verts])
        ev0 = (bme.verts[ek[0]].co).copy()
        ev1 = (bme.verts[ek[1]].co).copy()

        f1 = bme.faces[list_1[0]]
        f1_edge_keys = [ tuple([v.index for v in e.verts]) for e in f1.edges ]

        f2 = bme.faces[list_1[1]]
        f2_edge_keys = [ tuple([v.index for v in e.verts]) for e in f2.edges ]

        if val > 0:
            ev0n0 = (bme.verts[get_k0n_(ek, f1_edge_keys)].co).copy()
            ev1n0 = (bme.verts[get_k1n_(ek, f1_edge_keys)].co).copy()
            vec0 = (ev0n0 - ev0)
            vec1 = (ev1n0 - ev1)
            ev0_ang = round((vec0.angle((ev1 - ev0), any)), 6)
            ev1_ang = round((vec1.angle((ev0 - ev1), any)), 6)
            d1 = get_d1_(ev0_ang, (round(pi * 0.5, 6)), d)
            d2 = get_d2_(ev1_ang, (round(pi * 0.5, 6)), d)
            if b0 == True:
                ev0_tmp = ev0 + (vec0 * (val / 100))
                ev1_tmp = ev1 + (vec1 * (val / 100))
            elif b0 == False:
                ev0_tmp = ev0 + (vec0.normalized() * d1)
                ev1_tmp = ev1 + (vec1.normalized() * d2)

        elif val < 0:
            ev0n1 = (bme.verts[get_k0n_(ek, f2_edge_keys)].co).copy()
            ev1n1 = (bme.verts[get_k1n_(ek, f2_edge_keys)].co).copy()
            vec0 = (ev0n1 - ev0)
            vec1 = (ev1n1 - ev1)
            ev0_ang = round((vec0.angle((ev1 - ev0), any)), 6)
            ev1_ang = round((vec1.angle((ev0 - ev1), any)), 6)
            d1 = get_d1_(ev0_ang, (round(pi * 0.5, 6)), d)
            d2 = get_d2_(ev1_ang, (round(pi * 0.5, 6)), d)
            if b0 == True:
                ev0_tmp = ev0 - (vec0 * (val / 100))
                ev1_tmp = ev1 - (vec1 * (val / 100))
            elif b0 == False:
                ev0_tmp = ev0 - (vec0.normalized() * d1)
                ev1_tmp = ev1 - (vec1.normalized() * d2)

    else:
        pass

    # -- -- -- --
    if  ev0_tmp == None:
        pass
    else:
        if b1 == True:
            tmp = []
            bme.verts.new(ev0_tmp)
            bme.verts.index_update()
            tmp.append(bme.verts[-1])

            bme.verts.new(ev1_tmp)
            bme.verts.index_update()
            tmp.append(bme.verts[-1])

            bme.edges.new(tmp)
            bme.edges.index_update()

        elif b1 == False:
            bme.verts[ek[0]].co = ev0_tmp
            bme.verts[ek[1]].co = ev1_tmp

# ------ panel 0 ------
class es_p0(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    #bl_idname = 'es_p0_id'
    bl_label = 'Edge Slide'
    bl_context = 'mesh_edit'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        layout.operator('es.op0_id', text = 'Slide')

# ------ operator 0 ------
class es_op0(bpy.types.Operator):
    bl_idname = 'es.op0_id'
    bl_label = 'Edge Slide'
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    d = FloatProperty( name = '', default = 0.1, min = -100.0, max = 100.0, step = 1, precision = 3 )      # distance
    prc = FloatProperty( name = '', default = 10.0, min = -100.0, max = 100.0, step = 1000, precision = 3 )      # percent
    b0 = BoolProperty( name = 'Percent', default = False )
    b1 = BoolProperty( name = 'New edge.', default = True )

    @classmethod
    def poll(cls, context):
        return (context.active_object and context.active_object.type == 'MESH' and context.mode == 'EDIT_MESH')

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        row = box.row(align = False)
        row.prop(self, 'b1')
        row.prop(self, 'b0')
        
        if self.b0 == True:
            row1 = box.split(0.60, align = True)
            row1.label(text = 'Percent of edge length:')
            row1.prop(self, 'prc', slider = True)
        else:
            row1 = box.split(0.30, align = True)
            row1.label(text = 'Distance:')
            row1.prop(self, 'd', slider = False)

    def execute(self, context):
        d = self.d
        prc = self.prc
        b0 = self.b0
        b1 = self.b1

        edit_mode_out()
        ob_act = context.active_object
        bme = bmesh.new()
        bme.from_mesh(ob_act.data)
        
        list_0 = [ e.index for e in bme.edges if e.select and e.is_valid ]

        if len(list_0) == 0:
            self.report({'INFO'}, 'One edge must be selected.')
            edit_mode_in()
            return {'CANCELLED'}
        else:
            for ei in list_0:
                e = bme.edges[ei]
                list_1 = [f.index for f in e.link_faces]      # list of faces (face indices) connected to this edge
                n_ = len(list_1)
                f_(bme, e, list_1, n_, d, prc, b0, b1)
        
        bme.to_mesh(ob_act.data)
        edit_mode_in()
        return {'FINISHED'}

# ------ ------
class_list = [ es_op0, es_p0 ]

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