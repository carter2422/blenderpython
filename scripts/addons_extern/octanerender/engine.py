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

import subprocess
import os
import time
import datetime
import mathutils
import bpy
import octanerender.settings
from octanerender.utils import *
from octanerender.export import *
from octanerender.ocs_nodes import *

class OctaneRenderEngine(bpy.types.RenderEngine):
    bl_idname = 'OCT_RENDER'
    bl_label = "Octane Render"
    bl_postprocess = False

    def render(self, scene):
        self.update_stats('', 'Octane: export started for frame# %d (see console for progress), please wait...' % (scene.frame_current))
        # Preset status to ERROR in case of plugin crash
        update_status(3,'Something wrong happened, please check console logs')

        # Accessors to both render environments
        octane_render = scene.octane_render
        blender_render = scene.render
        world = scene.world

        # Let's start
        start_time = datetime.datetime.now()

        # Get octane_render name
        baseName = fixName(octane_render.project_name)
        if baseName == '' or hasSpace(baseName):
            error('Project name is empty or contains spaces "%s"' % baseName)

        # Set and check project path
        basePath = absPath(octane_render.path)
        if not os.path.isdir(basePath) or hasSpace(basePath):
            error('Project directory is invalid or contains spaces "%s" ("%s")' % (octane_render.path,basePath))
        octanerender.dst_dir = basePath

        # Set and check image output path
        animPath = absPath(octane_render.image_output)
        if octanerender.pullImage == True:
            if (not os.path.isdir(animPath)) or hasSpace(animPath):
                error('Image output directory is invalid or contains spaces "%s" ("%s")' % (octane_render.path,animPath))

        # Set octane scene and obj filenames
        ocsFile = absPath('%s/%s.ocs' % (basePath,baseName))
        ocsTemp = absPath('%s/%s.ocs.temp' % (basePath,baseName))
        objFile = absPath('%s/%s.obj' % (basePath,baseName))
        objTemp = absPath('%s/%s.obj.temp' % (basePath,baseName))
        mtlFile = absPath('%s/%s.mtl' % (basePath,baseName))
        mtlTemp = absPath('%s/%s.mtl.temp' % (basePath,baseName))
        log ('Output ocs: "%s"' % (ocsFile))
        log ('Output obj: "%s"' % (objFile))
        log ('Output mtl: "%s"' % (mtlFile))

        #Set the unit factor (meters, centimeters, inches, etc...
        unitFactor = 1
        unitFactor = {0:0.001,1:0.01,2:0.1,3:1,4:10,5:100,6:1000,7:0.0254,8:0.3048,9:0.9144,10:201.168,11:1609.344}[int(octane_render.unit_size)]
        log ('Unit Factor (rescaling): %.4f' % (unitFactor))

        first_frame = True
        scene.frame_set(octanerender.frameStart)
        octanerender.frameCurrent = octanerender.frameStart
        renderRunning = False
        octanerender.delayed_copies = []
        x = blender_render.resolution_x
        y = blender_render.resolution_y
        resSize = blender_render.resolution_percentage/100
        while True:
            log ('Exporting frame #%d' % (scene.frame_current))
            if octanerender.cameraUpdateOnly == True:
                log ('Camera update only, skipping OBJ export')
            frame_time = datetime.datetime.now()
            # Export only first frame if fly mode, otherwise all frames
            if ((not octanerender.flyMode) or first_frame) and octanerender.cameraUpdateOnly == False:
                obj_list = obj_export(scene)
                mtl_list = write_obj(objTemp, mtlFile, obj_list, scene, unitFactor)
                if octane_render.export_materials:
                    write_mtl(mtlTemp, mtl_list, scene, octane_render.export_copy_images)
                #first_frame = False

            # Return to blender if export mode
            if not octanerender.launchOctane and octanerender.cameraUpdateOnly == False:
                safe_rename(objTemp,objFile)
                safe_rename(mtlTemp,mtlFile)
                break

            axes = ['x','y','z']
            paramDsp=''

            command_args = []
            # Check Octane binary
            exeFile = absPath(octane_render.binary)
            if not os.path.isfile(exeFile):
                error('Invalid Octane binary file "%s" ("%s")' % (octane_render.binary,exeFile))
            command_args.append(exeFile)

            # Set mesh object to use
            command_args.append('-m')
            command_args.append('%s.obj' % (baseName))

            # Manage Camera settings
            if octane_render.export_camera:
                # Check if we have a valid camera
                camOBJ = scene.camera
                if not camOBJ:
                    error('Scene has no camera selected')
                camCAM = camOBJ.data
                if camCAM.type != 'PERSP':
                    error('Only Perspective cameras can be exported')
                log ('Using camera : <%s.%s>' % (camOBJ.name,camCAM.name))

                # Set Lens Shift and fov
                fov = camCAM.angle*180.0/3.1415926536

                if y > x:
                    # Portrait mode
                    command_args.append('--cam-lensshift-right')
                    command_args.append('%f' % (camCAM.shift_x * y / x))
                    command_args.append('--cam-lensshift-up')
                    command_args.append('%f' % (camCAM.shift_y))
                    fov *= x / y
                else:
                    # Landscape mode
                    command_args.append('--cam-lensshift-right')
                    command_args.append('%f' % (camCAM.shift_x))
                    command_args.append('--cam-lensshift-up')
                    command_args.append('%f' % (camCAM.shift_y * x / y))

                command_args.append('--cam-fov')
                command_args.append('%f' % (fov))

                # Manage Lens Aperture
                if camCAM.OCT_use_lens_aperture:
                    command_args.append('--cam-aperture')
                    command_args.append('%f' % (camCAM.OCT_lens_aperture))
                    log ('Lens aperture: %f' % (camCAM.OCT_lens_aperture))

                # Manage Focal Depth / Depth of Field
                fd = 100.0
                log ('Using Depth of Field from : %s' % (camCAM.name))
                if camCAM.dof_object:
                    tarOBJ = bpy.data.objects.get(camCAM.dof_object.name)
                    if camCAM.dof_object.name == camOBJ.name:
                        error('Narcissic camera... stop looking at yourself!')
                    fd = (tarOBJ.location - camOBJ.location).magnitude
                    log ('Using DoF with distance to <%s> : %f * unitSize' % (tarOBJ.name,fd))
                else:
                    fd = camCAM.dof_distance
                    if fd < 0.00001:
                        fd = 0
                    log ('Using DoF from blender camera: %f * unitSize' % (fd))
                fd *= unitFactor
                # Ignore DoF of 0
                if fd > 0:
                    command_args.append('--cam-focaldepth')
                    command_args.append('%f' % (fd))

                # Set camera position and target
                matrix = camOBJ.matrix_world
                if octane_render.export_ROTX90 == True:
                    position = rotate90x(matrix_vect(matrix,[0.0,0.0,0.0,1.0]))
                    # position = rotate90x(camOBJ.location)
                    target = rotate90x(matrix_vect(matrix,[0.0,0.0,-1.0,1.0]))
                    up = rotate90x(matrix_vect(matrix,[0.0,1.0,0.0,0.0]))
                else:
                    position = matrix_vect(matrix,[0.0,0.0,0.0,1.0])
                    # position = camOBJ.location
                    target = matrix_vect(matrix,[0.0,0.0,-1.0,1.0])
                    up = matrix_vect(matrix,[0.0,1.0,0.0,0.0])
                for i in range(3):
                    command_args.append('--cam-pos-%s' % (axes[i]))
                    command_args.append('%f' % (position[i]*unitFactor))
                    if i==0:paramDsp=''
                    paramDsp+= '%s %f ' % (axes[i],position[i]*unitFactor)
                log ('Camera position: %s' % (paramDsp))
                for i in range(3):
                    command_args.append('--cam-target-%s' % (axes[i]))
                    command_args.append('%f' % (target[i]*unitFactor))
                    if i==0:paramDsp=''
                    paramDsp+= '%s %f ' % (axes[i],target[i]*unitFactor)
                log ('Camera target: %s' % (paramDsp))
                for i in range(3):
                    command_args.append('--cam-up-%s' % (axes[i]))
                    command_args.append('%f' % (up[i]*unitFactor))
                    if i==0:paramDsp=''
                    paramDsp+= '%s %f ' % (axes[i],up[i]*unitFactor)
                log ('Camera up: %s' % (paramDsp))

                # Manage camera Motion
                if camCAM.OCT_use_camera_motion:
                    currentFrame=scene.frame_current
                    # Interpolate on next frame
                    if camCAM.OCT_interpolate_frame=='0':
                        scene.frame_set(currentFrame + 1)
                        log ('Motion interploate on next frame')
                    # Interpolate on previous frame
                    elif currentFrame>1:
                        scene.frame_set(currentFrame - 1)
                        log ('Motion interpolate on previous frame')

                    matrix = camOBJ.matrix_world
                    if octane_render.export_ROTX90 == True:
                        position = rotate90x(matrix_vect(matrix,[0.0,0.0,0.0,1.0]))
                        target = rotate90x(matrix_vect(matrix,[0.0,0.0,-1.0,1.0]))
                        up = rotate90x(matrix_vect(matrix,[0.0,1.0,0.0,0.0]))
                    else:
                        position = matrix_vect(matrix,[0.0,0.0,0.0,1.0])
                        target = matrix_vect(matrix,[0.0,0.0,-1.0,1.0])
                        up = matrix_vect(matrix,[0.0,1.0,0.0,0.0])
                    up = rotate90x(matrix_vect(matrix,[0.0,1.0,0.0,0.0]))

                    for i in range(3):
                        command_args.append('--cam-motion-pos-%s' % (axes[i]))
                        command_args.append('%f' % (position[i]*unitFactor))
                        if i==0:paramDsp=''
                        paramDsp+= '%s %f ' % (axes[i],position[i]*unitFactor)
                    log ('Camera motion position: %s' % (paramDsp))
                    for i in range(3):
                        command_args.append('--cam-motion-target-%s' % (axes[i]))
                        command_args.append('%f' % (target[i]*unitFactor))
                        if i==0:paramDsp=''
                        paramDsp+= '%s %f ' % (axes[i],target[i]*unitFactor)
                    log ('Camera motion target: %s' % (paramDsp))
                    for i in range(3):
                        command_args.append('--cam-motion-up-%s' % (axes[i]))
                        command_args.append('%f' % (up[i]*unitFactor))
                        if i==0:paramDsp=''
                        paramDsp+= '%s %f ' % (axes[i],up[i]*unitFactor)
                    log ('Camera motion up: %s' % (paramDsp))
                    scene.frame_set(currentFrame)

            projectFileAlreadyExists = False
            if os.path.isfile(ocsFile):
                    projectFileAlreadyExists=True
                    log ('Project file already exists')

            # Manage the resolution option
            if  octane_render.resolution:
                log ('Resolution set to %d x %d at %d%%' % (x,y,resSize*100))
                command_args.append('--film-width')
                command_args.append('%i' % (x*resSize))
                command_args.append('--film-height')
                command_args.append('%i' % (y*resSize))

            #Set the GPUs option
            if octane_render.GPU_selector:
                for val in octane_render.GPU_use_list.split(' '):
                        command_args.append('-g')
                        command_args.append('%s' % (val))
                log ('GPUs to use: %s' % (octane_render.GPU_use_list))

            outputExtension = 'png'
            if octane_render.output_mode == 'OUTPUT_EXR' or octane_render.output_mode == 'OUTPUT_EXR_TM':
                outputExtension = 'exr'
            # Set the image name based on frame number
            pngFile = absPath('%s/%s_%06d.%s' %(animPath,baseName,scene.frame_current,outputExtension))
            # Setting stuff if pulling image
            if octanerender.pullImage:
                # Set the exit after rendering flag (for animation or pulling back image)
                command_args.append('-e')
                command_args.append('-q')
                if octane_render.output_mode == 'OUTPUT_PNG':
                    command_args.append('--output-png')
                if octane_render.output_mode == 'OUTPUT_PNG16':
                    command_args.append('--output-png16')
                if octane_render.output_mode == 'OUTPUT_EXR':
                    command_args.append('--output-exr')
                if octane_render.output_mode == 'OUTPUT_EXR_TM':
                    command_args.append('--output-exr-tm')
                command_args.append(pngFile)

            # Set samples to render
            command_args.append('-s')
            command_args.append('%d' % (octanerender.maxSamples))
            log ('Samples per image: %d' % (octanerender.maxSamples))

            # Create OCS from template if it doesn't exisits or replace forced, otherwise load from ocs
            if not projectFileAlreadyExists or octanerender.replace_project:
                OCS = ocsParse(template_ocs.splitlines())
                ocsMeshNameUpdate(OCS, objFile)
            else:
                OCS = ocsParseFile(ocsFile)
            projectFileAlreadyExists = True

            if octane_render.write_ocs:
                ocsMaterialsUpdate(OCS, mtl_list)

            # Update ocs Mesh Preview kernel
            if world.OCT_kernel_use:
                ocsKernelUpdate(OCS, scene)

            # Update ocs Mesh Preview Environment
            if world.OCT_environment_use:
                ocsEnvironmentUpdate(OCS, scene)

            # Update ocs Mesh Preview Environment
            if world.OCT_imager_use:
                ocsImagerUpdate(OCS, scene)

            ocsWriteFile(ocsTemp,OCS)

            # Check if ocs needs to be overwritten or obj relinked
            #if projectFileAlreadyExists and not octanerender.replace_project:
            #    if octane_render.relink_obj == True:
            #        log ('Project exists and obj will be relinked')
            command_args.append('-r')
            command_args.append(objFile)
            #    else:
            #        log ('Project exists and obj will NOT be relinked')
            #else:
            #    log ('Create or replace project')
            #    command_args.append('-l')
            #    command_args.append(objFile)
            #    command_args.append('-n')
            octanerender.replace_project = False
            # Last argument: ocs file
            command_args.append(ocsFile)

            abort_render = False
            while True:
                if renderRunning:
                    # There's already a frame being rendered, wait for it to finish
                    log ('Waiting for previous frame to finish')
                    #self.update_stats('', 'Now rendering frame# %d (see console for progress), please wait...' % (frameRunning))
                    while octane_process.poll() == None:
                        if self.test_break():
                            try:
                                octane_process.terminate()
                                abort_render = True
                            except:
                                pass
                            break
                        time.sleep(1)
                    # Render finished, pull image
                    result = self.begin_result(0, 0, x*resSize, y*resSize)
                    try:
                        log ('Load image from file: %s' % o_pngFile)
                        result.layers[0].load_from_file(o_pngFile)
                    except:
                        log ('Unable to load image from file: %s' % o_pngFile)
                    self.end_result(result)
                    self.update_stats('', 'Octane: last frame/export took %s, now rendering frame# %d (see console for progress), please wait...' % (elapsed_short(frame_time),frameRunning + scene.frame_step))
                    renderRunning = False
                    # That was last frame to render
                    if frameRunning >= octanerender.frameStop:
                        break
                    if abort_render:
                        error ('Render aborted by user')
#               else:
                # Rename OBJ/MTL before launching Octane
                if ((not octanerender.flyMode) or first_frame) and octanerender.cameraUpdateOnly == False:
                    safe_rename(objTemp,objFile)
                    safe_rename(mtlTemp,mtlFile)
                    safe_rename(ocsTemp,ocsFile)
                    for (src,dst) in octanerender.delayed_copies:
                        copy_file(src,dst)
                    octanerender.delayed_copies = []
                first_frame = False
                # Now let's start the magic!
                log ('Launching Octane: {}'.format(command_args))
                octane_process = subprocess.Popen(command_args,executable=exeFile)
                o_pngFile = pngFile
                renderRunning = True
                frameRunning = scene.frame_current
                # Exit loop if not pulling image
                if not octanerender.pullImage:
                    break
                # Exit loop if another frame to render
                if scene.frame_current < octanerender.frameStop:
                    break

            # Step into next frame
            scene.frame_set(scene.frame_current + scene.frame_step)
            octanerender.frameCurrent = scene.frame_current
            if scene.frame_current > octanerender.frameStop:
                # Was last frame, exiting
                scene.frame_set(octanerender.frameStart)
                break

        # Yes, we made it!
        # octane_render.replace_project = False
        update_status(0,'Completed in %s' % elapsed_long(start_time))

    def render2(self, scene):
        self.update_stats('', 'Octane: export started for frame# %d (see console for progress), please wait...' % (scene.frame_current))
        # Preset status to ERROR in case of plugin crash
        update_status(3,'Something wrong happened, please check console logs')

        # Accessors to both render environments
        octane_render = scene.octane_render
        blender_render = scene.render
        world = scene.world

        # Let's start
        start_time = datetime.datetime.now()

        # Get octane_render name
        baseName = fixName(octane_render.project_name)
        if baseName == '' or hasSpace(baseName):
            error('Project name is empty or contains spaces "%s"' % baseName)

        # Set and check project path
        basePath = absPath(octane_render.path)
        if not os.path.isdir(basePath) or hasSpace(basePath):
            error('Project directory is invalid or contains spaces "%s" ("%s")' % (octane_render.path,basePath))
        octanerender.dst_dir = basePath

        # Set and check image output path
        animPath = absPath(octane_render.image_output)
        if octanerender.pullImage == True:
            if (not os.path.isdir(animPath)) or hasSpace(animPath):
                error('Image output directory is invalid or contains spaces "%s" ("%s")' % (octane_render.path,animPath))

        # Set octane scene and obj filenames
        ocsFile = absPath('%s/%s.ocs' % (basePath,baseName))
        ocsTemp = absPath('%s/%s.ocs.temp' % (basePath,baseName))
        objFile = absPath('%s/%s.obj' % (basePath,baseName))
        objTemp = absPath('%s/%s.obj.temp' % (basePath,baseName))
        mtlFile = absPath('%s/%s.mtl' % (basePath,baseName))
        mtlTemp = absPath('%s/%s.mtl.temp' % (basePath,baseName))
        log ('Output ocs: "%s"' % (ocsFile))
        log ('Output obj: "%s"' % (objFile))
        log ('Output mtl: "%s"' % (mtlFile))

        #Set the unit factor (meters, centimeters, inches, etc...
        unitFactor = 1
        unitFactor = {0:0.001,1:0.01,2:0.1,3:1,4:10,5:100,6:1000,7:0.0254,8:0.3048,9:0.9144,10:201.168,11:1609.344}[int(octane_render.unit_size)]
        log ('Unit Factor (rescaling): %.4f' % (unitFactor))

        renderRunning = False
        if octane_render.panel_mode == MODE_EXPORT:
            exportScene()
            update_status(0,'Completed in %s' % elapsed_long(start_time))
            return
        elif octane_render.panel_mode == MODE_RENDER or octane_render.panel_mode == MODE_CAMERA:
            exportScene()
            startRender(0,0)
            if octanerender.pullImage: waitRender()
            update_status(0,'Completed in %s' % elapsed_long(start_time))
            return
        elif octane_render.panel_mode == MODE_BUCKET:
            exportScene()
            for i in range(1,octane_render.bucketX):
                for j in range(1,octane_render.bucketY):
                    if renderRunning: waitRender()
                    pngFile = absPath('%s/%s_%02dx%02d.png' %(animPath,baseName,i,j))
                    startRender(i,j)
                    renderRunning = True
            update_status(0,'Completed in %s' % elapsed_long(start_time))
            return
        elif octane_render.panel_mode == MODE_ANIM:
            for i in range(octanerender.frameStart,octanerender.frameStop,octanerender.frameStep):
                    exportScene()
                    if renderRunning: waitRender()
                    pngFile = absPath('%s/%s_%06d.png' %(animPath,baseName,scene.frame_current))
                    startRender(0,0)
                    renderRunning = True
            waitRender()
            update_status(0,'Completed in %s' % elapsed_long(start_time))
            return


        first_frame = True
        scene.frame_set(octanerender.frameStart)
        octanerender.frameCurrent = octanerender.frameStart
        renderRunning = False
        octanerender.delayed_copies = []
        x = blender_render.resolution_x
        y = blender_render.resolution_y
        resSize = blender_render.resolution_percentage/100
        while True:
            log ('Exporting frame #%d' % (scene.frame_current))
            frame_time = datetime.datetime.now()
            # Export only first frame if fly mode, otherwise all frames
            if (not octanerender.flyMode) or first_frame:
                obj_list = obj_export(scene)
                mtl_list = write_obj(objTemp, mtlFile, obj_list, scene, unitFactor)
                if octane_render.export_materials:
                    write_mtl(mtlTemp, mtl_list, scene, octane_render.export_copy_images)
                #first_frame = False

            # Return to blender if export mode
            if not octanerender.launchOctane:
                safe_rename(objTemp,objFile)
                safe_rename(mtlTemp,mtlFile)
                break

            axes = ['x','y','z']
            paramDsp=''

            command_args = []
            # Check Octane binary
            exeFile = absPath(octane_render.binary)
            if not os.path.isfile(exeFile):
                error('Invalid Octane binary file "%s" ("%s")' % (octane_render.binary,exeFile))
            command_args.append(exeFile)

            # Set mesh object to use
            command_args.append('-m')
            command_args.append('%s.obj' % (baseName))

            # Manage Camera settings
            if octane_render.export_camera:
                # Check if we have a valid camera
                camOBJ = scene.camera
                if not camOBJ:
                    error('Scene has no camera selected')
                camCAM = camOBJ.data
                if camCAM.type != 'PERSP':
                    error('Only Perspective cameras can be exported')
                log ('Using camera : <%s.%s>' % (camOBJ.name,camCAM.name))

                # Set Lens Shift and fov
                fov = camCAM.angle*180.0/3.1415926536

                if y > x:
                    # Portrait mode
                    command_args.append('--cam-lensshift-right')
                    command_args.append('%f' % (camCAM.shift_x * y / x))
                    command_args.append('--cam-lensshift-up')
                    command_args.append('%f' % (camCAM.shift_y))
                    fov *= x / y
                else:
                    # Landscape mode
                    command_args.append('--cam-lensshift-right')
                    command_args.append('%f' % (camCAM.shift_x))
                    command_args.append('--cam-lensshift-up')
                    command_args.append('%f' % (camCAM.shift_y * x / y))

                command_args.append('--cam-fov')
                command_args.append('%f' % (fov))

                # Manage Lens Aperture
                if camCAM.OCT_use_lens_aperture:
                    command_args.append('--cam-aperture')
                    command_args.append('%f' % (camCAM.OCT_lens_aperture))
                    log ('Lens aperture: %f' % (camCAM.OCT_lens_aperture))

                # Manage Focal Depth / Depth of Field
                fd = 100.0
                log ('Using Depth of Field from : %s' % (camCAM.name))
                if camCAM.dof_object:
                    tarOBJ = bpy.data.objects.get(camCAM.dof_object.name)
                    if camCAM.dof_object.name == camOBJ.name:
                        error('Narcissic camera... stop looking at yourself!')
                    fd = (tarOBJ.location - camOBJ.location).magnitude
                    log ('Using DoF with distance to <%s> : %f * unitSize' % (tarOBJ.name,fd))
                else:
                    fd = camCAM.dof_distance
                    if fd < 0.00001:
                        fd = 0
                    log ('Using DoF from blender camera: %f * unitSize' % (fd))
                fd *= unitFactor
                # Ignore DoF of 0
                if fd > 0:
                    command_args.append('--cam-focaldepth')
                    command_args.append('%f' % (fd))

                # Set camera position and target
                matrix = camOBJ.matrix_world
                if octane_render.export_ROTX90 == True:
                    position = rotate90x(matrix_vect(matrix,[0.0,0.0,0.0,1.0]))
                    target = rotate90x(matrix_vect(matrix,[0.0,0.0,-1.0,1.0]))
                    up = rotate90x(matrix_vect(matrix,[0.0,1.0,0.0,0.0]))
                else:
                    position = matrix_vect(matrix,[0.0,0.0,0.0,1.0])
                    target = matrix_vect(matrix,[0.0,0.0,-1.0,1.0])
                    up = matrix_vect(matrix,[0.0,1.0,0.0,0.0])
                for i in range(3):
                    command_args.append('--cam-pos-%s' % (axes[i]))
                    command_args.append('%f' % (position[i]*unitFactor))
                    if i==0:paramDsp=''
                    paramDsp+= '%s %f ' % (axes[i],position[i]*unitFactor)
                log ('Camera position: %s' % (paramDsp))
                for i in range(3):
                    command_args.append('--cam-target-%s' % (axes[i]))
                    command_args.append('%f' % (target[i]*unitFactor))
                    if i==0:paramDsp=''
                    paramDsp+= '%s %f ' % (axes[i],target[i]*unitFactor)
                log ('Camera target: %s' % (paramDsp))
                for i in range(3):
                    command_args.append('--cam-up-%s' % (axes[i]))
                    command_args.append('%f' % (up[i]*unitFactor))
                    if i==0:paramDsp=''
                    paramDsp+= '%s %f ' % (axes[i],up[i]*unitFactor)
                log ('Camera up: %s' % (paramDsp))

                # Manage camera Motion
                if camCAM.OCT_use_camera_motion:
                    currentFrame=scene.frame_current
                    # Interpolate on next frame
                    if camCAM.OCT_interpolate_frame=='0':
                        scene.frame_set(currentFrame + 1)
                        log ('Motion interploate on next frame')
                    # Interpolate on previous frame
                    elif currentFrame>1:
                        scene.frame_set(currentFrame - 1)
                        log ('Motion interpolate on previous frame')

                    matrix = camOBJ.matrix_world
                    if octane_render.export_ROTX90 == True:
                        position = rotate90x(matrix_vect(matrix,[0.0,0.0,0.0,1.0]))
                        target = rotate90x(matrix_vect(matrix,[0.0,0.0,-1.0,1.0]))
                        up = rotate90x(matrix_vect(matrix,[0.0,1.0,0.0,0.0]))
                    else:
                        position = matrix_vect(matrix,[0.0,0.0,0.0,1.0])
                        target = matrix_vect(matrix,[0.0,0.0,-1.0,1.0])
                        up = matrix_vect(matrix,[0.0,1.0,0.0,0.0])
                    up = rotate90x(matrix_vect(matrix,[0.0,1.0,0.0,0.0]))

                    for i in range(3):
                        command_args.append('--cam-motion-pos-%s' % (axes[i]))
                        command_args.append('%f' % (position[i]*unitFactor))
                        if i==0:paramDsp=''
                        paramDsp+= '%s %f ' % (axes[i],position[i]*unitFactor)
                    log ('Camera motion position: %s' % (paramDsp))
                    for i in range(3):
                        command_args.append('--cam-motion-target-%s' % (axes[i]))
                        command_args.append('%f' % (target[i]*unitFactor))
                        if i==0:paramDsp=''
                        paramDsp+= '%s %f ' % (axes[i],target[i]*unitFactor)
                    log ('Camera motion target: %s' % (paramDsp))
                    for i in range(3):
                        command_args.append('--cam-motion-up-%s' % (axes[i]))
                        command_args.append('%f' % (up[i]*unitFactor))
                        if i==0:paramDsp=''
                        paramDsp+= '%s %f ' % (axes[i],up[i]*unitFactor)
                    log ('Camera motion up: %s' % (paramDsp))
                    scene.frame_set(currentFrame)

            projectFileAlreadyExists = False
            if os.path.isfile(ocsFile):
                    projectFileAlreadyExists=True
                    log ('Project file already exists')

            # Manage the resolution option
            if  octane_render.resolution:
                log ('Resolution set to %d x %d at %d%%' % (x,y,resSize*100))
                command_args.append('--film-width')
                command_args.append('%i' % (x*resSize))
                command_args.append('--film-height')
                command_args.append('%i' % (y*resSize))

            #Set the GPUs option
            if octane_render.GPU_selector:
                for val in octane_render.GPU_use_list.split(' '):
                        command_args.append('-g')
                        command_args.append('%s' % (val))
                log ('GPUs to use: %s' % (octane_render.GPU_use_list))

            outputExtension = 'png'
            if octane_render.output_mode == 'OUPUT_EXR' or octane_render.output_mode == 'OUTPUT_EXR_TM':
                outputExtension = 'exr'
            # Set the image name based on frame number
            pngFile = absPath('%s/%s_%06d.%s' %(animPath,baseName,scene.frame_current,outputExtension))
            # Setting stuff if pulling image
            if octanerender.pullImage:
                # Set the exit after rendering flag (for animation or pulling back image)
                command_args.append('-e')
                command_args.append('-q')
                if octane_render.output_mode == 'OUTPUT_PNG':
                    command_args.append('--output-png')
                if octane_render.output_mode == 'OUTPUT_PNG16':
                    command_args.append('--output-png16')
                if octane_render.output_mode == 'OUTPUT_EXR':
                    command_args.append('--output-exr')
                if octane_render.output_mode == 'OUTPUT_EXR_TM':
                    command_args.append('--output-exr-tm')
                command_args.append(pngFile)

            # Set samples to render
            command_args.append('-s')
            command_args.append('%d' % (octanerender.maxSamples))
            log ('Samples per image: %d' % (octanerender.maxSamples))

            # Create OCS from template if it doesn't exisits or replace forced, otherwise load from ocs
            if not projectFileAlreadyExists or octanerender.replace_project:
                OCS = ocsParse(template_ocs.splitlines())
                ocsMeshNameUpdate(OCS, objFile)
            else:
                OCS = ocsParseFile(ocsFile)
            projectFileAlreadyExists = True

            if octane_render.write_ocs:
                ocsMaterialsUpdate(OCS, mtl_list)

            # Update ocs Mesh Preview kernel
            if world.OCT_kernel_use:
                ocsKernelUpdate(OCS, scene)

            # Update ocs Mesh Preview Environment
            if world.OCT_environment_use:
                ocsEnvironmentUpdate(OCS, scene)

            # Update ocs Mesh Preview Environment
            if world.OCT_imager_use:
                ocsImagerUpdate(OCS, scene)

            ocsWriteFile(ocsTemp,OCS)

            # Check if ocs needs to be overwritten or obj relinked
            #if projectFileAlreadyExists and not octanerender.replace_project:
            #    if octane_render.relink_obj == True:
            #        log ('Project exists and obj will be relinked')
            command_args.append('-r')
            command_args.append(objFile)
            #    else:
            #        log ('Project exists and obj will NOT be relinked')
            #else:
            #    log ('Create or replace project')
            #    command_args.append('-l')
            #    command_args.append(objFile)
            #    command_args.append('-n')
            octanerender.replace_project = False
            # Last argument: ocs file
            command_args.append(ocsFile)

            abort_render = False
            while True:
                if renderRunning:
                    # There's already a frame being rendered, wait for it to finish
                    log ('Waiting for previous frame to finish')
                    #self.update_stats('', 'Now rendering frame# %d (see console for progress), please wait...' % (frameRunning))
                    while octane_process.poll() == None:
                        if self.test_break():
                            try:
                                octane_process.terminate()
                                abort_render = True
                            except:
                                pass
                            break
                        time.sleep(1)
                    # Render finished, pull image
                    result = self.begin_result(0, 0, x*resSize, y*resSize)
                    try:
                        log ('Load image from file: %s' % o_pngFile)
                        result.layers[0].load_from_file(o_pngFile)
                    except:
                        log ('Unable to load image from file: %s' % o_pngFile)
                    self.end_result(result)
                    self.update_stats('', 'Octane: last frame/export took %s, now rendering frame# %d (see console for progress), please wait...' % (elapsed_short(frame_time),frameRunning + scene.frame_step))
                    renderRunning = False
                    # That was last frame to render
                    if frameRunning >= octanerender.frameStop:
                        break
                    if abort_render:
                        error ('Render aborted by user')
#               else:
                # Rename OBJ/MTL before launching Octane
                if (not octanerender.flyMode) or first_frame:
                    safe_rename(objTemp,objFile)
                    safe_rename(mtlTemp,mtlFile)
                    safe_rename(ocsTemp,ocsFile)
                    for (src,dst) in octanerender.delayed_copies:
                        copy_file(src,dst)
                    octanerender.delayed_copies = []
                first_frame = False
                # Now let's start the magic!
                log ('Launching Octane: {}'.format(command_args))
                octane_process = subprocess.Popen(command_args,executable=exeFile)
                o_pngFile = pngFile
                renderRunning = True
                frameRunning = scene.frame_current
                # Exit loop if not pulling image
                if not octanerender.pullImage:
                    break
                # Exit loop if another frame to render
                if scene.frame_current < octanerender.frameStop:
                    break

            # Step into next frame
            scene.frame_set(scene.frame_current + scene.frame_step)
            octanerender.frameCurrent = scene.frame_current
            if scene.frame_current > octanerender.frameStop:
                # Was last frame, exiting
                scene.frame_set(octanerender.frameStart)
                break

        # Yes, we made it!
        # octane_render.replace_project = False
        update_status(0,'Completed in %s' % elapsed_long(start_time))

