
# ***** BEGIN GPL LICENSE BLOCK *****
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# If you have Internet access, you can find the license text at
# http://www.gnu.org/licenses/gpl.txt,
# if not, write to the Free Software Foundation,
# Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
# ***** END GPL LICENCE BLOCK *****
# --------------------------------------------------------------------------

__bpydoc__ = """\
This plugin fills in another gap in the Blender modelling experience.  It provides a means of
setting up an unlimited amount of "background images", or to be more precise "reference images".
noThese planes can be positioned/scaled/deformed to your liking and will seemingly appear behind your
transparently rendered geometry.  In fact the reference planes are transparent
themselves and drawn on top of the geometry.  This means it is possible to use the planes for
both sides of your geometry (front/back, right/left, top/bottom), whatever way you look at them,
they will always be drawn transparently on top of the geometry, only appearing to be in a certain
3 dimensional position.

Documentation
Go to User Preferences->Addons and enable the TranspRef addon in the 3D View section.
A TransRef pulldown will appear in the right pane (pull + icon on right of 3D view).
It will be empty until you select a standard Mesh->Plane with four vertices.
Then an Activate button will appear.  Click this and you will be left with a File Path Selector.
Click the file browser icon and load up an image, the image will be projected over the scene contents,
carefully filling the space bounded by the selected plane, which you can afterwards translate,
rotate, scale and deform(editmode) to your wishes.  When you selet an image, also a Transparency slider
will appear, put it somewhere low so you can see your geometry behind the reference planes.

NOTE: the reference planes shouldnt occlude object selection, thats why you can only select them
      by clicking the plane edges.

NOTE: you can create as many reference planes as needed.  Reselecting a plane later, enables you to
      access image path and transparency values.

HINT: you can use the reference planes from both sides. 
I recommend to model in orthogonal mode (which is a good idea anyhow) if you want this to work correctly.

BEWARE:  reference state will be saved along with your blend file, but you will have to manually enable
TranspRef once every Blender session and load your file after having done this.
"""

# many thanks go to lobo_nz for hacking in the original load/save code !
bl_info = {
	"name": "TranspRef",
	"author": "Gert De Roost",
	"version": (2, 0, 6),
	"blender": (2, 6, 3),
	"location": "View3D > UI > TranspRef",
	"description": "Adding transparent reference images to VIEW3D.",
	"warning": "",
	"wiki_url": "",
	"tracker_url": "",
	"category": "3D View"}

if "bpy" in locals():
    import imp


import bpy
from bpy_extras import *
from math import sqrt
from mathutils import *
from bgl import *
import os
import time
from bpy.app.handlers import persistent


imagelist = []
planelist = []
transplist = []
startedlist = []
resetlist = []
filenm = {}
state = {}
remembv = {}
position = 0
started = 0
cbon = 0
waiting = 0
ok = 0
start = 1
oldobjname = None
scnfilenm = ""
tm = time.time()
    
bpy.types.Scene.Transp = bpy.props.FloatProperty(
		name = "Transparency", 
		description = "Enter transparency",
        default = 0.5,
        min = 0,
        max = 1)
bpy.types.Scene.Filename = bpy.props.StringProperty(
		name="Image",
		attr="custompath",# this a variable that will set or get from the scene
		description="path to reference image",
		maxlen= 1024,
		subtype='FILE_PATH',
		default= "")

for region in bpy.context.area.regions:
	if region.type == "UI":
		regionui = region



class TranspRefPanel(bpy.types.Panel):
	bl_label = "TranspRef"
	bl_space_type = "VIEW_3D"
	bl_region_type = "UI"
	
	def draw(self, context):
		
		global cbon, regionui, region3d, start, handle
		if not(cbon):
			cbon = 1
			for region in bpy.context.area.regions:
				if region.type == "UI":
					regionui = region
			for region in bpy.context.area.regions:
				if region.type == "WINDOW":
					region3d = region
					handle = region.callback_add(redraw, (), 'POST_PIXEL')
		scn = context.scene
		if waiting:
			self.layout.operator("view3d.transpref", text="Activate")
		if started:
			self.layout.prop(scn, 'Filename')
		if started == 2:
			self.layout.prop(scn, 'Transp')
		if start:
			region3d.tag_redraw()
		start = 0


class TranspRef(bpy.types.Operator):
	bl_idname = "view3d.transpref"
	bl_label = "TranspRef"
	bl_description = "Adding transparent reference images to VIEW3D."
	bl_options = {"REGISTER"}
	
	def invoke(self, context, event):
		global operator, regionui
		operator = self
		do_transpref(self)
		
		return {'FINISHED'}


def register():
	bpy.utils.register_module(__name__)
	bpy.app.handlers.load_post.append(loaddata)

def unregister():
	bpy.utils.unregister_module(__name__)
	bpy.context.region.callback_remove(handle)


if __name__ == "__main__":
	register()




def do_transpref(self):
	
	global imagelist, transplist, planelist
	global position, st, started
	
	position = 0
	started = 1
	region3d.tag_redraw()
	
	

def getscreencoords(vector):
	global mtrix, plane
	region = bpy.context.region
	rv3d = bpy.context.space_data.region_3d
	vector = vector * mtrix	
	vector = vector + plane.location
	svector = view3d_utils.location_3d_to_region_2d(region, rv3d, vector)
	if svector == None:
		return [0, 0]
	else:
		return svector[0], svector[1]


def savenewplane(newplane, newtransp, newpath):
	try:
		save_planelist = []
		save_transplist = []
		save_pathlist = []
		#load the saved data
		txt = bpy.data.texts["savedrefplanes"]
		evallist = txt.lines
		save_planelist = eval(evallist[0].body)
		save_transplist = eval(evallist[1].body)
		save_pathlist = eval(evallist[2].body)
		txt.clear()
	except:
		save_planelist = []
		save_transplist = []
		save_pathlist = []
		#create new text
		txt = bpy.data.texts.new("savedrefplanes")

	#append new plane info
	save_planelist.append(newplane.name)
	save_transplist.append(newtransp)
	save_pathlist.append(newpath)
    
	#write save_planelist to text object
	txt.write("[")
	for i in range(len(save_planelist)):
		if i != 0:
			txt.write(", ")
		txt.write("'"+save_planelist[i]+"'")
	txt.write("]\n")
    
	#write save_transplist to text object
	txt.write("[")
	for i in range(len(save_transplist)):
		if i != 0:
			txt.write(", ")
		txt.write(str(save_transplist[i]))
	txt.write("]\n")
    
	#write save_pathlist to text object
	txt.write("[")
	for i in range(len(save_pathlist)):
		if i != 0:
			txt.write(", ")
		txt.write("'"+save_pathlist[i]+"'")
	txt.write("]\n")


def loadimage(filename):
	global imagelist, transplist, planelist
	
	obj = bpy.context.active_object
	bpy.ops.image.open(filepath = filename)
	image = bpy.data.images[os.path.basename(filename)]
	image.gl_load(GL_NEAREST, GL_NEAREST)
	
	imagelist.insert(0, image)
	planelist.insert(0, obj)
	obj.draw_type = "BOUNDS"
	transplist.insert(0, 0.5)

	savenewplane(obj, 0.5, filename)

	



def drawreference(image, vectors, viewwidth, viewheight, matrix, transparency):
	"""
	Draws Reference-imageplanes
	
	image = the image to draw
	vectors = global vector-coordinates of 4 plane corners
	viewport = viewport of current area
	matrix = perspectivematrix of current area
	transparency = transparency of the image from 0.0 to 1.0
	
	"""
	glMatrixMode(GL_PROJECTION)
	glLoadIdentity()
	reg = bpy.context.region
	glOrtho(0, reg.width, 0, reg.height, -1, 2)
	glMatrixMode(GL_MODELVIEW)
	glLoadIdentity()
	
	image.gl_load()
	glBindTexture(GL_TEXTURE_2D, image.bindcode)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)	
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)	
	glEnable(GL_TEXTURE_2D)
	glColor4f(1, 1, 1, transparency)
	glEnable(GL_BLEND)
	glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
	glBegin(GL_QUADS)
	glTexCoord2f(0.0, 0.0)
	x, y = getscreencoords(vectors[3])
	glVertex3f(x, y, 0)
	glTexCoord2f(0.0, 1.0)
	x, y = getscreencoords(vectors[2])
	glVertex3f(x, y, 0)
	glTexCoord2f(1.0, 1.0)
	x, y = getscreencoords(vectors[1])
	glVertex3f(x, y, 0)
	glTexCoord2f(1.0, 0.0)
	x, y = getscreencoords(vectors[0])
	glVertex3f(x, y, 0)
	glEnd()
	glBindTexture(GL_TEXTURE_2D, 0)
	glDisable(GL_BLEND)
	glDisable(GL_TEXTURE_2D)


def getplanevectors():

	global imagelist, transplist, planelist, vectorlist
	global mtrix, plane, remembv

	if plane.rotation_mode == "AXIS_ANGLE":
		return
		# How to find the axis WXYZ values ?
		ang =  plane.rotation_axis_angle
		mat_rotX = Matrix.Rotation(ang, 4, ang)
		mat_rotY = Matrix.Rotation(ang, 4, ang)
		mat_rotZ = Matrix.Rotation(ang, 4, ang)
	elif plane.rotation_mode == "QUATERNION":
		w, x, y, z = plane.rotation_quaternion
		x = -x
		y = -y
		z = -z
		quat = Quaternion([w, x, y, z])
		mtrix = quat.to_matrix()
		mtrix.resize_4x4()
	else:
		ax, ay, az = plane.rotation_euler
		mat_rotX = Matrix.Rotation(-ax, 4, 'X')
		mat_rotY = Matrix.Rotation(-ay, 4, 'Y')
		mat_rotZ = Matrix.Rotation(-az, 4, 'Z')
	if plane.rotation_mode == "XYZ":
		mtrix = mat_rotX * mat_rotY * mat_rotZ
	elif plane.rotation_mode == "XZY":
		mtrix = mat_rotX * mat_rotZ * mat_rotY
	elif plane.rotation_mode == "YXZ":
		mtrix = mat_rotY * mat_rotX * mat_rotZ
	elif plane.rotation_mode == "YZX":
		mtrix = mat_rotY * mat_rotZ * mat_rotX
	elif plane.rotation_mode == "ZXY":
		mtrix = mat_rotZ * mat_rotX * mat_rotY
	elif plane.rotation_mode == "ZYX":
		mtrix = mat_rotZ * mat_rotY * mat_rotX

	sx, sy, sz = plane.scale
	mat_scX = Matrix.Scale(sx, 4, Vector([1, 0, 0]))
	mat_scY = Matrix.Scale(sy, 4, Vector([0, 1, 0]))
	mat_scZ = Matrix.Scale(sz, 4, Vector([0, 0, 1]))
	mtrix = mat_scX * mat_scY * mat_scZ * mtrix
	
	
	mesh = plane.data
	if plane.mode == "EDIT" and plane == bpy.context.active_object:
		bpy.ops.object.editmode_toggle()
		bpy.ops.object.editmode_toggle()
	for vertidx in mesh.polygons[0].vertices:
		vector = Vector(mesh.vertices[vertidx].co[:])
		vectorlist.append(vector)
		


def redraw():
	global imagelist, transplist, planelist, vectorlist
	global position, waiting, operator
	global plane, started, filenm, state, oldobjname
	global scnfilenm, remembv
	
	# Test if selection is already reference plane.
	if bpy.context.area.type != "VIEW_3D":
		return
		
	scene = bpy.context.scene
	selobj = bpy.context.active_object
	try:
		dummy = state[selobj]
	except:
		state[selobj] = 0
		
	for plane in planelist:
		
		try:
			mesh = plane.data
			vert = mesh.vertices[0]
		except:
			posn = planelist.index(plane)
			planelist.pop(posn)
			imagelist.pop(posn)
			transplist.pop(posn)
			filenm[plane] = ""
			state[plane] = 0
			remembv[plane] = {}
	
	
	if selobj != None:
	
		if selobj.name != oldobjname and state[selobj] >= 2:
			scene.Filename = filenm[selobj]
			scene.Transp = transplist[planelist.index(selobj)]
		oldobjname = selobj.name
		
		if scnfilenm == "":
			scene.Filename = ""
			scnfilenm = "dummy"
		
		if checkplane(selobj):
			if state[selobj] == 0:
				waiting = 1 
				started = 0
				state[selobj] = 1
			if state[selobj] == 3:
				waiting = 0
				started = 2
				position = planelist.index(selobj)
				if scene.Filename != filenm[selobj] and scene.Filename != "":
					filenm[selobj] = scene.Filename
					planelist.pop(position)
					imagelist.pop(position)
					transplist.pop(position)
					loadimage(filenm[selobj])
				transplist[position] = bpy.context.scene.Transp
			if state[selobj] == 2:
				if scene.Filename != "":
					filenm[selobj] = scene.Filename
					state[selobj] = 3
					waiting = 0
					started = 2
					loadimage(filenm[selobj])
				else:
					waiting = 0
					started = 1 
					scene.Filename = ""
			if state[selobj] < 2:
				waiting = 1
				if started:
					state[selobj] = 2
					scene.Filename == ""
					scnfilenm = ""
					filenm[selobj] = ""
					waiting = 0
					started = 1
	
		regionui.tag_redraw()
		
		

	for plane in planelist:
		if state[plane] == 3:
			vectorlist = []
			getplanevectors()		
		
			for area in bpy.context.screen.areas:
				for sp in area.spaces:
					if sp.type == "VIEW_3D":
						viewwidth = bpy.context.area.width
						viewheight = bpy.context.area.height
						matrix = sp.region_3d.perspective_matrix	
						posn = planelist.index(plane)
						drawreference(imagelist[posn], vectorlist, viewwidth, viewheight, matrix, transplist[posn])



def checkplane(obj):
	
	# Test if selection is exactly one non-subdivided plane.
	if obj == None:
		return 0
	mesh = obj.data
	if (len(mesh.polygons) > 1) or (len(mesh.polygons[0].vertices) == 3):
		return 0
	return 1
    

@persistent
def loaddata(dummy):
	
	global imagelist, planelist, transplist, filenm, state
	global waiting, started, start

	scene = bpy.context.scene
	scene.Filename = ""
	start = 1 
	
	try:
		txt = bpy.data.texts["savedrefplanes"]
		#load the saved data
		evallist = txt.lines        
		save_planelist = eval(evallist[0].body)
		save_transplist = eval(evallist[1].body)
		save_pathlist = eval(evallist[2].body)
	except:
		filenm = {}
		state = {}
		waiting = 0
		started = 0
	
	try:
		dummy = planelist[0]
	except:
		imagelist = []
		planelist = []
		transplist = []
	
	for i in range(len(save_planelist)):
		obj = bpy.data.objects[save_planelist[i]]
		planelist.append(obj)
		state[obj] = 3
	for i in range(len(save_transplist)):
		transplist.append(save_transplist[i])
	for i in range(len(save_pathlist)):
		bpy.ops.image.open(filepath = save_pathlist[i])
		image = bpy.data.images[os.path.basename(save_pathlist[i])]
		image.gl_load(GL_NEAREST, GL_NEAREST)
		imagelist.append(image)
		filenm[planelist[i]] = save_pathlist[i]
		
		
		
		

