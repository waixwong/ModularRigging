import maya.cmds as cmd
import sys

sys.path.append('/Users/WEI/python_path')
from vector import *


class SlidingPivotFoot:
    def __init__(self, ankle_jnt, ctrl, footCurve):
        self.ankle = ankle_jnt
        self.ctrl = ctrl
        self.footCurve = footCurve

        # create locators at jnt location:
        self.locator = self.locator_at_obj(ankle_jnt, ankle_jnt + '_loc')
        cmd.setAttr(cmd.listRelatives(self.locator, shapes=True)[0] + '.localPositionY', 0)
        self.ctrl_loc = self.locator_at_obj(ankle_jnt, ankle_jnt + '_dupLoc')

        self._establish_connections()

    def _establish_connections(self):
        reverseRzNode = cmd.shadingNode('multDoubleLinear', n='reverse_Rx', asUtility=True)
        normalizeNode = cmd.shadingNode('vectorProduct', n='normalize', asUtility=True)

        cmd.setAttr(normalizeNode + '.operation', 0)
        cmd.setAttr(normalizeNode + '.normalizeOutput', 1)
        cmd.setAttr(normalizeNode + '.input1Y', 0.001)

        cmd.connectAttr(self.ctrl + '.rx', normalizeNode + '.input1X')

        cmd.setAttr(reverseRzNode + '.input2', -1)
        cmd.connectAttr(self.ctrl + '.rz', reverseRzNode + '.input1')
        cmd.connectAttr(reverseRzNode + '.output', normalizeNode + '.input1Z')

        cmd.connectAttr(normalizeNode + '.outputX', self.locator + '.tz')
        cmd.connectAttr(normalizeNode + '.outputZ', self.locator + '.tx')

        cmd.connectAttr(self.locator + '.tz', self.ctrl_loc + '.rotatePivotZ')
        cmd.connectAttr(self.locator + '.tx', self.ctrl_loc + '.rotatePivotX')
        # cmd.setAttr(self.ctrl_loc+'.rotatePivotY', 0)

        cmd.connectAttr(self.ctrl + '.rotate', self.ctrl_loc + '.rotate')

        self._reconstructCurve()

    def locator_at_obj(self, obj, name):
        pos = cmd.xform(obj, q=True, ws=True, t=True)
        locator = cmd.spaceLocator(n=name, p=pos, r=False)[0]

        cmd.xform(locator, cp=True)
        return locator


    def _reconstructCurve(self):
        # this method reconstruct a curve by normalize each point on the original curve,
        # thus makes an approxiate circle which has the same # of cvs as the original curve.

        # duplicate original curve:
        obj = cmd.duplicate(self.footCurve, inputConnections=False, n='duplicated_' + self.footCurve)[0]
        cvs = cmd.ls(obj + '.cv[*]', flatten=True)
        for cv in cvs:
            point = cmd.xform(cv, q=True, t=True, ws=True)
            vector = Vector(point[0], point[1], point[2])
            normalized = vector.normalized();
            newPoint = (normalized.x, normalized.y, normalized.z)
            cmd.xform(cv, t=newPoint, ws=True)


s = SlidingPivotFoot('ankle', 'ctrl', 'footCurve')