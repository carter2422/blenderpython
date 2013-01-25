##  Instructions
##  UI Panel placed in Text Data Properties - Each element has a tooltip with basic description.
##  
##  To Setup or enable text Animation check the "Animate Text?" option in the Typing Animation.
##  
##  By Default only "Text to Type" and "Typing Speed" are required.
##  "Text to Type" can be set by typing into the text box or by Clicking the "Use Current Text" button. 
##  Clicking the button will grab the current body of the Text Object itself.
##  
##  The "Typing Speed"  is the speed in frames. So setting it to 2 means every 2 frames a new letter will appear. 
##  
##  "Start Frame" can be chosen by setting it in the number selector or by clicking the "Use Current Frame" button beside it. 
##  Clicking the button use the current frame from the animation timeline. 
##  
##  The "Calculated End Frame" shows you what frame the text will finish typing on based upon the Amount of text, the Start frame and the typing Speed.
##  The "Calculated End Frame" is the defalt end frame unless checking the "Set Different End Frame?" option.
##  When checking this optiion more Options appear.
##  Choosing a different End Frame causes the remaining text to suddenly appear if it is less then the "Calculated End Frame".
##  
##  Setting the End Frame can be done in the same way as setting the Start Frame.


bl_info = {
      "name": "Animated Typing Text",
      "author": "Jared Felsman ",
      "version": (0, 0, 2),     
      "blender": (2, 6, 3),
      "api": 43969,
      "location": "UV/Image Editor > Properties > Image",
      "description": "Animates Text as if it is being typed.",
      "warning": "Not really sure it works correctly.",
      "category":"Animation"}

import bpy



def animate_text(scene):

    objects = scene.objects

    for obj in objects:
        if obj.type == "FONT" and "runAnimation" in obj and obj.runAnimation:
            endFrame = obj.startFrame+(len(obj.defaultTextBody)*obj.typeSpeed)
            if obj.manualEndFrame:
                endFrame = obj.endFrame
                
            if scene.frame_current < obj.startFrame:
                obj.data.body = ""

            elif scene.frame_current >= obj.startFrame and scene.frame_current <= endFrame:
                frameStringLength = (scene.frame_current-obj.startFrame)/obj.typeSpeed                 
                obj.data.body = obj.defaultTextBody[0:int(frameStringLength)]
                
            elif scene.frame_current > endFrame:
                obj.data.body = obj.defaultTextBody    
    



class makeTextAnimatedPanel(bpy.types.Panel):
    bl_label="Typing Animation"
    bl_space_type='PROPERTIES'
    bl_region_type='WINDOW'
    bl_idname = "OBJECT_PT_animtext"
    bl_context="data"
    
    bpy.types.Object.defaultTextBody = bpy.props.StringProperty(name="Text to Type",description="The text string you wish to be animated.", options={'HIDDEN'})
    bpy.types.Object.startFrame = bpy.props.IntProperty(name="Start Frame", description="The frame to start the typing animation on.")
    bpy.types.Object.endFrame = bpy.props.IntProperty(name="End Frame", description="The frame to stop the typing animation on.")
    bpy.types.Object.typeSpeed = bpy.props.IntProperty(name="Typing Speed",description="The speed in frames. E.G. 2 = every 2 frames.", default=2) 
    bpy.types.Object.runAnimation = bpy.props.BoolProperty(name="Animate Text?",description="Run this during animation?",default=False)
    bpy.types.Object.manualEndFrame = bpy.props.BoolProperty(name="Set different End Frame?",description="If this is set and the value is less then calculated frame the remaining text will suddenly appear.",default=False)
    
    @classmethod
    def poll( self, context ):
        if context.object and context.object.type == 'FONT':
            return True
    

    def draw(self, context):
        
        layout = self.layout
        obj = bpy.context.active_object
        row = layout.row()
        row.prop(obj, "runAnimation")

        if obj.runAnimation:
            row = layout.row()
            row.prop(obj, "defaultTextBody")
           
            row = layout.row()
            row.operator("animate.set_text", text="Use Current Text" ,icon="TEXT")
            
            row = layout.row()
            row.prop(obj, "typeSpeed")

            row = layout.row()
            row.prop(obj, "startFrame")
            row.operator("animate.set_start_frame", text="Use Current Frame",icon="TIME")
            
            row = layout.row()
            row.label(text="Calculated End Frame : "+str(obj.startFrame+(len(obj.defaultTextBody)*obj.typeSpeed)))
            row.prop(obj, "manualEndFrame")
            
            if obj.manualEndFrame:
                row = layout.row()
                row.prop(obj, "endFrame")
                row.operator("animate.set_end_frame", text="Use Current Frame", icon="PREVIEW_RANGE")
            



class OBJECT_OT_SetTextButton(bpy.types.Operator):
    bl_idname = "animate.set_text"
    bl_label = "Use Current Text"
    bl_description = "Set the Text to be typed to the current Text of the Text object."
 
    def execute(self, context):
        context.active_object.defaultTextBody = context.active_object.data.body
        return{'FINISHED'}  
    
class OBJECT_OT_SetStartFrameButton(bpy.types.Operator):
    bl_idname = "animate.set_start_frame"
    bl_label = "Use Current Frame"
    bl_description = "Set Start Frame to same value as Current Animation Frame."
 
    def execute(self, context):
        context.active_object.startFrame = bpy.context.scene.frame_current
        return{'FINISHED'} 

class OBJECT_OT_SetEndFrameButton(bpy.types.Operator):
    bl_idname = "animate.set_end_frame"
    bl_label = "Use Current Frame"
    bl_description = "Set End Frame to same value as Current Animation Frame."
 
    def execute(self, context):
        context.active_object.endFrame = bpy.context.scene.frame_current
        return{'FINISHED'}         
        
def register():
    bpy.utils.register_class(makeTextAnimatedPanel)
    bpy.utils.register_class(OBJECT_OT_SetTextButton)
    bpy.utils.register_class(OBJECT_OT_SetStartFrameButton)
    bpy.utils.register_class(OBJECT_OT_SetEndFrameButton)
    bpy.app.handlers.frame_change_pre.append(animate_text)



def unregister():
    bpy.utils.unregister_class(makeTextAnimatedPanel)
    bpy.utils.unregister_class(OBJECT_OT_SetTextButton)
    bpy.utils.unregister_class(OBJECT_OT_SetStartFrameButton)
    bpy.utils.unregister_class(OBJECT_OT_SetEndFrameButton)
    bpy.app.handlers.frame_change_pre.remove(animate_text)


if __name__ == "__main__":
    register()