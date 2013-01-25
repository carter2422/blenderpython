# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	 See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

__bpydoc__ = """\
GreaseParticles - greasepencil draw with particles.


Documentation

First go to User Preferences->Addons and enable the GreaseParticles addon in the Paint category.
Enable and GreaseParticles shows up in the 3Dview properties panel.	 Click activate to activate,
click deactivate to stop.
When activated greasepencil strokes will be converted in curves and these in meshes automatically.
You can find these meshcurves as sibling of the GPLAYERNAME_empty object, which is itself a child
of the active object.
When drawing the first stroke on a fresh greasepencil layer, the addon will generate a ParticleSettings
datablock with standard settings: emit from Verts, number particles: 2000, start frame: -2.
You should adapt this ParticleSettings object to suit your drawing needs. Of course you can first 
create a ParticleSettings object yourself with the same name as the greasepencil layer
you are drawing on.	 When "Emit from" is set to Faces, GreaseParticles will close the curve of every
stroke, creating one face per stroke.
With the "Approximation" setting one can set the approximation error distance of the
simplification of the curves in Blender Units, so this setting will depend on the size of your object.
Set to zero to have loads of vertices to emit particles from, set higher to have less verts.
Dont set too low when using "Emit from Faces", because theres a limit in vertices per face, you
could end up with a partial face...
When drawing polylines, they will be approximated into curves, except when you set Approximation to 0.
At the end of each stroke particles will be created.
"""


bl_info = {
	"name": "GreaseParticles",
	"author": "Gert De Roost",
	"version": (0, 4, 1),
	"blender": (2, 6, 3),
	"location": "View3D > Properties",
	"description": "Greasepencil draw with particles.",
	"warning": "",
	"wiki_url": "",
	"tracker_url": "",
	"category": "Paint"}

if "bpy" in locals():
	import imp


import bpy
import bmesh
import mathutils
import math


activated = 0
setedit = 0
vertcodict = {}
lendict = {}


bpy.types.Scene.Approx = bpy.props.FloatProperty(
		name = "Approximation", 
		description = "Curve approximation in Blender Units",
		default = 0.1,
		min = 0)

class GreaseParticlesPanel(bpy.types.Panel):
	bl_label = "GreaseParticles"
	bl_space_type = "VIEW_3D"
	bl_region_type = "UI"
#	bl_options = {'DEFAULT_CLOSED'}
	
	def draw_header(self, context):
		
		if not(activated):
			self.layout.operator("paint.greaseparticles", text="Activate")
		else:
			self.layout.operator("paint.greaseparticles", text="Deactivate")
			
	def draw(self, context):
		
		scn = bpy.context.scene
		if activated:
			self.layout.prop(scn, "Approx")


class GreaseParticles(bpy.types.Operator):
	bl_idname = "paint.greaseparticles"
	bl_label = "GreaseParticles"
	bl_description = "Greasepencil draw with particles"
	bl_options = {"REGISTER"}
	
	def invoke(self, context, event):
		
		global activated, contxt, _handle
		
		contxt = bpy.context
		
		if not(activated):
			activated = 1
			_handle = context.region.callback_add(redraw, (), 'PRE_VIEW')
			context.window_manager.modal_handler_add(self)
			return {'RUNNING_MODAL'}
		else:
			activated = 0
			context.region.callback_remove(_handle)
			return {'FINISHED'}

	def modal(self, context, event):

		global mousex, mousey
		
		mousex = event.mouse_region_x
		mousey = event.mouse_region_y
		
		return {'PASS_THROUGH'}
		
		

def register():
	bpy.utils.register_module(__name__)


def unregister():
	bpy.utils.unregister_module(__name__)


if __name__ == "__main__":
	register()



def redraw():
	
	global setedit, vertcodict, lendict
	
	region = contxt.region
	scn = contxt.scene
	if mousex < 0 or mousex > region.width or mousey < 0 or mousey > region.height:
		return
	obj = contxt.active_object
	pencil = obj.grease_pencil
	if pencil == None:
		return
	layer = obj.grease_pencil.layers.active
	if layer.active_frame.is_edited:
		setedit = 1
		return
	if setedit:
		setedit = 0
		layerempty = bpy.data.objects.get(layer.info + "_empty")
		if layerempty == None:
			bpy.ops.object.add(type='EMPTY', location=obj.location, rotation=obj.rotation_euler)
			contxt.active_object.name = layer.info + "_empty"
			layerempty = contxt.active_object
			obj.select = True
			contxt.scene.objects.active = obj
			bpy.ops.object.parent_set(type='OBJECT')
		psettings = bpy.data.particles.get(layer.info)
		if psettings == None:
			psettings = bpy.data.particles.new(layer.info)
			psettings.count = 2000
			psettings.frame_start = -2
			psettings.emit_from = "VERT"
		bpy.ops.gpencil.convert(type="CURVE")
		curve = contxt.active_object
		curvedata = curve.data
		if len(curvedata.splines) == 1 and len(curvedata.splines[0].bezier_points) == 1:
			bpy.ops.object.delete()
			obj.select = True
			contxt.scene.objects.active = obj
			return
		if psettings.emit_from == "FACE":
			for spline in curvedata.splines:
				spline.use_cyclic_u = 1
				
		simpobj = contxt.active_object
		if scn.Approx != 0:
			mainsimplify(contxt, simpobj, ["distance", "BEZIER", 0, 5, scn.Approx, 5, 0, True])
			curve = contxt.active_object
			curve.select = False
			simpobj.select = True
			contxt.scene.objects.active = simpobj
			bpy.ops.object.delete()
			curve.select = True
			simpobj.select = False
			contxt.scene.objects.active = curve
		else:
			curve.name = "simple_" + curve.name
		
		erased = 0
		for key in list(lendict.keys()):
			frame = lendict[key][2]
			if not(key in frame.strokes[:]):
				name = lendict[key][0]
				old = bpy.data.objects.get(name)
				curve.select = False
				old.select = True
				contxt.scene.objects.active = old
				del vertcodict[old.name]
				del lendict[key]
				bpy.ops.object.delete()
				curve.select = True
				contxt.scene.objects.active = curve
				for stroke in frame.strokes:
					if not(stroke in lendict.keys()):
						lendict[stroke] = (curve.name, len(stroke.points), frame)
				erased = 1
			
		if not(erased):
			brk = 0			
			for frame in layer.frames:
				for stroke in frame.strokes:
					if stroke in lendict.keys():
						if len(stroke.points) != lendict[stroke][1]:							
							name = lendict[stroke][0]
							old = bpy.data.objects.get(name)
							curve.select = False
							old.select = True
							contxt.scene.objects.active = old
							del vertcodict[old.name]
							bpy.ops.object.delete()
							del lendict[stroke]
							lendict[stroke] = (curve.name, len(stroke.points), frame)
							curve.select = True
							contxt.scene.objects.active = curve
							for stroke in frame.strokes:
								if not(stroke in lendict.keys()):
									lendict[stroke] = (curve.name, len(stroke.points), frame)
									brk = 1
							if brk:
								break
				for stroke in frame.strokes:
					if not(stroke in lendict.keys()):
						lendict[layer.active_frame.strokes[-1]] = (curve.name, len(layer.active_frame.strokes[-1].points), frame)

		bpy.ops.object.convert(target='MESH', keep_original=False)
		curve = contxt.active_object
		mesh = curve.data
		mesh.update()
		bm = bmesh.new()
		bm.from_mesh(mesh)
		colist = []
		vertlist = []
		for v in bm.verts:
			colist.append(v.co[:])
			vertlist.append(v)
		for key in vertcodict.keys():
			if key != curve.name:
				print (key)
				for cos in vertcodict[key]:
					if cos in colist:
						vert = vertlist[colist.index(cos)]
						bm.verts.remove(vert)
		colist = []
		vlist = []
		for v in bm.verts:
			colist.append(v.co[:])
			vlist.append(v)
		if psettings.emit_from == "FACE":
			bm.faces.new(vlist)
		if len(bm.verts) == 0:
			print ("WEG")
			bpy.ops.object.delete()
		else:
			bm.to_mesh(mesh)
			mesh.update(calc_edges=True)
			vertcodict[curve.name] = colist[:]
					
			bpy.ops.object.particle_system_add()
			curve.particle_systems[0].name = curve.name
			curve.particle_systems[0].settings = psettings
			layerempty.select = True
			contxt.scene.objects.active = layerempty
			bpy.ops.object.parent_set(type='OBJECT')
			curve.select = False
		obj.select = True
		contxt.scene.objects.active = obj
		layer.select = True
		
		
		
		
# Here starts Simplify Curve code kindly taken from the addon supplied with official Blender release 2.63
# 
		
def simplypoly(splineVerts, options):
	# main vars
	newVerts = [] # list of vertindices to keep
	points = splineVerts # list of 3dVectors
	pointCurva = [] # table with curvatures
	curvatures = [] # averaged curvatures per vert
	for p in points:
		pointCurva.append([])
	order = options[3] # order of sliding beziercurves
	k_thresh = options[2] # curvature threshold
	dis_error = options[6] # additional distance error

	# get curvatures per vert
	for i, point in enumerate(points[:-(order-1)]):
		BVerts = points[i:i+order]
		for b, BVert in enumerate(BVerts[1:-1]):
			deriv1 = getDerivative(BVerts, 1/(order-1), order-1)
			deriv2 = getDerivative(BVerts, 1/(order-1), order-2)
			curva = getCurvature(deriv1, deriv2)
			pointCurva[i+b+1].append(curva)

	# average the curvatures
	for i in range(len(points)):
		avgCurva = sum(pointCurva[i]) / (order-1)
		curvatures.append(avgCurva)

	# get distancevalues per vert - same as Ramer-Douglas-Peucker
	# but for every vert
	distances = [0.0] #first vert is always kept
	for i, point in enumerate(points[1:-1]):
		dist = altitude(points[i], points[i+2], points[i+1])
		distances.append(dist)
	distances.append(0.0) # last vert is always kept

	# generate list of vertindices to keep
	# tested against averaged curvatures and distances of neighbour verts
	newVerts.append(0) # first vert is always kept
	for i, curv in enumerate(curvatures):
		if (curv >= k_thresh*0.01
		or distances[i] >= dis_error*0.1):
			newVerts.append(i)
	newVerts.append(len(curvatures)-1) # last vert is always kept

	return newVerts

# get binomial coefficient
def binom(n, m):
	b = [0] * (n+1)
	b[0] = 1
	for i in range(1, n+1):
		b[i] = 1
		j = i-1
		while j > 0:
			b[j] += b[j-1]
			j-= 1
	return b[m]

# get nth derivative of order(len(verts)) bezier curve
def getDerivative(verts, t, nth):
	order = len(verts) - 1 - nth
	QVerts = []

	if nth:
		for i in range(nth):
			if QVerts:
				verts = QVerts
			derivVerts = []
			for i in range(len(verts)-1):
				derivVerts.append(verts[i+1] - verts[i])
			QVerts = derivVerts
	else:
		QVerts = verts

	if len(verts[0]) == 3:
		point = mathutils.Vector((0, 0, 0))
	if len(verts[0]) == 2:
		point = mathutils.Vector((0, 0))

	for i, vert in enumerate(QVerts):
		point += binom(order, i) * math.pow(t, i) * math.pow(1-t, order-i) * vert
	deriv = point

	return deriv

# get curvature from first, second derivative
def getCurvature(deriv1, deriv2):
	if deriv1.length == 0: # in case of points in straight line
		curvature = 0
		return curvature
	curvature = (deriv1.cross(deriv2)).length / math.pow(deriv1.length, 3)
	return curvature

#########################################
#### Ramer-Douglas-Peucker algorithm ####
#########################################
# get altitude of vert
def altitude(point1, point2, pointn):
	edge1 = point2 - point1
	edge2 = pointn - point1
	if edge2.length == 0:
		altitude = 0
		return altitude
	if edge1.length == 0:
		altitude = edge2.length
		return altitude
	alpha = edge1.angle(edge2)
	altitude = math.sin(alpha) * edge2.length
	return altitude

# iterate through verts
def iterate(points, newVerts, error):
	new = []
	for newIndex in range(len(newVerts)-1):
		bigVert = 0
		alti_store = 0
		for i, point in enumerate(points[newVerts[newIndex]+1:newVerts[newIndex+1]]):
			alti = altitude(points[newVerts[newIndex]], points[newVerts[newIndex+1]], point)
			if alti > alti_store:
				alti_store = alti
				if alti_store >= error:
					bigVert = i+1+newVerts[newIndex]
		if bigVert:
			new.append(bigVert)
	if new == []:
		return False
	return new

#### get SplineVertIndices to keep
def simplify_RDP(splineVerts, options):
	#main vars
	error = options[4]

	# set first and last vert
	newVerts = [0, len(splineVerts)-1]

	# iterate through the points
	new = 1
	while new != False:
		new = iterate(splineVerts, newVerts, error)
		if new:
			newVerts += new
			newVerts.sort()
	return newVerts

##########################
#### CURVE GENERATION ####
##########################
# set bezierhandles to auto
def setBezierHandles(newCurve):
	bpy.ops.object.mode_set(mode='EDIT', toggle=True)
	bpy.ops.curve.select_all(action='SELECT')
	bpy.ops.curve.handle_type_set(type='AUTOMATIC')
	bpy.ops.object.mode_set(mode='OBJECT', toggle=True)

# get array of new coords for new spline from vertindices
def vertsToPoints(newVerts, splineVerts, splineType):
	# main vars
	newPoints = []

	# array for BEZIER spline output
	if splineType == 'BEZIER':
		for v in newVerts:
			newPoints += splineVerts[v].to_tuple()

	# array for nonBEZIER output
	else:
		for v in newVerts:
			newPoints += (splineVerts[v].to_tuple())
			if splineType == 'NURBS':
				newPoints.append(1) #for nurbs w=1
			else: #for poly w=0
				newPoints.append(0)
	return newPoints

#########################
#### MAIN OPERATIONS ####
#########################

def mainsimplify(context, obj, options):
	#print("\n_______START_______")
	# main vars
	mode = options[0]
	output = options[1]
	degreeOut = options[5]
	keepShort = options[7]
	bpy.ops.object.select_all(action='DESELECT')
	scene = context.scene
	splines = obj.data.splines.values()

	# create curvedatablock
	curve = bpy.data.curves.new("simple_"+obj.name, type = 'CURVE')

	# go through splines
	for spline_i, spline in enumerate(splines):
		# test if spline is a long enough
		if len(spline.points) >= 7 or keepShort:
			#check what type of spline to create
			if output == 'INPUT':
				splineType = spline.type
			else:
				splineType = output
			
			# get vec3 list to simplify
			if spline.type == 'BEZIER': # get bezierverts
				splineVerts = [splineVert.co.copy()
								for splineVert in spline.bezier_points.values()]

			else: # verts from all other types of curves
				splineVerts = [splineVert.co.to_3d()
								for splineVert in spline.points.values()]

			# simplify spline according to mode
			if mode == 'distance':
				newVerts = simplify_RDP(splineVerts, options)

			if mode == 'curvature':
				newVerts = simplypoly(splineVerts, options)

			# convert indices into vectors3D
			newPoints = vertsToPoints(newVerts, splineVerts, splineType)

			# create new spline			   
			newSpline = curve.splines.new(type = splineType)

			# put newPoints into spline according to type
			if splineType == 'BEZIER':
				newSpline.bezier_points.add(int(len(newPoints)*0.33))
				newSpline.bezier_points.foreach_set('co', newPoints)
			else:
				newSpline.points.add(int(len(newPoints)*0.25 - 1))
				newSpline.points.foreach_set('co', newPoints)

			# set degree of outputNurbsCurve
			if output == 'NURBS':
				newSpline.order_u = degreeOut

			# splineoptions
			newSpline.use_endpoint_u = spline.use_endpoint_u

	# create ne object and put into scene
	newCurve = bpy.data.objects.new("simple_"+obj.name, curve)
	scene.objects.link(newCurve)
	newCurve.select = True
	scene.objects.active = newCurve
	newCurve.matrix_world = obj.matrix_world

	# set bezierhandles to auto
	setBezierHandles(newCurve)

	#print("________END________\n")
	return




