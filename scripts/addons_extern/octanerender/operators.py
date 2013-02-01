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
from bpy.props import *
from  octanerender.utils import *

# Button for exporting only
class BUTTON_OCT_export(bpy.types.Operator):
    bl_idname = "ops.button_export"
    bl_label = "Export OBJ/MTL only"
    bl_description = "Only export OBJ/MTL"

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        scene = context.scene
        octane_render = scene.octane_render
        # Exit edit mode before exporting, so current object states are exported properly.
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode='OBJECT')

        log ('Exporting OBJ/MTL only')
        octanerender.cameraUpdateOnly = False
        octanerender.launchOctane = False
        octanerender.flyMode = False
        octanerender.pullImage = False
        octanerender.maxSamples = 0
        octanerender.frameStart = scene.frame_current
        octanerender.frameStop  = octanerender.frameStart

        bpy.ops.render.render()
        notify_user (self)
        return{'FINISHED'}

    def invoke(self, context, event):
        return self.execute(context)

# Button for rendering Still Image
class BUTTON_OCT_render(bpy.types.Operator):
    bl_idname = "ops.button_render"
    bl_label = "Render Still Image"
    bl_description = "Export OBJ/MTL, create OCS if it doesn't exist and render"

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        scene = context.scene
        octane_render = scene.octane_render
        # Exit edit mode before exporting, so current object states are exported properly.
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode='OBJECT')

        log ('Rendering still image')
        octanerender.cameraUpdateOnly = False
        octanerender.launchOctane = True
        octanerender.flyMode = False
        octanerender.pullImage = octane_render.import_render
        if octanerender.pullImage:
            octanerender.maxSamples = octane_render.samples_still
        else:
            octanerender.maxSamples = 64000
        octanerender.frameStart = scene.frame_current
        octanerender.frameStop  = octanerender.frameStart

        octanerender.replace_project = octane_render.replace_project
        octane_render.replace_project = False
        if octane_render.import_render:
            log('Call to render with INVOKE_AREA')
            bpy.ops.render.render('INVOKE_AREA')
        else:
            log('Call to render without options')
            bpy.ops.render.render()
        notify_user (self)
        return{'FINISHED'}

    def invoke(self, context, event):
        return self.execute(context)

# Button for rendering Bucket Images
class BUTTON_OCT_bucket(bpy.types.Operator):
    bl_idname = "ops.button_bucket"
    bl_label = "Bucket Rendering"
    bl_description = "Export OBJ/MTL, create OCS if it doesn't exist and render tiles"

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        scene = context.scene
        octane_render = scene.octane_render
        # Exit edit mode before exporting, so current object states are exported properly.
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode='OBJECT')

        log ('Bucket Rendering %dx%d' % (octane_render.bucketX, octane_render.bucketY))
        octanerender.cameraUpdateOnly = False
        octanerender.launchOctane = True
        octanerender.flyMode = False
        octanerender.bucketMode = True
        octanerender.pullImage = True
        octanerender.maxSamples = octane_render.samples_still
        octanerender.frameStart = scene.frame_current
        octanerender.frameStop  = octanerender.frameStart

        octanerender.replace_project = octane_render.replace_project
        octane_render.replace_project = False
        bpy.ops.render.render('INVOKE_AREA')
        notify_user (self)
        return{'FINISHED'}

    def invoke(self, context, event):
        return self.execute(context)

# Button for rendering animation
class BUTTON_OCT_animation(bpy.types.Operator):
    bl_idname = "ops.button_animation"
    bl_label = "Render Animation"
    bl_description = "Export OBJ/MTL and render animation frame(s)"

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        scene = context.scene
        octane_render = scene.octane_render
        # Exit edit mode before exporting, so current object states are exported properly.
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode='OBJECT')

        log ('Rendering animation from frame #%d to #%d' % (scene.frame_start,scene.frame_end))
        octanerender.cameraUpdateOnly = False
        octanerender.launchOctane = True
        octanerender.flyMode = False
        octanerender.pullImage = True
        octanerender.maxSamples = octane_render.export_samples_per_image
        octanerender.frameStart = scene.frame_start
        octanerender.frameStop  = scene.frame_end

        octanerender.replace_project = octane_render.replace_project
        octane_render.replace_project = False
        scene.frame_set(scene.frame_start)
        bpy.ops.render.render('INVOKE_AREA')
        notify_user (self)
        return{'FINISHED'}

    def invoke(self, context, event):
        return self.execute(context)

# Button for rendering camera animation only
class BUTTON_OCT_fly(bpy.types.Operator):
    bl_idname = "ops.button_fly"
    bl_label = "Camera Animation"
    bl_description = "Export OBJ/MTL only once and render animation frame(s)"

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        scene = context.scene
        octane_render = scene.octane_render
        # Exit edit mode before exporting, so current object states are exported properly.
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode='OBJECT')

        log ('Rendering camera/light only animation from frame #%d to #%d' % (scene.frame_start,scene.frame_end))
        if octane_render.export_camera == False:
            update_status(2,'You must export camera in this mode')
            notify_user (self)
            return{'FINISHED'}

        octanerender.cameraUpdateOnly = False
        octanerender.launchOctane = True
        octanerender.flyMode = True
        octanerender.pullImage = True
        octanerender.maxSamples = octane_render.export_samples_per_image
        octanerender.frameStart = scene.frame_start
        octanerender.frameStop  = scene.frame_end

        octanerender.replace_project = octane_render.replace_project
        octane_render.replace_project = False
        scene.frame_set(scene.frame_start)
        bpy.ops.render.render('INVOKE_AREA')
        notify_user (self)
        return{'FINISHED'}

    def invoke(self, context, event):
        return self.execute(context)

# Button for rendering camera update only
class BUTTON_OCT_updatecam(bpy.types.Operator):
    bl_idname = "ops.button_updatecam"
    bl_label = "Update camera in Octane"
    bl_description = "Doesn't export and call Octane with new camera setting"

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        scene = context.scene
        octane_render = scene.octane_render
        # Exit edit mode before exporting, so current object states are exported properly.
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode='OBJECT')

        log ('Rendering still image')
        octanerender.cameraUpdateOnly = True
        octanerender.launchOctane = True
        octanerender.flyMode = False
        octanerender.pullImage = octane_render.import_render
        if octanerender.pullImage:
            octanerender.maxSamples = octane_render.samples_still
        else:
            octanerender.maxSamples = 64000
        octanerender.frameStart = scene.frame_current
        octanerender.frameStop  = octanerender.frameStart

        octanerender.replace_project = octane_render.replace_project
        octane_render.replace_project = False
        if octane_render.import_render:
            log('Call to render with INVOKE_AREA')
            bpy.ops.render.render('INVOKE_AREA')
        else:
            log('Call to render without options')
            bpy.ops.render.render()
        notify_user (self)
        return{'FINISHED'}

    def invoke(self, context, event):
        return self.execute(context)




# Button to push active camera into camera name field
class BUTTON_OCT_select_camera(bpy.types.Operator):
    bl_idname = "ops.button_select_camera"
    bl_label = "Select"
    bl_description = "Select active camera"

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        scene = context.scene
        octane_render = scene.octane_render
        if scene.objects.active.type=='CAMERA':
            octane_render.active_camera=scene.objects.active.name
            update_status(0,'Camera <%s> assigned to Octane exporter' % scene.objects.active.name)
        else:
            update_status(2,'<%s> is not a CAMERA' % scene.objects.active.name)
        notify_user (self)
        return{'FINISHED'}

    def invoke(self, context, event):
        return self.execute(context)

# Button to push active light into light name field
class BUTTON_OCT_select_light_source(bpy.types.Operator):
    bl_idname = "ops.button_select_light_source"
    bl_label = "Select"
    bl_description = "Select active light source"

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        scene = context.scene
        octane_render = scene.octane_render
        if scene.objects.active.type=='LAMP':
            octane_render.active_light = scene.objects.active.name
            update_status(0,'Lamp <%s> assigned to Octane exporter' % scene.objects.active.name)
        else:
            update_status(2,'<%s> is not a LAMP' % scene.objects.active.name)
        notify_user (self)
        return{'FINISHED'}

    def invoke(self, context, event):
        return self.execute(context)

# Manage samples presets for still image
class PRESET_still_samples(bpy.types.Operator):
    bl_idname = "ops.menu_still_presets"
    bl_label = "Samples Presets"
    #bl_options = {'REGISTER', 'UNDO'}

    export_samples_presets = EnumProperty(
        name="Presets",
        description="Samples per image presets",
        items=(
            ("0",  "Very Low (8)", ""),
            ("1", "Low (32)", ""),
            ("2",  "Medium (256)", ""),
            ("3",  "Medium/High (512)", ""),
            ("4",  "High (1024)", ""),
            ("5",  "Very High (4096)", ""),
            ("6",  "Too High (8192)", ""),
            ("7",  "Insane (16384)", "")
            ),
        default= "4")

    def execute(self, context):
        scene = context.scene
        octane_render = scene.octane_render
        octane_render.samples_still = {"0": 8, "1": 32, "2": 256, "3": 512, "4": 1024, "5": 4096, "6": 8192, "7": 16384 }[self.properties.export_samples_presets]
        return {'FINISHED'}

# Manage samples presets for animation
class PRESET_export_samples(bpy.types.Operator):
    bl_idname = "ops.menu_export_presets"
    bl_label = "Samples Presets"
    #bl_options = {'REGISTER', 'UNDO'}

    export_samples_presets = EnumProperty(
        name="Presets",
        description="Samples per image presets",
        items=(
            ("0",  "Very Low (8)", ""),
            ("1", "Low (32)", ""),
            ("2",  "Medium (256)", ""),
            ("3",  "Medium/High (512)", ""),
            ("4",  "High (1024)", ""),
            ("5",  "Very High (4096)", ""),
            ("6",  "Too High (8192)", ""),
            ("7",  "Insane (16384)", "")
            ),
        default= "2")

    def execute(self, context):
        scene = context.scene
        octane_render = scene.octane_render
        octane_render.export_samples_per_image = {"0": 8, "1": 32, "2": 256, "3": 512, "4": 1024, "5": 4096, "6": 8192, "7": 16384  }[self.properties.export_samples_presets]
        return {'FINISHED'}

class PROPERTIES_octane_fixaspect(bpy.types.Operator):
    bl_idname = 'octane.fixaspect'
    bl_label ="Fix pixel aspect ratio"
    bl_options = {'REGISTER'}

    def execute(self, context):
        rd = bpy.context.scene.render
        rd.pixel_aspect_x =1
        rd.pixel_aspect_y = 1
        log ('Forced reset pixel to square')

        return {'FINISHED'}

    def invoke(self, context, event):
        return self.execute(context)

class PROPERTIES_octane_fixmaterial(bpy.types.Operator):
    bl_idname = 'octane.fixmaterial'
    bl_label ="Let Octane fix material settings"
    bl_options = {'REGISTER'}

    def execute(self, context):
        log ('Fixing material')
        mat = active_node_mat(context.material)
        ray = mat.raytrace_transparency
        if bpy.context.scene.octane_render.ignore_intensity:
            if mat.diffuse_intensity < 1.0: mat.diffuse_intensity = 1.0
            if mat.specular_intensity < 1.0: mat.specular_intensity = 1.0
        if not (mat.use_transparency and mat.transparency_method == 'RAYTRACE' and ray.ior > 1.0):
            mat.use_transparency = False
            mat.alpha = 1
        return {'FINISHED'}

    def invoke(self, context, event):
        return self.execute(self, context, event)

class PROPERTIES_octane_fixtexture(bpy.types.Operator):
    bl_idname = 'octane.fixtexture'
    bl_label ="Let Octane fix texture settings"
    bl_options = {'REGISTER'}

    def execute(self, context):
        log ('Fixing texture')
        tex = context.texture_slot
        tex.texture.type = 'IMAGE'
        tex.texture_coords ='UV'
        tex.mapping ='FLAT'
        return {'FINISHED'}

    def invoke(self, context, event):
        return self.execute(context)

class PROPERTIES_octane_fixmappings(bpy.types.Operator):
    bl_idname = 'octane.fixmappings'
    bl_label ="Let Octane fix texture mappings"
    bl_options = {'REGISTER'}

    def execute(self, context):
        log ('Fixing mappings')
        #
        return {'FINISHED'}

    def invoke(self, context, event):
        return self.execute(context)

class PROPERTIES_octane_newtexture(bpy.types.Operator):
    bl_idname = 'octane.newtexture'
    bl_label ="Let Octane fix texture mappings"
    bl_options = {'REGISTER'}

    def execute(self, context):
        log ('New Texture')
        bpy.ops.texture.new()
        return {'FINISHED'}

    def invoke(self, context, event):
        return self.execute(context)

# Make Diffuse Material
class BUTTON_OCT_make_diffuse(bpy.types.Operator):
    bl_idname = "ops.button_make_diffuse"
    bl_label = "Diffuse"
    bl_description = "Set Material as Octane Diffuse"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        mat = active_node_mat(context.material)
        ray = mat.raytrace_transparency

        mat.use_transparency = False
        mat.alpha = 1.0
        ray.ior = 1.0
        mat.specular_intensity = 0.000
        if bpy.context.scene.octane_render.ignore_intensity:
            mat.specular_color.r = 0.000
            mat.specular_color.g = 0.000
            mat.specular_color.b = 0.000
        return{'FINISHED'}

    def invoke(self, context, event):
        return self.execute(context)

# Make Glossy Material
class BUTTON_OCT_make_glossy(bpy.types.Operator):
    bl_idname = "ops.button_make_glossy"
    bl_label = "Glossy"
    bl_description = "Set Material as Octane Glossy"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        mat = active_node_mat(context.material)
        ray = mat.raytrace_transparency

        mat.use_transparency = False
        mat.alpha = 1.0
        ray.ior = 1.0
        if mat.specular_intensity == 0.0:
            mat.specular_intensity = 0.8
        if (mat.specular_color.r+mat.specular_color.g+mat.specular_color.b) == 0.0:
            mat.specular_color.r = 0.001
            mat.specular_color.g = 0.001
            mat.specular_color.b = 0.001
        return{'FINISHED'}

    def invoke(self, context, event):
        return self.execute(context)

# Make Specular Material
class BUTTON_OCT_make_specular(bpy.types.Operator):
    bl_idname = "ops.button_make_specular"
    bl_label = "Specular"
    bl_description = "Set Material as Octane Specular"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        mat = active_node_mat(context.material)
        ray = mat.raytrace_transparency

        mat.use_transparency = True
        mat.transparency_method = 'RAYTRACE'
        mat.alpha = 0.5
        if ray.ior == 1.0:
            ray.ior = 1.5
        if mat.specular_intensity == 0.0:
            mat.specular_intensity = 0.8
        if (mat.specular_color.r+mat.specular_color.g+mat.specular_color.b) == 0.0:
            mat.specular_color.r = 0.001
            mat.specular_color.g = 0.001
            mat.specular_color.b = 0.001
        return{'FINISHED'}

    def invoke(self, context, event):
        return self.execute(context)

# IOR Presets
class PRESET_ior_presets(bpy.types.Operator):
    bl_idname = "ops.menu_ior_presets"
    bl_label = "IOR Presets"
    #bl_options = {'REGISTER', 'UNDO'}

    ior_presets = EnumProperty(
        name="ior_presets",
        description="Indices of Refraction",
        items=(
            ("0", "Minimum (1.001)", ""),
            ("1", "Soap bubble (1.100)", ""),
            ("2", "Liquid Methane (1.150)", ""),
            ("3", "Ice (1.310)", ""),
            ("4", "Water (1.326)", ""),
            ("5", "Clear Plastic (1.400)", ""),
            ("6", "Polyacrilate (1.485)", ""),
            ("7", "Acrylic Glass (1.491)", ""),
            ("8", "Standard Glass (1.500)", ""),
            ("9", "Crown Glass (1.510)", ""),
            ("10", "Quartz (1.550)", ""),
            ("11", "Polycarbonate (1.564)", ""),
            ("12", "Saphire (1.760)", ""),
            ("13", "Ruby (1.779)", ""),
            ("14", "Cristal (1.870)", ""),
            ("15", "Diamond (2.417)", "")
            ),
        default= "8")

    def execute(self, context):
        mat = active_node_mat(context.material)
        #ray = mat.raytrace_transparency
        mat.OCT_index = {
            "0": 1.001, "1": 1.100, "2": 1.150,
            "3": 1.310, "4": 1.326, "5": 1.400,
            "6": 1.485, "7": 1.491, "8": 1.500,
            "9": 1.510, "10": 1.550, "11": 1.564,
            "12": 1.760, "13": 1.779, "14": 1.870,
            "15": 2.417 }[self.properties.ior_presets]
        return {'FINISHED'}


