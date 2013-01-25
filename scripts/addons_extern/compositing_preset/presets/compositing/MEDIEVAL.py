import bpy
bpy.types.Scene.bf_author = "Gillan"
bpy.types.Scene.bf_category = "Grading"
bpy.types.Scene.bf_description = "This kind of atmosphere, is typical of historical movies"
Scene = bpy.context.scene
Tree = Scene.node_tree

Node_G = bpy.data.node_groups.new("Medieval", type='COMPOSITE')

Node_1 = Node_G.nodes.new('HUE_SAT')
Node_1.color_saturation = 0.816
Node_1.color_value = 1.560

Node_2 = Node_G.nodes.new('COLORBALANCE')
Node_2.location = (200, 50)
Node_2.correction_method = 'LIFT_GAMMA_GAIN'
Node_2.lift = [0.426, 0.0, 0.9]
Node_2.gamma = [1.081, 1.098, 1.064]
Node_2.gain = [0.54, 0.427, 0.353]

Node_3 = Node_G.nodes.new('CURVE_RGB')
Node_3.location = (650, 100)
Rcurve, Gcurve, Bcurve, Ccurve = Node_3.mapping.curves[0:4]
Ccurve.points.new(0.03889, 0.0)
Ccurve.points.new(0.40556, 0.84444)
Node_3.mapping.update()

Node_4 = Node_G.nodes.new('HUE_SAT')
Node_4.location = (900, 0)
Node_4.color_hue = 0.524
Node_4.color_saturation = 0.728
Node_4.color_value = 1.512

Node_G.inputs.new("Source", 'RGBA')
Node_G.outputs.new("Result", 'RGBA')
Node_G.links.new(Node_1.outputs[0], Node_2.inputs[1])
Node_G.links.new(Node_2.outputs[0], Node_3.inputs[1])
Node_G.links.new(Node_3.outputs[0], Node_4.inputs[1])
Node_G.links.new(Node_G.inputs[0], Node_1.inputs[1])
Node_G.links.new(Node_G.outputs[0], Node_4.outputs[0])

Tree.nodes.new("GROUP", group = Node_G)
