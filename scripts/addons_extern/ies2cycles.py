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

# <pep8 compliant>

bl_info = {
    "name": "IES to Cycles",
    "author": "Lockal S.",
    "version": (0, 3),
    "blender": (2, 6, 5),
    "location": "File > Import > IES Lamp Data (.ies)",
    "description": "Import IES lamp data to cycles",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Import-Export"
}

import bpy
import os

from math import log, pow, pi
from operator import add, truediv

def clamp(x, min, max):
    if x < min:
        return min
    elif x > max:
        return max
    return x

def t2rgb(t):
    if t <= 6500:
        a = [0, -2902.1955373783176, -8257.7997278925690]
        b = [0, 1669.5803561666639, 2575.2827530017594]
        c = [1, 1.3302673723350029, 1.8993753891711275]

    else:
        a = [1745.0425298314172, 1216.6168361476490, -8257.7997278925690]
        b = [-2666.3474220535695, -2173.1012343082230, 2575.2827530017594]
        c = [0.55995389139931482, 0.70381203140554553, 1.8993753891711275]

    color = map(add, map(truediv, a, map(add, [t] * 3, b)), c)
    return [max(0, min(x, 1)) for x in color] + [1]


def simple_interp(k, x, y):
    for i in range(len(x)):
        if k == x[i]:
            return y[i]
        elif k < x[i]:
            return y[i] + (k - x[i]) * (y[i - 1] - y[i]) / (x[i - 1] - x[i])


def read_lamp_data(log, filename, multiplier, image_format, color_temperature):
    version_table = {
        'IESNA:LM-63-1986': 1986,
        'IESNA:LM-63-1991': 1991,
        'IESNA91': 1991,
        'IESNA:LM-63-1995': 1995,
        'IESNA:LM-63-2002': 2002,
    }

    name = os.path.splitext(os.path.split(filename)[1])[0]

    file = open(filename, 'rt', encoding='cp1252')
    content = file.read()
    file.close()
    s, content = content.split('\n', 1)

    if s in version_table:
        version = version_table[s]
    else:
        log({'DEBUG'}, 'IES file does not specify any version')
        version = None

    keywords = dict()

    while content and not content.startswith('TILT='):
        s, content = content.split('\n', 1)

        if s.startswith('['):
            endbracket = s.find(']')
            if endbracket != -1:
                keywords[s[1:endbracket]] = s[endbracket + 1:].strip()

    s, content = content.split('\n', 1)

    if not s.startswith('TILT'):
        log({'ERROR'}, 'TILT keyword not found, check your IES file')
        return {'CANCELED'}

    file_data = content.replace(',', ' ').split()

    lamps_num = int(file_data[0])
    #if lamps_num != 1.0:
    #    print('Only 1 lamp is supported at this moment')

    lumens_per_lamp = float(file_data[1])
    candela_mult = float(file_data[2])
    
    v_angles_num = int(file_data[3])
    h_angles_num = int(file_data[4])
    if not v_angles_num or not h_angles_num:
        log({'ERROR'}, 'TILT keyword not found, check your IES file')
        return {'CANCELED'}
    
    photometric_type = int(file_data[5])

    units_type = int(file_data[6])
    #if units_type not in [1, 2]:
    #    print('Units type should be either 1 (feet) or 2 (meters)')

    width = float(file_data[7])
    length = float(file_data[8])
    height = float(file_data[9])

    ballast_factor = float(file_data[10])

    future_use = float(file_data[11])
    if future_use != 1.0:
        print('Invalid future use field')

    input_watts = float(file_data[12])

    v_angs = [float(s) for s in file_data[13:13 + v_angles_num]]
    h_angs = [float(s) for s in file_data[13 + v_angles_num:
                                          13 + v_angles_num + h_angles_num]]

    if v_angs[0] == 0 and v_angs[-1] == 90:
        lamp_cone_type = 'TYPE90'
    elif v_angs[0] == 0 and v_angs[-1] == 180:
        lamp_cone_type = 'TYPE180'
    else:
        log({'DEBUG'}, 'Lamps with vertical angles (%d-%d) are not supported' %
                       (v_angs[0], v_angs[-1]))
        lamp_cone_type = 'TYPE180'

    # read candela values
    offset = 13 + len(v_angs) + len(h_angs)
    candela_num = len(v_angs) * len(h_angs)
    candela_values = [float(s) for s in file_data[offset:offset + candela_num]]

    if image_format == 'VCURVES':
        # reshape 1d array to 2d array
        candela_2d = list(zip(*[iter(candela_values)] * len(v_angs)))
        # scale vertical angles to [0, 1] range
        x_data = [0.5 + 0.5 * x / v_angs[-1] for x in v_angs]
        # approximate multidimentional lamp data to single dimention
        y_data = [sum(x) / len(x) for x in zip(*candela_2d)]
        y_data_max = max(y_data)
        intensity = max(500, min(y_data_max * multiplier, 5000))
        lamp_data = list(zip(x_data, [0.5 + 0.5 * y / y_data_max for y in y_data]))
        
        return add_img(name=name,
                       intensity=intensity,
                       lamp_cone_type=lamp_cone_type, 
                       image_format=image_format, 
                       color_temperature=color_temperature, 
                       lamp_data=lamp_data)
                       
    # reshape 1d array to 2d array
    candela_2d = list(zip(*[iter(candela_values)] * len(v_angs)))

    # check if angular offsets are the same
    v_d = [v_angs[i] - v_angs[i - 1] for i in range(1, len(v_angs))]
    h_d = [h_angs[i] - h_angs[i - 1] for i in range(1, len(h_angs))]

    v_same = all(abs(v_d[i] - v_d[i - 1]) < 0.001 for i in range(1, len(v_d)))
    h_same = all(abs(h_d[i] - h_d[i - 1]) < 0.001 for i in range(1, len(h_d)))

    if not v_same:
        vmin, vmax = v_angs[0], v_angs[-1]
        divisions = int((vmax - vmin) / max(1, min(v_d)))
        step = (vmax - vmin) / divisions

        # Approximating non-uniform vertical angles with step = step
        new_v_angs = [vmin + i * step for i in range(divisions + 1)]
        new_candela_2d = [[simple_interp(ang, v_angs, line)
                           for ang in new_v_angs] for line in candela_2d]
        # print(candela_2d)
        # print(new_candela_2d)
        v_angs = new_v_angs
        candela_2d = new_candela_2d

    if not h_same:
        log({'DEBUG'}, 'Different offsets for horizontal angles!')

    candela_2d = [[line[0]] + list(line) + [line[-1]] for line in candela_2d]

    # flatten 2d array to 1d
    candela_values = [y for x in candela_2d for y in x]

    maxval = max(candela_values)
    intensity = max(500, min(maxval * multiplier, 5000))

    if image_format == 'PNG':
        float_buffer=False
        filepath='//' + name + '.png'
    else:
        float_buffer=True
        filepath='//' + name + '.exr'
        
    img = bpy.data.images.new(name, len(v_angs) + 2, len(h_angs),
                              float_buffer=float_buffer)

    for i in range(len(candela_values)):
        val = candela_mult * candela_values[i] / maxval
        img.pixels[4 * i] = img.pixels[4 * i + 1] = img.pixels[4 * i + 2] = val

    bpy.ops.import_lamp.gen_exr('INVOKE_DEFAULT', 
                                image_name=img.name,
                                intensity=intensity,
                                lamp_cone_type=lamp_cone_type,
                                image_format=image_format,
                                color_temperature=color_temperature,
                                filepath=filepath)

    return {'FINISHED'}


def scale_coords(nt, sock_in, sock_out, size):
    add = nt.nodes.new('MATH')
    add.operation = 'ADD'
    nt.links.new(add.inputs[0], sock_in)
    add.inputs[1].default_value = 1.0 / (size - 2)

    mul = nt.nodes.new('MATH')
    mul.operation = 'MULTIPLY'
    nt.links.new(mul.inputs[0], add.outputs[0])
    mul.inputs[1].default_value = (size - 2.0) / size

    nt.links.new(sock_out, mul.outputs[0])

def add_h_angles(nt, x, y, out):
    na = nt.nodes.new('MATH')
    na.operation = 'MULTIPLY'
    nt.links.new(na.inputs[0], x)
    nt.links.new(na.inputs[1], x)

    nb = nt.nodes.new('MATH')
    nb.operation = 'MULTIPLY'
    nt.links.new(nb.inputs[0], y)
    nt.links.new(nb.inputs[1], y)

    nc = nt.nodes.new('MATH')
    nc.operation = 'ADD'
    nt.links.new(nc.inputs[0], na.outputs[0])
    nt.links.new(nc.inputs[1], nb.outputs[0])

    nd = nt.nodes.new('MATH')
    nd.operation = 'POWER'
    nt.links.new(nd.inputs[0], nc.outputs[0])
    nd.inputs[1].default_value = 0.5
    
    nf = nt.nodes.new('MATH')
    nf.operation = 'ADD'
    nt.links.new(nf.inputs[0], x)
    nt.links.new(nf.inputs[1], nd.outputs[0])

    ng = nt.nodes.new('MATH')
    ng.operation = 'DIVIDE'
    nt.links.new(ng.inputs[0], y)
    nt.links.new(ng.inputs[1], nf.outputs[0])

    nh = nt.nodes.new('MATH')
    nh.operation = 'ARCTANGENT'
    nt.links.new(nh.inputs[0], ng.outputs[0])
    
    nj = nt.nodes.new('MATH')
    nj.operation = 'DIVIDE'
    nt.links.new(nj.inputs[0], nh.outputs[0])
    nj.inputs[1].default_value = pi

    nk = nt.nodes.new('MATH')
    nk.operation = 'ADD'
    nt.links.new(nk.inputs[0], nj.outputs[0])
    nk.inputs[1].default_value = 0.5
    
    nt.links.new(out, nk.outputs[0])


def add_img(name, intensity, lamp_cone_type, image_format, color_temperature, filepath=None, lamp_data=None):
    if image_format != 'VCURVES':
        img = bpy.data.images[name]
        img.filepath_raw = filepath
        img.file_format = image_format
        img.save()

    nt = bpy.data.node_groups.new('Lamp ' + name, 'SHADER')
    n0 = nt.nodes.new('SEPRGB')

    ne = nt.nodes.new('MATH')
    ne.operation = 'ARCCOSINE'
    nt.links.new(ne.inputs[0], n0.outputs[2])

    ni = nt.nodes.new('MATH')
    ni.operation = 'DIVIDE'
    nt.links.new(ni.inputs[0], ne.outputs[0])

    if lamp_cone_type == 'TYPE180':
        ni.inputs[1].default_value = pi
    else:  # TYPE90:
        ni.inputs[1].default_value = pi / 2
    
    if image_format == 'VCURVES':
        nt_data = nt.nodes.new('CURVE_VEC')
        nt.links.new(nt_data.inputs[1], ni.outputs[0])
        for x, y in lamp_data[:-1]:
            pt = nt_data.mapping.curves[0].points.new(x, y)
            pt.handle_type = 'VECTOR'
            
        if lamp_cone_type == 'TYPE180':
            nt_data.mapping.curves[0].points[-1].location[1] = lamp_data[-1][1]
            nt_data.mapping.curves[0].points[-1].handle_type = 'VECTOR'
        else:
            pt = nt_data.mapping.curves[0].points.new(0.9999, lamp_data[-1][1])
            pt.handle_type = 'VECTOR'
            nt_data.mapping.curves[0].points[-1].location[1] = 0.5 # no light
            nt_data.mapping.curves[0].points[-1].handle_type = 'VECTOR'
        
        nt_data_sep = nt.nodes.new('SEPRGB')
        nt.links.new(nt_data_sep.inputs[0], nt_data.outputs[0])
        nt_data_out = nt_data_sep.outputs[0]
    else:
        n2 = nt.nodes.new('COMBRGB')
        scale_coords(nt, ni.outputs[0], n2.inputs[0], img.size[0])
        if img.size[1] > 1:
            add_h_angles(nt, n0.outputs[0], n0.outputs[1], n2.inputs[1])
        nt_data = nt.nodes.new('TEX_IMAGE')
        nt_data.image = img
        nt_data.color_space = 'NONE'
        nt.links.new(nt_data.inputs[0], n2.outputs[0])
        nt_data_out = nt_data.outputs[0]
    
    i1 = nt.inputs.new('Vector', 'VECTOR')
    i2 = nt.inputs.new('Strength', 'VALUE')
    nt.links.new(n0.inputs[0], i1)

    nmult = nt.nodes.new('MATH')
    nmult.operation = 'MULTIPLY'
    nt.links.new(nmult.inputs[0], i2)

    o1 = nt.outputs.new('Intensity', 'VALUE')
    nt.links.new(o1, nmult.outputs[0])

    if lamp_cone_type == 'TYPE180' or image_format == 'VCURVES':
        nt.links.new(nmult.inputs[1], nt_data_out)
    else:  # TYPE90
        nlt = nt.nodes.new('MATH')
        nlt.operation = 'LESS_THAN'
        nt.links.new(nlt.inputs[0], ni.outputs[0])
        nlt.inputs[1].default_value = 1.0

        nif = nt.nodes.new('MATH')
        nif.operation = 'MULTIPLY'
        nt.links.new(nif.inputs[0], nt_data_out)
        nt.links.new(nif.inputs[1], nlt.outputs[0])

        nt.links.new(nmult.inputs[1], nif.outputs[0])

    lampdata = bpy.data.lamps.new('Lamp ' + name, 'POINT')
    lampdata.use_nodes = True
    lnt = lampdata.node_tree

    #for node in lnt.nodes:
    #    print(node)

    lnt_grp = lnt.nodes.new('GROUP', group=nt)
    lnt.nodes['Emission'].inputs[0].default_value = t2rgb(color_temperature)
    lnt.links.new(lnt.nodes['Emission'].inputs[1], lnt_grp.outputs[0])
    lnt_grp.inputs[1].default_value = intensity

    lnt_map = lnt.nodes.new('MAPPING')
    lnt_map.rotation[0] = pi
    lnt.links.new(lnt_grp.inputs[0], lnt_map.outputs[0])

    lnt_geo = lnt.nodes.new('NEW_GEOMETRY')
    lnt.links.new(lnt_map.inputs[0], lnt_geo.outputs[1])

    lamp = bpy.data.objects.new('Lamp ' + name, lampdata)
    lamp.location = bpy.context.scene.cursor_location
    bpy.context.scene.objects.link(lamp)

    for ob in bpy.data.objects:
        ob.select = False

    lamp.select = True
    bpy.context.scene.objects.active = lamp

    return {'FINISHED'}


from bpy_extras.io_utils import ImportHelper, ExportHelper
from bpy.props import StringProperty, FloatProperty, EnumProperty, IntProperty
from bpy.types import Operator

format_prop_items = (
    ('OPEN_EXR', "EXR", "Save images to EXR format (up to 5 textures)"),
    ('PNG', "PNG", "Save images to PNG format")
)
format_prop_default = 'PNG'

if bpy.app.build_revision >= b'52886':
    format_prop_items += (('VCURVES', "Vector Curves", "Save lamp data in Vector Curves node"), )
    format_prop_default = 'VCURVES'


class ImportIES(Operator, ImportHelper):
    """Import IES lamp data and generate a node group for cycles"""
    bl_idname = "import_lamp.ies"
    bl_label = "Import IES to Cycles"

    filter_glob = StringProperty(default="*.ies", options={'HIDDEN'})

    lamp_strength = FloatProperty(
        name="Strength",
        description="Multiplier for lamp strength",
        default=1.0,
    )
    
    image_format = EnumProperty(
        name='Convert to',
        items=format_prop_items, 
        default=format_prop_default,
    )
    
    color_temperature = IntProperty(
        name="Color Temperature",
        description="Color temperature of lamp, 3000=soft white, 5000=cool white, 6500=daylight",
        default=6500,
    )
    
    def execute(self, context):
        return read_lamp_data(self.report, self.filepath, self.lamp_strength, 
            self.image_format, self.color_temperature)


class ExportLampEXR(Operator, ExportHelper):
    """Export IES lamp data in EXR format"""
    bl_idname = "import_lamp.gen_exr"
    bl_label = "Export lamp to image"

    image_name = StringProperty(options={'HIDDEN'})
    intensity = FloatProperty(options={'HIDDEN'})
    lamp_cone_type = EnumProperty(
        items=(('TYPE90', "0-90", "Angles from 0 to 90 degrees"),
               ('TYPE180', "0-180", "Angles from 0 to 90 degrees")),
        options={'HIDDEN'}
    )
    image_format = EnumProperty(items=format_prop_items, options={'HIDDEN'})
    color_temperature = IntProperty(options={'HIDDEN'})
    use_filter_image = True

    def execute(self, context):
        return add_img(name=self.image_name, 
                       intensity=self.intensity,
                       lamp_cone_type=self.lamp_cone_type, 
                       image_format=self.image_format, 
                       color_temperature=self.color_temperature,
                       filepath=self.filepath)

    def invoke(self, context, event):
        if self.image_format == 'PNG':
            self.filename_ext = ".png"
        else:
            self.filename_ext = ".exr"

        return ExportHelper.invoke(self, context, event)


def menu_func(self, context):
    self.layout.operator(ImportIES.bl_idname, text='IES Lamp Data (.ies)')


def register():
    bpy.utils.register_class(ImportIES)
    bpy.utils.register_class(ExportLampEXR)
    bpy.types.INFO_MT_file_import.append(menu_func)


def unregister():
    bpy.utils.unregister_class(ImportIES)
    bpy.types.INFO_MT_file_import.remove(menu_func)


if __name__ == "__main__":
    register()
    
    # test call
    # bpy.ops.import_lamp.ies('INVOKE_DEFAULT')