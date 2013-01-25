import bpy
bpy.types.Scene.bf_author = "Fabio Russo (ruesp83)"
bpy.types.Scene.bf_category = "General"
bpy.types.Scene.bf_description = "Vignetting is a reduction of an image's brightness or saturation at the periphery compared to the image center."
Scene = bpy.context.scene
Tree = Scene.node_tree

Node_G = bpy.data.node_groups.new("Vignetting", type='COMPOSITE')

Node_0 = Node_G.nodes.new('BRIGHTCONTRAST')
Node_0.location = (0, 100)

Node_1 = Node_G.nodes.new('LENSDIST')
Node_1.location = (200, 0)
Node_1.inputs['Distort'].default_value = 1

Node_2 = Node_G.nodes.new('MATH')
Node_2.location = (400, 0)
Node_2.operation = 'GREATER_THAN'
Node_2.inputs[1].default_value = 0

Node_3 = Node_G.nodes.new('BLUR')
Node_3.filter_type = 'FAST_GAUSS'
Node_3.size_x = 150
Node_3.size_y = 150
Node_3.location = (600, 0)

Node_4 = Node_G.nodes.new('MIX_RGB')
Node_4.blend_type = 'MULTIPLY'
Node_4.inputs['Fac'].default_value = 1
Node_4.location = (800, 200)

Node_G.inputs.new("Source", 'RGBA')
Node_G.outputs.new("Result", 'RGBA')
Node_G.links.new(Node_1.outputs[0], Node_2.inputs[0])
Node_G.links.new(Node_2.outputs[0], Node_3.inputs[0])
Node_G.links.new(Node_3.outputs[0], Node_4.inputs[1])
Node_G.links.new(Node_0.outputs[0], Node_1.inputs[0])
Node_G.links.new(Node_0.outputs[0], Node_4.inputs[2])
Node_G.links.new(Node_G.inputs[0], Node_0.inputs[0])
Node_G.links.new(Node_G.outputs[0], Node_4.outputs[0])

Tree.nodes.new("GROUP", group = Node_G)
