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

# <pep8 compliant>
import bpy
from rna_prop_ui import PropertyPanel
from properties_material import active_node_mat

class TEXTURE_OCT_specials(bpy.types.Menu):
    bl_label = "Texture Specials"
    COMPAT_ENGINES = {'OCT_RENDER'}

    def draw(self, context):
        layout = self.layout

        layout.operator("texture.slot_copy", icon='COPYDOWN')
        layout.operator("texture.slot_paste", icon='PASTEDOWN')

def context_tex_datablock(context):
    idblock = context.material
    if idblock:
        return active_node_mat(idblock)

    idblock = context.lamp
    if idblock:
        return idblock

    idblock = context.world
    if idblock:
        return idblock

    idblock = context.brush
    return idblock


class TextureButtonsPanel():
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "texture"

    @classmethod
    def poll(cls, context):
        tex = context.texture
        return tex and (tex.type != 'NONE' or tex.use_nodes) and (context.scene.render.engine in cls.COMPAT_ENGINES)

class TEXTURE_OCT_context_texture(TextureButtonsPanel, bpy.types.Panel):
    bl_label = ""
    bl_options = {'HIDE_HEADER'}
    COMPAT_ENGINES = {'OCT_RENDER'}

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        if not hasattr(context, "texture_slot"):
            return False
        return ((context.material or context.world or context.lamp or context.brush or context.texture)
            and (engine in cls.COMPAT_ENGINES))

    def draw(self, context):
        layout = self.layout
        slot = context.texture_slot
        node = context.texture_node
        space = context.space_data
        tex = context.texture
        idblock = context_tex_datablock(context)
        pin_id = space.pin_id

        if not isinstance(pin_id, bpy.types.Material):
            pin_id = None

        tex_collection = (pin_id is None) and (node is None) and (not isinstance(idblock, bpy.types.Brush))

        if tex_collection:
            row = layout.row()
            row.template_list(idblock, "texture_slots", idblock, "active_texture_index", rows=2)
            col = row.column(align=True)
            col.operator("texture.slot_move", text="", icon='TRIA_UP').type = 'UP'
            col.operator("texture.slot_move", text="", icon='TRIA_DOWN').type = 'DOWN'
            col.menu("TEXTURE_OCT_specials", icon='DOWNARROW_HLT', text="")
        split = layout.split(percentage=0.65)
        col = split.column()
        if tex_collection:
            col.template_ID(idblock, "active_texture", new="texture.new")
            #col.template_ID(idblock, "active_texture", new="octane.newtexture")
        elif node:
            col.template_ID(node, "texture", new="texture.new")
            #col.template_ID(node, "texture", new="octane.newtexture")
        elif idblock:
            col.template_ID(idblock, "texture", new="texture.new")
            #col.template_ID(idblock, "texture", new="octane.newtexture")

        if tex and tex.type != 'IMAGE':
            layout.label("Only Image type is supported. Please fix below", icon='ERROR')
            split = layout.split(percentage=0.2)
            split.label(text="Type:")
            split.prop(tex, "type", text="")
#       return



class TEXTURE_OCT_preview(TextureButtonsPanel, bpy.types.Panel):
    bl_label = "Preview"
    COMPAT_ENGINES = {'OCT_RENDER'}

    def draw(self, context):
        layout = self.layout
        tex = context.texture
        slot = getattr(context, "texture_slot", None)
        idblock = context_tex_datablock(context)
        if idblock:
            layout.template_preview(tex, parent=idblock, slot=slot)
        else:
            layout.template_preview(tex, slot=slot)


class TextureSlotPanel(TextureButtonsPanel):
    COMPAT_ENGINES = {'OCT_RENDER'}

    @classmethod
    def poll(cls, context):
        if not hasattr(context, "texture_slot"):
            return False
        engine = context.scene.render.engine
        return TextureButtonsPanel.poll(self, context) and (engine in cls.COMPAT_ENGINES)


# Texture Type Panels #
class TextureTypePanel(TextureButtonsPanel):

    @classmethod
    def poll(cls, context):
        tex = context.texture
        engine = context.scene.render.engine
        return tex and ((tex.type == cls.tex_type and not tex.use_nodes) and (engine in cls.COMPAT_ENGINES))

class TEXTURE_OCT_image(TextureTypePanel, bpy.types.Panel):
    bl_label = "Image"
    tex_type = 'IMAGE'
    COMPAT_ENGINES = {'OCT_RENDER'}

    def draw(self, context):
        layout = self.layout
        tex = context.texture
        layout.template_image(tex, "image", tex.image_user)#, compact=True)

class TEXTURE_OCT_slot(TextureSlotPanel, bpy.types.Panel):
    bl_label = "Octane Texture Mapping"
    COMPAT_ENGINES = {'OCT_RENDER'}

    @classmethod
    def poll(cls, context):
        idblock = context_tex_datablock(context)
        if isinstance(idblock, bpy.types.Brush) and not context.sculpt_object:
            return False

        if not getattr(context, "texture_slot", None):
            return False

        engine = context.scene.render.engine
        return (engine in cls.COMPAT_ENGINES)

    def draw(self, context):
        layout = self.layout

        idblock = context_tex_datablock(context)

        tex = context.texture_slot
        # textype = context.texture

        #~ if tex.texture.type != 'IMAGE' or tex.texture_coords !='UV' or tex.mapping !='FLAT':
            #~ bpy.ops.octane.fixtexture()

        fixme = False
        if tex.texture_coords !='UV':
            layout.label("Only UV coordinates are supported. Please fix below", icon='ERROR')
            split = layout.split(percentage=0.3)
            col = split.column()
            col.label(text="Coordinates:")
            col = split.column()
            col.prop(tex, "texture_coords", text="")
            fixme = True

        if tex.mapping !='FLAT':
            layout.label("Only flat mapping is supported. Please fix below", icon='ERROR')
            split = layout.split(percentage=0.3)
            split.label(text="Projection:")
            split.prop(tex, "mapping", text="")
            fixme = True

        if fixme: return

        if not isinstance(idblock, bpy.types.Brush):
            split = layout.split(percentage=0.3)
            if tex.uv_layer == '':
                split.label(text="Layer:",icon='ERROR')
            else:
                split.label(text="Layer:")
            ob = context.object
            if ob and ob.type == 'MESH':
                split.prop_search(tex, "uv_layer", ob.data, "uv_textures", text="")
            else:
                split.label("Object type does not support UV mapping")
#               split.prop(tex, "uv_layer", text="")
        layout.prop(tex, "scale")
        layout.label("(Z will be ignored)")
        if isinstance(idblock, bpy.types.Material):
            split = layout.split()

            col = split.column()
            col.label(text="Diffuse:")
            col.prop(tex, "use_map_normal", text="Normal Map")
            col.prop(tex, "use_map_color_diffuse", text="Diffuse Color")
            col.prop(tex, "use_map_alpha", text="Opacity Map")

            col = split.column()
            col.label(text="Specular:")
            col.prop(tex, "use_map_color_spec", text = "Specular Color")
            col.prop(tex, "use_map_hardness", text="Hardness Map")

def register():
    bpy.utils.register_module(__name__)


def unregister():
    bpy.utils.unregister_module(__name__)

if __name__ == "__main__":
    register()
