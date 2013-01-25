#######################################################################
# will add unique noise modifiers to each of selected object f-curves #
# first record a keyframe for this to work (to generate the f-curves) #
# then you can change settings and apply the noise again to refresh   #
#######################################################################

bl_info = {
    "name": "Add Noise Modifiers",
    "author": "liero",
    "version": (0, 3, 0),
    "blender": (2, 6, 1),
    "location": "View3D > Tool Shelf",
    "description": "Add noise modifiers to f-curves in all selected objects...",
    "category": "Animation"}

import bpy, random

bpy.types.WindowManager.fc_type = bpy.props.EnumProperty( name='', items=[('available','Available','Adds some noise to every animated property'), ('scale','Scaling','Add a keyframe first'), ('rotation','Rotation','Add a keyframe first'), ( 'location','Location','Add a keyframe first')], description='Add noise to this type of f-curve - Add a keyframe first', default='available')
bpy.types.WindowManager.amplitude = bpy.props.FloatProperty( name='Amplitude', description='Amplitude: how much does the property change over time', min=0, max=25, default=5)
bpy.types.WindowManager.time_scale = bpy.props.FloatProperty( name='Time Scale', description='Time Scale: how fast does the noise animation plays', min=0, max=250, default=50)
bpy.types.WindowManager.fc_X = bpy.props.BoolProperty(name='X', default=True, description='Operate on X f-curve')
bpy.types.WindowManager.fc_Y = bpy.props.BoolProperty(name='Y', default=True, description='Operate on Y f-curve')
bpy.types.WindowManager.fc_Z = bpy.props.BoolProperty(name='Z', default=True, description='Operate on Z f-curve')

def acciones(objetos):
    act = []
    for obj in objetos:
        if obj.animation_data:
            act.append(obj.animation_data.action)
    return act

class AddNoise(bpy.types.Operator):
    bl_idname = 'animation.add_noise'
    bl_label = 'Add Modifiers'
    bl_description = 'Add noise modifiers to selected objects f-curves'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return(bpy.context.selected_objects)

    def execute(self, context):
        wm = context.window_manager
        xyz = [4]
        if wm.fc_X: xyz.append(0)
        if wm.fc_Y: xyz.append(1)
        if wm.fc_Z: xyz.append(2)
        error = 1

        for act in acciones(bpy.context.selected_objects):
            for fc in act.fcurves:
                if fc.data_path.find(wm.fc_type) > -1 or wm.fc_type == 'available':
                    if fc.array_index in xyz:
                        for m in fc.modifiers:
                            if m.type == 'NOISE': fc.modifiers.remove(m)
                        n = fc.modifiers.new('NOISE')
                        n.strength = wm.amplitude
                        n.scale = wm.time_scale
                        n.phase = int(random.random() * 999)
                        error = 0
        if error: self.report({'INFO'}, 'First create one keyframe for this objects')
        return{'FINISHED'}

class RemoveNoise(bpy.types.Operator):
    bl_idname = 'animation.remove_noise'
    bl_label = 'Clear Modifiers'
    bl_description = 'Remove noise modifiers from selected objects f-curves'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return(bpy.context.selected_objects)

    def execute(self, context):
        wm = context.window_manager
        xyz = [4]
        if wm.fc_X: xyz.append(0)
        if wm.fc_Y: xyz.append(1)
        if wm.fc_Z: xyz.append(2)

        for act in acciones(bpy.context.selected_objects):
            for fc in act.fcurves:
                if fc.data_path.find(wm.fc_type) > -1 or wm.fc_type == 'available':
                    if fc.array_index in xyz:
                        for m in fc.modifiers:
                            if m.type == 'NOISE':
                                fc.modifiers.remove(m)
        return{'FINISHED'}

class RemoveData(bpy.types.Operator):
    bl_idname = 'animation.remove_data'
    bl_label = 'Bake Frame'
    bl_description = 'Clear all animation data for selected objects'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return(bpy.context.selected_objects)

    def execute(self, context):
        sel = bpy.context.selected_objects
        for obj in sel: obj.animation_data_clear()
        for act in acciones(sel): act.user_clear()

        return{'FINISHED'}

class NModPanel(bpy.types.Panel):
    bl_label = 'Noise Modifiers'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'

    def draw(self, context):
        wm = context.window_manager
        layout = self.layout
        column = layout.column(align=True)
        column.prop(wm,'fc_type')
        column.operator('animation.add_noise', icon='ZOOMIN')
        column.operator('animation.remove_noise', icon='ZOOMOUT')
        row = layout.row()
        row.prop(wm, 'fc_X')
        row.prop(wm, 'fc_Y')
        row.prop(wm, 'fc_Z')
        column = layout.column(align=True)
        column.prop(wm,'amplitude')
        column.prop(wm,'time_scale')
        layout.operator('animation.remove_data', icon='X')

def register():
    bpy.utils.register_class(AddNoise)
    bpy.utils.register_class(RemoveNoise)
    bpy.utils.register_class(RemoveData)
    bpy.utils.register_class(NModPanel)

def unregister():
    bpy.utils.unregister_class(AddNoise)
    bpy.utils.unregister_class(RemoveNoise)
    bpy.utils.unregister_class(RemoveData)
    bpy.utils.unregister_class(NModPanel)

if __name__ == '__main__':
    register()
