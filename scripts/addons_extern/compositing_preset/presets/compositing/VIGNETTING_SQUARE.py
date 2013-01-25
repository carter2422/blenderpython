import bpy
bpy.types.Scene.bf_author = "Francois Tarlier"
bpy.types.Scene.bf_category = "General"
bpy.types.Scene.bf_description = "Vignetting is a reduction of an image's brightness or saturation at the periphery compared to the image center."
Scene = bpy.context.scene
Tree = Scene.node_tree

Node_G = bpy.data.node_groups.new("Vignetting Square", type='COMPOSITE')

Node_0 = Node_G.nodes.new('BRIGHTCONTRAST')
Node_0.location = (0, 100)

Node_1 = Node_G.nodes.new('MATH')
Node_1.operation = 'GREATER_THAN'
Node_1.location = (200, 0)
Node_1.inputs[1].default_value = 0

Node_1_a = Node_G.nodes.new('MATH')
Node_1_a.location = (200, -200)
Node_1_a.operation = 'LESS_THAN'
Node_1_a.inputs[1].default_value = 0

Node_2 = Node_G.nodes.new('SCALE')
Node_2.location = (400, 0)
Node_2.space = 'RELATIVE'
Node_2.inputs['X'].default_value = 0.950
Node_2.inputs['Y'].default_value = 0.990

Node_3 = Node_G.nodes.new('ROTATE')
Node_3.location = (600, 0)
Node_3.filter_type = 'BICUBIC'

Node_4 = Node_G.nodes.new('TRANSLATE')
Node_4.location = (800, 0)

Node_5 = Node_G.nodes.new('MIX_RGB')
Node_5.inputs['Fac'].default_value = 1
Node_5.location = (1000, -100)

Node_6 = Node_G.nodes.new('BLUR')
Node_6.filter_type = 'FAST_GAUSS'
Node_6.size_x = 93
Node_6.size_y = 120
Node_6.location = (1200, -100)

Node_7 = Node_G.nodes.new('INVERT')
Node_7.location = (1400, -100)

Node_8 = Node_G.nodes.new('HUE_SAT')
Node_8.location = (1600, -300)
Node_8.color_value = 0.0

Node_G.inputs.new("Source", 'RGBA')
Node_G.outputs.new("Result", 'RGBA')
Node_G.links.new(Node_1.outputs[0], Node_2.inputs[0])
Node_G.links.new(Node_2.outputs[0], Node_3.inputs[0])
Node_G.links.new(Node_3.outputs[0], Node_4.inputs[0])
Node_G.links.new(Node_4.outputs[0], Node_5.inputs[2])
Node_G.links.new(Node_1_a.outputs[0], Node_5.inputs[1])
Node_G.links.new(Node_5.outputs[0], Node_6.inputs[0])
Node_G.links.new(Node_6.outputs[0], Node_7.inputs[1])
Node_G.links.new(Node_7.outputs[0], Node_8.inputs[0])
Node_G.links.new(Node_0.outputs[0], Node_1.inputs[0])
Node_G.links.new(Node_0.outputs[0], Node_1_a.inputs[0])
Node_G.links.new(Node_0.outputs[0], Node_8.inputs[1])
Node_G.links.new(Node_G.inputs[0], Node_0.inputs[0])
Node_G.links.new(Node_G.outputs[0], Node_8.outputs[0])

Tree.nodes.new("GROUP", group = Node_G)
