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
import datetime
import unicodedata
import octanerender

def active_node_mat(mat):
    # TODO, 2.4x has a pipeline section, for 2.5 we need to communicate
    # which settings from node-materials are used
    if mat is not None:
        mat_node = mat.active_node_material
        if mat_node:
            return mat_node
        else:
            return mat
    return None

def elapsed_short(start):
    delta = datetime.datetime.now() - start
    return '%d.%03d secs' % (delta.seconds,delta.microseconds/1000)

def elapsed_long(start):
    delta = datetime.datetime.now() - start
    if delta.days == 0:
        return '%dh%dm%d.%02d' % (delta.seconds/3600, delta.seconds%3600/60, delta.seconds%60, delta.microseconds/10000)
    else:
        return '%dd %dh%dm%d.%02d' % (delta.days, delta.seconds/3600, delta.seconds%3600/60, delta.seconds%60, delta.microseconds/10000)

def notify_user( there ):
    if octanerender.Status_Severity == 0:
        there.report({'INFO'}, octanerender.Status_Text)
    if octanerender.Status_Severity == 1:
        there.report({'WARNING'}, octanerender.Status_Text)
    if octanerender.Status_Severity == 2:
        there.report({'ERROR'}, octanerender.Status_Text)

def update_status(severity,status):
    # 0 = Info
    # 1 = Warning
    # 2 = Error
    octanerender.Status_Severity = severity
    octanerender.Status_Text = status
    octanerender.Status_Display = True
    if severity == 0:
        log ('Status set to Info: ' + status)
    elif severity == 1:
        log ('Status set to Warning: ' + status)
    elif severity == 2:
        log ('Status set to Error: ' + status)
    else:
        # to avoid preset of error log into console
        octanerender.Status_Severity = 2

def log(log):
    if octanerender.Verbose:
        #print ('Octane plug-in ' + octanerender.Version + ' on %d.%d.%d' % tuple(bpy.app.version) + '.' + (bpy.app.build_revision) + ' : ' + (log))
        print ('Octane plug-in ' + octanerender.Version + ' on %d.%d.%d' % tuple(bpy.app.version) + ' : ' + (log))

def error(error):
    update_status(2,error)
    raise Exception("Octane plug-in: "+error)

def matrix_vect(mat,vec):
    vecr = [0,0,0,0]
    for i in range(4):
        for j in range(4):
            vecr[i] += vec[j] * mat[i][j]
    return vecr

def rotate90x(vect):
    return [vect[0],vect[2],-vect[1]]

def absPath(name):
    return os.path.abspath( bpy.path.abspath(name) )

def hasSpace(name):
    if name.find(' ') < 0:
        return False
    else:
        return True

def fixName(name):
    res = ''
    if name == None:
        res = 'None'
    else:
        res = unicodedata.normalize('NFKD', name).encode('ascii','ignore').decode('ascii','ignore').replace(' ','_')
    if name != res:
        log ('Fixed name <%s> to <%s>' % (name,res))
    return res

def copy_file(source, dest):
    log ('Copying file "%s" to "%s"' % (source,dest))
    file = open(source, 'rb')
    data = file.read()
    file.close()
    file = open(dest, 'wb')
    file.write(data)
    file.close()

def safe_rename(src,dst):
    # Stupid Windows!
    if os.path.isfile(dst):
        os.remove(dst)
    # Let's do the real job
    os.rename(src,dst)

# Return image to use in a sequence
def get_sequence(tex,frame):
    start = tex.image_user.frame_start
    offset = tex.image_user.frame_offset
    duration = tex.image_user.frame_duration
    cyclic = tex.image_user.use_cyclic
    #log('Frame %d, Start %d, Offset %d, Duration %d, Cyclic %s' % (frame,start,offset,duration,cyclic))
    seq = frame + offset - start + 1
    if seq <= 1:
        return 1
    if seq > duration:
        if not cyclic:
            return duration
        else:
            return seq % duration
    return seq

def get_rootname(name):
    digits = 0
    while name[-1].isnumeric():
        name = name[:-1]
        digits += 1
    if digits == 0:
        error ('Unable to find sequence number in <%s>' % (name))
    return name, digits
