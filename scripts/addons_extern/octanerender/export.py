# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 3
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# This script by Lionel Zamouth

import os
import bpy
import math
import mathutils
import datetime
import octanerender
from octanerender.utils import *

# Build list of objects to export
def obj_export(scene):
    octane_render = scene.octane_render
    log ('Begin OBJ/MTL export')

    # Select objects to export: all or only selected ones
    #if octane_render.export_sel_only:
    #    objects = bpy.context.selected_objects
    #else:
    objects = scene.objects

    # Browse all objects
    export_objects=[]
    for obj in objects:
        # Select only following object types:
        if obj.type in ['MESH', 'SURFACE', 'META', 'FONT', 'CURVE', 'EMPTY']:
            # Select only non hidden objects based upon Octane export setting
            if obj.hide_render == False or octane_render.export_remove_hidden == False:
                # Select only non hidden objects based upon Octane export setting
                if obj.hide == False or octane_render.export_remove_invisible == False:
                    # Select only objects in visible layers
                    #if scene.layers[next((i for i in range(len(obj.layers)) if obj.layers[i]))]:
                    #    log ('Selected for export: <%s>' % (obj.name))
                    export_objects.append(obj)
    return export_objects

def test_nurbs_compat(ob):
    if ob.type != 'Curve':
        return False
    for nu in ob.data:
        if (not nu.knotsV) and nu.type != 1: # not a surface and not bezier
            return True
    return False

# XXX not converted
def write_nurb(file, ob, ob_mat):
    tot_verts = 0
    cu = ob.data

    # use negative indices
    Vector = Blender.mathutils.Vector
    for nu in cu:

        if nu.type==0:          DEG_ORDER_U = 1
        else:                           DEG_ORDER_U = nu.orderU-1  # Tested to be correct

        if nu.type==1:
            log('\tWarning, bezier curve: %' % (ob.name) % ' only poly and nurbs curves supported')
            continue

        if nu.knotsV:
            log('\tWarning, surface: %s' % (ob.name) % ' only poly and nurbs curves supported')
            continue

        if len(nu) <= DEG_ORDER_U:
            log('\tWarning, orderU is lower then vert count, skipping: %s' % (ob.name))
            continue

        pt_num = 0
        do_closed = (nu.flagU & 1)
        do_endpoints = (do_closed==0) and (nu.flagU & 2)

        for pt in nu:
            pt = Vector(pt[0], pt[1], pt[2]) * ob_mat
            file.write('v %.6f %.6f %.6f\n' % (pt[0], pt[1], pt[2]))
            pt_num += 1
        tot_verts += pt_num

        file.write('g %s\n' % (ob.name)) # fixName(ob.getData(1)) could use the data name too
        file.write('cstype bspline\n') # not ideal, hard coded
        file.write('deg %d\n' % DEG_ORDER_U) # not used for curves but most files have it still

        curve_ls = [-(i+1) for i in range(pt_num)]

        # 'curv' keyword
        if do_closed:
            if DEG_ORDER_U == 1:
                pt_num += 1
                curve_ls.append(-1)
            else:
                pt_num += DEG_ORDER_U
                curve_ls = curve_ls + curve_ls[0:DEG_ORDER_U]

        file.write('curv 0.0 1.0 %s\n' % (' '.join( [str(i) for i in curve_ls] ))) # Blender has no U and V values for the curve

        # 'parm' keyword
        tot_parm = (DEG_ORDER_U + 1) + pt_num
        tot_parm_div = float(tot_parm-1)
        parm_ls = [(i/tot_parm_div) for i in range(tot_parm)]

        if do_endpoints: # end points, force param
            for i in range(DEG_ORDER_U+1):
                parm_ls[i] = 0.0
                parm_ls[-(1+i)] = 1.0

        file.write('parm u %s\n' % ' '.join( [str(i) for i in parm_ls] ))

        file.write('end\n')

    return tot_verts

# Write MTL file
def write_mtl(mtlFile, mtl_dict, scene, copy_images):
    start_time = datetime.datetime.now()
    log('MTL file: "%s"' % (mtlFile))

    # Set Ambient color
    world = scene.world
    if world:
        worldAmb = world.ambient_color[:]
    else:
        worldAmb = 0.0, 0.0, 0.0

    dst_dir = os.path.dirname(mtlFile)
    # Copy texture file if needed, return path
    def copy_image(image):
        fn_full = absPath(image.filepath)
        # Remove spaces from destination image file name
        fn_base = fixName(os.path.basename(fn_full))
        fn_dest = os.path.join(dst_dir, fn_base)
        if copy_images:
            if not os.path.exists(fn_dest):
                copy_file(fn_full,fn_dest)
            rel = fn_base
        else:
            # Drop an error if not copying image and file name has spaces
            if hasSpace(fn_full):
                error('Invalid texture file name "%s" (contains spaces). Rename file or use "Copy Image" export option' % (fn_full))
            rel = fn_full
        return rel

    def delayed_copy_sequence(tex,frame):
        # Get file number in sequence
        seq = get_sequence(tex,frame)
        # Source path
        fn_full = absPath(tex.image.filepath)
        src_dir = os.path.dirname(fn_full)
        # Separate name and extension
        name, ext = os.path.splitext(os.path.basename(fn_full))
        # Get name without original sequence number and
        root, digits = get_rootname(name)
        fmt = '%%0%dd' % (digits)
        #log('Root <%s> Format <%s> Seq <%d> Ext <%s>' % (root,fmt,seq,ext))
        src_file = root + (fmt % seq) + ext
        dst_file = 'SEQ-' + fixName(root) + ext
        src_path = os.path.join(src_dir,src_file)
        dst_path = os.path.join(dst_dir,dst_file)
        octanerender.delayed_copies += ((src_path,dst_path),)
        #copy_file(src_path,dst_path)
        return dst_file

    # Convert hardness to glossiness
    def Glossiness(Hardness):
        return (Hardness - 1) * 1000.0 / 510.0 #1.9607843137254901

    file = open(mtlFile, "w")
    # XXX
    # file.write('# Blender MTL File: %s\n' % Blender.Get('filepath').split('\\')[-1].split('/')[-1])
    file.write('# Material Count: %i\n' % len(mtl_dict))
    # Write material/image combinations we have used.
    mat_blender = {}
    for key, (name, mat, img) in sorted(mtl_dict.items()):
        mat_blender[name] = mat

    for mtl_mat_name, mat in sorted(mat_blender.items()):
        # Get the Blender data for the material and the image.
        if mtl_mat_name =='':
            realmat='Null'
        else:
            realmat=mtl_mat_name
        file.write('newmtl %s\n' % mtl_mat_name) # Define a new material: matname_imgname
        log ('Processing <%s>' % (mtl_mat_name))
        if mat:
            file.write('Kd %.6f %.6f %.6f\n' % tuple([c for c in mat.diffuse_color]) )    # Diffuse
            if tuple([c for c in mat.specular_color]) == (0.0,0.0,0.0):
                pass
                # log ('<%s> set as diffuse' % mtl_mat_name)
                # Diffuse material in Octane
            elif mat.use_transparency and mat.transparency_method=='RAYTRACE' and mat.raytrace_transparency.ior > 1.0:
                # Specular material in Octane
                # log ('<%s> set as specular' % mtl_mat_name)
                #file.write('Kd %.6f %.6f %.6f\n' % tuple([c*mat.diffuse_intensity for c in mat.diffuse_color]) )   # Transmission
                file.write('Ks %.6f %.6f %.6f\n' % tuple([c for c in mat.specular_color]))   # Reflection
                file.write('Ni %.6f\n' % mat.raytrace_transparency.ior) # Refraction index
                file.write('Ns %.6f\n' % (mat.specular_hardness * 1000.0 / 511.0))
            else:
                # Glossy
                # log ('<%s> set as glossy' % mtl_mat_name)
                if scene.octane_render.double_specular:
                    file.write('Ks %.6f %.6f %.6f\n' % tuple([c*2 for c in mat.specular_color])) # Specular
                else:
                    file.write('Ks %.6f %.6f %.6f\n' % tuple([c for c in mat.specular_color])) # Specular
                file.write('Ns %.6f\n' % (mat.specular_hardness * 1000.0 / 511.0))
            file.write('d %0.3f\n' % mat.alpha) # No alpha
            file.write('illum 2\n')
        else:
            #write a dummy material here?
            file.write('Ns 0\n')
            file.write('Ka %.6f %.6f %.6f\n' %  tuple([c for c in worldAmb])  ) # Ambient, uses mirror colour,
            file.write('Kd 0.8 0.8 0.8\n')
            file.write('Ks 0.8 0.8 0.8\n')
            file.write('d 1\n') # No alpha
            file.write('illum 2\n') # light normaly


        if mat: # No face image. if we have a material search for MTex image.
            #log ('Mat <%s>' % mat.name)
            for mtex in mat.texture_slots:
                #log ('Texture <%s>' % mtex.name)
                if mtex and mtex.texture.type == 'IMAGE':
                    if not mtex.texture.image:
                        error ('Check texture slots for material <%s>' % mtl_mat_name)
                    #try:
                    if mtex.texture.image.source == 'FILE':
                        # Texture is an image file
                        log ('Source image : "%s"' % (absPath(mtex.texture.image.filepath)))
                        filename = copy_image(mtex.texture.image)
                    elif mtex.texture.image.source == 'SEQUENCE':
                        # Texture is a sequence
                        if not copy_image:
                            error('You must enable Copy Image for sequence textures')
                        filename = delayed_copy_sequence(mtex.texture, scene.frame_current)
                    else:
                        # Other texture type are not supported
                        error('Only image types of File and Sequence are supported')

                    if mtex.use_map_color_diffuse:
                        file.write('map_Kd %s\n' % filename) # Diffuse mapping image
                    if mtex.use_map_normal:
                        file.write('map_bump %s\n' % filename) # Bump mapping image
                    if mtex.use_map_color_spec:
                        file.write('map_Ks %s\n' % filename) # Specular mapping image
                    if mtex.use_map_alpha:
                        file.write('map_d %s\n' % filename) # Alpha mapping image
                    if mtex.use_map_mirror:
                        file.write('map_Ka %s\n' % filename) # Mirror mapping image
                    if mtex.use_map_hardness:
                        file.write('map_Ns %s\n' % filename) # Hardness to affect roughness in octane
                    #except:
                        # Texture has no image though its an image type, best ignore.
                        #log ('Warning: could not process material <%s> of type IMAGE - skipping' % (mtl_mat_name))

        file.write('\n\n')
    file.close()
    delta = datetime.datetime.now() - start_time
    log ('MTL export time: %d.%03ds' % (delta.seconds,delta.microseconds/1000))

def write_obj(objFile, mtlFile, objects, scene, unitFactor):

    start_time = datetime.datetime.now()
    octane_render = scene.octane_render
    log('OBJ file: "%s"' % (objFile))

    EXPORT_TRI = octane_render.export_tri
    EXPORT_EDGES = octane_render.export_edges
    EXPORT_NORMALS = octane_render.export_normals
    EXPORT_NORMALS_HQ = octane_render.export_HQ
    EXPORT_UV = octane_render.export_UV
    EXPORT_MTL = octane_render.export_materials
    EXPORT_COPY_IMAGES = octane_render.export_copy_images,
    EXPORT_APPLY_MODIFIERS = octane_render.export_apply_modifiers
    EXPORT_ROTX90 = octane_render.export_ROTX90
    EXPORT_BLEN_OBS = True,
    EXPORT_GROUP_BY_OB = False,
    EXPORT_GROUP_BY_MAT = False,
    EXPORT_KEEP_VERT_ORDER = False,
    EXPORT_POLYGROUPS = octane_render.export_polygroups
    EXPORT_CURVE_AS_NURBS = octane_render.export_curves_as_nurbs

    def veckey3d(v):
        return round(v.x, 6), round(v.y, 6), round(v.z, 6)

    def veckey2d(v):
        return round(v[0], 6), round(v[1], 6)

    def findVertexGroupName(face, vWeightMap):
        """
        Searches the vertexDict to see what groups is assigned to a given face.
        We use a frequency system in order to sort out the name because a given vetex can
        belong to two or more groups at the same time. To find the right name for the face
        we list all the possible vertex group names with their frequency and then sort by
        frequency in descend order. The top element is the one shared by the highest number
        of vertices is the face's group
        """
        weightDict = {}
        for vert_index in face.vertices:
            vWeights = vWeightMap[vert_index]
            for vGroupName, weight in vWeights:
                weightDict[vGroupName] = weightDict.get(vGroupName, 0.0) + weight

        if weightDict:
            return max((weight, vGroupName) for vGroupName, weight in weightDict.items())[1]
        else:
            return '(null)'

    # TODO: implement this in C? dunno how it should be called...
    def getVertsFromGroup(me, group_index):
        ret = []

        for i, v in enumerate(me.vertices):
            for g in v.groups:
                if g.group == group_index:
                    ret.append((i, g.weight))

        return ret

    file = open(objFile, "w", encoding="utf8", newline="\n")
    fw = file.write

    # Write Header
    fw('# Blender v%s OBJ File: %s\n' % (bpy.app.version_string, os.path.basename(objFile)))
    fw('# www.blender.org\n')

    # Tell the obj file what material file to use.
    if EXPORT_MTL:
        file.write('mtllib %s\n' % ( os.path.basename(mtlFile)))

    if EXPORT_ROTX90:
        mat_xrot90= mathutils.Matrix.Rotation(-math.pi/2, 4, 'X')

    # Initialize totals, these are updated each object
    totverts = totuvco = totno = 1
    face_vert_index = 1
    globalNormals = {}

    # A Dict of Materials
    # (material.name, image.name):matname_imagename # matname_imagename has gaps removed.
    mtl_dict = {}
    copy_set = set()
    # Get all meshes
    for ob_main in objects:
        #log ('Processing <%s>' % (ob_main.name))
        start_obj = datetime.datetime.now()

        # Ignore dupli children
        if ob_main.parent and ob_main.parent.dupli_type != 'NONE':
            log('<%s> is a dupli child - ignoring' % (ob_main.name))
            continue
        # Skip empties not in a dupli group
        if ob_main.type == 'EMPTY' and ob_main.dupli_type == 'NONE':
            log('<%s> is an EMPTY not in a dupli group - skipping' % (ob_main.name))
            continue
        obs = []
        # Create list from parent
        if ob_main.dupli_type != 'NONE':
            log('Creating dupli_list on <%s>' % (ob_main.name))
            ob_main.dupli_list_create(scene)
            obs = [(dob.object, dob.matrix) for dob in ob_main.dupli_list]
            log('-> <%s> has %d dupli children  ' % (ob_main.name,len(obs)))
        else:
            obs = [(ob_main, ob_main.matrix_world)]

        for ob, ob_mat in obs:

            # Nurbs curve support attempt
            if EXPORT_CURVE_AS_NURBS and test_nurbs_compat(ob):
                if EXPORT_ROTX90:
                    ob_mat = ob_mat * mat_xrot90
                    totverts += write_nurb(file, ob, ob_mat)
                continue

            try:
                me = ob.to_mesh(scene, EXPORT_APPLY_MODIFIERS, 'RENDER')
            except RuntimeError:
                me = None
            if me is None:
                continue

            if EXPORT_ROTX90:
                me.transform(mat_xrot90 * ob_mat)
            else:
                me.transform(ob_mat)

            if EXPORT_UV:
                faceuv = len(me.uv_textures) > 0
                if faceuv:
                    uv_layer = me.uv_textures.active.data[:]
            else:
                faceuv = False

            me_verts = me.vertices[:]

            # Make our own list so it can be sorted to reduce context switching
            face_index_pairs = [ (face, index) for index, face in enumerate(me.tessfaces)]
            # faces = [ f for f in me.faces ]

            if EXPORT_EDGES:
                edges = me.edges
            else:
                edges = []

            if not (len(face_index_pairs)+len(edges)+len(me.vertices)): # Make sure there is somthing to write

                # clean up
                bpy.data.meshes.remove(me)

                continue # dont bother with this mesh.

            # XXX
            # High Quality Normals
            if EXPORT_NORMALS and face_index_pairs:
                me.calc_normals()
            if ob.type == "META": # or ob.type == "CURVE":
                materials = ob.data.materials[:]
            else:
                materials = me.materials[:]
            material_names = [m.name if m else None for m in materials]

#            materialNames = []
#            materialItems = [m for m in materials]

            # avoid bad index errors
            if not materials:
                materials = [None]
                material_names = ["Null"]

#            if materials:
#                for mat in materials:
#                    if mat: # !=None
#                        material_names.append(mat.name)
#                    else:
#                        material_names.append(None)
                # Cant use LC because some materials are None.
                # materialNames = map(lambda mat: mat.name, materials) # Bug Blender, dosent account for null materials, still broken.

            # Possible there null materials, will mess up indicies
            # but at least it will export, wait until Blender gets fixed.
            #materialNames.extend((16-len(materialNames)) * [None])
            #materialItems.extend((16-len(materialItems)) * [None])

            # Sort by Material, then images
            # so we dont over context switch in the obj file.
            if EXPORT_KEEP_VERT_ORDER:
                pass
            elif faceuv:
                face_index_pairs.sort(key=lambda a: (a[0].material_index, hash(uv_layer[a[1]].image), a[0].use_smooth))
            elif len(materials) > 1:
                face_index_pairs.sort(key=lambda a: (a[0].material_index, a[0].use_smooth))
            else:
                # no materials
                face_index_pairs.sort(key=lambda a: a[0].use_smooth)

            #faces = [pair[0] for pair in face_index_pairs]

            # Set the default mat to no material and no image.
            contextMat = (0, 0) # Can never be this, so we will label a new material teh first chance we get.
            contextSmooth = None # Will either be true or false,  set bad to force initialization switch.

            if EXPORT_BLEN_OBS or EXPORT_GROUP_BY_OB:
                name1 = ob.name
                name2 = ob.data.name
                if name1 == name2:
                    obnamestring = fixName(name1)
                else:
                    obnamestring = '%s_%s' % (fixName(name1), fixName(name2))

                if EXPORT_BLEN_OBS:
                    fw('o %s\n' % obnamestring)  # Write Object name
                else:  # if EXPORT_GROUP_BY_OB:
                    fw('g %s\n' % obnamestring)

            # Vert
            for v in me.vertices:
                fw('v %.6f %.6f %.6f\n' % tuple(v.co*unitFactor))

            # UV
            if faceuv:
                # in case removing some of these dont get defined.
                uv = uvkey = uv_dict = f_index = uv_index = None

                uv_face_mapping = [[0, 0, 0, 0] for i in range(len(face_index_pairs))]  # a bit of a waste for tri's :/

                uv_dict = {}  # could use a set() here
                uv_layer = me.tessface_uv_textures.active.data
                for f, f_index in face_index_pairs:
                    for uv_index, uv in enumerate(uv_layer[f_index].uv):
                        uvkey = veckey2d(uv)
                        try:
                            uv_face_mapping[f_index][uv_index] = uv_dict[uvkey]
                        except:
                            uv_face_mapping[f_index][uv_index] = uv_dict[uvkey] = len(uv_dict)
                            fw('vt %.6f %.6f\n' % uv[:])
                            #file.write('vt %.6f %.6f\n' % tuple(uv))

                uv_unique_count = len(uv_dict)

                del uv, uvkey, uv_dict, f_index, uv_index
                # Only need uv_unique_count and uv_face_mapping

            # NORMAL, Smooth/Non smoothed.
            if EXPORT_NORMALS:
                for f, f_index in face_index_pairs:
                    if f.use_smooth:
                        for v_idx in f.vertices:
                            v = me_verts[v_idx]
                            noKey = veckey3d(v.normal)
                            if noKey not in globalNormals:
                                globalNormals[noKey] = totno
                                totno += 1
                                fw('vn %.6f %.6f %.6f\n' % noKey)
                    else:
                        # Hard, 1 normal from the face.
                        noKey = veckey3d(f.normal)
                        if noKey not in globalNormals:
                            globalNormals[noKey] = totno
                            totno += 1
                            fw('vn %.6f %.6f %.6f\n' % noKey)

            if not faceuv:
                f_image = None

            # XXX
            if EXPORT_POLYGROUPS:
                # Retrieve the list of vertex groups
                vertGroupNames = ob.vertex_groups.keys()

                currentVGroup = ''
                # Create a dictionary keyed by face id and listing, for each vertex, the vertex groups it belongs to
                vgroupsMap = [[] for _i in range(len(me_verts))]
                for v_idx, v_ls in enumerate(vgroupsMap):
                    v_ls[:] = [(vertGroupNames[g.group], g.weight) for g in me_verts[v_idx].groups]

            for f, f_index in face_index_pairs:
                f_smooth = f.use_smooth
                f_mat = min(f.material_index, len(materials) - 1)

                if faceuv:
                    tface = uv_layer[f_index]
                    f_image = tface.image

                # MAKE KEY
                if faceuv and f_image:  # Object is always true.
                    key = fixName(material_names[f_mat]), fixName(f_image.name)
                else:
                    key = fixName(material_names[f_mat]), "None"  # No image, use None instead.

                # Write the vertex group
                if EXPORT_POLYGROUPS:
                    if ob.vertex_groups:
                        # find what vertext group the face belongs to
                        vgroup_of_face = findVertexGroupName(f, vgroupsMap)
                        if vgroup_of_face != currentVGroup:
                            currentVGroup = vgroup_of_face
                            fw('g %s\n' % vgroup_of_face)

                # CHECK FOR CONTEXT SWITCH
                if key == contextMat:
                    pass  # Context alredy switched, dont do anything
                else:
                    if key[0] == "None" and key[1] == "None":
                        # Write a null material, since we know the context has changed.
                        if EXPORT_GROUP_BY_MAT:
                            # can be mat_image or (null)
                            fw('g %s_%s\n' % (fixName(ob.name), fixName(ob.data.name)) ) # can be mat_image or (null)
                        fw('usemtl Null\n') # mat, image

                    else:
                        mat_data = mtl_dict.get(key)
                        if not mat_data:
                            # First add to global dict so we can export to mtl
                            # Then write mtl

                            # Make a new names from the mat and image name,
                            # converting any spaces to underscores with fixName.

                            # If none image dont bother adding it to the name
                            #if key[1] == None:
                            mat_data = mtl_dict[key] = ('%s'%fixName(key[0])), materials[f_mat], f_image
#                           else:
#                              mat_data = mtl_dict[key] = ('%s_%s' % (fixName(key[0]), fixName(key[1]))), materialItems[f_mat], f_image

                        if EXPORT_GROUP_BY_MAT:
                            fw('g %s_%s_%s\n' % (fixName(ob.name), fixName(ob.data.name), mat_data[0]) ) # can be mat_image or (null)

                        fw('usemtl %s\n' % mat_data[0]) # can be mat_image or (null)

                contextMat = key
                if f_smooth != contextSmooth:
                    if f_smooth:  # on now off
                        fw('s 1\n')
                        contextSmooth = f_smooth
                    else:  # was off now on
                        fw('s off\n')
                        contextSmooth = f_smooth

                f_v_orig = [(vi, me_verts[v_idx]) for vi, v_idx in enumerate(f.vertices)]

                if not EXPORT_TRI or len(f_v_orig) == 3:
                    f_v_iter = (f_v_orig, )
                else:
                    f_v_iter = (f_v_orig[0], f_v_orig[1], f_v_orig[2]), (f_v_orig[0], f_v_orig[2], f_v_orig[3])

                # support for triangulation
                for f_v in f_v_iter:
                    fw('f')

                    if faceuv:
                        if EXPORT_NORMALS:
                            if f_smooth:  # Smoothed, use vertex normals
                                for vi, v in f_v:
                                    fw(" %d/%d/%d" %
                                               (v.index + totverts,
                                                totuvco + uv_face_mapping[f_index][vi],
                                                globalNormals[veckey3d(v.normal)],
                                                ))  # vert, uv, normal

                            else:  # No smoothing, face normals
                                no = globalNormals[veckey3d(f.normal)]
                                for vi, v in f_v:
                                    fw(" %d/%d/%d" %
                                               (v.index + totverts,
                                                totuvco + uv_face_mapping[f_index][vi],
                                                no,
                                                ))  # vert, uv, normal
                        else:  # No Normals
                            for vi, v in f_v:
                                fw(" %d/%d" % (
                                           v.index + totverts,
                                           totuvco + uv_face_mapping[f_index][vi],
                                           ))  # vert, uv

                        face_vert_index += len(f_v)

                    else:  # No UV's
                        if EXPORT_NORMALS:
                            if f_smooth:  # Smoothed, use vertex normals
                                for vi, v in f_v:
                                    fw(" %d//%d" % (
                                               v.index + totverts,
                                               globalNormals[veckey3d(v.normal)],
                                               ))
                            else:  # No smoothing, face normals
                                no = globalNormals[veckey3d(f.normal)]
                                for vi, v in f_v:
                                    fw(" %d//%d" % (v.index + totverts, no))
                        else:  # No Normals
                            for vi, v in f_v:
                                fw(" %d" % (v.index + totverts))

                fw('\n')

            # Write edges.
            if EXPORT_EDGES:
                for ed in edges:
                    if ed.is_loose:
                        fw('f %d %d\n' % (ed.vertices[0] + totverts, ed.vertices[1] + totverts))

            # Make the indices global rather then per mesh
            totverts += len(me_verts)
            if faceuv:
                totuvco += uv_unique_count

            # clean up
            bpy.data.meshes.remove(me)

        if ob_main.dupli_type != 'NONE':
            ob_main.dupli_list_clear()
        log ('Processed <%s> in %s' % (ob_main.name,elapsed_short(start_obj)))
    file.close()
    log ('OBJ export time: %s' % elapsed_short(start_time))
    return mtl_dict

