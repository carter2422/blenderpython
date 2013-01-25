import bpy
bpy.types.Scene.bf_author = "Gillan"
bpy.types.Scene.bf_category = "Grading"
bpy.types.Scene.bf_description = "Coldest recreates the shadows blue and blue lights that were raging in science fiction films of the 80's, of course, be accompanied by a lot of glow and glare. “Cold Enhanced” desaturates warm colors and boosts cold."
Scene = bpy.context.scene
Tree = Scene.node_tree

Node_G = bpy.data.node_groups.new("Cold Enhanced", type='COMPOSITE')

Node_1 = Node_G.nodes.new('HUECORRECT')
Hcurve, Scurve, Vcurve = Node_1.mapping.curves[0:3]
while len(Scurve.points) > 2:
    Scurve.points.remove(Scurve.points[0])
Scurve.points[0].location = (0.0, 0.0)
Scurve.points[-1].location = (1.0, 0.0)
Scurve.points.new(0.52, 0.92)
Node_1.mapping.update()

Node_G.inputs.new("Image", 'RGBA')
Node_G.outputs.new("Result", 'RGBA')

Node_G.links.new(Node_G.inputs[0], Node_1.inputs[1])
Node_G.links.new(Node_G.outputs[0], Node_1.outputs[0])

Tree.nodes.new("GROUP", group = Node_G)
