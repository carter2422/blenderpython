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

import bpy
import os
import octanerender.settings
from octanerender.utils import *
from octanerender.labels import getLabel

def base_poll(cls, context):
    rd = context.scene.render
    return (rd.use_game_engine==False) and (rd.engine in cls.COMPAT_ENGINES)

# Main Octane Panel
class OctaneWorldButtonsPanel():
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "world"
    # COMPAT_ENGINES must be defined in each subclass, external engines can add themselves here

    @classmethod
    def poll(cls, context):
        rd = context.scene.render
        return rd.engine == 'OCT_RENDER' and rd.use_game_engine == False

class WORLD_OCT_context_world(OctaneWorldButtonsPanel, bpy.types.Panel):
    bl_label = ""
    bl_options = {'HIDE_HEADER'}
    COMPAT_ENGINES = {'OCT_RENDER'}

    @classmethod
    def poll(cls, context):
        rd = context.scene.render
        return (not rd.use_game_engine) and (rd.engine in cls.COMPAT_ENGINES)

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        world = context.world
        space = context.space_data

        texture_count = world and len(world.texture_slots.keys())

        split = layout.split(percentage=0.65)
        if scene:
            split.template_ID(scene, "world", new="world.new")
        elif world:
            split.template_ID(space, "pin_id")

        if texture_count:
            split.label(text=str(texture_count), icon='TEXTURE')

# Octane Mesh Preview Kernel
class RENDER_OCT_world_kernel(OctaneWorldButtonsPanel, bpy.types.Panel):
    bl_label = "Octane Mesh Preview Kernel"
    COMPAT_ENGINES = {'OCT_RENDER'}

    @classmethod
    def poll(cls, context):
        return super().poll(context)

    def draw_header(self, context):
        world = context.world
        self.layout.prop(world, "OCT_kernel_use")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        world = context.world

        if not world.OCT_kernel_use:
            layout.enabled = False
        layout.prop(world, "OCT_kernel", expand=True)

        if world.OCT_kernel == 'directlighting':
            # Direct Lightning
            row = layout.row()
            row.prop(world, "OCT_use_speculardepth")
            row = row.row()
            row.enabled = world.OCT_use_speculardepth
            row.prop(world, "OCT_speculardepth")

            row = layout.row()
            row.prop(world, "OCT_use_glossydepth")
            row = row.row()
            row.enabled = world.OCT_use_glossydepth
            row.prop(world, "OCT_glossydepth")

            row = layout.row()
            row.prop(world, "OCT_use_aodist")
            row = row.row()
            row.enabled = world.OCT_use_aodist
            row.prop(world, "OCT_aodist")

        else:
            # Path Tracing
            row = layout.row()
            row.prop(world, "OCT_use_alphashadows")
            row = row.row()
            row.enabled = world.OCT_use_alphashadows
            row.prop(world, "OCT_alphashadows", expand=True)

            row = layout.row()
            row.prop(world, "OCT_use_maxdepth")
            row = row.row()
            row.enabled = world.OCT_use_maxdepth
            row.prop(world, "OCT_maxdepth")

            row = layout.row()
            row.prop(world, "OCT_use_rrprob")
            row = row.row()
            row.enabled = world.OCT_use_rrprob
            row.prop(world, "OCT_rrprob")

        # Common stuff
        row = layout.row()
        row.prop(world, "OCT_use_rayepsilon")
        row = row.row()
        row.enabled = world.OCT_use_rayepsilon
        row.prop(world, "OCT_rayepsilon")

        row = layout.row()
        row.prop(world, "OCT_use_filtersize")
        row = row.row()
        row.enabled = world.OCT_use_filtersize
        row.prop(world, "OCT_filtersize")

        row = layout.row()
        row.prop(world, "OCT_use_alphachannel")
        row = row.row()
        row.enabled = world.OCT_use_alphachannel
        row.prop(world, "OCT_alphachannel", expand=True)

        row = layout.row()
        row.enabled = world.OCT_use_alphachannel and world.OCT_alphachannel == "true"
        row.prop(world, "OCT_use_keep_environment")
        row = row.row()
        row.enabled = world.OCT_use_keep_environment
        row.prop(world, "OCT_keep_environment", expand=True)




# Octane Mesh Preview Environment
class RENDER_OCT_world_environment(OctaneWorldButtonsPanel, bpy.types.Panel):
    bl_label = "Octane Mesh Preview Environment"
    COMPAT_ENGINES = {'OCT_RENDER'}

    @classmethod
    def poll(cls, context):
        return super().poll(context)

    def draw_header(self, context):
        world = context.world
        self.layout.prop(world, "OCT_environment_use")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        world = context.world
        octane_render = scene.octane_render

        if not world.OCT_environment_use:
            layout.enabled = False
        layout.prop(world, "OCT_environment", expand=True)

        if world.OCT_environment == 'texture environment':
            # Texture Environment
            layout.prop(world, "OCT_texture_type", expand=True)
            if world.OCT_texture_type == 'FLOAT':
                # Float Texture
                row = layout.row()
                row.prop(world, "OCT_use_texture_float")
                row = row.row()
                row.enabled = world.OCT_use_texture_float
                row.prop(world, "OCT_texture_float")
            else:
                # Image Texture
                row = layout.row()
                #row.prop(world, "OCT_use_texture_image")
                #row = row.row()
                #row.enabled = world.OCT_use_texture_image
                if not os.path.isfile(world.OCT_texture_image):
                    row.prop(world, "OCT_texture_image", icon="ERROR")
                else:
                    row.prop(world, "OCT_texture_image")

            row = layout.row()
            row.prop(world, "OCT_use_texture_XY")
            row = row.row()
            row.enabled = world.OCT_use_texture_XY
            row.prop(world, "OCT_texture_X")

            #row = layout.row()
            #row.prop(world, "OCT_use_texture_XY")
            row = row.row()
            row.enabled = world.OCT_use_texture_XY
            row.prop(world, "OCT_texture_Y")
        else:
            # Daylight Environment
            row = layout.row()
            if world.OCT_active_light == "":
                row.label('Select active Sun light :', icon='ERROR')
            else:
                lampOBJ = bpy.data.objects[world.OCT_active_light]
                if not lampOBJ:
                    row.label('Select active Sun light :', icon='ERROR')
                else:
                    if lampOBJ.type != 'LAMP':
                        row.label('Select active Sun light :', icon='ERROR')
                    else:
                        lampLAMP = lampOBJ.data
                        if lampLAMP.type != 'SUN':
                            row.label('Select active Sun light :', icon='ERROR')
                        else:
                            row.label('Select active Sun light :', icon='LAMP_SUN')
            row.prop_search(world, "OCT_active_light", bpy.data, "objects", text="")

            row = layout.row()
            row.prop(world, "OCT_use_turbidity")
            row = row.row()
            row.enabled = world.OCT_use_turbidity
            row.prop(world, "OCT_turbidity")

            row = layout.row()
            row.prop(world, "OCT_use_northoffset")
            row = row.row()
            row.enabled = world.OCT_use_northoffset
            row.prop(world, "OCT_northoffset")

        row = layout.row()
        row.prop(world, "OCT_use_power")
        row = row.row()
        row.enabled = world.OCT_use_power
        row.prop(world, "OCT_power")

class RENDER_OCT_world_imager(OctaneWorldButtonsPanel, bpy.types.Panel):
    bl_label = "Octane Mesh Preview Imager"
    COMPAT_ENGINES = {'OCT_RENDER'}

    @classmethod
    def poll(cls, context):
        return super().poll(context)

    def draw_header(self, context):
        world = context.world
        self.layout.prop(world, "OCT_imager_use")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        world = context.world
        octane_render = scene.octane_render

        if not world.OCT_imager_use:
            layout.enabled = False

        row = layout.row()
        row.prop(world, "OCT_use_exposure")
        row = row.row()
        row.enabled = world.OCT_use_exposure
        row.prop(world, "OCT_exposure")

        row = layout.row()
        row.prop(world, "OCT_use_fstop")
        row = row.row()
        row.enabled = world.OCT_use_fstop
        row.prop(world, "OCT_fstop")

        row = layout.row()
        row.prop(world, "OCT_use_ISO")
        row = row.row()
        row.enabled = world.OCT_use_ISO
        row.prop(world, "OCT_ISO")

        row = layout.row()
        row.prop(world, "OCT_use_gamma")
        row = row.row()
        row.enabled = world.OCT_use_gamma
        row.prop(world, "OCT_gamma")

        row = layout.row()
        row.prop(world, "OCT_use_response")
        row = row.row()
        row.enabled = world.OCT_use_response
        row.prop(world, "OCT_response")

        row = layout.row()
        row.prop(world, "OCT_use_vignetting")
        row = row.row()
        row.enabled = world.OCT_use_vignetting
        row.prop(world, "OCT_vignetting")

        row = layout.row()
        row.prop(world, "OCT_use_saturation")
        row = row.row()
        row.enabled = world.OCT_use_saturation
        row.prop(world, "OCT_saturation")

        row = layout.row()
        row.prop(world, "OCT_use_hotpixel_removal")
        row = row.row()
        row.enabled = world.OCT_use_hotpixel_removal
        row.prop(world, "OCT_hotpixel_removal")

        row = layout.row()
        row.prop(world, "OCT_use_premultiplied_alpha")
        row = row.row()
        row.enabled = world.OCT_use_premultiplied_alpha
        row.prop(world, "OCT_premultiplied_alpha", expand=True)

def register():
    bpy.utils.register_module(__name__)


def unregister():
    bpy.utils.unregister_module(__name__)

if __name__ == "__main__":
    register()
