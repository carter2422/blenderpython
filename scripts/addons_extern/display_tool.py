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
    'name': 'display_tool',
    'author': '',
    'version': (0, 1, 7),
    'blender': (2, 6, 5),
    'api': 53207,
    'location': 'View3D > UI > Mesh Display',
    'description': '',
    'warning': '',
    'wiki_url': '',
    'tracker_url': '',
    'category': 'Mesh' }

# ------ ------
import bpy, blf, bgl
import bmesh
from bpy.props import BoolProperty, PointerProperty, FloatProperty, EnumProperty, IntProperty
from bpy_extras.view3d_utils import location_3d_to_region_2d, region_2d_to_location_3d
from mathutils.geometry import intersect_line_plane
from mathutils import Vector
from math import degrees

# ------ ------
def edit_mode_out():
    bpy.ops.object.mode_set(mode = 'OBJECT')

def edit_mode_in():
    bpy.ops.object.mode_set(mode = 'EDIT')

# ------ ------
def draw_callback_px(self, context):

    if context.mode == "EDIT_MESH":
        en0 = context.scene.dt_custom_props.en0

        font_id = 0
        font_size = context.scene.dt_custom_props.fs
    
        ob_act = context.active_object
        bme = bmesh.from_edit_mesh(ob_act.data)
        mtrx = ob_act.matrix_world
    
        list_0 = [v.index for v in bme.verts if v.select]
        if len(list_0) != 0:
            p = bme.verts[list_0[0]].co.copy()
            p_loc_2d = location_3d_to_region_2d(context.region, context.space_data.region_3d, p)
        
            q = mtrx * bme.verts[list_0[0]].co.copy()
            q_loc_2d = location_3d_to_region_2d(context.region, context.space_data.region_3d, q)
        
            # -- -- -- -- distance to adjacent vertices
            if context.scene.dt_custom_props.b0 == True:
                list_ = [[v.index for v in e.verts] for e in bme.verts[list_0[0]].link_edges]
                for ek in list_:
                    vi = [i for i in ek if i != list_0[0]][0]
                    p1 = bme.verts[vi].co.copy()
                    loc_0_3d = mtrx * ((p + p1) * 0.5)
                    loc_0_2d = location_3d_to_region_2d(context.region, context.space_data.region_3d, loc_0_3d)
                    bgl.glColor4f(1.0, 1.0, 0.0, context.scene.dt_custom_props.a)
                    blf.position(font_id, loc_0_2d[0] + 4, loc_0_2d[1] + 4, 0)
                    blf.size(font_id, font_size, context.user_preferences.system.dpi)
                    blf.draw(font_id, str(round((p - p1).length, 4)))
        
            bgl.glLineStipple(4, 0xAAAA)
            bgl.glEnable(bgl.GL_LINE_STIPPLE)
        
            # -- -- -- -- distance to axis local global
            if context.scene.dt_custom_props.b1 == True:
        
                # -- -- -- -- local
                if en0 == 'opt0':
        
                    # -- -- -- -- x axis
                    px = mtrx * Vector((0.0, p[1], p[2]))
                    px_loc_2d = location_3d_to_region_2d(context.region, context.space_data.region_3d, px)
        
                    bgl.glEnable(bgl.GL_BLEND)
                    bgl.glColor4f(1.0, 0.0, 0.0, context.scene.dt_custom_props.a)
                    bgl.glBegin(bgl.GL_LINES)
                    bgl.glVertex2f(q_loc_2d[0], q_loc_2d[1])
                    bgl.glVertex2f(px_loc_2d[0], px_loc_2d[1])
                    bgl.glEnd()
                    bgl.glDisable(bgl.GL_BLEND)
        
                    if context.scene.dt_custom_props.b2 == False:
                        lx = (q_loc_2d + px_loc_2d) * 0.5
                        bgl.glColor4f(1.0, 0.0, 0.0, context.scene.dt_custom_props.a)
                        blf.position(font_id, lx[0] + 4, lx[1] + 4, 0)
                        blf.size(font_id, font_size, context.user_preferences.system.dpi)
                        blf.draw(font_id, str(round(p[0], 4)))
        
                    # -- -- -- -- y axis
                    py = mtrx * Vector((p[0], 0.0, p[2]))
                    py_loc_2d = location_3d_to_region_2d(context.region, context.space_data.region_3d, py)
                    
                    bgl.glEnable(bgl.GL_BLEND)
                    bgl.glColor4f(0.0, 1.0, 0.0, context.scene.dt_custom_props.a)
                    bgl.glBegin(bgl.GL_LINES)
                    bgl.glVertex2f(q_loc_2d[0], q_loc_2d[1])
                    bgl.glVertex2f(py_loc_2d[0], py_loc_2d[1])
                    bgl.glEnd()
                    bgl.glDisable(bgl.GL_BLEND)
                
                    if context.scene.dt_custom_props.b2 == False:
                        ly = (q_loc_2d + py_loc_2d) * 0.5
                        bgl.glColor4f(0.0, 1.0, 0.0, context.scene.dt_custom_props.a)
                        blf.position(font_id, ly[0] + 4, ly[1] + 4, 0)
                        blf.size(font_id, font_size, context.user_preferences.system.dpi)
                        blf.draw(font_id, str(round(p[1], 4)))
        
                    # -- -- -- -- z axis
                    pz = mtrx * Vector((p[0], p[1], 0.0))
                    pz_loc_2d = location_3d_to_region_2d(context.region, context.space_data.region_3d, pz)
                
                    bgl.glEnable(bgl.GL_BLEND)
                    bgl.glColor4f(0.0, 0.0, 1.0, context.scene.dt_custom_props.a)
                    bgl.glBegin(bgl.GL_LINES)
                    bgl.glVertex2f(q_loc_2d[0], q_loc_2d[1])
                    bgl.glVertex2f(pz_loc_2d[0], pz_loc_2d[1])
                    bgl.glEnd()
                    bgl.glDisable(bgl.GL_BLEND)
            
                    if context.scene.dt_custom_props.b2 == False:
                        lz = (q_loc_2d + pz_loc_2d) * 0.5
                        bgl.glColor4f(0.0, 0.0, 1.0, context.scene.dt_custom_props.a)
                        blf.position(font_id, lz[0] + 4, lz[1] + 4, 0)
                        blf.size(font_id, font_size, context.user_preferences.system.dpi)
                        blf.draw(font_id, str(round(p[2], 4)))
        
                    # -- -- -- --
                    if context.scene.dt_custom_props.b2 == True and context.scene.dt_custom_props.b1 == True:
                        blf.size(font_id, font_size, context.user_preferences.system.dpi)
                
                        bgl.glColor4f(1.0, 0.0, 0.0, context.scene.dt_custom_props.a)
                        blf.position(font_id, q_loc_2d[0] + 4, q_loc_2d[1] + 4 + font_size + 4 + font_size + 4, 0)
                        blf.draw(font_id, 'x ' + str(round(p[0], 4)))
                
                        bgl.glColor4f(0.0, 1.0, 0.0, context.scene.dt_custom_props.a)
                        blf.position(font_id, q_loc_2d[0] + 4, q_loc_2d[1] + 4 + font_size + 4, 0)
                        blf.draw(font_id, 'y ' + str(round(p[1], 4)))
        
                        bgl.glColor4f(0.0, 0.0, 1.0, context.scene.dt_custom_props.a)
                        blf.position(font_id, q_loc_2d[0] + 4, q_loc_2d[1] + 4, 0)
                        blf.draw(font_id, 'z ' + str(round(p[2], 4)))
        
                # -- -- -- -- global
                elif en0 == 'opt1':
        
                    # -- -- -- -- x axis
                    ip_x = intersect_line_plane(q, q + (Vector((1.0, 0.0, 0.0)) * 0.1), Vector((0.0, 1.0, 0.0)), Vector((1.0, 0.0, 0.0)))
                    ip_x_loc_2d = location_3d_to_region_2d(context.region, context.space_data.region_3d, ip_x)
        
                    bgl.glEnable(bgl.GL_BLEND)
                    bgl.glColor4f(1.0, 0.0, 0.0, context.scene.dt_custom_props.a)
                    bgl.glBegin(bgl.GL_LINES)
                    bgl.glVertex2f(q_loc_2d[0], q_loc_2d[1])
                    bgl.glVertex2f(ip_x_loc_2d[0], ip_x_loc_2d[1])
                    bgl.glEnd()
                    bgl.glDisable(bgl.GL_BLEND)
        
                    if context.scene.dt_custom_props.b2 == False:
                        loc_1_2d = (q_loc_2d + ip_x_loc_2d) * 0.5
                        bgl.glColor4f(1.0, 0.0, 0.0, context.scene.dt_custom_props.a)
                        blf.position(font_id, loc_1_2d[0] + 4, loc_1_2d[1] + 4, 0)
                        blf.size(font_id, font_size, context.user_preferences.system.dpi)
                        blf.draw(font_id, str(round((q - ip_x).length, 4)))
        
                    # -- -- -- -- y axis
                    ip_y = intersect_line_plane(q, q + (Vector((0.0, 1.0, 0.0)) * 0.1), Vector((1.0, 0.0, 0.0)), Vector((0.0, 1.0, 0.0)))
                    ip_y_loc_2d = location_3d_to_region_2d(context.region, context.space_data.region_3d, ip_y)
        
                    bgl.glEnable(bgl.GL_BLEND)
                    bgl.glColor4f(0.0, 1.0, 0.0, context.scene.dt_custom_props.a)
                    bgl.glBegin(bgl.GL_LINES)
                    bgl.glVertex2f(q_loc_2d[0], q_loc_2d[1])
                    bgl.glVertex2f(ip_y_loc_2d[0], ip_y_loc_2d[1])
                    bgl.glEnd()
                    bgl.glDisable(bgl.GL_BLEND)
        
                    if context.scene.dt_custom_props.b2 == False:
                        loc_2_2d = (q_loc_2d + ip_y_loc_2d) * 0.5
                        bgl.glColor4f(0.0, 1.0, 0.0, context.scene.dt_custom_props.a)
                        blf.position(font_id, loc_2_2d[0] + 4, loc_2_2d[1] + 4, 0)
                        blf.size(font_id, font_size, context.user_preferences.system.dpi)
                        blf.draw(font_id, str(round((q - ip_y).length, 4)))
        
                    # -- -- -- -- z axis
                    ip_z = intersect_line_plane(q, q + (Vector((0.0, 0.0, 1.0)) * 0.1), Vector((1.0, 0.0, 0.0)), Vector((0.0, 0.0, 1.0)))
                    ip_z_loc_2d = location_3d_to_region_2d(context.region, context.space_data.region_3d, ip_z)
        
                    bgl.glEnable(bgl.GL_BLEND)
                    bgl.glColor4f(0.0, 0.0, 1.0, context.scene.dt_custom_props.a)
                    bgl.glBegin(bgl.GL_LINES)
                    bgl.glVertex2f(q_loc_2d[0], q_loc_2d[1])
                    bgl.glVertex2f(ip_z_loc_2d[0], ip_z_loc_2d[1])
                    bgl.glEnd()
                    bgl.glDisable(bgl.GL_BLEND)
        
                    if context.scene.dt_custom_props.b2 == False:
                        loc_3_2d = (q_loc_2d + ip_z_loc_2d) * 0.5
                        bgl.glColor4f(0.0, 0.0, 1.0, context.scene.dt_custom_props.a)
                        blf.position(font_id, loc_3_2d[0] + 4, loc_3_2d[1] + 4, 0)
                        blf.size(font_id, font_size, context.user_preferences.system.dpi)
                        blf.draw(font_id, str(round((q - ip_z).length, 4)))
        
                    # -- -- -- --
                    if context.scene.dt_custom_props.b2 == True and context.scene.dt_custom_props.b1 == True:
                        blf.size(font_id, font_size, context.user_preferences.system.dpi)
                
                        bgl.glColor4f(1.0, 0.0, 0.0, context.scene.dt_custom_props.a)
                        blf.position(font_id, q_loc_2d[0] + 4, q_loc_2d[1] + 4 + font_size + 4 + font_size + 4, 0)
                        blf.draw(font_id, 'x ' + str(round((q - ip_x).length, 4)))
                
                        bgl.glColor4f(0.0, 1.0, 0.0, context.scene.dt_custom_props.a)
                        blf.position(font_id, q_loc_2d[0] + 4, q_loc_2d[1] + 4 + font_size + 4, 0)
                        blf.draw(font_id, 'y ' + str(round((q - ip_y).length, 4)))
                
                        bgl.glColor4f(0.0, 0.0, 1.0, context.scene.dt_custom_props.a)
                        blf.position(font_id, q_loc_2d[0] + 4, q_loc_2d[1] + 4, 0)
                        blf.draw(font_id, 'z ' + str(round((q - ip_z).length, 4)))
        
            # -- -- -- -- mouse location
            if context.scene.dt_custom_props.b4 == True:
        
                rgn = context.region      # region
                rgn_3d = context.space_data.region_3d      # region 3d
        
                bgl.glEnable(bgl.GL_BLEND)
                bgl.glColor4f(1.0, 1.0, 1.0, context.scene.dt_custom_props.a)
                bgl.glBegin(bgl.GL_LINES)
                bgl.glVertex2f(0, dt_buf.y )
                bgl.glVertex2f(dt_buf.x - 15, dt_buf.y)
                bgl.glEnd()
                bgl.glDisable(bgl.GL_BLEND)
        
                bgl.glEnable(bgl.GL_BLEND)
                bgl.glColor4f(1.0, 1.0, 1.0, context.scene.dt_custom_props.a)
                bgl.glBegin(bgl.GL_LINES)
                bgl.glVertex2f(rgn.width, dt_buf.y )
                bgl.glVertex2f(dt_buf.x + 15, dt_buf.y)
                bgl.glEnd()
                bgl.glDisable(bgl.GL_BLEND)
        
                bgl.glEnable(bgl.GL_BLEND)
                bgl.glColor4f(1.0, 1.0, 1.0, context.scene.dt_custom_props.a)
                bgl.glBegin(bgl.GL_LINES)
                bgl.glVertex2f(dt_buf.x, 0 )
                bgl.glVertex2f(dt_buf.x, dt_buf.y - 15)
                bgl.glEnd()
                bgl.glDisable(bgl.GL_BLEND)
        
                bgl.glEnable(bgl.GL_BLEND)
                bgl.glColor4f(1.0, 1.0, 1.0, context.scene.dt_custom_props.a)
                bgl.glBegin(bgl.GL_LINES)
                bgl.glVertex2f(dt_buf.x, rgn.height )
                bgl.glVertex2f(dt_buf.x, dt_buf.y + 15)
                bgl.glEnd()
                bgl.glDisable(bgl.GL_BLEND)
                bgl.glDisable(bgl.GL_LINE_STIPPLE)
        
                t = str(dt_buf.x) + ', ' + str(dt_buf.y)
                lo = region_2d_to_location_3d(context.region, context.space_data.region_3d, Vector((dt_buf.x, dt_buf.y)), Vector((0.0, 0.0, 0.0)))
                t1 = '( ' + str(round(lo[0], 4)) + ', ' + str(round(lo[1], 4)) + ', ' + str(round(lo[2], 4)) + ' )'
        
                bgl.glColor4f(1.0, 1.0, 1.0, context.scene.dt_custom_props.a)
                blf.position(font_id, dt_buf.x + 15, dt_buf.y + 15, 0)
                blf.size(font_id, 14, context.user_preferences.system.dpi)
                blf.draw(font_id, t1 if context.scene.dt_custom_props.b5 == True else t)
        
            bgl.glDisable(bgl.GL_LINE_STIPPLE)
        
            # -- -- -- -- angles
            if context.scene.dt_custom_props.b3 == True:
                list_ek = [[v.index for v in e.verts] for e in bme.verts[list_0[0]].link_edges]
                n1 = len(list_ek)
                
                for j in range(n1):
                    vec1 = p - bme.verts[[ i for i in list_ek[j] if i != list_0[0] ][0]].co.copy()
                    vec2 = p - bme.verts[[ i for i in list_ek[(j + 1) % n1] if i != list_0[0]][0]].co.copy()
                    ang = vec1.angle(vec2)
        
                    a_loc_2d = location_3d_to_region_2d(context.region, context.space_data.region_3d, mtrx * (((p - (vec1.normalized() * 0.1)) + (p - (vec2.normalized() * 0.1))) * 0.5))
        
                    bgl.glColor4f(0.0, 0.757, 1.0, context.scene.dt_custom_props.a)
                    blf.position(font_id, a_loc_2d[0], a_loc_2d[1], 0)
                    blf.size(font_id, font_size, context.user_preferences.system.dpi)
                    blf.draw(font_id, str(round(ang, 4) if context.scene.dt_custom_props.b6 == True else round(degrees(ang), 2)))
        
            # -- -- -- -- tool on/off
            bgl.glColor4f(1.0, 1.0, 1.0, 1.0)
            blf.position(font_id, 150, 10, 0)
            blf.size(font_id, 20, context.user_preferences.system.dpi)
            blf.draw(font_id, 'Ruler On')

# ------ ------
class dt_p_group0(bpy.types.PropertyGroup):
    a = FloatProperty( name = '', default = 1.0, min = 0.1, max = 1.0, step = 10, precision = 1 )
    fs = IntProperty( name = '', default = 14, min = 12, max = 40, step = 1 )
    b0 = BoolProperty( name = '', default = False )
    b1 = BoolProperty( name = '', default = True )
    b2 = BoolProperty( name = '', default = False )
    b3 = BoolProperty( name = '', default = False )
    b4 = BoolProperty( name = '', default = False )
    b5 = BoolProperty( name = '', default = False )
    b6 = BoolProperty( name = '', default = False )
    en0 = EnumProperty( items =( ('opt0', 'Local', ''), ('opt1', 'Global', '') ), name = '', default = 'opt0' )

# ------ ------
class dt_buf():
    mha = 0
    text = 'Enable'
    x = 0
    y = 0

# ------ operator 0 ------
class dt_op0(bpy.types.Operator):
    bl_idname = 'dt.op0_id'
    bl_label = 'Display Tool'
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return (context.active_object and context.active_object.type == 'MESH' and context.mode == 'EDIT_MESH')

    def modal(self, context, event):
        context.area.tag_redraw()
        if event.type == 'MOUSEMOVE':
            dt_buf.x = event.mouse_region_x
            dt_buf.y = event.mouse_region_y

        if dt_buf.mha == -1:
            context.space_data.draw_handler_remove(self._handle, 'WINDOW')
            dt_buf.mha = 0
            dt_buf.text = 'Enable'
            return {"CANCELLED"}

        if context.mode != "EDIT_MESH":
            context.space_data.draw_handler_remove(self._handle, 'WINDOW')
            dt_buf.mha = 0
            dt_buf.text = 'Enable'
            return {"CANCELLED"}
        return {"PASS_THROUGH"}

    def invoke(self, context, event):
        if context.area.type == 'VIEW_3D':
            if dt_buf.mha < 1:
                dt_buf.mha = 1
                dt_buf.text = 'Disable'
                context.window_manager.modal_handler_add(self)
                self._handle = context.space_data.draw_handler_add(draw_callback_px, (self, context), 'WINDOW', 'POST_PIXEL')
                return {"RUNNING_MODAL"}
            else:
                dt_buf.mha = -1
                if 'dt_custom_props' in bpy.context.scene:
                    del bpy.context.scene['dt_custom_props']
                return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, 'View3D not found, cannot run operator')
            return {'CANCELLED'}

# ------ ------
def menu_(self, context):
    layout = self.layout
    
    layout.separator()
    col = layout.column()
    col.label(text = 'Ruler:')

    row = col.split(0.60, align = True)
    row.operator('dt.op0_id', text = dt_buf.text )

    if dt_buf.text == 'Disable':
        col.label('Ruler Font Settings:')
        row_ = col.split(0.50, align = True)
        row_.prop(context.scene.dt_custom_props, 'fs', text = 'Size', slider = True)
        row_.prop(context.scene.dt_custom_props, 'a', text = 'Alpha', slider = True)
    
        col.prop(context.scene.dt_custom_props, 'b0', text = 'Edge Length')
    
        row3 = col.row(align = False)
        row3.prop(context.scene.dt_custom_props, 'b3', text = 'Angle', toggle = False)
        if context.scene.dt_custom_props.b3 == True:
           row3.prop(context.scene.dt_custom_props, 'b6', text = 'Radians', toggle = False)
    
        col.prop(context.scene.dt_custom_props, 'b1', text = 'Distance To Axis', toggle = False)
        if context.scene.dt_custom_props.b1 == True:
            row1 = col.split(0.60, align = True)
            row1.prop(context.scene.dt_custom_props, 'en0', text = '')
            row1.prop(context.scene.dt_custom_props, 'b2', text = 'Mode', toggle = True)
    
        row2 = col.split(0.80, align = True)
        row2.prop(context.scene.dt_custom_props, 'b4', text = 'Mouse Location', toggle = False)
        if context.scene.dt_custom_props.b4 == True:
            row2.prop(context.scene.dt_custom_props, 'b5', text = 'Bu', toggle = True)

# ------ ------
class_list = [ dt_op0, dt_p_group0 ]
               
# ------ register ------
def register():
    for c in class_list:
        bpy.utils.register_class(c)
    bpy.types.Scene.dt_custom_props = PointerProperty(type = dt_p_group0)
    bpy.types.VIEW3D_PT_view3d_meshdisplay.append(menu_)

# ------ unregister ------
def unregister():
    for c in class_list:
        bpy.utils.unregister_class(c)
    if 'dt_custom_props' in bpy.context.scene:
        del bpy.context.scene['dt_custom_props']
    bpy.types.VIEW3D_PT_view3d_meshdisplay.remove(menu_)

# ------ ------
if __name__ == "__main__":
    register()