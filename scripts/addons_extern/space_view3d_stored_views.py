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

bl_info = {
    "name": "Stored Views",
    "description": "Save and restore User defined views, pov, layers and display configs.",
    "author": "nfloyd",
    "version": (0, 2, 2),
    "blender": (2, 5, 7),
    "api": 36339,
    "location": "View3D > Properties > Stored Views",
    "warning": 'beta release',
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.5/Py/Scripts/3D_interaction/stored_views",
    "tracker_url": "http://projects.blender.org/tracker/index.php?func=detail&aid=27476",
    "category": "3D View"}

# ACKNOWLEDGMENT
# ==============
# import/export functionality is mostly based
#   on Bart Crouch's Theme Manager Addon


# CHANGELOG
# =========
# 0.1.0 : _ initial release
# 0.2.0 : _ quadview support
#         _ import/export functionality from/to preset files
#           inspired - that is an euphemism - from Bart Crouch Theme Manager Addon
#         _ import data from an another scene
# 0.2.1 : _ improved previous / toggle logic
#         _ fix : object reference works if name has changed
#         _ fix for python api change 36710
#         _ checks on data import (scene or preset file)
# 0.2.2 : _ fixed : previous / toggle
#         _ io filtering
#         _ stored views name display in 3d view (experimental)
#         _ UI tweaks
#         _ generate unique view name
#         _ added wiki and tracker url

# TODO: quadview complete support : investigate. Where's the data?
# TODO: lock_camera_and_layers. investigate usage
# TODO: list reordering

import gzip
import os
import pickle
import shutil
import hashlib

import bpy
import blf

try:  # < r36710
    from io_utils import ExportHelper, ImportHelper
except:  # >= r36710
    from bpy_extras.io_utils import ExportHelper, ImportHelper

# If view name display is enabled,
#   it will check periodically if the view has been modified
#   since last set.
#   VIEW_MODIFIED_TIMER is the time in seconds between these checks.
#   It can be increased, if the view become sluggish
VIEW_MODIFIED_TIMER = 1


def get_preset_path():
    # locate stored_views preset folder
    paths = bpy.utils.preset_paths("stored_views")
    if not paths:
        # stored_views preset folder doesn't exist, so create it
        paths = [os.path.join(bpy.utils.user_resource('SCRIPTS'), "presets",
            "stored_views")]
        if not os.path.exists(paths[0]):
            os.makedirs(paths[0])

    return(paths)


def stored_views_sanitize_data(scene, clear_swap=False):
    modes = ['POV', 'VIEWS', 'DISPLAY', 'LAYERS']
    for mode in modes:
        data = stored_views_get_data(mode, scene)
        if clear_swap:
            while len(data.swap) > 0:
                data.swap.remove(0)
        check_objects_references(mode, data.list)


def check_objects_references(mode, list):
    for key, item in list.items():
        if mode == 'POV' or mode == 'VIEWS':
            if mode == 'VIEWS':
                item = item.pov

            if item.perspective == "CAMERA":
                try:
                    camera = bpy.data.objects[item.camera_name]
                    item.camera_pointer = camera.as_pointer()
                except:
                    try:  # pick a default camera TODO: ask to pick?
                        camera = bpy.data.cameras[0]
                        item.camera_name = camera.name
                        item.camera_pointer = camera.as_pointer()
                    except:  # couldn't find a camera in the scene
                        list.remove(key)  # TODO: create one instead?

            if item.lock_object_name != "":
                try:  # get object from name string
                    object = bpy.data.objects[item.lock_object_name]
                    item.lock_object_pointer = object.as_pointer()
                except:
                    item.lock_object_name = ""


def initialize():
    bpy.types.Scene.stored_views = bpy.props.PointerProperty(type=StoredViewsData)
    scenes = bpy.data.scenes
    for scene in scenes:
        stored_views_sanitize_data(scene, clear_swap=True)


class PointOfViewItem(bpy.types.PropertyGroup):
    distance = bpy.props.FloatProperty()
    location = bpy.props.FloatVectorProperty(subtype='TRANSLATION')
    rotation = bpy.props.FloatVectorProperty(subtype='QUATERNION',
                                             size=4)
    name = bpy.props.StringProperty()
    perspective = bpy.props.EnumProperty(items=[('PERSP', '', ''),
                                                ('ORTHO', '', ''),
                                                ('CAMERA', '', '')])
    lens = bpy.props.FloatProperty()
    clip_start = bpy.props.FloatProperty()
    clip_end = bpy.props.FloatProperty()
    lock_cursor = bpy.props.BoolProperty()
    cursor_location = bpy.props.FloatVectorProperty()
    view_matrix_md5 = bpy.props.StringProperty()
    camera_name = bpy.props.StringProperty()
    camera_type = bpy.props.StringProperty()
    camera_pointer = bpy.props.IntProperty()
    lock_object_name = bpy.props.StringProperty()
    lock_object_pointer = bpy.props.IntProperty()


class PointOfViewsData(bpy.types.PropertyGroup):
    list = bpy.props.CollectionProperty(type=PointOfViewItem)
    swap = bpy.props.CollectionProperty(type=PointOfViewItem)
    current_index = bpy.props.IntProperty()
    previous_index = bpy.props.IntProperty()


class LayersItem(bpy.types.PropertyGroup):
    view_layers = bpy.props.BoolVectorProperty(size=20)
    scene_layers = bpy.props.BoolVectorProperty(size=20)
    lock_camera_and_layers = bpy.props.BoolProperty()
    name = bpy.props.StringProperty()


class LayersData(bpy.types.PropertyGroup):
    list = bpy.props.CollectionProperty(type=LayersItem)
    swap = bpy.props.CollectionProperty(type=LayersItem)
    current_index = bpy.props.IntProperty()
    previous_index = bpy.props.IntProperty()


class DisplayItem(bpy.types.PropertyGroup):
    name = bpy.props.StringProperty()
    viewport_shade = bpy.props.EnumProperty(items=[('BOUNDBOX', 'BOUNDBOX', 'BOUNDBOX'),
                                                   ('WIREFRAME', 'WIREFRAME', 'WIREFRAME'),
                                                   ('SOLID', 'SOLID', 'SOLID'),
                                                   ('TEXTURED', 'TEXTURED', 'TEXTURED')])
    show_only_render = bpy.props.BoolProperty()
    show_outline_selected = bpy.props.BoolProperty()
    show_all_objects_origin = bpy.props.BoolProperty()
    show_relationship_lines = bpy.props.BoolProperty()
    show_floor = bpy.props.BoolProperty()
    show_axis_x = bpy.props.BoolProperty()
    show_axis_y = bpy.props.BoolProperty()
    show_axis_z = bpy.props.BoolProperty()
    grid_lines = bpy.props.IntProperty()
    grid_scale = bpy.props.FloatProperty()
    grid_subdivisions = bpy.props.IntProperty()
    material_mode = bpy.props.EnumProperty(items=[('TEXTURE_FACE', '', ''),
                                                  ('MULTITEXTURE', '', ''),
                                                  ('GLSL', '', '')])
    show_textured_solid = bpy.props.BoolProperty()
    quad_view = bpy.props.BoolProperty()
    lock_rotation = bpy.props.BoolProperty()
    show_sync_view = bpy.props.BoolProperty()
    use_box_clip = bpy.props.BoolProperty()


class DisplaysData(bpy.types.PropertyGroup):
    list = bpy.props.CollectionProperty(type=DisplayItem)
    swap = bpy.props.CollectionProperty(type=DisplayItem)
    current_index = bpy.props.IntProperty()
    previous_index = bpy.props.IntProperty()


class ViewItem(bpy.types.PropertyGroup):
    pov = bpy.props.PointerProperty(type=PointOfViewItem)
    layers = bpy.props.PointerProperty(type=LayersItem)
    display = bpy.props.PointerProperty(type=DisplayItem)
    name = bpy.props.StringProperty()


class ViewsData(bpy.types.PropertyGroup):
    list = bpy.props.CollectionProperty(type=ViewItem)
    swap = bpy.props.CollectionProperty(type=ViewItem)
    current_index = bpy.props.IntProperty()
    previous_index = bpy.props.IntProperty()


class IOFilters(bpy.types.PropertyGroup):
    views = bpy.props.BoolProperty(name="Views", default=True)
    point_of_views = bpy.props.BoolProperty(name="POVs", default=True)
    layers = bpy.props.BoolProperty(name="Layers", default=True)
    displays = bpy.props.BoolProperty(name="Displays", default=True)


class StoredViewsSettings(bpy.types.PropertyGroup):
    mode = bpy.props.EnumProperty(name="Mode",
                                  items=[('VIEWS', 'Views', ''),
                                         ('POV', 'POV', ''),
                                         ('LAYERS', 'Layers', ''),
                                         ('DISPLAY', 'Display', '')],
                                  default='VIEWS')
    show_view_name = bpy.props.BoolProperty(default=False)
    show_io_panel = bpy.props.BoolProperty(default=False)
    show_settings_panel = bpy.props.BoolProperty(default=False)
    io_filters = bpy.props.PointerProperty(type=IOFilters)


class StoredViewsData(bpy.types.PropertyGroup):
    point_of_views = bpy.props.PointerProperty(type=PointOfViewsData)
    layers = bpy.props.PointerProperty(type=LayersData)
    displays = bpy.props.PointerProperty(type=DisplaysData)
    views = bpy.props.PointerProperty(type=ViewsData)
    settings = bpy.props.PointerProperty(type=StoredViewsSettings)
    view_modified = bpy.props.BoolProperty()


class VIEW3D_stored_views_save(bpy.types.Operator):
    bl_idname = "stored_views.save"
    bl_label = "Save Current"
    bl_description = "Save the view 3d current state"

    index = bpy.props.IntProperty()

    def execute(self, context):
        scn = context.scene
        sv = scn.stored_views
        data = stored_views_get_data()

        if self.index == -1:  # new item
            item = data.list.add()
            data.previous_index = data.current_index
            data.current_index = len(data.list) - 1
            # generate new name
            default_name = "unnamed"
            names = []
            for i in data.list:
                i_name = i.name
                if i_name.startswith(default_name):
                    names.append(i_name)
            names.sort()
            try:
                l_name = names[-1]
                post_fix = l_name.rpartition('.')[2]
                if post_fix.isnumeric():
                    post_fix = str(int(post_fix) + 1).zfill(3)
                else:
                    if post_fix == default_name:
                        post_fix = "001"
                item.name = default_name + "." + post_fix
            except:
                item.name = default_name
        else:
            item = data.list[self.index]
            data.previous_index = data.current_index
            data.current_index = self.index
        stored_views_save_item(item)

        if "stored_views_draw_started" not in context.window_manager and sv.settings.show_view_name:
            init_draw()
        sv.view_modified = False
        return {'FINISHED'}


class VIEW3D_stored_views_set(bpy.types.Operator):
    bl_idname = "stored_views.set"
    bl_label = "Set"
    bl_description = "Update the view 3D according to this view"

    index = bpy.props.IntProperty()

    def execute(self, context):
        data = stored_views_get_data()
        item_stored = data.list[self.index]
        data.previous_index = data.current_index
        data.current_index = self.index

        stored_views_update_view3D(item_stored)
        data = stored_views_get_data()
        if "stored_views_draw_started" not in context.window_manager and context.scene.stored_views.settings.show_view_name:
            init_draw()

        context.scene.stored_views.view_modified = False
        return {'FINISHED'}


class VIEW3D_stored_views_delete(bpy.types.Operator):
    bl_idname = "stored_views.delete"
    bl_label = "Delete"
    bl_description = "Delete this view"

    index = bpy.props.IntProperty()

    def execute(self, context):

        data = stored_views_get_data()

        if data.current_index > self.index:
            data.current_index -= 1
        elif data.current_index == self.index:
            if data.previous_index == -1:
                data.current_index = -2
                stored_views_save_item(data.swap[2])
            else:
                data.current_index = -1
                stored_views_save_item(data.swap[1])

        if data.previous_index > self.index:
            data.previous_index -= 1
        elif data.previous_index == self.index:
            if data.current_index == -1:
                data.previous_index = -2
                stored_views_save_item(data.swap[2])
            else:
                data.previous_index = -1
                stored_views_save_item(data.swap[1])
        data.list.remove(self.index)

        return {'FINISHED'}


class VIEW3D_stored_views_previous(bpy.types.Operator):
    bl_idname = "stored_views.previous"
    bl_label = "Previous"
    bl_description = "Toggle between views"

    def execute(self, context):

        data = stored_views_get_data()

        is_view_modified = stored_views_view3D_modified()
        context.scene.stored_views.view_modified = False
        previous_index = int
        if is_view_modified:
            # current index is actual previous index
            previous_index = data.current_index
        else:
            previous_index = data.previous_index
        # get previous item
        previous_item = None
        if previous_index == -1:  # swap
            previous_item = data.swap[1]
        elif previous_index == -2:
            previous_item = data.swap[2]
        else:
            previous_item = data.list[previous_index]

        # handle to view before update
        current_index = int
        if is_view_modified:
            if previous_index == -1:
                stored_views_save_item(data.swap[2])  # save to temp
                data.swap[2].name = ""
                current_index = -2
            else:
                stored_views_save_item(data.swap[1])  # save to temp
                data.swap[1].name = ""
                current_index = -1
        else:
            current_index = data.current_index

        # update view with previous item
        stored_views_update_view3D(previous_item)

        # update indexes
        data.current_index = previous_index
        data.previous_index = current_index

        return {'FINISHED'}


class VIEW3D_stored_views_export(bpy.types.Operator, ExportHelper):
    bl_idname = "stored_views.export"
    bl_label = "Export Stored Views preset"
    bl_description = "Export the current Stored Views to a .blsv preset file"

    filename_ext = ".blsv"
    filepath = bpy.props.StringProperty(\
        default=os.path.join(get_preset_path()[0], "untitled"))
    filter_glob = bpy.props.StringProperty(default="*.blsv", options={'HIDDEN'})
    preset_name = bpy.props.StringProperty(name="Preset name",
        default="",
        description="Name of the stored views preset")

    def execute(self, context):
        # create dictionary with all information
        dump = {"info": {}, "data": {}}
        dump["info"]["script"] = bl_info['name']
        dump["info"]["script_version"] = bl_info['version']
        dump["info"]["version"] = bpy.app.version
        dump["info"]["build_revision"] = bpy.app.build_revision
        dump["info"]["preset_name"] = self.preset_name

        # defaults
        if not self.preset_name:
            dump["info"]["preset_name"] = "Custom Preset"

        # get current stored views settings
        scene = bpy.context.scene
        sv = scene.stored_views

        def dump_view_list(dict, list):
            if str(type(list)) == "<class 'bpy_prop_collection_idprop'>":
                for i, struct_dict in enumerate(list):
                    dict[i] = {"name": str,
                               "pov": {},
                               "layers": {},
                               "display": {}}
                    dict[i]["name"] = struct_dict.name
                    dump_item(dict[i]["pov"], struct_dict.pov)
                    dump_item(dict[i]["layers"], struct_dict.layers)
                    dump_item(dict[i]["display"], struct_dict.display)

        def dump_list(dict, list):
            if str(type(list)) == "<class 'bpy_prop_collection_idprop'>":
                for i, struct in enumerate(list):
                    dict[i] = {}
                    dump_item(dict[i], struct)

        def dump_item(dict, struct):
            for prop in struct.bl_rna.properties:
                if prop.identifier == "rna_type":
                    # not a setting, so skip
                    continue
                val = getattr(struct, prop.identifier)
                if str(type(val)) in ["<class 'bpy_prop_array'>",
                                      "<class 'mathutils.Quaternion'>",
                                      "<class 'mathutils.Vector'>"]:
                    # array
                    dict[prop.identifier] = [v \
                        for v in val]
                else:
                    # single value
                    dict[prop.identifier] = val

        io_filters = sv.settings.io_filters
        dump["data"] = {"point_of_views": {},
                        "layers": {},
                        "displays": {},
                        "views": {}}

        others_data = [(dump["data"]["point_of_views"], sv.point_of_views.list, io_filters.point_of_views),
                       (dump["data"]["layers"], sv.layers.list, io_filters.layers),
                       (dump["data"]["displays"], sv.displays.list, io_filters.displays)]
        for list_data in others_data:
            if list_data[2] == True:
                dump_list(list_data[0], list_data[1])

        views_data = (dump["data"]["views"], sv.views.list)
        if io_filters.views == True:
            dump_view_list(views_data[0], views_data[1])

        # save to file
        filepath = self.filepath
        filepath = bpy.path.ensure_ext(filepath, self.filename_ext)
        file = gzip.open(filepath, mode='w')
        pickle.dump(dump, file)
        file.close()
        stored_views_load_presets()

        return{'FINISHED'}


class VIEW3D_stored_views_import(bpy.types.Operator, ImportHelper):
    bl_idname = "stored_views.import"
    bl_label = "Import Stored Views preset"
    bl_description = "Import a .blsv preset file to the current Stored Views"

    filename_ext = ".blsv"
    filter_glob = bpy.props.StringProperty(default="*.blsv", options={'HIDDEN'})
    replace = bpy.props.BoolProperty(name="Replace",
                                     default=True,
                                     description="Replace current stored views, otherwise append")

    def execute(self, context):
        # apply chosen preset
        if self.replace:
            bpy.ops.stored_views.replace(filepath=self.filepath)
        else:
            bpy.ops.stored_views.append(filepath=self.filepath)
        # copy preset to presets folder
        filename = os.path.basename(self.filepath)
        try:
            shutil.copyfile(self.filepath,
                os.path.join(get_preset_path()[0], filename))
        except:
            self.report('ERROR', "Stored Views: preset applied, but installing failed (preset already exists?)")
            return{'CANCELLED'}
        # reload presets list
        stored_views_load_presets()

        return{'FINISHED'}


class VIEW3D_stored_views_append(bpy.types.Operator):
    bl_idname = "stored_views.append"
    bl_label = "Append Stored Views preset"
    bl_description = "Append preset to current stored views"

    filepath = bpy.props.StringProperty(name="File Path",
                                        description="Filepath of preset",
                                        maxlen=1024,
                                        default="",
                                        subtype='FILE_PATH')

    def execute(self, context):
        # filepath should always be given
        if not self.filepath:
            self.report("ERROR", "Could not find preset")
            return{'CANCELLED'}

        # load file
        try:
            file = gzip.open(self.filepath, mode='r')
            dump = pickle.load(file)
            file.close()
            dump["info"]["script"]
        except:
            self.report("ERROR", "Could not read stored views preset")
            return{'CANCELLED'}

        stored_views_apply_preset(dump, replace=False)

        return{'FINISHED'}


class VIEW3D_stored_views_append_from_scene(bpy.types.Operator):
    bl_idname = "stored_views.append_from_scene"
    bl_label = "Append stored views of scene"
    bl_description = "Append current stored views with those from another scene"

    scene_name = bpy.props.StringProperty(name="Scene Name",
                                        description="A current blend scene",
                                        default="")

    def execute(self, context):
        # filepath should always be given
        if not self.scene_name:
            self.report("ERROR", "Could not find scene")
            return{'CANCELLED'}

        stored_views_apply_from_scene(self.scene_name, replace=False)

        return{'FINISHED'}


class VIEW3D_stored_views_replace(bpy.types.Operator):
    bl_idname = "stored_views.replace"
    bl_label = "Replace Stored Views config"
    bl_description = "Replace current stored views data by a new preset"

    filepath = bpy.props.StringProperty(name="File Path",
                                        description="Filepath of preset",
                                        maxlen=1024,
                                        default="",
                                        subtype='FILE_PATH')

    def execute(self, context):
        # filepath should always be given
        if not self.filepath:
            self.report("ERROR", "Could not find preset")
            return{'CANCELLED'}

        # load file
        try:
            file = gzip.open(self.filepath, mode='r')
            dump = pickle.load(file)
            file.close()
            dump["info"]["script"]
        except:
            self.report("ERROR", "Could not read stored views preset")
            return{'CANCELLED'}

        stored_views_apply_preset(dump, replace=True)

        return{'FINISHED'}


class VIEW3D_stored_views_replace_from_scene(bpy.types.Operator):
    bl_idname = "stored_views.replace_from_scene"
    bl_label = "Replace stored views from scene"
    bl_description = "Replace current stored views by those from another scene"

    scene_name = bpy.props.StringProperty(name="Scene Name",
                                        description="A current blend scene",
                                        default="")

    def execute(self, context):
        # filepath should always be given
        if not self.scene_name:
            self.report("ERROR", "Could not find scene")
            return{'CANCELLED'}

        stored_views_apply_from_scene(self.scene_name, replace=True)

        return{'FINISHED'}

# FUNCTIONS


def stored_views_get_data(mode=None, scene=None):
    if scene == None:
        scene = bpy.context.scene
    stored_views = scene.stored_views
    if mode == None:
        mode = stored_views.settings.mode

    if mode == 'VIEWS':
        data = stored_views.views
    elif mode == 'POV':
        data = stored_views.point_of_views
    elif mode == 'LAYERS':
        data = stored_views.layers
    elif mode == 'DISPLAY':
        data = stored_views.displays

    if len(data.swap) == 0:  # swap empty
        for i in range(3):  # initialize
            data.swap.add()

    return data


def stored_views_save_item(item):
    context = bpy.context
    scene = context.scene
    view3d = context.space_data
    mode = scene.stored_views.settings.mode

    if mode == 'VIEWS' or mode == 'POV':
        pov_item = item
        if mode == 'VIEWS':
            pov_item = item.pov
        region3d = view3d.region_3d
        pov_item.distance = region3d.view_distance
        pov_item.location = region3d.view_location
        pov_item.rotation = region3d.view_rotation
        pov_item.view_matrix_md5 = stored_views_get_view_matrix_md5()
        pov_item.perspective = region3d.view_perspective
        pov_item.lens = view3d.lens
        pov_item.clip_start = view3d.clip_start
        pov_item.clip_end = view3d.clip_end

        if region3d.view_perspective == 'CAMERA':
            pov_item.camera_type = view3d.camera.type  # type : 'CAMERA' or 'MESH'
            pov_item.camera_name = view3d.camera.name  # store string instead of object
            pov_item.camera_pointer = view3d.camera.as_pointer()
        if view3d.lock_object != None:
            pov_item.lock_object_name = view3d.lock_object.name  # idem
            pov_item.lock_object_pointer = view3d.lock_object.as_pointer()  # idem

        pov_item.lock_cursor = view3d.lock_cursor
        pov_item.cursor_location = view3d.cursor_location

    if mode == 'VIEWS' or mode == 'LAYERS':
        layers_item = item
        if mode == 'VIEWS':
            layers_item = item.layers
        layers_item.view_layers = view3d.layers
        layers_item.scene_layers = scene.layers
        layers_item.lock_camera_and_layers = view3d.lock_camera_and_layers

    if mode == 'VIEWS' or mode == 'DISPLAY':
        display_item = item
        if mode == 'VIEWS':
            display_item = item.display
        display_item.viewport_shade = view3d.viewport_shade
        display_item.show_only_render = view3d.show_only_render
        display_item.show_outline_selected = view3d.show_outline_selected
        display_item.show_all_objects_origin = view3d.show_all_objects_origin
        display_item.show_relationship_lines = view3d.show_relationship_lines
        display_item.show_floor = view3d.show_floor
        display_item.show_axis_x = view3d.show_axis_x
        display_item.show_axis_y = view3d.show_axis_y
        display_item.show_axis_z = view3d.show_axis_z
        display_item.grid_lines = view3d.grid_lines
        display_item.grid_scale = view3d.grid_scale
        display_item.grid_subdivisions = view3d.grid_subdivisions
        display_item.material_mode = scene.game_settings.material_mode
        display_item.show_textured_solid = view3d.show_textured_solid
        if view3d.region_quadview != None:
            display_item.quad_view = True
            display_item.lock_rotation = view3d.region_quadview.lock_rotation
            display_item.show_sync_view = view3d.region_quadview.show_sync_view
            display_item.use_box_clip = view3d.region_quadview.use_box_clip
        else:
            display_item.quad_view = False

    return


def stored_views_update_view3D(item):
    context = bpy.context
    scene = context.scene
    view3d = context.space_data
    mode = scene.stored_views.settings.mode

    if mode == 'VIEWS' or mode == 'POV':
        pov_item = item
        if mode == 'VIEWS':
            pov_item = item.pov
        region3d = view3d.region_3d
        region3d.view_distance = pov_item.distance
        region3d.view_location = pov_item.location
        region3d.view_rotation = pov_item.rotation
        region3d.view_perspective = pov_item.perspective
        view3d.lens = pov_item.lens
        view3d.clip_start = pov_item.clip_start
        view3d.clip_end = pov_item.clip_end
        view3d.lock_cursor = pov_item.lock_cursor
        if pov_item.lock_cursor == True:
            # update cursor only if view is locked to cursor
            view3d.cursor_location = pov_item.cursor_location
        if pov_item.perspective == "CAMERA":
            try:  # get camera from name string
                view3d.camera = bpy.data.objects[pov_item.camera_name]
            except:
                scene_objects = bpy.data.objects
                found = False
                for o in scene_objects:
                    p = o.as_pointer()
                    if p == pov_item.camera_pointer:
                        pov_item.camera_name = o.name
                        view3d.camera = bpy.data.objects[pov_item.camera_name]
                        found = True
                        break
                if found == False:
                    pass
        if pov_item.lock_object_name != "":
            try:  # get object from name string
                view3d.lock_object = bpy.data.objects[pov_item.lock_object_name]
            except:
                scene_objects = bpy.data.objects
                found = False
                for o in scene_objects:
                    p = o.as_pointer()
                    if p == pov_item.lock_object_pointer:
                        pov_item.lock_object_name = o.name
                        view3d.lock_object = bpy.data.objects[pov_item.lock_object_name]
                        found = True
                        break
                if found == False:
                    pass

    if mode == 'VIEWS' or mode == 'LAYERS':
        layer_item = item
        if mode == 'VIEWS':
            layer_item = item.layers
        view3d.lock_camera_and_layers = layer_item.lock_camera_and_layers
        if layer_item.lock_camera_and_layers == True:
            scene.layers = layer_item.scene_layers
        else:
            view3d.layers = layer_item.view_layers

    if mode == 'VIEWS' or mode == 'DISPLAY':
        display_item = item
        if mode == 'VIEWS':
            display_item = item.display
        view3d.viewport_shade = display_item.viewport_shade
        view3d.show_only_render = display_item.show_only_render
        view3d.show_outline_selected = display_item.show_outline_selected
        view3d.show_all_objects_origin = display_item.show_all_objects_origin
        view3d.show_relationship_lines = display_item.show_relationship_lines
        view3d.show_floor = display_item.show_floor
        view3d.show_axis_x = display_item.show_axis_x
        view3d.show_axis_y = display_item.show_axis_y
        view3d.show_axis_z = display_item.show_axis_z
        view3d.grid_lines = display_item.grid_lines
        view3d.grid_scale = display_item.grid_scale
        view3d.grid_subdivisions = display_item.grid_subdivisions
        scene.game_settings.material_mode = display_item.material_mode
        view3d.show_textured_solid = display_item.show_textured_solid
        if display_item.quad_view == True and view3d.region_quadview == None:
            bpy.ops.screen.region_quadview()

        elif display_item.quad_view == False and view3d.region_quadview != None:
            bpy.ops.screen.region_quadview()
        if view3d.region_quadview != None:
            view3d.region_quadview.lock_rotation = display_item.lock_rotation
            view3d.region_quadview.show_sync_view = display_item.show_sync_view
            view3d.region_quadview.use_box_clip = display_item.use_box_clip

    return


def stored_views_view3D_modified():
    context = bpy.context
    scene = context.scene
    view3d = context.space_data
    mode = scene.stored_views.settings.mode
    data = stored_views_get_data()

    swap_current = None
    if data.current_index == -1:
        swap_current = data.swap[1]
    elif data.current_index == -2:
        swap_current = data.swap[2]
    else:
        swap_current = data.list[data.current_index]

    if mode == 'VIEWS' or mode == 'POV':
        pov_current = swap_current
        if mode == 'VIEWS':
            pov_current = swap_current.pov

        region3d = view3d.region_3d
        if region3d.view_perspective != pov_current.perspective:
            return True

        md5 = stored_views_get_view_matrix_md5()
        if (md5 != pov_current.view_matrix_md5 and
            region3d.view_perspective != "CAMERA"):
            return True

    if mode == 'VIEWS' or mode == 'LAYERS':
        layers_current = swap_current
        if mode == 'VIEWS':
            layers_current = swap_current.layers

        if layers_current.lock_camera_and_layers != view3d.lock_camera_and_layers:
            return True
        if layers_current.lock_camera_and_layers == True:
            for i in range(20):
                if layers_current.scene_layers[i] != scene.layers[i]:
                    return True
        else:
            for i in range(20):
                if layers_current.view_layers[i] != view3d.layers[i]:
                    return True

    if mode == 'VIEWS' or mode == 'DISPLAY':
        excludes = ["material_mode", "quad_view", "lock_rotation", "show_sync_view", "use_box_clip", "name"]
        display_current = swap_current
        if mode == 'VIEWS':
            display_current = swap_current.display
        for k, v in display_current.items():
            if k not in excludes:
                if getattr(view3d, k) != getattr(display_current, k):
                    return True

        if display_current.material_mode != scene.game_settings.material_mode:
            return True

        if view3d.region_quadview == None:
            if display_current.quad_view == True:
                return True
        else:
            if display_current.quad_view == False:
                return True
            else:
                tests = ["lock_rotation", "show_sync_view", "use_box_clip"]
                for t in tests:
                    if getattr(view3d.region_quadview, t) != getattr(display_current, t):
                        return True

    return False


def stored_views_copy_item(source, dest):
    for k, v in source.items():
        dest[k] = v
    return


def stored_views_get_view_matrix_md5():
    region3d = bpy.context.space_data.region_3d
    md5 = hashlib.md5(str(region3d.view_matrix).encode('utf-8')).hexdigest()
    return md5


def stored_views_load_presets():
    # find preset files
    paths = get_preset_path()
    preset_files = []
    for path in paths:
        for root, dirs, files in os.walk(path):
            for file in files:
                if file.endswith(".blsv"):
                    preset_files.append(os.path.join(root, file))

    # read preset names
    preset_list = []
    for filename in preset_files:
        # load file
        try:
            file = gzip.open(filename, mode='r')
            dump = pickle.load(file)
            file.close()
            preset_name = dump["info"]["preset_name"]
            sort_name = preset_name.lower()
            preset_list.append([sort_name, preset_name, filename])
        except:
            continue
    preset_list.sort()

    # find popup width
    sizes = [blf.dimensions(0, preset_name)[0] + 25 for \
        i, preset_name, path in preset_list]
    popup_max = 400
    popup_min = 250
    if len(sizes) > 1:
        sizes.sort()
        max_size = sizes[-1] + 10
    else:
        max_size = blf.dimensions(0, "No presets found")[0] + 10
    width = max(popup_min, max_size)
    width = min(popup_max, width)
    # store settings in window-manager
    bpy.context.window_manager["stored_views_presets"] = preset_list
    bpy.context.window_manager["stored_views_presets_width"] = width


def stored_views_apply_preset(dump, replace=True):
    # apply preset
    scene = bpy.context.scene
    sv = bpy.context.scene.stored_views
    io_filters = sv.settings.io_filters
    sv_data = {"point_of_views": sv.point_of_views,
               "views": sv.views,
               "layers": sv.layers,
               "displays": sv.displays}

    for sv_struct, props in dump["data"].items():
        is_filtered = getattr(io_filters, sv_struct)
        if is_filtered == False:
            continue
        sv_list = sv_data[sv_struct].list
        sv_swap = sv_data[sv_struct].swap
        if replace == True:  # clear swap and list
            while len(sv_swap) > 0:
                sv_swap.remove(0)
            while len(sv_list) > 0:
                sv_list.remove(0)
        for key, prop_struct in props.items():
            sv_item = sv_list.add()
            for subprop, subval in prop_struct.items():
                if type(subval) == type({}):  # views : pov, layers, displays
                    v_subprop = getattr(sv_item, subprop)
                    for v_subkey, v_subval in subval.items():
                        if type(v_subval) == type([]):  # array like of pov,...
                            v_array_like = getattr(v_subprop, v_subkey)
                            for i in range(len(v_array_like)):
                                v_array_like[i] = v_subval[i]
                        else:
                            setattr(v_subprop, v_subkey, v_subval)  # others
                elif type(subval) == type([]):
                    array_like = getattr(sv_item, subprop)
                    for i in range(len(array_like)):
                        array_like[i] = subval[i]
                else:
                    setattr(sv_item, subprop, subval)

    stored_views_sanitize_data(scene, clear_swap=False)


def stored_views_apply_from_scene(scene_name, replace=True):
    scene = bpy.context.scene
    sv = bpy.context.scene.stored_views
    io_filters = sv.settings.io_filters

    structs = [sv.views, sv.point_of_views, sv.layers, sv.displays]
    if replace == True:
        for st in structs:  # clear swap and list
            while len(st.swap) > 0:
                st.swap.remove(0)
            while len(st.list) > 0:
                st.list.remove(0)

    f_sv = bpy.data.scenes[scene_name].stored_views
    f_structs = [f_sv.views, f_sv.point_of_views, f_sv.layers, f_sv.displays]
    is_filtered = [io_filters.views, io_filters.point_of_views, io_filters.layers, io_filters.displays]

    for i in range(len(f_structs)):
        if is_filtered[i] == False:
            continue
        for j in f_structs[i].list:
            item = structs[i].list.add()
            #stored_views_copy_item(j, item)
            for k, v in j.items():
                item[k] = v

    stored_views_sanitize_data(scene, clear_swap=False)


def init_draw():
    bpy.context.window_manager["stored_views_draw_started"] = True
    sv = bpy.context.scene.stored_views
    sv.settings.show_view_name = False
    bpy.ops.stored_views.draw()


def draw_callback_px(self, context):

    r_width = context.region.width
    r_height = context.region.height
    font_id = 0  # XXX, need to find out how best to get this.

    blf.size(font_id, 11, 72)
    text_size = blf.dimensions(0, self.view_name)

    text_x = r_width - text_size[0] - 10
    text_y = r_height - text_size[1] - 8
    blf.position(font_id, text_x, text_y, 0)
    blf.draw(font_id, self.view_name)


class VIEW3D_stored_views_draw(bpy.types.Operator):
    bl_idname = "stored_views.draw"
    bl_label = "Show current"
    bl_description = "Toggle the display current view name in the view 3D"

    _timer = None

    @classmethod
    def poll(cls, context):
        #return context.mode=='OBJECT'
        return True

    def modal(self, context, event):
        if context.area:
            context.area.tag_redraw()

        if context.area.type != "VIEW_3D":
            return {"PASS_THROUGH"}

        sv = context.scene.stored_views
        data = stored_views_get_data()

        if len(data.list) == 0:
            self.view_name = ""
            return {"PASS_THROUGH"}
        if data.current_index >= 0:
            self.view_name = data.list[data.current_index].name
        elif data.current_index < 0:
            self.view_name = data.swap[data.current_index].name
        else:
            return {"PASS_THROUGH"}

        if not sv.view_modified:
            if event.type == 'TIMER':
                if stored_views_view3D_modified():
                    sv.view_modified = True
        else:
            self.view_name = ""

        if sv.settings.show_view_name == False:
            context.region.callback_remove(self._handle)
            context.window_manager.event_timer_remove(self._timer)
            return {'FINISHED'}

        return {"PASS_THROUGH"}

#    def invoke(self, context, event):
    def execute(self, context):
        if context.area.type == "VIEW_3D":
            sv = context.scene.stored_views
            if not sv.settings.show_view_name:
                sv.settings.show_view_name = True
                context.window_manager.modal_handler_add(self)
                self._handle = context.region.callback_add(draw_callback_px,
                    (self, context), "POST_PIXEL")
                self._timer = context.window_manager.event_timer_add(VIEW_MODIFIED_TIMER, context.window)
                self.view_name = ""
                return {"RUNNING_MODAL"}
            else:
                sv.settings.show_view_name = False
                return {'RUNNING_MODAL'}
        else:
            self.report({"WARNING"}, "View3D not found, can't run operator")
            return {"CANCELLED"}


# FIXME: popup no used for now
class VIEW3D_stored_views_load_preset(bpy.types.Operator):
    bl_idname = "stored_views.load_preset"
    bl_label = "Load Preset"
    bl_options = {'REGISTER'}

    def draw(self, context):
        # popup interface
        layout = self.layout
        scn = context.scene

        scenes = bpy.data.scenes
        settings = scn.stored_views.settings
        preset_list = context.window_manager["stored_views_presets"]

        row = layout.row(align=True)
        filters = settings.io_filters
        row.prop(filters, "views", toggle=True)
        row.prop(filters, "point_of_views", toggle=True)
        row.prop(filters, "layers", toggle=True)
        row.prop(filters, "displays", toggle=True)

        row = layout.row(align=True)
        row.operator("stored_views.import", icon='FILESEL', text="import")
        row.operator("stored_views.export", icon='NEWFOLDER', text="export")
        row = layout.row()
        row.separator()

        col = layout.column(align=False)
        for s in scenes:
            if s.name != scn.name:
                row = col.row(align=True)
                row.operator("stored_views.replace_from_scene",
                             text=s.name,
                             icon='SCENE_DATA').scene_name = s.name
                row.operator("stored_views.append_from_scene",
                             text="",
                             icon='ZOOMIN').scene_name = s.name
        for i, preset, path in preset_list:
            row = col.row(align=True)
            row.operator("stored_views.replace",
                         text=preset,
                         icon='WORDWRAP_ON').filepath = path
            row.operator("stored_views.append",
                         text="",
                         icon='ZOOMIN').filepath = path

        if not preset_list:
            col.label("No Stored Views presets found")

    def execute(self, context):
        # invoke popup
        if "stored_views_presets_width" not in context.window_manager:
            # happens when new blend-file is loaded and wm is destroyed
            stored_views_load_presets()
        width = context.window_manager["stored_views_presets_width"]
        return context.window_manager.invoke_popup(self, width)


class VIEW3D_PT_properties_stored_views(bpy.types.Panel):
    bl_label = "Stored Views"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

#    # Operator : popup panel for IO
#    def draw_header(self, context):
#        self.layout.operator("stored_views.load_preset",
#                             icon='SCRIPTWIN',
#                             text="",
#                             emboss=False)

    def draw(self, context):

        layout = self.layout
        scn = context.scene
        sv = scn.stored_views
        settings = sv.settings
        mode = settings.mode
        data = stored_views_get_data()

        if "stored_views_presets" not in context.window_manager:
            # happens when new blend-file is loaded and wm is destroyed
            stored_views_load_presets()
        preset_list = context.window_manager["stored_views_presets"]
        scenes = bpy.data.scenes

        row = layout.row(align=True)
        row.prop(settings, "show_io_panel", icon='ARROW_LEFTRIGHT',
                             text="IO", emboss=True)
        row.prop(settings, "show_settings_panel", icon='SETTINGS',
                             text="Options", emboss=True)

        if settings.show_io_panel:
            box = layout.box()
            row = box.row(align=True)
            filters = settings.io_filters
            row.label(text="", icon='FILTER')
            row.separator()
            row.prop(filters, "views", toggle=True)
            row.prop(filters, "point_of_views", toggle=True)
            row.prop(filters, "layers", toggle=True)
            row.prop(filters, "displays", toggle=True)
            row.separator()
            row = box.row(align=True)
            row.operator("stored_views.import", icon='FILESEL', text="import")
            row.operator("stored_views.export", icon='NEWFOLDER', text="export")

            col = box.column(align=True)
            for s in scenes:
                if s.name != scn.name:
                    row = col.row(align=True)
                    row.operator("stored_views.replace_from_scene",
                                 text=s.name,
                                 icon='SCENE_DATA').scene_name = s.name
                    row.operator("stored_views.append_from_scene",
                                 text="",
                                 icon='ZOOMIN').scene_name = s.name

            for i, preset, path in preset_list:
                row = col.row(align=True)
                row.operator("stored_views.replace",
                             text=preset,
                             icon='WORDWRAP_ON').filepath = path
                row.operator("stored_views.append",
                             text="",
                             icon='ZOOMIN').filepath = path
            if not preset_list:
                col.label("No Stored Views presets found")

        if settings.show_settings_panel:
            box = layout.box()
            row = box.row()
            row.operator("stored_views.draw", text="Toggle name display")
            status_string = ""
            if settings.show_view_name:
                status_string = "Status : enabled"
            else:
                status_string = "Status : disabled"
            row = box.row()
            row.label(text=status_string)

        list = data.list
        # UI : mode
        col = layout.column(align=True)
        col.prop_enum(settings, "mode", 'VIEWS')
        row = col.row(align=True)
        row.prop_enum(settings, "mode", 'POV')
        row.prop_enum(settings, "mode", 'LAYERS')
        row.prop_enum(settings, "mode", 'DISPLAY')

        # UI : operators
        row = layout.row()
        if len(list) > 0:  # show previous only if at least one set
            row.operator("stored_views.previous",
                     text="Previous", icon="FILE_REFRESH")
        row.operator("stored_views.save").index = -1

        # UI : items list
        if len(list) > 0:
            row = layout.row()
            box = row.box()
            # items list
            for i in range(len(list)):
                icon_string = "MESH_CUBE"  # default icon
                # TODO: icons for display
                if mode == 'POV':
                    persp = list[i].perspective
                    if persp == 'PERSP':
                        icon_string = "MESH_CUBE"
                    elif persp == 'ORTHO':
                        icon_string = "MESH_PLANE"
                    elif persp == 'CAMERA':
                        if list[i].camera_type != 'CAMERA':
                            icon_string = 'OBJECT_DATAMODE'
                        else:
                            icon_string = "OUTLINER_DATA_CAMERA"
                if mode == 'LAYERS':
                    if list[i].lock_camera_and_layers == True:
                        icon_string = 'SCENE_DATA'
                    else:
                        icon_string = 'RENDERLAYERS'

                if mode == 'DISPLAY':
                    shade = list[i].viewport_shade
                    if shade == 'TEXTURED':
                        icon_string = 'TEXTURE_SHADED'
                    elif shade == 'SOLID':
                        icon_string = 'SOLID'
                    elif shade == 'WIREFRAME':
                        icon_string = "WIRE"
                    elif shade == 'BOUNDBOX':
                        icon_string = 'BBOX'

                subrow = box.row(align=True)
                if data.current_index == i and sv.view_modified == False and settings.show_view_name == True:
                    subrow.label(text="", icon='SMALL_TRI_RIGHT_VEC')
                subrow.operator("stored_views.set",
                                text="", icon=icon_string).index = i
                subrow.prop(list[i], "name")
                subrow.operator("stored_views.save",
                                text="", icon="REC").index = i
                subrow.operator("stored_views.delete",
                                text="", icon="PANEL_CLOSE").index = i


def register():
    bpy.utils.register_module(__name__)
    initialize()


def unregister():
    bpy.utils.unregister_module(__name__)


if __name__ == "__main__":
    register()
