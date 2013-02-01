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

from bl_ui import properties_data_mesh
for member in dir(properties_data_mesh):
    subclass = getattr(properties_data_mesh, member)
    try:
        subclass.COMPAT_ENGINES.add('OCT_RENDER')
    except:
        pass
del properties_data_mesh

from bl_ui import properties_scene
for member in dir(properties_scene):
    subclass = getattr(properties_scene, member)
    try:
        subclass.COMPAT_ENGINES.add('OCT_RENDER')
    except:
        pass
del properties_scene

from bl_ui import properties_texture
for member in dir(properties_texture):
    subclass = getattr(properties_texture, member)
    try:
        subclass.COMPAT_ENGINES.add('OCT_RENDER')
    except:
        pass
del properties_texture

from bl_ui import properties_data_lamp
for member in dir(properties_data_lamp):
    subclass = getattr(properties_data_lamp, member)
    try:
        subclass.COMPAT_ENGINES.add('OCT_RENDER')
    except:
        pass
del properties_data_lamp

from bl_ui import properties_particle
for member in dir(properties_particle):
    subclass = getattr(properties_particle, member)
    try:
        subclass.COMPAT_ENGINES.add('OCT_RENDER')
    except:
        pass
del properties_particle
