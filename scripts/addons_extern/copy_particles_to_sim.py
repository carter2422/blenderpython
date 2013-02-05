bl_info = {
    "name": "Copy Particles to Rigid Bodies",
    "version": (0, 0, 5),
    "blender": (2, 6, 5),
    "location": "View3D > Tool Shelf",
    "description": "Transfers dupliobjects from a PS to a Rigid Bodies simulation",
    "category": "Animation",
}

import bpy, random


class Particles_to_Sim(bpy.types.Operator):
    bl_idname = 'object.particles_to_simulation'
    bl_label = 'Copy Particles'
    bl_description = 'Transfers dupliobjects from a PS to a Rigid Bodies simulation'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = bpy.context.object
        return(obj and obj.particle_systems)

    def execute(self, context):
        wm = bpy.context.window_manager
        scn = bpy.context.scene
        fps = scn.render.fps
        obj = bpy.context.object
        set = obj.particle_systems[0].settings
        par = obj.particle_systems[0].particles

        # to avoid PS cache troubles
        obj.particle_systems[0].seed += 1

        # get dupliobject from particles system
        if set.render_type == 'OBJECT': duplist = [set.dupli_object]
        elif set.render_type == 'GROUP': duplist = set.dupli_group.objects[:]
        else:
            return{'FINISHED'}

        # check if dupliobjects are valid
        for d in duplist:
            if not d.rigid_body:
                return{'FINISHED'}

        # an Empty as parent allows to move / rotate later
        bpy.ops.object.add(type='EMPTY')
        bpy.context.object.name = 'Bullet Particles'
        bpy.ops.object.select_all(action='DESELECT')
        root = scn.objects.active
        delta = obj.location * wm.use_loc
        root.location = delta

        for p in par:
            dup = random.choice(duplist)
            btime = round(p.birth_time,2)
            scn.frame_set(btime)
            phy = bpy.data.objects.new('particle.000', dup.data)
            scn.objects.link(phy)
            scn.objects.active = phy #..?
            phy.select = True
            phy.rotation_euler = p.rotation.to_euler()
            bpy.ops.rigidbody.objects_add(type='ACTIVE')
            scn.frame_set(scn.frame_current) #..?
            phy.parent = root
            phy.select = False

            # copy some rigid body settings
            phy.rigid_body.collision_shape = dup.rigid_body.collision_shape
            phy.rigid_body.restitution = dup.rigid_body.restitution
            phy.rigid_body.linear_damping = dup.rigid_body.linear_damping
            phy.rigid_body.angular_damping = dup.rigid_body.angular_damping
            phy.rigid_body.friction = dup.rigid_body.friction
            phy.rigid_body.mass = dup.rigid_body.mass

            # keyframe unborn particle
            phy.scale = [p.size] * 3
            phy.location = p.location - delta
            phy.rigid_body.kinematic = True
            phy.keyframe_insert('location', frame = btime)
            phy.rigid_body.keyframe_insert('kinematic', frame = btime)

            # keyframe particle pop
            if not set.show_unborn:
                phy.scale = [0] * 3
                phy.keyframe_insert('scale', frame = btime - wm.pre_frames)
                phy.scale = [p.size] * 3
                phy.keyframe_insert('scale', frame = btime)

            # keyframe alive particle
            phy.location += p.velocity / fps * wm.vel_mult
            phy.keyframe_insert('location', frame = btime + 1)
            phy.rigid_body.kinematic = False
            phy.rigid_body.keyframe_insert('kinematic', frame = btime + 2)

        # hide emmitter
        obj.hide = obj.hide_render = True
        scn.frame_set(scn.frame_start)
        bpy.ops.object.select_all(action='DESELECT')
        scn.objects.active = root
        root.select = True

        return{'FINISHED'}


class PanelP2RB(bpy.types.Panel):
    bl_label = 'Particles to Simulation'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'

    def draw(self, context):
        wm = bpy.context.window_manager
        obj = bpy.context.object
        set = obj.particle_systems[0].settings
        layout = self.layout
        layout.operator('object.particles_to_simulation')
        layout.prop(wm, 'use_loc')
        column = layout.column(align=True)
        column.prop(wm, 'vel_mult')
        if not set.show_unborn:
            column.prop(wm, 'pre_frames')

bpy.types.WindowManager.vel_mult=bpy.props.FloatProperty(name='Speed',
        min=0.01, max=50, default=1, description='Particle speed multiplier')
bpy.types.WindowManager.use_loc=bpy.props.BoolProperty(name='Origin at emiter',
        default=False, description='Use emiter start position rather than world center to place simulation root object')
bpy.types.WindowManager.pre_frames=bpy.props.IntProperty(name='Grow time',
        min=1, max=50, default=1, description='Frames to scale particles before simulating')


def register():
    bpy.utils.register_class(Particles_to_Sim)
    bpy.utils.register_class(PanelP2RB)


def unregister():
    bpy.utils.unregister_class(Particles_to_Sim)
    bpy.utils.unregister_class(PanelP2RB)

if __name__ == '__main__':
    register()