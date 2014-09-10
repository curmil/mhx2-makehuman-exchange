# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
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

# Project Name:        MakeHuman
# Product Home Page:   http://www.makehuman.org/
# Code Home Page:      http://code.google.com/p/makehuman/
# Authors:             Thomas Larsson
# Script copyright (C) Thomas Larsson 2014

import bpy
from bpy.props import *
from bpy_extras.io_utils import ImportHelper

from .utils import updateScene
from .drivers import getArmature

# ---------------------------------------------------------------------
#   VisemeData class
# ---------------------------------------------------------------------

class VisemeData:
    def __init__(self):
        self._visemes = None
        self._moho = None
        self._layout = None
        self._mouthShapes = None

    def load(self):
        from .load_json import loadJsonRelative
        if self._moho is None:
            struct = loadJsonRelative("data/hm8/faceshapes/faceshapes.json")
            self._mouthShapes = [key for key in struct["targets"].keys() if key[0:4] in ["mout", "lips", "tong"]]
            struct = loadJsonRelative("data/hm8/faceshapes/visemes.json")
            self._layout = struct["layout"]
            self._visemes = struct["visemes"]
            self._moho = struct["moho"]


theVis = VisemeData()


def getMouthShapes():
    theVis.load()
    return theVis._mouthShapes

def getLayout():
    theVis.load()
    return theVis._layout

def getVisemes():
    theVis.load()
    return theVis._visemes

def getMoho():
    theVis.load()
    return theVis._moho


# ---------------------------------------------------------------------
#   Set viseme
# ---------------------------------------------------------------------

def setViseme(rig, vis, useKey=False, frame=1):
    for key in getMouthShapes():
        rig["Mhs"+key] = 0.0
    for key,value in getVisemes()[vis]:
        rig["Mhs"+key] = value
    if useKey:
        for key in getMouthShapes():
            rig.keyframe_insert('["Mhs%s"]' % key, frame=frame)


class VIEW3D_OT_SetVisemeButton(bpy.types.Operator):
    bl_idname = "mhx2.set_viseme"
    bl_label = "X"
    bl_description = "Set viseme"
    bl_options = {'UNDO'}

    viseme = StringProperty()

    def execute(self, context):
        rig = getArmature(context.object)
        if rig:
            setViseme(rig, self.viseme)
            updateScene(context)
        return{'FINISHED'}

# ---------------------------------------------------------------------
#   Load Moho
# ---------------------------------------------------------------------

def loadMoho(rig, context, filepath, offs):
    context.scene.objects.active = rig
    moho = getMoho()
    bpy.ops.object.mode_set(mode='POSE')
    fp = open(filepath, "rU")
    for line in fp:
        words= line.split()
        if len(words) < 2:
            pass
        else:
            frame = int(words[0]) + offs
            vis = moho[words[1]]
            setViseme(rig, vis, True, frame)
    fp.close()
    #setInterpolation(rig)
    updateScene(context)
    print("Moho file %s loaded" % filepath)


class VIEW3D_OT_LoadMohoButton(bpy.types.Operator, ImportHelper):
    bl_idname = "mhx2.load_moho"
    bl_label = "Load Moho"
    bl_description = "Load Moho (.dat) file"
    bl_options = {'UNDO'}

    filename_ext = ".dat"
    filter_glob = StringProperty(default="*.dat", options={'HIDDEN'})
    filepath = StringProperty(subtype='FILE_PATH')

    def execute(self, context):
        rig = getArmature(context.object)
        if rig:
            loadMoho(rig, context, self.filepath, 1.0)
        return{'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

# ---------------------------------------------------------------------
#   Delete lipsync
# ---------------------------------------------------------------------

def deleteLipsync(rig):
    if rig.animation_data is None:
        return
    act = rig.animation_data.action
    for fcu in act.fcurves:
        if (fcu.data_path[0:5] == '["Mhs' and
            fcu.data_path[5:9] in ["mout", "lips", "tong"]):
                act.fcurves.remove(fcu)
    for key in getMouthShapes():
        rig["Mhs"+key] = 0.0


class VIEW3D_OT_DeleteLipsyncButton(bpy.types.Operator):
    bl_idname = "mhx2.delete_lipsync"
    bl_label = "Delete Lipsync"
    bl_description = "Delete F-curves associated with lipsync"
    bl_options = {'UNDO'}

    def execute(self, context):
        rig = getArmature(context.object)
        if rig:
            deleteLipsync(rig)
        updateScene(context)
        return{'FINISHED'}