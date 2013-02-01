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

import bpy, os
import octanerender
from octanerender.labels import getLabel
from bpy.props import PointerProperty, StringProperty, BoolProperty, EnumProperty, IntProperty, CollectionProperty, FloatProperty

def addProperties():
    class OctaneTexture(bpy.types.PropertyGroup):
        pass
    class OctaneRenderSettings(bpy.types.PropertyGroup):
        pass

    bpy.utils.register_class(OctaneTexture)
    bpy.utils.register_class(OctaneRenderSettings)

    bpy.types.Scene.octane_render = PointerProperty(type=OctaneRenderSettings, name="Octane Render", description="Octane Render Settings")

# Octane Render Plug-in
    OctaneRenderSettings.panel_mode = EnumProperty(
        items=(
            ("MODE_RENDER", "Image",     "Render still image"),
            ("MODE_EXPORT", "Export",    "Only exports to OBJ/MTL"),
            ("MODE_ANIM",   "Animation", "Render animation"),
            ("MODE_FLY",    "Fly",       "Render camera animation only"),
            #("MODE_BUCKET", "Bucket",    "bucket Rendering"),
            ("MODE_CAMERA", "Cam update",    "Only update camera"),
            ),
        name="Panel Mode",
        description="Render/Export target",
        default="MODE_RENDER")

    OctaneRenderSettings.output_mode = EnumProperty(
        items=(
            ("OUTPUT_PNG",    "PNG",    "Output to png"),
            ("OUTPUT_PNG16",  "PNG16",  "Output to png16"),
            ("OUTPUT_EXR",    "EXR",    "Output to exr"),
            ("OUTPUT_EXR_TM", "EXR-TM", "Output to exr-tm"),
            ),
        name="Output Mode",
        description="Output file format",
        default="OUTPUT_PNG")

    OctaneRenderSettings.import_render = BoolProperty(
        name="Import render in Blender",
        description="Guess what? It will import the render in Blender",
        default = False)

    OctaneRenderSettings.samples_still = IntProperty(
        name='Samples',
        description="Number of samples to render before pulling back the image",
        min=4,
        max=64000,
        default = 1024)

    OctaneRenderSettings.image_output = StringProperty(
        name="Images Output",
        description="Output path for png images",
        maxlen = 512,
        default = "",
        subtype='FILE_PATH')


    OctaneRenderSettings.export_samples_per_image = IntProperty(
        attr="",
        name="Samples",
        description="Samples per image",
        min=4,
        max=64000,
        default=256)

#   OctaneRenderSettings.export_samples_presets = EnumProperty(
#       name="Presets",
#       description="Samples per image presets",
#       items=(
#           ("0",  "Very Low (8)", ""),
#           ("1", "Low (32)", ""),
#           ("2",  "Medium (256)", ""),
#           ("3",  "Medium/High (512)", ""),
#           ("4",  "High (1024)", ""),
#           ("5",  "Very High (4096)", ""),
#           ("6",  "Too High (8192)", ""),
#           ("7",  "Insane (16384)", "")
#           ),
#       default= "2")

    OctaneRenderSettings.export_samples_per_image_old = IntProperty(
        name="Previous Samples",
        description="Previous Samples",
        min=4,
        max=64000,
        default = 256)

    OctaneRenderSettings.bucketX = IntProperty(
        name="Width",
        description="Tiles on X axis",
        min=2,
        max=16,
        default = 2)

    OctaneRenderSettings.bucketY = IntProperty(
        name="Height",
        description="Tiles on Y axis",
        min=2,
        max=16,
        default = 2)

# Octane Project Settings
    OctaneRenderSettings.path = StringProperty(
        name="Project Path",
        description="Requires Absolute Path",
        maxlen = 512,
        default = "",
        subtype='DIR_PATH')

    OctaneRenderSettings.project_name = StringProperty(
        name="Project name",
        description="Octane project name",
        maxlen = 128,
        default = "")

    OctaneRenderSettings.unit_size = EnumProperty(
        name="Native Unit Size",
        description="Native Units",
        items=(
            ("11",  "Miles", ""),
            ("10", "Furlongs", ""),
            ("9",   "Yards", ""),
            ("8",   "Feets", ""),
            ("7",   "Inches", ""),
            ("6",   "Kilometers", ""),
            ("5",   "Hectometers", ""),
            ("4",   "Decameters", ""),
            ("3",   "Meters", ""),
            ("2",   "Decimeters", ""),
            ("1",   "Centimeters", ""),
            ("0",   "Milimeters", "")
            ),
        default= "3")

# Octane Environement Settings

    OctaneRenderSettings.replace_project = BoolProperty(
        name="Create or replace OCS file",
        description="Will create or overwrite the ocs file",
        default = True)

    OctaneRenderSettings.relink_obj = BoolProperty(
        name="Relink OBJ to existing OCS",
        description="Force OBJ mesh file to relink into rendered OCS",
        default = True)

    OctaneRenderSettings.write_ocs = BoolProperty(
        name="Write materials into OCS file",
        description="Will write some parameters directly into the ocs file - EXPERIMENTAL!",
        default = False)

    # Camera Properties
    OctaneRenderSettings.export_camera = BoolProperty(
        name="Export Camera from Scene",
        description="Select camera and click button",
        default = True)

# Octane Export Settings

    # Context
    OctaneRenderSettings.export_sel_only = BoolProperty(
        name="(Ignored)Selection Only",
        description="Only export objects in visible selection. Else export whole scene",
        default = False)

    OctaneRenderSettings.export_remove_hidden = BoolProperty(
        name="Remove Hidden",
        description="Remove objects with restricted rendability from export result",
        default = False)

    OctaneRenderSettings.export_remove_invisible = BoolProperty(
        name="Remove Invisible",
        description="Remove objects with restricted visibility from export result",
        default = False)

    # Output Opyions
    OctaneRenderSettings.export_apply_modifiers = BoolProperty(
        name="Apply Modifiers",
        description="Use transformed mesh data from each object. May break vert order for morph targets",
        default = True)

    OctaneRenderSettings.export_ROTX90=BoolProperty(
        name="Rotate X90",
        description="Rotate on export so Blenders UP is translated into OBJs UP",
        default = True)

    OctaneRenderSettings.export_copy_images = BoolProperty(
        name="Copy Images",
        description="Copy image files to the export directory, never overwrite",
        default = True)

    # Export Options
    OctaneRenderSettings.export_edges = BoolProperty(
        name="Edges",
        description="Edges not connected to faces",
        default = False)

    OctaneRenderSettings.export_tri=BoolProperty(
        name="Triangulate",
        description="Triangulate quads",
        default = False)

    OctaneRenderSettings.export_materials = BoolProperty(
        name="Materials",
        description="Write a separate MTL file with the OBJ",
        default = True)

    OctaneRenderSettings.export_UV=BoolProperty(
        name="UVs",
        description="Export texface UV coords",
        default = True)

    OctaneRenderSettings.export_normals = BoolProperty(
        name="Normals",
        description="Export vertex normal data (Ignored on import)",
        default = False)

    OctaneRenderSettings.export_HQ = BoolProperty(
        name="HQ",
        description="Calculate high quality normals for rendering",
        default = False)

    OctaneRenderSettings.export_polygroups = BoolProperty(
        name="Polygroups",
        description="Export vertex groups as OBJ groups (one group per face approximation)",
        default = False)

    OctaneRenderSettings.export_curves_as_nurbs = BoolProperty(
        name="Nurbs",
        description="Export 3D nurbs curves and polylines as OBJ curves, (bezier not supported)",
        default = False)

# Octane System settings
    OctaneRenderSettings.binary = StringProperty(
        name="Octane Binary",
        description="Requires Absolute Path",
        maxlen = 512,
        default = "",
        subtype='FILE_PATH')

    OctaneRenderSettings.GPU_selector = BoolProperty(
        name="GPU Devices to use",
        description="Custom GPU devices config",
        default = False)

    OctaneRenderSettings.GPU_use_list = StringProperty(
        name=getLabel('GPU_use_list'),
        description="List of GPUs to use (ex: 0 1 2)",
        maxlen = 128,
        default = "")

    OctaneRenderSettings.resolution = BoolProperty(
        name=getLabel('resolution'),
        description="Export resolution",
        default = True)

    OctaneRenderSettings.verbose = BoolProperty(
        name="Verbose logging in console",
        description="Log Octane plug-in events in console",
        default = True)

    OctaneRenderSettings.double_specular = BoolProperty(
        name="Double specularity in MTL file",
        description="Will double the specular value to cancel Octane import logic",
        default = False)

    OctaneRenderSettings.ignore_intensity = BoolProperty(
        name="Force intensity of color values to 1",
        description="Will force the intensity of diffuse/specular to 1",
        default = False)

# Add custom properties to World

# Mesh Preview Kernel
    bpy.types.World.OCT_kernel_use = BoolProperty(
        name="",
        description="Use blender to drive Mesh Preview Kernel",
        default=False)

    bpy.types.World.OCT_kernel = EnumProperty(
        items=(
            ("directlighting", "Direct Lightning", "Use directlight kernel"),
            ("pathtracing", "Path Tracing",     "Use pathtracing kernel"),
            ),
        name="Preview Kernel Manager",
        description="Select which kernel to use",
        default="directlighting")

    # Common settings to DL and PT
    bpy.types.World.OCT_use_rayepsilon = BoolProperty(
        name="",
        description="Override OCS rayepsilon value",
        default = False)

    bpy.types.World.OCT_rayepsilon = FloatProperty(
        name="Ray Epsilon",
        description="Set OCS rayepsilon value",
        min=0.0001, max=0.10, step = 1.0, precision = 4, default=0.001)

    bpy.types.World.OCT_use_filtersize = BoolProperty(
        name="",
        description="Override OCS filtersize value",
        default = False)

    bpy.types.World.OCT_filtersize = FloatProperty(
        name="Filter Size",
        description="Override OCS filtersize value",
        min=1.5, max=8.0, step = 10.0, default=1.5)

    bpy.types.World.OCT_use_alphachannel = BoolProperty(
        name="",
        description="Override OCS alphachannel value",
        default = False)

    bpy.types.World.OCT_alphachannel = EnumProperty(
        items=(
            ("true",  "Use Alpha Channel", "Use Alpha Channel"),
            ("false", "No Alpha Channel",  "Turn off Alpha Channel"),
            ),
        name="Alpha Channel",
        description="Set OCS alphachannel value",
        default = "false")

    bpy.types.World.OCT_use_keep_environment = BoolProperty(
        name="",
        description="Override OCS keep_environment value",
        default = False)

    bpy.types.World.OCT_keep_environment = EnumProperty(
        items=(
            ("true",  "Keep Environment", "Keep Environment"),
            ("false", "Hide Environment", "Hide Environment"),
            ),
        name="Keep Environment",
        description="Set OCS keep_environment value",
        default = "false")

    # DL Settings
    bpy.types.World.OCT_use_speculardepth = BoolProperty(
        name="",
        description="Override OCS speculardepth value",
        default = False)
    bpy.types.World.OCT_speculardepth = IntProperty(
        name="Specular Depth",
        description="Set OCS speculardepth value",
        min=1, max=1024, step = 1, default=5)

    bpy.types.World.OCT_use_glossydepth = BoolProperty(
        name="",
        description="Override OCS glossydepth value",
        default = False)
    bpy.types.World.OCT_glossydepth = IntProperty(
        name="Glossy Depth",
        description="Set OCS glossydepth value",
        min=1, max=1024, step = 1, default=1)

    bpy.types.World.OCT_use_aodist = BoolProperty(
        name="",
        description="Override OCS aodist value",
        default = False)
    bpy.types.World.OCT_aodist = FloatProperty(
        name="AO distance",
        description="Set OCS aodist value",
        min=0.01, max=1024.0, step = 100.0, default=3.0)

    # PT Settings
    bpy.types.World.OCT_use_maxdepth = BoolProperty(
        name="",
        description="Override OCS maxdepth value",
        default = False)
    bpy.types.World.OCT_maxdepth = IntProperty(
        name="Max Depth",
        description="Set OCS maxdepth value",
        min=1, max=2048, step = 1, default=16)

    bpy.types.World.OCT_use_rrprob = BoolProperty(
        name="",
        description="Override OCS rrprob value",
        default = False)
    bpy.types.World.OCT_rrprob = FloatProperty(
        name="RR Prob",
        description="Set OCS rrprob value",
        min=0.0, max=1.0, step = 1.0, default=0.0)

    bpy.types.World.OCT_use_alphashadows = BoolProperty(
        name="",
        description="Override OCS alphashadows value",
        default = False)
    bpy.types.World.OCT_alphashadows = EnumProperty(
        items=(
            ("true",  "Use Alpha Shadows", "Use Alpha Shadows"),
            ("false", "No Alpha Shadows",  "Turn off Alpha Shadows"),
            ),
        name="Alpha Shadows",
        description="Set OCS alphashadows value",
        default = "false")

# Mesh Preview Environment
    bpy.types.World.OCT_environment_use = BoolProperty(
        name="",
        description="Use Blender to drive Mesh Preview Environment",
        default=False)

    bpy.types.World.OCT_environment = EnumProperty(
        items=(
            ("texture environment",  "Texture",  "Use Texture Environment"),
            ("daylight", "Daylight", "Use Daylight Environment"),
            ),
        name="Preview Environment Manager",
        description="Select which environment to use",
        default="texture environment")

    # Common settings
    bpy.types.World.OCT_use_power = BoolProperty(
        name="",
        description="Override OCS environment power value",
        default=False)
    bpy.types.World.OCT_power = FloatProperty(
        name="Power",
        description="Set OCS power value",
        min=0.0, max=1000.0, step = 10.0, default=1.0)

    # Daylight
    bpy.types.World.OCT_active_light = StringProperty(
        name="Sun lamp",
        description="Set a Sun Light Source",
        maxlen = 128,
        default = "")

    bpy.types.World.OCT_use_turbidity = BoolProperty(
        name="",
        description="Override OCS turbidity power value",
        default=False)
    bpy.types.World.OCT_turbidity = FloatProperty(
        name="Turbidity",
        description="Set OCS turbidity value",
        min=0.0, max=16.0, step = 1.0, default=2.20)

    bpy.types.World.OCT_use_northoffset = BoolProperty(
        name="",
        description="Override OCS northoffset power value",
        default=False)
    bpy.types.World.OCT_northoffset = FloatProperty(
        name="North Offset",
        description="Set OCS northoffset value",
        min=-1.0, max=1.0, step = 1.0, default=0.0)

    # Texture
    bpy.types.World.OCT_texture_type = EnumProperty(
        items=(
            ("FLOAT", "Float", "Use Float Environment"),
            ("IMAGE", "Image", "Use Image Environment"),
            ),
        name="Texture type",
        description="Select which kind of texture to use",
        default="FLOAT")

    bpy.types.World.OCT_use_texture_float = BoolProperty(
        name="",
        description="Override OCS texture_float power value",
        default=False)
    bpy.types.World.OCT_texture_float = FloatProperty(
        name="Float",
        description="Set float value",
        min=0.0, max=1.0, step = 1.0, default=1.0)

    bpy.types.World.OCT_use_texture_image = BoolProperty(
        name="",
        description="Override OCS texture_image power value",
        default=False)
    bpy.types.World.OCT_texture_image = StringProperty(
        name="Image File",
        description="Image will NOT be copied",
        maxlen = 512,
        default = "",
        subtype='FILE_PATH')

    bpy.types.World.OCT_use_texture_XY = BoolProperty(
        name="",
        description="Override OCS texture_X/Y value",
        default=False)
    bpy.types.World.OCT_texture_X = FloatProperty(
        name="X Rotation",
        description="Set OCS rotation X value",
        min=-1.0, max=1.0, step = 1.0, precision = 3, default=0.0)
    bpy.types.World.OCT_texture_Y = FloatProperty(
        name="Y Rotation",
        description="Set OCS rotation Y value",
        min=-1.0, max=1.0, step = 1.0, precision = 3, default=0.0)

# Mesh Preview Imager
    bpy.types.World.OCT_imager_use = BoolProperty(
        name="",
        description="Use Blender to drive Mesh Preview Imager",
        default=False)

    bpy.types.World.OCT_use_exposure = BoolProperty(
        name="",
        description="Override OCS exposure value",
        default=False)
    bpy.types.World.OCT_exposure = FloatProperty(
        name="Exposure",
        description="Set OCS exposure value",
        min=0.0, max=4096.0, step = 1.0, precision = 2, default=1.0)

    bpy.types.World.OCT_use_fstop = BoolProperty(
        name="",
        description="Override OCS fstop value",
        default=False)
    bpy.types.World.OCT_fstop = FloatProperty(
        name="F-Stop",
        description="Set OCS fstop value",
        min=0.0, max=64.0, step = 1.0, precision = 2, default=2.8)

    bpy.types.World.OCT_use_ISO = BoolProperty(
        name="",
        description="Override OCS ISO value",
        default=False)
    bpy.types.World.OCT_ISO = FloatProperty(
        name="ISO",
        description="Set OCS ISO value",
        min=1.0, max=800.0, step = 100.0, precision = 2, default=100.0)

    bpy.types.World.OCT_use_gamma = BoolProperty(
        name="",
        description="Override OCS gamma value",
        default=False)
    bpy.types.World.OCT_gamma = FloatProperty(
        name="Gamma",
        description="Set OCS gamma value",
        min=0.10, max=32.0, step = 1.0, precision = 2, default=1.0)

    bpy.types.World.OCT_use_response = BoolProperty(
        name="",
        description="Override OCS response value",
        default=False)
    bpy.types.World.OCT_response = EnumProperty(
        name="Response",
        description="Camera Response",
        items=(
            ("99",  "Agfacolor Futura 100CD", ""),
            ("100", "Agfacolor Futura 200CD", ""),
            ("101", "Agfacolor Futura 400CD", ""),
            ("102", "Agfacolor Futura II 100CD", ""),
            ("103", "Agfacolor Futura II 200CD", ""),
            ("104", "Agfacolor Futura II 400CD", ""),
            ("105", "Agfacolor HDC 100 plusCD", ""),
            ("106", "Agfacolor HDC 200 plusCD", ""),
            ("107", "Agfacolor HDC 400 plusCD", ""),
            ("108", "Agfacolor Optima II 100CD", ""),
            ("109", "Agfacolor Optima II 200CD", ""),
            ("110", "Agfacolor ultra 050 CD", ""),
            ("111", "Agfacolor Vista 100CD", ""),
            ("112", "Agfacolor Vista 200CD", ""),
            ("113", "Agfacolor Vista 400CD", ""),
            ("114", "Agfacolor Vista 800CD", ""),
            ("115", "Agfachrome CT precisa 100CD", ""),
            ("116", "Agfachrome CT precisa 200CD", ""),
            ("117", "Agfachrome RSX2 050CD", ""),
            ("118", "Agfachrome RSX2 100CD", ""),
            ("119", "Agfachrome RSX2 200CD", ""),
            ("201", "Advantix 100CD", ""),
            ("202", "Advantix 200CD", ""),
            ("203", "Advantix 400CD", ""),
            ("204", "Gold 100CD", ""),
            ("205", "Gold 200CD", ""),
            ("206", "Max Zoom 800CD", ""),
            ("207", "Portra 100TCD", ""),
            ("208", "Portra 160NCCD", ""),
            ("209", "Portra 160VCCD", ""),
            ("210", "Portra 800CD", ""),
            ("211", "Portra 400VCCD", ""),
            ("212", "Portra 400NCCD", ""),
            ("213", "Ektachrome 100 plusCD", ""),
            ("214", "Ektachrome 320TCD", ""),
            ("215", "Ektachrome 400XCD", ""),
            ("216", "Ektachrome 64CD", ""),
            ("217", "Ektachrome 64TCD", ""),
            ("218", "Ektachrome E100SCD", ""),
            ("219", "Ektachrome 100CD", ""),
            ("220", "Kodachrome 200CD", ""),
            ("221", "Kodachrome 25", ""),
            ("222", "Kodachrome 64CD", ""),
            ("301", "F125CD", ""),
            ("302", "F250CD", ""),
            ("303", "F400CD", ""),
            ("304", "FCICD", ""),
            ("305", "dscs315_1", ""),
            ("306", "dscs315_2", ""),
            ("307", "dscs315_3", ""),
            ("308", "dscs315_4", ""),
            ("309", "dscs315_5", ""),
            ("310", "dscs315_6", ""),
            ("311", "FP2900Z", ""),
            ("400", "Linear/Off", ""),
            ),
        default= "105")

    bpy.types.World.OCT_use_vignetting = BoolProperty(
        name="",
        description="Override OCS vignetting value",
        default=False)
    bpy.types.World.OCT_vignetting = FloatProperty(
        name="Vignetting",
        description="Set OCS vignetting value",
        min=0.0, max=1.0, step = 1.0, precision = 2, default=0.3)

    bpy.types.World.OCT_use_saturation = BoolProperty(
        name="",
        description="Override OCS saturation value",
        default=False)
    bpy.types.World.OCT_saturation = FloatProperty(
        name="Saturation",
        description="Set OCS saturation value",
        min=0.0, max=4.0, step = 1.0, precision = 2, default=1.0)

    bpy.types.World.OCT_use_hotpixel_removal = BoolProperty(
        name="",
        description="Override OCS hotpixel_removal value",
        default=False)
    bpy.types.World.OCT_hotpixel_removal = FloatProperty(
        name="Hotpixel Removal",
        description="Set OCS hotpixel_removal value",
        min=0.0, max=1.0, step = 1.0, precision = 2, default=1.0)

    bpy.types.World.OCT_use_premultiplied_alpha = BoolProperty(
        name="",
        description="Override OCS premultiplied_alpha value",
        default = False)
    bpy.types.World.OCT_premultiplied_alpha = EnumProperty(
        items=(
            ("true",  "Enable Premult. Alpha", "Enable Premultiplied Alpha"),
            ("false", "Disable Premult. Alpha",  "Disable Premultiplied Alpha"),
            ),
        name="Premultiplied Alpha",
        description="Set OCS premultiplied_alpha value",
        default = "false")

# Add custom properties to Camera

    bpy.types.Camera.OCT_use_lens_aperture = BoolProperty(
        name=getLabel('lens_aperture'),
        description="Lens Aperture",
        default = False)

    bpy.types.Camera.OCT_lens_aperture = FloatProperty(
        attr="",
        name="Value",
        description="Value",
        min=0.01, max=100, step = 100.0, default=1.0)

    bpy.types.Camera.OCT_use_camera_motion = BoolProperty(
        name="Camera motion",
        description="Use camera motion for animation",
        default = False)

    bpy.types.Camera.OCT_interpolate_frame = EnumProperty(
        name=getLabel('interpolate_frame'),
        description="Interpolate frame",
        items=(
            ("0",  "Next Frame", ""),
            ("1", "Previous Frame", "")
            ),
        default= "0")

# Add custom material properties

    bpy.types.Material.OCT_material_type = EnumProperty(
        name="Material type",
        description="Octane material type",
        items=(
            ("diffuse",  "Diffuse", ""),
            ("glossy",   "Glossy", ""),
            ("specular", "Specular", ""),
            ),
        default= "glossy")

    bpy.types.Material.OCT_index = FloatProperty(
        name="Indice of Refraction",
        description="IOR",
        min=1.001, max=8.0, step = 1.0, default=1.5,precision=3)

    bpy.types.Material.OCT_roughnessfloat = FloatProperty(
        name="Roughness",
        description="Roughness",
        min=0.0000001, max=1.0, step = 1.0, default=0.001,precision=7)

    bpy.types.Material.OCT_filmwidth = FloatProperty(
        name="Film Width",
        description="Film Width",
        min=0.0, max=1.0, step = 1.0, default=0.0,precision=3)

    bpy.types.Material.OCT_filmindex = FloatProperty(
        name="Film Index",
        description="Film Index",
        min=1.001, max=8.0, step = 1.0, default=1.5,precision=3)

    bpy.types.Material.OCT_smooth = BoolProperty(
        name="Smooth",
        description="Smooth normals",
        default = True)

    bpy.types.Material.OCT_emitter_type = EnumProperty(
        name="Emitter type",
        description="Octane emitter type",
        items=(
            ("null emission", "null emission", ""),
            ("blackbody", "BlackBody", ""),
            ("texture",   "Texture", ""),
            ),
        default= "null emission")

    bpy.types.Material.OCT_temperature = FloatProperty(
        name="Temperature",
        description="Emitter Temperature",
        min=500, max=12000, step = 1000.0, default=6250,precision=0)

    bpy.types.Material.OCT_power = FloatProperty(
        name="Power",
        description="Emitter Power",
        min=0.0, max=100.0, step = 1.0, default=1.0)

    bpy.types.Material.OCT_normalize = BoolProperty(
        name="Normalize",
        description="Emitter Normalize",
        default=False)



    bpy.types.Material.OCT_diffuse  = PointerProperty(type=OctaneTexture, name="diffuse", description="Octane Texture")
    bpy.types.Material.OCT_specular = PointerProperty(type=OctaneTexture, name="specular", description="Octane Texture")
    bpy.types.Material.OCT_bump = PointerProperty(type=OctaneTexture, name="bump", description="Octane Texture")
    bpy.types.Material.OCT_normal = PointerProperty(type=OctaneTexture, name="normal", description="Octane Texture")
    bpy.types.Material.OCT_opacity = PointerProperty(type=OctaneTexture, name="opacity", description="Octane Texture")
    bpy.types.Material.OCT_emission = PointerProperty(type=OctaneTexture, name="emission", description="Octane Texture")
    bpy.types.Material.OCT_roughness = PointerProperty(type=OctaneTexture, name="roughness", description="Octane Texture")

    OctaneTexture.diffuse = EnumProperty(
        name="Diffuse",
        description="Octane texture type",
        items=(
            ("RGBspectrum",  "RGBspectrum", ""),
            ("image",        "image", ""),
            ("alphaimage",   "alphaimage", ""),
            ("floatimage",   "floatimage", ""),
            ),
        default = "RGBspectrum")

    OctaneTexture.specular = EnumProperty(
        name="Specular",
        description="Octane texture type",
        items=(
            ("RGBspectrum",  "RGBspectrum", ""),
            ("image",        "image", ""),
            ("alphaimage",   "alphaimage", ""),
            ("floatimage",   "floatimage", ""),
            ("floattexture", "floattexture", ""),
            ),
        default = "RGBspectrum")

    OctaneTexture.bump = EnumProperty(
        name="Bump input",
        description="Octane texture type",
        items=(
            ("none",  "none", ""),
            ("floatimage",   "floatimage", ""),
            ),
        default = "none")

    OctaneTexture.normal = EnumProperty(
        name="Normal input",
        description="Octane texture type",
        items=(
            ("none",  "none", ""),
            ("image",        "image", ""),
            ),
        default = "none")

    OctaneTexture.opacity = EnumProperty(
        name="Opacity input",
        description="Octane texture type",
        items=(
            ("image",        "image", ""),
            ("alphaimage",   "alphaimage", ""),
            ("floatimage",   "floatimage", ""),
            ("floattexture", "floattexture", ""),
            ),
        default = "floattexture")

    OctaneTexture.emission = EnumProperty(
        name="Texture type",
        description="Octane texture type",
        items=(
            ("image",        "image", ""),
            ("alphaimage",   "alphaimage", ""),
            ("floatimage",   "floatimage", ""),
            ("RGBspectrum", "RGBspectrum", ""),
            ),
        default = "RGBspectrum")

    OctaneTexture.roughness = EnumProperty(
        name="Texture type",
        description="Octane texture type",
        items=(
            ("image",        "image", ""),
            ("alphaimage",   "alphaimage", ""),
            ("floatimage",   "floatimage", ""),
            ("floattexture", "floattexture", ""),
            ),
        default = "floattexture")

    OctaneTexture.floattexture = FloatProperty(
            name="Float",
            description="Float",
            min=0.0, max=1.0, step = 1, default=1.0)

    OctaneTexture.texture = StringProperty(
            name="Texture",
            description="Octane texture",
            maxlen = 128,
            default = "")

    OctaneTexture.power = FloatProperty(
            name="Power",
            description="Power",
            min=0.0, max=1.0, step = 1, default=1.0)

    OctaneTexture.gamma = FloatProperty(
            name="Gamma",
            description="Gamma",
            min=0.1, max=8.0, step = 10, default=2.2)

    OctaneTexture.scale = FloatProperty(
            name="Scale",
            description="Scale",
            min=0.0, max=1000.0, step = 10, default=1.0)

    OctaneTexture.invert = BoolProperty(
            name="Invert",
            description="Invert",
            default = False)

    #bpy.types.Material.OctaneTexture = CollectionProperty(type=OctaneTexture)
    #bpy.utils.register_class(OctaneTexture)
    #bpy.types.Material.OCT_diffuse = OctaneTexture("Diffuse")
    #bpy.types.Material.OCT_diffuse = PointerProperty(type=OctaneTexture)
    #OCT_dif = CollectionProperty(name="Diffuse", type=OctaneTexture)
    #bpy.types.Material.OCT_diffuse = PointerProperty(name="OCT_d", type=OCT_dif)
    #~ bpy.types.Material.OCT_specular = PointerProperty(type=OctaneTexture, name="OCT_s")
    #~ bpy.types.Material.OCT_normal = PointerProperty(type=OctaneTexture, name="OCT_n")
    #~ bpy.types.Material.OCT_bump = PointerProperty(type=OctaneTexture, name="OCT_b")
    #~ bpy.types.Material.OCT_opacity = PointerProperty(type=OctaneTexture, name="OCT_o")
    #~ bpy.types.Material.OCT_emitter = PointerProperty(type=OctaneTexture, name="OCT_e")


def register():
    bpy.utils.register_module(__name__)

def unregister():
    del bpy.types.Material.OCT_diffuse
    del bpy.types.Material.OCT_specular
    del bpy.types.Material.OCT_normal
    del bpy.types.Material.OCT_bump
    del bpy.types.Material.OCT_opacity
    del bpy.types.Material.OCT_emission

    bpy.utils.unregister_module(__name__)


