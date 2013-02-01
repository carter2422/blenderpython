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
# This directory is a Python package.


bl_info = {
    "name": "Octane Render Extended",
    "author": "Lionel Zamouth",
    "version": (1,2,0),
    "blender": (2, 6, 2),
    "api": 45110,
    "location": "Info Header - Engine dropdown",
    "description": "Extended Octane Render addon - UNSUPPORTED",
    "warning": " This is NOT the official script from Refractive Software",
    "wiki_url": "",
    "tracker_url": "",
    "support": 'COMMUNITY',
    "category": "Render"}
Version = 'v1.20'
Supported = False


Verbose = True
Status_Display = False
Status_Text = ""
Status_Severity = 0
replace_project = False

cameraUpdateOnly = False
launchOctane = False
flyMode = False
bucketMode = False
pullImage = False
maxSamples = 0
frameStart = 1
frameStop = 1
frameCurrent = 1
frameStep = 1
delayed_copies = []
dst_dir = ""

# To support reload properly, try to access a package var, if it's there, reload everything
if "octane_data" in locals():
    import imp
    imp.reload(settings)
    imp.reload(utils)
    imp.reload(operators)
    imp.reload(ui_render)
    imp.reload(ui_world)
    imp.reload(ui_material)
    #imp.reload(ui_texture)
    imp.reload(ui_camera)
    imp.reload(properties)
    imp.reload(export)
    imp.reload(engine)
else:
    from octanerender import settings
    from octanerender import utils
    from octanerender import operators
    from octanerender import ui_render
    from octanerender import ui_world
    from octanerender import ui_material
    #from octanerender import ui_texture
    from octanerender import ui_camera
    from octanerender import properties
    from octanerender import export
    from octanerender import engine

octane_data = True

def register():
    import bpy
    bpy.utils.register_module(__name__)
    settings.addProperties()

def unregister():
    import bpy
    bpy.utils.unregister_module(__name__)
    del bpy.types.Scene.octane_render
