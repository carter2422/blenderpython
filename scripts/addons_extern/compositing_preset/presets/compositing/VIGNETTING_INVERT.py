import bpy
bpy.types.Scene.bf_author = "Mike Pan's"
bpy.types.Scene.bf_category = "General"
bpy.types.Scene.bf_description = "Vignetting is a reduction of an image's brightness or saturation at the periphery compared to the image center."
Scene = bpy.context.scene
Tree = Scene.node_tree

Node_G = bpy.data.node_groups.new("Vignetting Invert", type='COMPOSITE')

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
Node_3.size_x = 880
Node_3.size_y = 246
Node_3.location = (600, 0)

Node_4 = Node_G.nodes.new('BRIGHTCONTRAST')
Node_4.inputs['Bright'].default_value = 0.4
Node_4.inputs['Contrast'].default_value = 36.5
Node_4.location = (800, 0)

Node_5 = Node_G.nodes.new('INVERT')
Node_5.location = (1000, 0)

Node_6 = Node_G.nodes.new('MIX_RGB')
Node_6.blend_type = 'MULTIPLY'
Node_6.inputs['Fac'].default_value = 1
Node_6.location = (1200, 200)

Node_G.inputs.new("Source", 'RGBA')
Node_G.outputs.new("Result", 'RGBA')
Node_G.links.new(Node_1.outputs[0], Node_2.inputs[0])
Node_G.links.new(Node_2.outputs[0], Node_3.inputs[0])
Node_G.links.new(Node_3.outputs[0], Node_4.inputs[0])
Node_G.links.new(Node_4.outputs[0], Node_5.inputs[1])
Node_G.links.new(Node_5.outputs[0], Node_6.inputs[1])
Node_G.links.new(Node_0.outputs[0], Node_1.inputs[0])
Node_G.links.new(Node_0.outputs[0], Node_6.inputs[2])
Node_G.links.new(Node_G.inputs[0], Node_0.inputs[0])
Node_G.links.new(Node_G.outputs[0], Node_6.outputs[0])

Tree.nodes.new("GROUP", group = Node_G)
