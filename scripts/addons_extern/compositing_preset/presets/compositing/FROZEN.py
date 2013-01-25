import bpy
bpy.types.Scene.bf_author = "Gillan"
bpy.types.Scene.bf_category = "Grading"
bpy.types.Scene.bf_description = "Frozen, very effectively in cooling your images, especially when used together with a sharpen filter."
Scene = bpy.context.scene
Tree = Scene.node_tree

Node_G = bpy.data.node_groups.new("Frozen", type='COMPOSITE')

Node_1 = Node_G.nodes.new('HUE_SAT')
Node_1.color_saturation = 0.984

Node_2 = Node_G.nodes.new('COLORBALANCE')
Node_2.location = (200, 100)
Node_2.inputs['Fac'].default_value = 0.1
Node_2.correction_method = 'LIFT_GAMMA_GAIN'
Node_2.lift = [0.574, 0.757, 0.984]
Node_2.gamma = [1.180, 1.053, 0.770]
Node_2.gain = [0.865, 1.150, 1.260]

Node_G.inputs.new("Source", 'RGBA')
Node_G.outputs.new("Result", 'RGBA')
Node_G.links.new(Node_1.outputs[0], Node_2.inputs[1])
Node_G.links.new(Node_G.inputs[0], Node_1.inputs[1])
Node_G.links.new(Node_G.outputs[0], Node_2.outputs[0])

Tree.nodes.new("GROUP", group = Node_G)
