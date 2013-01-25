import bpy
bpy.types.Scene.bf_author = "Gillan"
bpy.types.Scene.bf_category = "Grading"
bpy.types.Scene.bf_description = "Matrix, a simple grading for the atmosphere of the virtual world of the matrix."
Scene = bpy.context.scene
Tree = Scene.node_tree

Node_G = bpy.data.node_groups.new("Matrix", type='COMPOSITE')

Node_1 = Node_G.nodes.new('COLORBALANCE')
Node_1.correction_method = 'LIFT_GAMMA_GAIN'
Node_1.inputs['Fac'].default_value = 0.7
Node_1.lift = [0.840, 1.000, 0.925]
Node_1.gamma = [0.968, 1.040, 0.926]
Node_1.gain = [0.951, 1.040, 0.907]

Node_G.inputs.new("Source", 'RGBA')
Node_G.outputs.new("Result", 'RGBA')
Node_G.links.new(Node_G.inputs[0], Node_1.inputs[1])
Node_G.links.new(Node_G.outputs[0], Node_1.outputs[0])

Tree.nodes.new("GROUP", group = Node_G)
