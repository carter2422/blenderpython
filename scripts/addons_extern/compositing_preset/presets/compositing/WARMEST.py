import bpy
bpy.types.Scene.bf_author = "Gillan"
bpy.types.Scene.bf_category = "Grading"
bpy.types.Scene.bf_description = "Warmest ignite your image."
Scene = bpy.context.scene
Tree = Scene.node_tree

Node_G = bpy.data.node_groups.new("Warmest", type='COMPOSITE')

Node_1 = Node_G.nodes.new('COLORBALANCE')
Node_1.correction_method = 'LIFT_GAMMA_GAIN'
Node_1.inputs['Fac'].default_value = 0.5
Node_1.lift = [1.160, 0.842, 0.807]
Node_1.gamma = [1.165, 0.932, 0.879]
Node_1.gain = [1.160, 1.075, 0.934]

Node_G.inputs.new("Source", 'RGBA')
Node_G.outputs.new("Result", 'RGBA')
Node_G.links.new(Node_G.inputs[0], Node_1.inputs[1])
Node_G.links.new(Node_G.outputs[0], Node_1.outputs[0])

Tree.nodes.new("GROUP", group = Node_G)
