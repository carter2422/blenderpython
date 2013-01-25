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
    "name": "Compositing Presets",
    "author": "Fabio Russo (ruesp83) <ruesp83@libero.it>",
    "version": (0, 7),
    "blender": (2, 6, 5),
    "api": 53057,
    "location": "Node Editor > Properties",
    "description": "Presets of nodes for the Compositing Nodes.",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.5/Py/Scripts/"
                "Compositing/Compositing_Presets",
    "tracker_url": "http://projects.blender.org/tracker/"
                   "?func=detail&aid=25621",
    "category": "Compositing"}


import bpy
import os
import sys
import math
from bpy.props import *


prec_preset = " "
show_info_preset = True
preview_msg = []
prec_tree_type = ''

if os.path.exists(bpy.utils.user_resource('SCRIPTS', path="addons" + os.sep +
                  "compositing_preset" + os.sep + "presets")):
    presets_folder = bpy.utils.user_resource('SCRIPTS', path="addons" + os.sep
                                             + "compositing_preset" + os.sep +
                                             "presets")
elif os.path.exists(bpy.utils.script_paths()[0] + os.sep + "addons" + os.sep +
                    "compositing_preset" + os.sep + "presets"):
    presets_folder = (bpy.utils.script_paths()[0] + os.sep + "addons" + os.sep
                      + "compositing_preset" + os.sep + "presets")
elif (bpy.utils.script_paths()[0] + os.sep + "addons_contrib" + os.sep +
        "compositing_preset" + os.sep + "presets"):
    presets_folder = (bpy.utils.script_paths()[0] + os.sep + "addons_contrib" +
                      os.sep + "compositing_preset" + os.sep + "presets")
else:
    print("COMPOSITING PRESETS -- MAJOR PROBLEM:"
          "COULD NOT LOCATE ADD-ON INSTALLATION PATH.")
    presets_folder = "error"


def Div_Description(desc, width):
    car = math.floor(width / 7)
    return [desc[i:i + car] for i in range(0, len(desc), car)]


def filter_py(ext):
    return (ext == ".py")


def draw_menu_presets(self, context):
    self.layout.menu("NODE_EDITOR_MT_presets", icon="FILE_SCRIPT")


def save_in_out_group_preset(fd, context):
    group = context.active_node.node_tree

    fd.write("# Inputs\n")
    for input in group.inputs:
        fd.write("Node_G.inputs.new(\"" + input.name + "\", '" + input.type
                 + "')\n")

    fd.write("# Outputs\n")
    for output in group.outputs:
        fd.write("Node_G.outputs.new(\"" + output.name + "\", '" + output.type
                 + "')\n")


#def save_property_node_group_preset(fd, context, name_node):


def save_nodes_group_preset(fd, context):
    group = context.active_node.node_tree

    i = 0
    dict_name = dict()
    for node in group.nodes:
        i += 1
        name_node = "Node_" + str(i)
        fd.write(name_node + " = Node_G.nodes.new('" + node.type +
                 "')\n")

        if (node.hide is not False):
            fd.write(name_node + ".hide = True\n")

        if (node.label != ''):
            fd.write(name_node + ".label = \"" + node.label + "\"\n")

        fd.write(name_node + ".location = (" + str(node.location[0]) + ", " +
                 str(node.location[1]) + ")\n")

        if (node.mute is not False):
            fd.write(name_node + ".mute = True\n")

        if (node.use_custom_color is not False):
            fd.write(name_node + ".use_custom_color = True\n")
            fd.write(name_node + ".color = (" + str(node.color[0]) + ", " +
                     str(node.color[1]) + ", " + str(node.color[2]) + ")\n")

        # height
        # show_options
        # show_preview
        # show_texture
        # width
        # width_hidden

        #write property
        #save_property_node_group_preset(fd, context, name_node):
        fd.write("\n")
        dict_name[node.name] = name_node

    return dict_name


def save_links_group_preset(fd, context, dict_name):
    group = context.active_node.node_tree

    for link in group.links:
        if (link.from_node is not None):
            name_from = link.from_node.name
        else:
            dict_name['Node_G'] = 'Node_G'
            name_from = 'Node_G'

        if (link.to_node is not None):
            name_to = link.to_node.name
        else:
            dict_name['Node_G'] = 'Node_G'
            name_to = 'Node_G'

        i = 0
        if (link.from_node is not None):
            for output in link.from_node.outputs:
                if (output != link.from_socket):
                    i += 1
                else:
                    break
        else:
            for in_gr in group.inputs:
                if (link.from_socket != in_gr):
                    i += 1
                else:
                    break

        j = 0
        if (link.to_node is not None):
            for input in link.to_node.inputs:
                if (input != link.to_socket):
                    j += 1
                else:
                    break
        else:
            for out_gr in group.outputs:
                if (link.to_socket != out_gr):
                    j += 1
                else:
                    break

        str_out = ".outputs["
        str_in = ".inputs["
        if (dict_name[name_from] == 'Node_G'):
            str_out = ".inputs["
        if (dict_name[name_to] == 'Node_G'):
            str_in = ".outputs["
        fd.write("Node_G.links.new(" + dict_name[name_from] + str_out +
                 str(i) + "], " + dict_name[name_to] + str_in + str(j) +
                 "])\n")


class PresetPreview(bpy.types.Operator):
    bl_idname = "node.presetpreview"
    bl_label = "preview preset"
    previewPath = bpy.props.StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        global preview_msg

        D = bpy.data

        image_name = NODE_EDITOR_MT_presets.bl_label + ".jpg"
        image_name = image_name.replace(" ", "_")
        image_path = self.previewPath + os.sep + image_name
        if not os.path.exists(image_path):
            preview_msg = ['WARNING', "Preview does not exist."]
            return {'CANCELLED'}

        #Check if has texture
        if D.images.find(image_name) == -1:
            bpy.ops.image.open(filepath=image_path)

        if "preset_preview" not in D.textures:
            D.textures.new("preset_preview", "IMAGE")

        if (D.textures["preset_preview"].image != D.images[image_name]):
            D.textures["preset_preview"].image = D.images[image_name]

        #Do everything possible to get Blender to reload the preview.
        D.images[image_name].reload()
        bpy.ops.wm.redraw_timer()
        D.scenes[bpy.context.scene.name].update()
        D.scenes[bpy.context.scene.name].frame_set(
            D.scenes[bpy.context.scene.name].frame_current)

        return {'FINISHED'}


class NODE_EDITOR_PT_ViewPreset(bpy.types.Operator):
    '''View preview preset'''
    bl_idname = "node.viewpreset"
    bl_label = "view preview preset"
    typePath = bpy.props.StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        global show_info_preset
        global preview_msg

        D = bpy.data

        show_info_preset = False
        if "preset_preview" in D.textures:
            D.textures.remove(D.textures[0])
        bpy.ops.node.presetpreview(previewPath=self.typePath)
        if (len(preview_msg) > 1):
            self.report({preview_msg[0]}, preview_msg[1])
        return {'FINISHED'}


class NODE_EDITOR_MT_presets(bpy.types.Menu):
    bl_label = "Group Presets"
    preset_operator = "script.execute_preset"
    presetsPath = []

    def draw(self, context):
        self.path_menu(self.presetsPath, self.preset_operator,
                       filter_ext=filter_py)


class NODE_EDITOR_PT_save_in_preset(bpy.types.Operator):
    bl_idname = "node.savepreset"
    bl_label = "Save a New Preset"

    sg_description = StringProperty(name="Description",
                                    description="Description of the preset",
                                    default='')
    sg_category = StringProperty(name="Category",
                                 description="Description of the category",
                                 default='')
    sg_author = StringProperty(name="Author", description="Name of the author",
                               default='')
    path = ""
    file_path = ""

    def execute(self, context):
        view = context.space_data
        sg_description = self.sg_description
        sg_category = self.sg_category
        sg_author = self.sg_author
        sg_name = context.active_node.node_tree.name

        if (view.tree_type == 'SHADER'):
            type = 'SHADER'

        if (view.tree_type == 'TEXTURE'):
            type = 'TEXTURE'

        if (view.tree_type == 'COMPOSITING'):
            type = 'COMPOSITE'

        try:
            fd = open(self.file_path, "w")
        except:
            self.report({'ERROR'}, "Insufficient permissions to write the"
                        " preset!")
            return {'CANCELLED'}

        fd.write("''' Scripts Automatically Generated by the Addon:"
                 " Compositing Preset '''\n\n")
        fd.write("import bpy\n")
        fd.write("\n")
        fd.write("# *** Info Preset: " + sg_name.title() + " ***\n")
        fd.write("bpy.types.Scene.bf_author = \"" + sg_author.title() + "\"\n")
        fd.write("bpy.types.Scene.bf_category = \"" + sg_category + "\"\n")
        fd.write("bpy.types.Scene.bf_description = \"" + sg_description +
                 "\"\n")
        fd.write("\n")
        fd.write("# *** Declaration Preset ***\n")
        fd.write("Scene = bpy.context.scene\n")
        fd.write("Tree = Scene.node_tree\n\n")
        fd.write("Node_G = bpy.data.node_groups.new(\"" + sg_name.title() +
                 "\", type='" + type + "')\n")
        fd.write("\n")
        fd.write("# *** Declaration Nodes ***\n")
        #Write Nodes with property
        dict_name_nodes = save_nodes_group_preset(fd, context)
        fd.write("# *** Declaration In\Out Preset ***\n")
        #Write In\Out Preset
        save_in_out_group_preset(fd, context)
        fd.write("\n")
        fd.write("# *** Declaration Links ***\n")
        #Write links
        save_links_group_preset(fd, context, dict_name_nodes)
        fd.write("\n")
        fd.write("# *** View Group in the Node Editor ***\n")
        fd.write("Tree.nodes.new(\"GROUP\", group = Node_G)\n")
        fd.close()
        self.report({'INFO'}, "Preset Created!")
        return {'FINISHED'}

    def invoke(self, context, event):
        view = context.space_data
        sg_name = context.active_node.node_tree.name

        if (sg_name == ''):
            self.report({'ERROR'}, "Enter the name of the new preset")
            return {'CANCELLED'}

        if ((sg_name[0:9] == 'NodeGroup') or (sg_name[0:8] == 'Untitled')):
            self.report({'ERROR'}, "Unable to call the group \"NodeGroup\" or"
                        " \"Untitled\"")
            return {'CANCELLED'}

        if (view.tree_type == 'SHADER'):
            self.path = presets_folder + os.sep + "shader"

        if (view.tree_type == 'TEXTURE'):
            self.path = presets_folder + os.sep + "texture"

        if (view.tree_type == 'COMPOSITING'):
            self.path = presets_folder + os.sep + "compositing"

        self.file_path = (self.path + os.sep +
                          sg_name.replace(" ", "_").upper() + ".py")

        if (os.path.exists(self.file_path) is True):
            self.report({'ERROR'}, "The name of the preset you want to save is"
                        " already in the list. Change it!")
            return {'CANCELLED'}

        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'sg_author', text="Author", icon='GREASEPENCIL')
        layout.prop(self, 'sg_category', text="Category", icon='SORTALPHA')
        layout.prop(self, 'sg_description', text="Description", icon='INFO')


class NODE_EDITOR_PT_save_group(bpy.types.Panel):
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_label = "Save Group"

    @classmethod
    def poll(cls, context):
        node = context.active_node
        return node and node.type == 'GROUP'

    def draw(self, context):
        layout = self.layout
        layout.operator("node.savepreset", text="Save Group -> Preset",
                        icon='FILE_SCRIPT')


class NODE_EDITOR_PT_preset(bpy.types.Panel):
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_label = "Group Presets"

    @classmethod
    def poll(cls, context):
        view = context.space_data
        return (view) and (view.id.use_nodes)

    def draw(self, context):
        global prec_preset
        global show_info_preset
        global preview_msg
        global prec_tree_type

        D = bpy.data
        layout = self.layout
        view = context.space_data
        scene = context.scene
        desc = scene.bf_description
        cat = scene.bf_category
        author = scene.bf_author

        col = layout.column(align=True)

        if (view.tree_type == 'SHADER') and (view.id.use_nodes):
            dir = [presets_folder + os.sep + "shader"]
            path = presets_folder + os.sep + "shader"
            NODE_EDITOR_MT_presets.presetsPath = dir
            if (prec_tree_type != 'SHADER'):
                NODE_EDITOR_MT_presets.bl_label = "Group Presets"
                prec_tree_type = 'SHADER'

        if (view.tree_type == 'TEXTURE') and (view.id.use_nodes):
            dir = [presets_folder + os.sep + "texture"]
            path = presets_folder + os.sep + "texture"
            NODE_EDITOR_MT_presets.presetsPath = dir
            if (prec_tree_type != 'TEXTURE'):
                NODE_EDITOR_MT_presets.bl_label = "Group Presets"
                prec_tree_type = 'TEXTURE'

        if (view.tree_type == 'COMPOSITING') and (view.id.use_nodes):
            dir = [presets_folder + os.sep + "compositing"]
            path = presets_folder + os.sep + "compositing"
            NODE_EDITOR_MT_presets.presetsPath = dir
            if (prec_tree_type != 'COMPOSITING'):
                NODE_EDITOR_MT_presets.bl_label = "Group Presets"
                prec_tree_type = 'COMPOSITING'

        col.menu("NODE_EDITOR_MT_presets",
                 text=NODE_EDITOR_MT_presets.bl_label)

        if (NODE_EDITOR_MT_presets.bl_label != "Group Presets"):
            if show_info_preset:
                col.operator("node.viewpreset", text="Show Info",
                             icon='INFO').typePath = path
            else:
                layout = self.layout
                layout.separator()
                col = layout.column()

                if (len(preview_msg) == 0):
                    row = col.row()
                    row.label("Preview:", icon='SEQ_PREVIEW')

                    row = col.row()
                    if D.textures.find("preset_preview") == -1:
                        D.textures.new("preset_preview", "IMAGE")
                    preview_texture = D.textures["preset_preview"]
                    row.template_preview(preview_texture)

                row = col.row()
                row.label("Author: ", icon='GREASEPENCIL')
                if (type(author).__name__ == 'str'):
                    row.label(author)

                row = col.row()
                row.label("Category: ", icon='SORTALPHA')
                if (type(cat).__name__ == 'str'):
                    row.label(cat)

                col.label("Description: ", icon='INFO')
                if (type(desc).__name__ == 'str'):
                    l_desc = Div_Description(desc, context.region.width)
                    for line_s in l_desc:
                        col.label(line_s)

            if (prec_preset != NODE_EDITOR_MT_presets.bl_label):
                show_info_preset = True
                prec_preset = NODE_EDITOR_MT_presets.bl_label
                preview_msg = []


def register():
    bpy.types.Scene.bf_description = StringProperty(name="Description",
                                                    description=
                                                    "Description of the "
                                                    "preset",
                                                    default="")
    bpy.types.Scene.bf_category = StringProperty(name="Category", description=
                                                 "Description of the category",
                                                 default="")
    bpy.types.Scene.bf_author = StringProperty(name="Author", description=
                                               "Name of the author",
                                               default="")
    bpy.utils.register_class(NODE_EDITOR_MT_presets)
    bpy.utils.register_class(NODE_EDITOR_PT_preset)
    bpy.utils.register_class(NODE_EDITOR_PT_save_group)
    bpy.utils.register_class(PresetPreview)
    bpy.utils.register_class(NODE_EDITOR_PT_ViewPreset)
    bpy.utils.register_class(NODE_EDITOR_PT_save_in_preset)
    #bpy.types.NODE_MT_add.append(draw_menu_presets)
    pass


def unregister():
    del bpy.types.Scene.bf_description
    del bpy.types.Scene.bf_category
    del bpy.types.Scene.bf_author
    bpy.utils.unregister_class(NODE_EDITOR_MT_presets)
    bpy.utils.unregister_class(NODE_EDITOR_PT_preset)
    bpy.utils.unregister_class(NODE_EDITOR_PT_save_group)
    bpy.utils.unregister_class(PresetPreview)
    bpy.utils.unregister_class(NODE_EDITOR_PT_ViewPreset)
    bpy.utils.unregister_class(NODE_EDITOR_PT_save_in_preset)
    #bpy.types.NODE_MT_add.remove(draw_menu_presets)
    pass


if __name__ == "__main__":
    register()
