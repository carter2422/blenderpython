import bpy
bpy.types.Scene.bf_author = "Gillan"
bpy.types.Scene.bf_category = "Grading"
bpy.types.Scene.bf_description = ""
Scene = bpy.context.scene
Tree = Scene.node_tree

Node_G = bpy.data.node_groups.new("Old TV", type='COMPOSITE')

Node_1 = Node_G.nodes.new('RGBTOBW')

Node_2 = Node_G.nodes.new('CURVE_RGB')
Node_2.location = (150, 150)
Rcurve, Gcurve, Bcurve, Ccurve = Node_2.mapping.curves[0:4]
Ccurve.points.new(0.133, 0.0)
Ccurve.points.new(0.4166, 0.877)
Ccurve.points.new(0.627, 0.95)
Rcurve.points.new(0.2, 0.188)
Bcurve.points.new(0.75, 0.8)
Node_2.mapping.update()

Node_G.inputs.new("Source", 'RGBA')
Node_G.outputs.new("Result", 'RGBA')
Node_G.links.new(Node_G.inputs[0], Node_1.inputs[0])
Node_G.links.new(Node_1.outputs[0], Node_2.inputs[1])
Node_G.links.new(Node_G.outputs[0], Node_2.outputs[0])

Tree.nodes.new("GROUP", group = Node_G)
