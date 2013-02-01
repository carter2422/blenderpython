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

# <pep8 compliant>

import os
import bpy
import mathutils
from octanerender.utils import *
from octanerender.ocs_templates import *

class ocsElem:
    def __init__(self, parent, name, value):
        self.parent = parent
        self.name = name
        self.value = value
        self.children = []

    def clean(self, name, value):
        self.name = name
        self.value = value
        self.children = []

    def replaceChildrenFrom(self, elem):
        id = self.getChildValue("id")
        self.children = []
        for child in elem.children:
            self.children.append(child)
        if id:
            self.setChildValue("id",id)

    def addChild(self, name, value):
        child = ocsElem(self, name, value)
        self.children.append( child )
        return child

    def delChild(self, name, value):
        # Will only delete the first Child with name/value
        for child in self.children:
            if child.name == name and child.value == value:
                children.remove(child)
                return True
        return False

    def getElemFromChild(self, name, value):
        if self.name == name and self.value == value:
            return self.parent
        for child in self.children:
            found = child.getElemFromChild(name, value)
            if found: return found
        return None

    def getElemFromName(self, name):
        if self.name == name:
            return self
        for child in self.children:
            found = child.getElemFromName(name)
            if found: return found
        return None

    def getChildValue(self, name):
        for child in self.children:
            if child.name == name:
                return child.value
        return None

    def setChildValue(self, name, value):
        for child in self.children:
            if child.name == name:
                child.value = value
                return True
        return False

    def dump(self):
        print ("[%s,%s]" % (self.name,self.value))
        for child in self.children:
            child.dump()

    def write(self, file, indent):
        if self.name == "": return
        if self.value == "":
            # Node
            file.write(" " * indent + ( "<%s>\n" % (self.name)))
            for child in self.children:
                child.write(file, indent+1)
            file.write(" " * indent + ( "</%s>\n" % (self.name)))
        else:
            # Value
            file.write(" " * indent + ( "<%s>%s</%s>\n" % (self.name,self.value,self.name)))

    def addParameters(self, value, minvalue, maxvalue, usetexturealphaui, isloglincapable, uselogscale, resolution, modified):
        parameters = self.addChild("parameters","")
        parameters.addChild("value", str(value))
        parameters.addChild("minvalue", minvalue)
        parameters.addChild("maxvalue", maxvalue)
        parameters.addChild("usetexturealphaui", usetexturealphaui)
        parameters.addChild("isloglincapable", isloglincapable)
        parameters.addChild("uselogscale", uselogscale)
        parameters.addChild("resolution", resolution)
        parameters.addChild("modified", modified)

    def addParametersBool(self, value):
        parameters = self.addChild("parameters","")
        if value: val = "true"
        else: val = "false"
        parameters.addChild("value", val)
        parameters.addChild("modified", "true")

    def addParametersStdFloatTexture(self, value):
        self.addParameters(value,"0","1","false","false","false","0.001","true")

    def addParametersRoughnessFloatTexture(self, value):
        self.addParameters(value,"1e-07","1","false","true","true","1e-07","true")

    def addNodePinInternal(self, id, typename, pintype):
        NodePin = self.addChild("NodePin", "")
        NodePin.addChild("typename", typename)
        NodePin.addChild("id", str(id))
        NodePin.addChild("pintype", pintype)
        NodePin.addChild("hasinternalnodegraph", "true")
        NodePin.addChild("basenodeid", "1")
        NodePin.addChild("basenodepinid", "0")
        internalnodegraph = NodePin.addChild("internalnodegraph", "")
        return internalnodegraph

    def addNodeGraph(self, typename):
        NodeGraph = self.addChild("NodeGraph", "")
        NodeGraph.addChild("name", typename)
        NodeGraph.addChild("currentnewnodeid", "2")
        NodeGraph.addChild("currentnewnodepinconnectionid", "1")
        nodes = NodeGraph.addChild("nodes", "")
        #~ Node = nodes.addChild("Node", "")
        NodeGraph.addChild("nodepinconnections", "")
        return nodes

    def addNode(self, name, typename):
        Node = self.addChild("Node", "")
        Node.addChild("name", name)
        Node.addChild("typename", typename)
        Node.addChild("id", "1")
        Node.addChild("position", "0 0")
        return Node

    def addNodePinExternal(self, id, typename, pintype):
        NodePin = self.addChild("NodePin", "")
        NodePin.addChild("typename", typename)
        NodePin.addChild("id", str(id))
        NodePin.addChild("pintype", pintype)
        NodePin.addChild("hasinternalnodegraph", "false")
        return NodePin

    def addFullNode(self, id, typename1, typename2, pintype):
        internalnodegraph = self.addNodePinInternal(id, typename1, pintype)
        nodes = internalnodegraph.addNodeGraph(typename1)
        Node = nodes.addNode(typename1, typename2)
        return Node, nodes

    def addRGBspectrum(self, id, typename, spectrum):
        Node, nodes = self.addFullNode(id, typename, "RGBspectrum", "20000")
        parameters = Node.addChild("parameters", "")
        parameters.addChild("rgbvalue", "%f %f %f" % tuple([c for c in spectrum]))
        Node.addChild("inputnodepins", "")

    def addFilmWidth(self, id, mat):
        Node, nodes = self.addFullNode(id, "filmwidth", "floattexture", "20000")
        Node.addParametersStdFloatTexture(mat.OCT_filmwidth)
        Node.addChild("inputnodepins", "")

    def addFilmIndex(self, id, mat):
        Node, nodes = self.addFullNode(id, "filmindex", "float", "20001")
        parameters = Node.addChild("parameters","")
        parameters.addChild("value", str(mat.OCT_filmindex))
        parameters.addChild("minvalue", "1")
        parameters.addChild("maxvalue", "8")
        parameters.addChild("usetextureui", "false")
        parameters.addChild("usetexturealphaui", "false")
        parameters.addChild("isloglincapable", "true")
        parameters.addChild("uselogscale", "true")
        parameters.addChild("modified", "false")
        Node.addChild("inputnodepins", "")

    def addIndex(self, id, mat):
        Node, nodes = self.addFullNode(id, "index", "float", "20001")
        parameters = Node.addChild("parameters","")
        parameters.addChild("value", str(mat.OCT_index))
        parameters.addChild("minvalue", "1")
        parameters.addChild("maxvalue", "8")
        parameters.addChild("usetextureui", "false")
        parameters.addChild("usetexturealphaui", "false")
        parameters.addChild("isloglincapable", "true")
        parameters.addChild("uselogscale", "true")
        parameters.addChild("modified", "false")
        Node.addChild("inputnodepins", "")

    def addRoughnessFloatTexture(self, id, mat):
        Node, nodes = self.addFullNode(id, "roughness", "floattexture", "20000")
        Node.addParametersRoughnessFloatTexture(mat.OCT_roughnessfloat)
        Node.addChild("inputnodepins", "")

    def addSpecularFloatTexture(self, id, mat):
        Node, nodes = self.addFullNode(id, "specular", "floattexture", "20000")
        Node.addParametersStdFloatTexture(mat.OCT_specular.floattexture)
        Node.addChild("inputnodepins", "")

    def addReflectionFloatTexture(self, id, mat):
        Node, nodes = self.addFullNode(id, "reflection", "floattexture", "20000")
        Node.addParametersStdFloatTexture(mat.OCT_specular.floattexture)
        Node.addChild("inputnodepins", "")

    def addNormalFloatTexture(self, id, mat):
        Node, nodes = self.addFullNode(id, "normal", "floattexture", "20000")
        Node.addParametersStdFloatTexture(0)
        Node.addChild("inputnodepins", "")

    def addSmooth(self, id, mat):
        Node, nodes = self.addFullNode(id, "smooth", "bool", "20003")
        Node.addParametersBool(mat.OCT_smooth)
        Node.addChild("inputnodepins", "")

    def addBumpNone(self, id, mat):
        Node, nodes = self.addFullNode(id, "bump", "floattexture", "20000")
        Node.addParametersStdFloatTexture(0)
        Node.addChild("inputnodepins", "")

    def addNormalNone(self, id, mat):
        Node, nodes = self.addFullNode(id, "normal", "floattexture", "20000")
        Node.addParametersStdFloatTexture(0)
        Node.addChild("inputnodepins", "")

    def addOpacityFloatTexture(self, id, mat):
        Node, nodes = self.addFullNode(id, "opacity", "floattexture", "20000")
        Node.addParameters(mat.OCT_opacity.floattexture,"0","1","true","false","false","0.001","true")
        Node.addChild("inputnodepins", "")

    def addTemperature(self, id, mat):
        Node, nodes = self.addFullNode(id, "temperature", "float", "20001")
        parameters = Node.addChild("parameters","")
        parameters.addChild("value", str(mat.OCT_temperature))
        parameters.addChild("minvalue", "500")
        parameters.addChild("maxvalue", "12000")
        parameters.addChild("usetextureui", "false")
        parameters.addChild("usetexturealphaui", "false")
        parameters.addChild("isloglincapable", "false")
        parameters.addChild("uselogscale", "false")
        parameters.addChild("modified", "false")
        Node.addChild("inputnodepins", "")

    def addPower(self, id, mat):
        Node, nodes = self.addFullNode(id, "power", "float", "20001")
        parameters = Node.addChild("parameters","")
        parameters.addChild("value", str(mat.OCT_power))
        parameters.addChild("minvalue", "0.01")
        parameters.addChild("maxvalue", "100")
        parameters.addChild("usetextureui", "false")
        parameters.addChild("usetexturealphaui", "false")
        parameters.addChild("isloglincapable", "true")
        parameters.addChild("uselogscale", "true")
        parameters.addChild("modified", "false")
        Node.addChild("inputnodepins", "")

    def addTexPower(self, id, OCT_tex):
        Node, nodes = self.addFullNode(id, "power", "floattexture", "20000")
        parameters = Node.addChild("parameters","")
        parameters.addChild("value", str(OCT_tex.power))
        parameters.addChild("minvalue", "0")
        parameters.addChild("maxvalue", "1")
        parameters.addChild("usetexturealphaui", "false")
        parameters.addChild("isloglincapable", "false")
        parameters.addChild("uselogscale", "false")
        parameters.addChild("resolution", "0.001")
        parameters.addChild("modified", "true")
        Node.addChild("inputnodepins", "")

    def addTexGamma(self, id, OCT_tex):
        Node, nodes = self.addFullNode(id, "gamma", "float", "20001")
        parameters = Node.addChild("parameters","")
        parameters.addChild("value", str(OCT_tex.gamma))
        parameters.addChild("minvalue", "0.1")
        parameters.addChild("maxvalue", "8")
        parameters.addChild("usetextureui", "false")
        parameters.addChild("usetexturealphaui", "false")
        parameters.addChild("isloglincapable", "true")
        parameters.addChild("uselogscale", "true")
        parameters.addChild("modified", "false")
        Node.addChild("inputnodepins", "")

    def addTexScale(self, id, OCT_tex, mat):
        Node, nodes = self.addFullNode(id, "scale", "float2", "20001")
        parameters = Node.addChild("parameters","")
        scaleX = 1.0
        scaleY = 1.0
        mtex = mat.texture_slots.get(OCT_tex.texture)
        if mtex:
            scaleX = mtex.scale.x
            scaleY = mtex.scale.y
        parameters.addChild("valuexy", "%f %f" % (scaleX,scaleY))
        parameters.addChild("minvalue", "0.001")
        parameters.addChild("maxvalue", "1000")
        parameters.addChild("modified", "false")
        Node.addChild("inputnodepins", "")

    def addTexInvert(self, id, OCT_tex):
        Node, nodes = self.addFullNode(id, "invert", "bool", "20003")
        Node.addParametersBool(OCT_tex.invert)
        Node.addChild("inputnodepins", "")

    def addNormalize(self, id, mat):
        Node, nodes = self.addFullNode(id, "normalize", "bool", "20003")
        Node.addParametersBool(mat.OCT_normalize)
        Node.addChild("inputnodepins", "")

    def addTexture(self, id, mat, OCT_tex, typename, channel):
        Node, nodes = self.addFullNode(id, channel, typename, "20000")
        mtex = mat.texture_slots.get(OCT_tex.texture)
        if mtex and mtex.texture.type == 'IMAGE':
            if not mtex.texture.image:
                error ('Check texture slots for material <%s>' % mat.name)
            if mtex.texture.image.source == 'FILE':
                filename = absPath(mtex.texture.image.filepath)
            elif mtex.texture.image.source == 'SEQUENCE':
                tex = mtex.texture
                frame = octanerender.frameCurrent
                seq = get_sequence(tex,frame)
                fn_full = absPath(tex.image.filepath)
                src_dir = os.path.dirname(fn_full)
                dst_dir = octanerender.dst_dir
                name, ext = os.path.splitext(os.path.basename(fn_full))
                root, digits = get_rootname(name)
                fmt = '%%0%dd' % (digits)
                src_file = root + (fmt % seq) + ext
                dst_file = 'SEQ-' + fixName(root) + ext
                src_path = os.path.join(src_dir,src_file)
                dst_path = os.path.join(dst_dir,dst_file)
                filename = dst_path
            else:
                error('Only image types of File and Sequence are supported')
        else:
            error ("Check your textures!!!")
        Node.addChild("linkedfilename", filename)
        Node.addChild("parameters","")
        inputnodepins = Node.addChild("inputnodepins", "")
        inputnodepins.addTexPower(0, OCT_tex)
        inputnodepins.addTexGamma(1, OCT_tex)
        inputnodepins.addTexScale(2, OCT_tex, mat)
        inputnodepins.addTexInvert(3, OCT_tex)

    def addEmissionNull(self, id, mat):
        Node, nodes = self.addFullNode(id, "emission", "null emission", "20006")
        Node.addChild("inputnodepins", "")

    def addEmissionBlackBody(self, id, mat):
        Node, nodes = self.addFullNode(id, "emission", "blackbody", "20006")
        inputnodepins = Node.addChild("inputnodepins", "")
        inputnodepins.addTemperature(0, mat)
        inputnodepins.addPower(1, mat)
        inputnodepins.addNormalize(2, mat)
        nodes.addChild("nodepinconnections", "")

    def addEmissionTexture(self, id, mat):
        Node, nodes = self.addFullNode(id, "emission", "texture emission", "20006")
        inputnodepins = Node.addChild("inputnodepins", "")
        if mat.OCT_emission.emission == "RGBspectrum":
            inputnodepins.addRGBspectrum(0, "texture", mat.specular_color)
        else:
            inputnodepins.addTexture(0, mat, mat.OCT_emission, mat.OCT_emission.emission, "texture")
        inputnodepins.addPower(1, mat)

    def addTransmissionNone(self, id, mat):
        NodePin = self.addChild("NodePin", "")
        NodePin.addChild("typename", "transmission")
        NodePin.addChild("id", str(id))
        NodePin.addChild("pintype", "20000")
        NodePin.addChild("hasinternalnodegraph", "false")

    def addDiffuse(self, id, mat):
        if mat.OCT_diffuse.diffuse == "RGBspectrum":
            self.addRGBspectrum(id, "diffuse", mat.diffuse_color)
        else:
            self.addTexture(id, mat, mat.OCT_diffuse, mat.OCT_diffuse.diffuse, "diffuse")

    def addSpecular(self, id, mat):
        if mat.OCT_specular.specular == "RGBspectrum":
            self.addRGBspectrum(id, "specular", mat.specular_color)
        elif mat.OCT_specular.specular == "floattexture":
            self.addSpecularFloatTexture(id, mat)
        else:
            self.addTexture(id, mat, mat.OCT_specular, mat.OCT_specular.specular, "specular")

    def addTransmission(self, id, mat):
        if mat.OCT_diffuse.diffuse == "RGBspectrum":
            self.addRGBspectrum(id, "transmission", mat.diffuse_color)
        else:
            self.addTexture(id, mat, mat.OCT_diffuse, mat.OCT_diffuse.diffuse, "transmission")

    def addReflection(self, id, mat):
        if mat.OCT_specular.specular == "RGBspectrum":
            self.addRGBspectrum(id, "reflection", mat.specular_color)
        elif mat.OCT_specular.specular == "floattexture":
            self.addSpecularFloatTexture(id, mat)
        else:
            self.addTexture(id, mat, mat.OCT_specular, mat.OCT_specular.specular, "reflection")

    def addBump(self, id, mat):
        if mat.OCT_bump.bump == "none":
            self.addBumpNone(id, mat)
        else:
            self.addTexture(id, mat, mat.OCT_bump, mat.OCT_bump.bump, "bump")

    def addNormal(self, id, mat):
        if mat.OCT_normal.normal == "none":
            self.addNormalNone(id, mat)
        else:
            self.addTexture(id, mat, mat.OCT_normal, mat.OCT_normal.normal, "normal")

    def addOpacity(self, id, mat):
        if mat.OCT_opacity.opacity == "floattexture":
            self.addOpacityFloatTexture(id, mat)
        else:
            self.addTexture(id, mat, mat.OCT_opacity, mat.OCT_opacity.opacity, "opacity")

    def addEmission(self, id, mat):
        if mat.OCT_emitter_type == "null emission":
            self.addEmissionNull(id, mat)
        elif mat.OCT_emitter_type == "blackbody":
            self.addEmissionBlackBody(id, mat)
        else:
            self.addEmissionTexture(id, mat)

    def addRoughness(self, id, mat):
        if mat.OCT_roughness.roughness == "floattexture":
            self.addRoughnessFloatTexture(id, mat)
        else:
            self.addTexture(id, mat, mat.OCT_roughness, mat.OCT_roughness.roughness, "roughness")

    def addExternalMaterial(self, name, inputid):
        mat = self.addChild("NodePin","")
        mat.addChild("typename",name)
        mat.addChild("id",str(inputid))
        mat.addChild("pintype","20005")
        mat.addChild("hasinternalnodegraph","false")

    def addMaterialDiffuse(self, mat):
        currentnewnodeid = 1
        currentnewnodepinconnectionid = 0
        nodes = self.addChild("nodes","")
        Node = nodes.addChild("Node", "")
        Node.addChild("name", mat.name)
        Node.addChild("typename", "diffuse")
        Node.addChild("id", "1")
        Node.addChild("position", "0 0")
        inputnodepins = Node.addChild("inputnodepins", "")

        inputnodepins.addDiffuse(0, mat)
        inputnodepins.addTransmissionNone(1, mat)
        inputnodepins.addBump(2, mat)
        inputnodepins.addNormal(3, mat)
        inputnodepins.addOpacity(4, mat)
        inputnodepins.addSmooth(5, mat)
        inputnodepins.addEmission(6, mat)
        return 7, 0

    def addMaterialGlossy(self, mat):
        currentnewnodeid = 1
        currentnewnodepinconnectionid = 0
        nodes = self.addChild("nodes","")
        Node = nodes.addChild("Node", "")
        Node.addChild("name", mat.name)
        Node.addChild("typename", "glossy")
        Node.addChild("id", "1")
        Node.addChild("position", "0 0")
        inputnodepins = Node.addChild("inputnodepins", "")

        inputnodepins.addDiffuse(0, mat)
        inputnodepins.addSpecular(1, mat)
        inputnodepins.addRoughness(2, mat)
        inputnodepins.addFilmWidth(3, mat)
        inputnodepins.addFilmIndex(4, mat)
        inputnodepins.addBump(5, mat)
        inputnodepins.addNormal(6, mat)
        inputnodepins.addOpacity(7, mat)
        inputnodepins.addSmooth(8, mat)
        return 9, 0

    def addMaterialSpecular(self, mat):
        currentnewnodeid = 1
        currentnewnodepinconnectionid = 0
        nodes = self.addChild("nodes","")
        Node = nodes.addChild("Node", "")
        Node.addChild("name", mat.name)
        Node.addChild("typename", "specular")
        Node.addChild("id", "1")
        Node.addChild("position", "0 0")
        inputnodepins = Node.addChild("inputnodepins", "")

        inputnodepins.addReflection(0, mat)
        inputnodepins.addTransmission(1, mat)
        inputnodepins.addIndex(2, mat)
        inputnodepins.addFilmWidth(3, mat)
        inputnodepins.addFilmIndex(4, mat)
        inputnodepins.addBump(5, mat)
        inputnodepins.addNormal(6, mat)
        inputnodepins.addOpacity(7, mat)
        inputnodepins.addSmooth(8, mat)
        inputnodepins.addRoughness(9, mat)
        return 10, 0

    def addInternalMaterial(self, mat, inputid):
        nodemat = self.addChild("NodePin","")
        nodemat.addChild("typename",mat.name)
        nodemat.addChild("id",str(inputid))
        nodemat.addChild("pintype","20005")
        nodemat.addChild("hasinternalnodegraph","true")
        #if mat.OCT_material_type == "glossy":
        nodemat.addChild("basenodeid","1")
        #else:
        #    nodemat.addChild("basenodeid","8")
        nodemat.addChild("basenodepinid","0")
        internalnodegraph = nodemat.addChild("internalnodegraph","")
        NodeGraph = internalnodegraph.addChild("NodeGraph","")
        currentnewnodeid = 1
        currentnewnodepinconnectionid = 0
        NodeGraph.addChild("name",mat.name)
        NodeGraph.addChild("currentnewnodeid",str(currentnewnodeid))
        NodeGraph.addChild("currentnewnodepinconnectionid",str(currentnewnodepinconnectionid))
        if mat.OCT_material_type == "diffuse":
            currentnewnodeid, currentnewnodepinconnectionid = NodeGraph.addMaterialDiffuse(mat)
        elif mat.OCT_material_type == "glossy":
            currentnewnodeid, currentnewnodepinconnectionid = NodeGraph.addMaterialGlossy(mat)
        elif mat.OCT_material_type == "specular":
            currentnewnodeid, currentnewnodepinconnectionid = NodeGraph.addMaterialSpecular(mat)
        else:
            error ("Shouldn't be there: unknown mat type")
        NodeGraph.addChild("nodepinconnections", "")
        NodeGraph.setChildValue("currentnewnodeid",str(currentnewnodeid))
        NodeGraph.setChildValue("currentnewnodepinconnectionid",str(currentnewnodepinconnectionid))

def ocsParse(OCSdata):
    rootElem = ocsElem(None, "", "")
    node = rootElem
    linenumber = 0
    for line in OCSdata:

        linenumber += 1
        line = line.lstrip()
        #print ("Processing line #%d: (%d) [%s]" % (linenumber,len(line),line))

        if len(line) == 0:
            # Empty line - skip
            #print ("Empty line")
            continue

        if line[-1] == "\n":
            line = line[:-1]

        if line[0] != "<":
            # Malformed line
            log ("Unexpected line #%d: %s" % (linenumber,line))
            continue

        if line[1] == "/":
            # Line closing a tag - going back
            node = node.parent
            continue

        end = line.find(">")
        name = line[1:end]
        if len(line) == len(name)+2:
            # No value : create child
            node = node.addChild(name,"")
            continue

        value = line[end+1:]
        end = value.find("<")
        if end == -1:
            # Malformed line
            log ("Unexpected line #%d: %s" % (linenumber,line))
            continue

        value = value[:end]
        node.addChild(name,value)
    return rootElem.children[0]

def ocsParseFile(fileName):
    file = open(fileName)
    if not file:
        return None
    header = file.readline()
    data = file.readlines()
    file.close()
    return ocsParse(data)

def ocsWriteFile(fileName, OCS):
    file = open(fileName,"w")
    file.write(ocs_header + "\n\n\n")
    OCS.write(file,0)
    file.close

def ocsSetChildParameter(OCS, name, valuetype, value):
    TMP = OCS.getElemFromChild("name", name)
    PRM = TMP.getElemFromName("parameters")
    PRM.setChildValue(valuetype, value)

def ocsKernelUpdate(OCS, scene):
    log ("Updating Mesh Preview Kernel")
    world = scene.world
    MPK = OCS.getElemFromChild("name","Mesh Preview Kernel")
    if not MPK: return
    kernel = MPK.getChildValue("typename")

    if world.OCT_kernel == "directlighting":
        if kernel != "directlighting":
            DL = ocsParse(template_dl.splitlines())
            MPK.replaceChildrenFrom(DL)
        if world.OCT_use_speculardepth:
            ocsSetChildParameter(MPK, "speculardepth", "value", "%d" % (world.OCT_speculardepth))
        if world.OCT_use_glossydepth:
            ocsSetChildParameter(MPK, "glossydepth", "value", "%d" % (world.OCT_glossydepth))
        if world.OCT_use_aodist:
            ocsSetChildParameter(MPK, "aodist", "value", "%f" % (world.OCT_aodist))

    elif world.OCT_kernel == "pathtracing":
        if kernel != "pathtracing":
            PT = ocsParse(template_pt.splitlines())
            MPK.replaceChildrenFrom(PT)
        if world.OCT_use_maxdepth:
            ocsSetChildParameter(MPK, "maxdepth", "value", "%d" % (world.OCT_maxdepth))
        if world.OCT_use_rrprob:
            ocsSetChildParameter(MPK, "rrprob", "value", "%f" % (world.OCT_rrprob))
        if world.OCT_use_alphashadows:
            ocsSetChildParameter(MPK, "alphashadows", "value", world.OCT_alphashadows)

    # common to DL and PT
    if world.OCT_use_rayepsilon:
        ocsSetChildParameter(MPK, "rayepsilon", "value", "%f" % (world.OCT_rayepsilon))
    if world.OCT_use_filtersize:
        ocsSetChildParameter(MPK, "filtersize", "value", "%f" % (world.OCT_filtersize))
    if world.OCT_use_alphachannel:
        ocsSetChildParameter(MPK, "alphachannel", "value", world.OCT_alphachannel)
    if world.OCT_use_keep_environment:
        ocsSetChildParameter(MPK, "keep_environment", "value", world.OCT_keep_environment)

def ocsEnvironmentUpdate(OCS, scene):
    log ("Updating Mesh Preview Environment")
    world = scene.world
    MPE = OCS.getElemFromChild("name","Mesh Preview Environment")
    if not MPE: return
    environment = MPE.getChildValue("typename")

    if world.OCT_environment == "texture environment":
        if environment != "texture environment":
            TE = ocsParse(template_te.splitlines())
            MPE.replaceChildrenFrom(TE)

        TMP = MPE.getElemFromName("NodePin")
        TEX = TMP.getElemFromName("Node")
        if not TEX: return
        tex = TEX.getChildValue("typename")

        if world.OCT_texture_type == "FLOAT":
            if tex != "floattexture":
                TE = ocsParse(template_floattexture.splitlines())
                TEX.replaceChildrenFrom(TE)
            if world.OCT_use_texture_float:
                ocsSetChildParameter(MPE, "texture", "value", "%f" % (world.OCT_texture_float))

        elif world.OCT_texture_type == "IMAGE":
            if tex != "image":
                TE = ocsParse(template_image.splitlines())
                TEX.replaceChildrenFrom(TE)
            TEX.setChildValue("linkedfilename", absPath(world.OCT_texture_image))

        if world.OCT_use_texture_XY:
            ocsSetChildParameter(MPE, "rotation", "valuexy", "%f %f" % (world.OCT_texture_X,world.OCT_texture_Y))
        if world.OCT_use_power:
            for c in MPE.children:
                if c.name == "inputnodepins":
                    n = c.children[1]
                    ocsSetChildParameter(n, "power", "value", "%f" % (world.OCT_power))

    elif world.OCT_environment == "daylight":
        if environment != "daylight":
            SL = ocsParse(template_sl.splitlines())
            MPE.replaceChildrenFrom(SL)

        light_param=''
        displayError=False
        try:
            light = bpy.data.objects[world.OCT_active_light]
            if light.type != 'LAMP':  displayError = True
            if light.data.type != 'SUN': displayError = True
        except:
            displayError=True
        if world.OCT_active_light=='' or displayError:
            error("Invalid sun light object or sun light not selected")
        log ('Using light : %s' % (light.name))
        matrix = mathutils.Matrix(light.matrix_world.copy())
        matrix.invert()
        # to enable with final
        # matrix = light.matrix_world.inverted()
        # print (matrix)
        if scene.octane_render.export_ROTX90 == True:
            matrix = rotate90x(matrix)

        for i in range(3):
            light_param += '%f' % (matrix[i][2])
            if i < 2: light_param += ' '
        log ('Sun direction: %s' % (light_param))
        ocsSetChildParameter(MPE, "sundir", "valuexyz", light_param)

        if world.OCT_use_turbidity:
            ocsSetChildParameter(MPE, "turbidity", "value", "%f" % (world.OCT_turbidity))
        if world.OCT_use_northoffset:
            ocsSetChildParameter(MPE, "northoffset", "value", "%f" % (world.OCT_northoffset))
        if world.OCT_use_power:
            ocsSetChildParameter(MPE, "power", "value", "%f" % (world.OCT_power))

def ocsImagerUpdate(OCS, scene):
    log ("Updating Mesh Preview Imager")
    world = scene.world
    MPI = OCS.getElemFromChild("name","Mesh Preview Imager")
    if not MPI: return
    imager = MPI.getChildValue("typename")

    if world.OCT_use_exposure:
        ocsSetChildParameter(MPI, "exposure", "value", "%f" % (world.OCT_exposure))
    if world.OCT_use_fstop:
        ocsSetChildParameter(MPI, "fstop", "value", "%f" % (world.OCT_fstop))
    if world.OCT_use_ISO:
        ocsSetChildParameter(MPI, "ISO", "value", "%f" % (world.OCT_ISO))
    if world.OCT_use_gamma:
        ocsSetChildParameter(MPI, "gamma", "value", "%f" % (world.OCT_gamma))
    if world.OCT_use_response:
        ocsSetChildParameter(MPI, "response", "currentcurveid", world.OCT_response)
    if world.OCT_use_vignetting:
        ocsSetChildParameter(MPI, "vignetting", "value", "%f" % (world.OCT_vignetting))
    if world.OCT_use_saturation:
        ocsSetChildParameter(MPI, "saturation", "value", "%f" % (world.OCT_saturation))
    if world.OCT_use_hotpixel_removal:
        ocsSetChildParameter(MPI, "hotpixel_removal", "value", "%f" % (world.OCT_hotpixel_removal))
    if world.OCT_use_premultiplied_alpha:
        ocsSetChildParameter(MPI, "premultiplied_alpha", "value", world.OCT_premultiplied_alpha)

def ocsMeshNameUpdate(OCS,objFile):
    MESH = OCS.getElemFromChild("typename", "mesh")
    MESH.setChildValue("name",os.path.basename(objFile))
    MESH.setChildValue("linkedfilename",objFile)

def ocsMaterialsUpdate(OCS, mat_list):
    MESH = OCS.getElemFromChild("typename", "mesh")
    meshid = MESH.getChildValue("id")
    inputnodepins = MESH.getElemFromName("inputnodepins")

    mat_blender = {}
    for key, (name, mat, img) in sorted(mat_list.items()):
        #(key,name,mat,img)
        mat_blender[name] = mat

    mat_octane = {}
    for NodePin in inputnodepins.children:
        mat_octane[NodePin.getChildValue("typename")] = NodePin

    log ("OCS Materials")
    saved_ids = {}
    for name, Node in mat_octane.items():
        if name in mat_blender:
            hasinternalnodegraph = Node.getChildValue("hasinternalnodegraph")
            log ("Mat <%s> already in ocs - internalnodegraph = %s" % (name, hasinternalnodegraph))
            if hasinternalnodegraph == "false":
                saved_ids[name] = Node.getChildValue("id")
                log ("Saved id <%s> for mat <%s>" % (saved_ids[name], name))
        else:
            log ("Mat <%s> not in blender - will be deleted" % name)

    log ("Blender Materials")
    saved_mats = {}
    for name, mat in mat_blender.items():
        if name in mat_octane:
            if mat_octane[name].getChildValue("hasinternalnodegraph") == "true":
                log ("Mat <%s> is internal - replacing" % name)
            else:
                log ("Mat <%s> has its own graph - keeping" % name)
                #saved_mats[name] =
        else:
            log ("Mat <%s> not in ocs file - creating" % name)

    childgraph = OCS.getElemFromName("childgraph")
    NodeGraph = childgraph.getElemFromName("NodeGraph")
    nodes = NodeGraph.getElemFromName("nodes")
    nodepinconnections = NodeGraph.getElemFromName("nodepinconnections")
    for Node in nodes.children:
        log ("Node <%s> <%s> : ID <%s>" % (Node.getChildValue("name"),Node.getChildValue("typename"),Node.getChildValue("id")))

    inputnodepins.children = []
    matpinid = 0
    for name, mat in sorted(mat_blender.items()):
        if name in saved_ids:
            inputnodepins.addExternalMaterial(name,matpinid)
        else:
            inputnodepins.addInternalMaterial(mat,matpinid)
        matpinid += 1
