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
from octanerender.utils import *
from rna_prop_ui import PropertyPanel

#class MATERIAL_OCT_sss_presets(bpy.types.Menu):
#   bl_label = "SSS Presets"
#   preset_subdir = "sss"
#   preset_operator = "script.execute_preset"
#   draw = bpy.types.Menu.draw_preset


class MATERIAL_OCT_specials(bpy.types.Menu):
    bl_label = "Material Specials"

    def draw(self, context):
        layout = self.layout
        layout.operator("object.material_slot_copy", icon='COPY_ID')
        layout.operator("material.copy", icon='COPYDOWN')
        layout.operator("material.paste", icon='PASTEDOWN')


class OctaneMaterialButtonsPanel():
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "material"
    # COMPAT_ENGINES must be defined in each subclass, external engines can add themselves here

    @classmethod
    def poll(cls, context):
        return context.material and (context.scene.render.engine in cls.COMPAT_ENGINES)


class MATERIAL_OCT_context_material(OctaneMaterialButtonsPanel, bpy.types.Panel):
    bl_label = ""
    bl_options = {'HIDE_HEADER'}
    COMPAT_ENGINES = {'OCT_RENDER'}

    @classmethod
    def poll(cls, context):
        # An exception, dont call the parent poll func because
        # this manages materials for all engine types

        engine = context.scene.render.engine
        return (context.material or context.object) and (engine in cls.COMPAT_ENGINES)

    def draw(self, context):
        layout = self.layout

        mat = context.material
        ob = context.object
        slot = context.material_slot
        space = context.space_data

        if ob:
            row = layout.row()

            row.template_list(ob, "material_slots", ob, "active_material_index", rows=2)

            col = row.column(align=True)
            col.operator("object.material_slot_add", icon='ZOOMIN', text="")
            col.operator("object.material_slot_remove", icon='ZOOMOUT', text="")

            col.menu("MATERIAL_MT_specials", icon='DOWNARROW_HLT', text="")

            if ob.mode == 'EDIT':
                row = layout.row(align=True)
                row.operator("object.material_slot_assign", text="Assign")
                row.operator("object.material_slot_select", text="Select")
                row.operator("object.material_slot_deselect", text="Deselect")

        split = layout.split(percentage=0.65)

        if ob:
            split.template_ID(ob, "active_material", new="material.new")
            row = split.row()
            if mat:
                row.prop(mat, "use_nodes", icon="NODETREE", text="")

            if slot:
                row.prop(slot, "link", text="")
            else:
                row.label()
        elif mat:
            split.template_ID(space, "pin_id")
            split.separator()

        if mat:
            layout.prop(mat, "type", expand=True)


class MATERIAL_OCT_preview(OctaneMaterialButtonsPanel, bpy.types.Panel):
    bl_label = "Preview"
    COMPAT_ENGINES = {'OCT_RENDER'}

    def draw(self, context):
        self.layout.template_preview(context.material)

class MATERIAL_OCT_properties(OctaneMaterialButtonsPanel, bpy.types.Panel):
    bl_label = "Material Properties"
    COMPAT_ENGINES = {'OCT_RENDER'}

    @classmethod
    def poll(cls, context):
        mat = active_node_mat(context.material)
        engine = context.scene.render.engine
        return mat and (mat.type in ('SURFACE', 'WIRE')) and (engine in cls.COMPAT_ENGINES)

    def draw(self, context):
        mat = active_node_mat(context.material)
        ray = mat.raytrace_transparency

        layout = self.layout
        layout.prop(mat, "OCT_material_type", expand=True)

        if mat.OCT_material_type == "diffuse":
            box = layout.box()
            box = box.column()
            box.prop(mat.OCT_diffuse, "diffuse",text="Diffuse input")
            if mat.OCT_diffuse.diffuse == "RGBspectrum":
                row = box.row()
                row.label("Diffuse color:")
                row.prop(mat, "diffuse_color", text="")
            else:
                box.prop_search(mat.OCT_diffuse, "texture", bpy.data, "textures", text="Diffuse map:")
                row = box.row()
                row.prop(mat.OCT_diffuse, "power")
                row.prop(mat.OCT_diffuse, "gamma")
                #row = box.row()
                #row.prop(mat.OCT_diffuse, "scale")
                row.prop(mat.OCT_diffuse, "invert")

            box = layout.box()
            box = box.column()
            box.prop(mat,"OCT_emitter_type")
            if mat.OCT_emitter_type == "blackbody":
                box.prop(mat, "OCT_temperature")
                box.prop(mat, "OCT_normalize")
                box.prop(mat, "OCT_power")
            elif mat.OCT_emitter_type == "texture":
                box.prop(mat.OCT_emission, "emission", text="Emission source")
                if mat.OCT_emission.emission == "RGBspectrum":
                    row = box.row()
                    row.label("Emission color:")
                    row.prop(mat, "specular_color", text="")
                else:
                    box.prop_search(mat.OCT_emission, "texture", bpy.data, "textures", text="Emission map:")
                    row = box.row()
                    row.prop(mat.OCT_emission, "power")
                    row.prop(mat.OCT_emission, "gamma")
                    #row = box.row()
                    #row.prop(mat.OCT_emission, "scale")
                    row.prop(mat.OCT_emission, "invert")
                box.prop(mat, "OCT_power")

        elif mat.OCT_material_type == "glossy":
            box = layout.box()
            box = box.column()
            box.prop(mat.OCT_diffuse, "diffuse",text="Diffuse input")
            if mat.OCT_diffuse.diffuse == "RGBspectrum":
                row = box.row()
                row.label("Diffuse color:")
                row.prop(mat, "diffuse_color", text="")
            else:
                box.prop_search(mat.OCT_diffuse, "texture", bpy.data, "textures", text="Diffuse map:")
                row = box.row()
                row.prop(mat.OCT_diffuse, "power")
                row.prop(mat.OCT_diffuse, "gamma")
                #row = box.row()
                #row.prop(mat.OCT_diffuse, "scale")
                row.prop(mat.OCT_diffuse, "invert")

            box = layout.box()
            box = box.column()
            box.prop(mat.OCT_specular, "specular",text="Specular input")
            if mat.OCT_specular.specular == "RGBspectrum":
                row = box.row()
                row.label("Specular color:")
                row.prop(mat, "specular_color", text="")
            elif mat.OCT_specular.specular == "floattexture":
                box.prop(mat.OCT_specular, "floattexture")
            else:
                box.prop_search(mat.OCT_specular, "texture", bpy.data, "textures", text="Specular map:")
                row = box.row()
                row.prop(mat.OCT_specular, "power")
                row.prop(mat.OCT_specular, "gamma")
                #row = box.row()
                #row.prop(mat.OCT_specular, "scale")
                row.prop(mat.OCT_specular, "invert")

            box = layout.box()
            col = box.column()
            col.prop(mat.OCT_roughness, "roughness", text="Roughness input")
            if mat.OCT_roughness.roughness == "floattexture":
                box.prop(mat, "OCT_roughnessfloat")
            else:
                box.prop_search(mat.OCT_roughness, "texture", bpy.data, "textures", text="Roughness map:")
                row = box.row()
                row.prop(mat.OCT_roughness, "power")
                row.prop(mat.OCT_roughness, "gamma")
                row.prop(mat.OCT_roughness, "invert")

            box = layout.box()
            col = box.column()
            col.prop(mat, "OCT_filmwidth")
            col.prop(mat, "OCT_filmindex")

        elif mat.OCT_material_type == "specular":
            box = layout.box()
            box = box.column()
            box.prop(mat.OCT_specular, "specular",text="Reflection input")
            if mat.OCT_specular.specular == "RGBspectrum":
                row = box.row()
                row.label("Reflection color:")
                row.prop(mat, "specular_color", text="")
            elif mat.OCT_specular.specular == "floattexture":
                box.prop(mat.OCT_specular, "floattexture")
            else:
                box.prop_search(mat.OCT_specular, "texture", bpy.data, "textures", text="Reflection map:")
                row = box.row()
                row.prop(mat.OCT_specular, "power")
                row.prop(mat.OCT_specular, "gamma")
                #row = box.row()
                #row.prop(mat.OCT_specular, "scale")
                row.prop(mat.OCT_specular, "invert")

            box = layout.box()
            box = box.column()
            box.prop(mat.OCT_diffuse, "diffuse",text="Transmission input")
            if mat.OCT_diffuse.diffuse == "RGBspectrum":
                row = box.row()
                row.label("Transmission color:")
                row.prop(mat, "diffuse_color", text="")
            else:
                box.prop_search(mat.OCT_diffuse, "texture", bpy.data, "textures", text="Transmission map:")
                row = box.row()
                row.prop(mat.OCT_diffuse, "power")
                row.prop(mat.OCT_diffuse, "gamma")
                #row = box.row()
                #row.prop(mat.OCT_diffuse, "scale")
                row.prop(mat.OCT_diffuse, "invert")

            box = layout.box()
            col = box.column()
            row = col.row(align=True)
            row.prop(mat, "OCT_index", text="IOR" )
            row.operator_menu_enum('ops.menu_ior_presets','ior_presets','IOR Presets')
            #col.prop(mat, "OCT_index")
            col.prop(mat, "OCT_filmwidth")
            col.prop(mat, "OCT_filmindex")

            box = layout.box()
            col = box.column()
            col.prop(mat.OCT_roughness, "roughness", text="Roughness input")
            if mat.OCT_roughness.roughness == "floattexture":
                box.prop(mat, "OCT_roughnessfloat")
            else:
                box.prop_search(mat.OCT_roughness, "texture", bpy.data, "textures", text="Roughness map:")
                row = box.row()
                row.prop(mat.OCT_roughness, "power")
                row.prop(mat.OCT_roughness, "gamma")
                row.prop(mat.OCT_roughness, "invert")

        else:
            error ("We should never have been here: unknown material type")

        box = layout.box()
        box = box.column()
        box.prop(mat.OCT_bump, "bump")
        if mat.OCT_bump.bump == "floatimage":
            box.prop_search(mat.OCT_bump, "texture", bpy.data, "textures", text="Bump map:")
            row = box.row()
            row.prop(mat.OCT_bump, "power")
            row.prop(mat.OCT_bump, "gamma")
            #row = box.row()
            #row.prop(mat.OCT_bump, "scale")
            row.prop(mat.OCT_bump, "invert")

        box = layout.box()
        box = box.column()
        box.prop(mat.OCT_normal, "normal")
        if mat.OCT_normal.normal == "image":
            box.prop_search(mat.OCT_normal, "texture", bpy.data, "textures", text="Normal map:")
            row = box.row()
            row.prop(mat.OCT_normal, "power")
            row.prop(mat.OCT_normal, "gamma")
            #row = box.row()
            #row.prop(mat.OCT_normal, "scale")
            row.prop(mat.OCT_normal, "invert")

        box = layout.box()
        box = box.column()
        box.prop(mat.OCT_opacity, "opacity")
        if mat.OCT_opacity.opacity == "floattexture":
            box.prop(mat.OCT_opacity, "floattexture")
        else:
            box.prop_search(mat.OCT_opacity, "texture", bpy.data, "textures", text="Opacity map:")
            row = box.row()
            row.prop(mat.OCT_opacity, "power")
            row.prop(mat.OCT_opacity, "gamma")
            #row = box.row()
            #row.prop(mat.OCT_opacity, "scale")
            row.prop(mat.OCT_opacity, "invert")


        layout.prop(mat, "OCT_smooth")


        #~ dofix = False
        #~ if bpy.context.scene.octane_render.ignore_intensity:
            #~ if mat.diffuse_intensity < 1.0: dofix = True
            #~ if mat.specular_intensity < 1.0: dofix = True
        #~ if not (mat.use_transparency and mat.transparency_method == 'RAYTRACE' and ray.ior > 1.0):
            #~ if mat.alpha < 1.0: dofix = True
            #~ if mat.use_transparency: dofix = True
        #~ if dofix:
            #~ bpy.ops.octane.fixmaterial()
#~
        #~ mat_type = ''
        #~ if (mat.specular_color.r+mat.specular_color.g+mat.specular_color.b) * mat.specular_intensity == 0.0:
            #~ # Material is Diffuse
            #~ mat_type = 'd'
        #~ elif mat.use_transparency and mat.transparency_method == 'RAYTRACE' and ray.ior > 1.0:
            #~ # Material is Specular
            #~ mat_type = 's'
        #~ else:
            #~ # Material is Glossy
            #~ mat_type = 'g'
#~
        #~ layout = self.layout
        #~ layout.label('Octane material setting :')
        #~ row = layout.row(align=True)
        #~ if mat_type == 'd':
            #~ row.operator('ops.button_make_diffuse',icon='COLOR')
        #~ else : row.operator('ops.button_make_diffuse')
        #~ if mat_type == 'g':
            #~ row.operator('ops.button_make_glossy',icon='COLOR')
        #~ else : row.operator('ops.button_make_glossy')
        #~ if mat_type == 's':
            #~ row.operator('ops.button_make_specular',icon='COLOR')
        #~ else : row.operator('ops.button_make_specular')
#~
        #~ if mat_type == 'd':
            #~ layout.label('Diffuse color and intensity :')
            #~ layout.prop(mat, "diffuse_color", text="")
            #~ layout.prop(mat, "diffuse_intensity", text="Intensity")
        #~ elif mat_type == 'g':
            #~ layout.label('Diffuse color and intensity :')
            #~ layout.prop(mat, "diffuse_color", text="")
            #~ if not bpy.context.scene.octane_render.ignore_intensity:
                #~ layout.prop(mat, "diffuse_intensity", text="Intensity")
            #~ layout.label('Specular color, intensity and hardness :')
            #~ layout.prop(mat, "specular_color", text="")
            #~ if not bpy.context.scene.octane_render.ignore_intensity:
                #~ layout.prop(mat, "specular_intensity", text="Intensity")
            #~ layout.prop(mat, "specular_hardness", text="Hardness")
        #~ else:
            #~ layout.label('Transmission color and intensity :')
            #~ layout.prop(mat, "diffuse_color", text="")
            #~ if not bpy.context.scene.octane_render.ignore_intensity:
                #~ layout.prop(mat, "diffuse_intensity", text="Intensity")
            #~ layout.label('Reflection color, intensity and hardness :')
            #~ layout.prop(mat, "specular_color", text="")
            #~ if not bpy.context.scene.octane_render.ignore_intensity:
                #~ layout.prop(mat, "specular_intensity", text="Intensity")
            #~ layout.prop(mat, "specular_hardness", text="Hardness")
            #~ row = layout.row(align=True)
            #~ row.prop(ray, "ior", text="IOR" )
            #~ row.operator_menu_enum('ops.menu_ior_presets','ior_presets','IOR Presets')

def register():
    bpy.utils.register_module(__name__)


def unregister():
    bpy.utils.unregister_module(__name__)

if __name__ == "__main__":
    register()
