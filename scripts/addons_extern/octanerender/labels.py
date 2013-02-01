# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 3
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

# This script by Lionel Zamouth

import octanerender

# 'label':['Official Text','Unsupported Text']
labels = {
    'resolution':       ['Resolution','Override Octane default resolution'],
    'replace_project':  ['Replace',     'Overwrite project .ocs file'],
    'export_camera':    ['Export Camera','Export Scene Camera settings'],
    'lens_aperture':    ['Lens Aperture','Set Lens Aperture'],
    'focal_depth':      ['Focal Depth','Use Blender Camera Focal Depth'],
    'export_sundir':    ['Export Sun Dir','Export Sun Direction'],
    'active_light':     ['Active Light Source','Sun Light'],
    'GPU_use_list':     ['GPUs to use',''],
    'image_output':     ['Image Output','Image Output'],
    'active_camera':    ['Active Camera','Camera'],
    'camera_motion':    ['Camera Motion','Motion interpolation'],
    'interpolate_frame':['Interpolate','Frame'],
    }

# Return appropriate label
def getLabel(name):
    if name in labels:
        if octanerender.Supported:
            return labels[name][0]
        else:
            return labels[name][1]
    return '#UNDEF'
