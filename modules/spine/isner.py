__author__ = 'WEI'
import maya.cmds as cmd
import maya.mel as mel

import utilities.joints as j

reload(j)
import utilities.general as general

reload(general)


class IsnerSpine():
    def __init__(self, joints, upperCtrl=None, lowerCtrl=None, globalScale=1, waves=1):
        self.joints = joints
        self.upperCtrl = upperCtrl
        self.lowerCtrl = lowerCtrl
        self.globalScale = globalScale
        self.waves = waves

        self._setup()

    def _setup(self):
        """
        make a normal ik spine:
        """
        sj = self.joints[0]
        ej = self.joints[-1]

        self.spineCurve = 'curve_bindSpine'
        # setup IK
        self.ikSpine = cmd.ikHandle(sj=sj, ee=ej, name='ikHandle_bindSpine', sol='ikSplineSolver', createCurve=True,
                                    ns=2)
        cmd.rename(self.ikSpine[2], self.spineCurve)

        # clusters
        clusterReturn = general.clusterCurve(self.spineCurve, 'cluster_spineIK')
        clusters = clusterReturn[0]
        self.clusterGrp = clusterReturn[1]

        # ==================controllers setup=============================
        if self.upperCtrl == None:
            self.upperCtrl = self._drawCtrl('ctrl_upperTorso', self.joints[-2])
        if self.lowerCtrl == None:
            self.lowerCtrl = self._drawCtrl('ctrl_lowerTorso', self.joints[1])

        for i in [0, 1]:
            cmd.parentConstraint(self.lowerCtrl, clusters[i], mo=True)
        for i in [2, 3, 4]:
            cmd.parentConstraint(self.upperCtrl, clusters[i], mo=True)

        self._setup_stretch()

        # setup double wave and single wave:
        if self.waves:
            self._setup_waves()

        self._cleanUp()

        # general.makeCtrlLayer(self.upperCtrl)
        # general.makeCtrlLayer(self.lowerCtrl)

        # =========================return value==========================
        # returnTuple = (ctrlGrps, hideGrp)
        # return returnTuple

    def _setup_stretch(self):
        # ==================stretchSpine setup=============================
        # create a curveInfo node to get the curve length
        curveInfoNode = cmd.arclen(self.spineCurve, constructionHistory=True)
        curveInfoNode = cmd.rename(curveInfoNode, self.spineCurve + 'Info')

        # Calculate stretch factor
        stretchMDnode = cmd.shadingNode('multiplyDivide', asUtility=True, name='spineIKstretchy_MD')
        cmd.connectAttr(curveInfoNode + '.arcLength', stretchMDnode + '.input1.input1X')
        nonScaleLength = cmd.getAttr(curveInfoNode + '.arcLength')

        # original curve length = nonscale length * global scale
        originalLengthMD = cmd.shadingNode('multiplyDivide', asUtility=True, name='spineCurveOriginalLength_MD')
        cmd.setAttr(originalLengthMD + '.input1X', nonScaleLength)
        if self.globalScale == 1:
            cmd.setAttr(originalLengthMD + '.input2X', 1)
        else:
            cmd.connectAttr(self.globalScale, originalLengthMD + '.input2X')

        originalLength = originalLengthMD + '.outputX'
        cmd.connectAttr(originalLength, stretchMDnode + '.input2X')
        cmd.setAttr(stretchMDnode + '.operation', 2)

        # create a switch for stretch
        condition = cmd.shadingNode('condition', asUtility=True, name='stretch_condition')
        cmd.connectAttr(stretchMDnode + '.output.outputX', condition + '.colorIfTrue.colorIfTrueR')
        cmd.setAttr(condition + '.operation', 0)
        cmd.setAttr(condition + '.firstTerm', 1)  # this attr goes into the switch (stretchy ON/OFF)
        cmd.setAttr(condition + '.secondTerm', 1)

        # attributes: stretchSpine:
        cmd.addAttr(self.upperCtrl, ln='stretchSpine', at='bool', dv=1, keyable=True)
        cmd.connectAttr(self.upperCtrl + '.stretchSpine', condition + '.firstTerm')

        # ==================hook the output value from condition node to joints==================
        # end effector (end joint) no need to stretch, exclude from joint list
        self.stretchJnts = self.joints[:len(self.joints) - 1]
        self.jntPMAdict = {}
        for joint in self.stretchJnts:
            jntPMAnode = cmd.shadingNode('plusMinusAverage', asUtility=True, name=joint + '_spine_compression_PMA')
            cmd.connectAttr(condition + '.outColorR', jntPMAnode + '.input1D[0]', force=True)
            cmd.connectAttr(jntPMAnode + '.output1D', joint + '.sx', f=True)
            self.jntPMAdict[joint] = jntPMAnode

        # =========================twist fix=============================
        ikHandle = self.ikSpine[0]
        cmd.setAttr(ikHandle + '.dTwistControlEnable', 1)
        cmd.setAttr(ikHandle + '.dWorldUpType', 4)
        cmd.setAttr(ikHandle + '.dWorldUpVectorX', 1)
        cmd.setAttr(ikHandle + '.dWorldUpVectorY', 0)
        cmd.setAttr(ikHandle + '.dWorldUpVectorEndX', 1)
        cmd.setAttr(ikHandle + '.dWorldUpVectorEndY', 0)
        cmd.connectAttr(self.lowerCtrl + '.xformMatrix', ikHandle + '.dWorldUpMatrix', f=True)
        cmd.connectAttr(self.upperCtrl + '.xformMatrix', ikHandle + '.dWorldUpMatrixEnd', f=True)

        cmd.makeIdentity(self.joints[0], apply=True, r=True)

        # ==========================warning box==========================
        # create warning box material:
        warningLambert = cmd.shadingNode('lambert', asShader=True, name='warningBox_material')
        sg = cmd.sets(renderable=True, noSurfaceShader=True, empty=True, name=warningLambert + 'SG')
        cmd.connectAttr(warningLambert + '.outColor', sg + '.surfaceShader', f=True)
        cmd.setAttr(warningLambert + '.transparency', 0.6, 0.6, 0.6)

        # set color change:
        cmd.addAttr(self.upperCtrl, ln='scaleFactor', at='float', dv=0, keyable=False)

        cmd.setAttr(self.upperCtrl + '.scaleFactor', 1.5)
        cmd.setAttr(warningLambert + '.color', 1, 0, 0, type='double3')
        cmd.setDrivenKeyframe(warningLambert + '.colorR', currentDriver=self.upperCtrl + '.scaleFactor')
        cmd.setDrivenKeyframe(warningLambert + '.colorG', currentDriver=self.upperCtrl + '.scaleFactor')
        cmd.setDrivenKeyframe(warningLambert + '.colorB', currentDriver=self.upperCtrl + '.scaleFactor')

        cmd.setAttr(self.upperCtrl + '.scaleFactor', 0.6)
        cmd.setDrivenKeyframe(warningLambert + '.colorR', currentDriver=self.upperCtrl + '.scaleFactor')
        cmd.setDrivenKeyframe(warningLambert + '.colorG', currentDriver=self.upperCtrl + '.scaleFactor')
        cmd.setDrivenKeyframe(warningLambert + '.colorB', currentDriver=self.upperCtrl + '.scaleFactor')

        cmd.setAttr(self.upperCtrl + '.scaleFactor', 1)
        cmd.setAttr(warningLambert + '.color', 0, 1, 0, type='double3')
        cmd.setDrivenKeyframe(warningLambert + '.colorR', cd=self.upperCtrl + '.scaleFactor')
        cmd.setDrivenKeyframe(warningLambert + '.colorG', cd=self.upperCtrl + '.scaleFactor')
        cmd.setDrivenKeyframe(warningLambert + '.colorB', cd=self.upperCtrl + '.scaleFactor')

        cmd.connectAttr(stretchMDnode + '.outputX', self.upperCtrl + '.scaleFactor')

        # assign material to warningbox
        for ctrl in [self.upperCtrl, self.lowerCtrl]:
            shapes = cmd.listRelatives(ctrl, shapes=True)
            for box in shapes:
                if cmd.ls(box, showType=True)[1] == 'mesh':
                    cmd.setAttr(box + '.castsShadows', 0)
                    cmd.setAttr(box + '.receiveShadows', 0)
                    cmd.setAttr(box + '.motionBlur', 0)
                    cmd.setAttr(box + '.primaryVisibility', 0)
                    cmd.setAttr(box + '.smoothShading', 0)
                    cmd.setAttr(box + '.visibleInReflections', 0)
                    cmd.setAttr(box + '.visibleInRefractions', 0)
                    cmd.select(box, r=True)
                    cmd.sets(e=True, forceElement=sg)
                    cmd.connectAttr(self.upperCtrl + '.stretchSpine', box + '.visibility')

    def _setup_waves(self):
        # ######## attributes: singleWave:
        singleWaveMD = cmd.shadingNode('multiplyDivide', asUtility=True, name='singleWave_MD')
        cmd.addAttr(self.upperCtrl, ln='singleWave', at='float', dv=0, minValue=-1, maxValue=1, keyable=True)
        cmd.connectAttr(self.upperCtrl + '.singleWave', singleWaveMD + '.input1X', force=True)
        cmd.setAttr(singleWaveMD + '.input2X', -1)

        # devide the joint chain:
        middleNum = len(self.stretchJnts) / 2  # note that the end joint should be excluded from the spineJnts list
        middleNum = int(middleNum)
        upperJnts = self.stretchJnts[middleNum:]
        lowerJnts = self.stretchJnts[:middleNum]

        for joint in upperJnts:
            jntPMAnode = self.jntPMAdict[joint]
            cmd.connectAttr(self.upperCtrl + '.singleWave', jntPMAnode + '.input1D[1]')
        for joint in lowerJnts:
            jntPMAnode = self.jntPMAdict[joint]
            cmd.connectAttr(singleWaveMD + '.outputX', jntPMAnode + '.input1D[1]')

        # ######## attribute: doubleWave:
        # make a main condition node: this node will send compression/expansion data to joints at two end.
        cmd.addAttr(self.upperCtrl, ln='doubleWave', at='float', dv=0, minValue=-5, maxValue=5, keyable=True)
        doubleWaveCondition = cmd.shadingNode('condition', asUtility=True, name='doubleWave_condition')
        # if doubleWave attr > 0: middle joints expansion
        cmd.connectAttr(self.upperCtrl + '.doubleWave', doubleWaveCondition + '.firstTerm')
        cmd.setAttr(doubleWaveCondition + '.operation', 2)  # greater than operation

        # set up positive value operation:
        doubleWavePosCondition = cmd.shadingNode('condition', asUtility=True, name='doubleWave_Pos_condition')
        cmd.connectAttr(self.upperCtrl + '.doubleWave', doubleWavePosCondition + '.firstTerm')
        cmd.setAttr(doubleWavePosCondition + '.operation', 4)  # less than operation

        PosMD = cmd.shadingNode('multiplyDivide', asUtility=True, name='doubleWave_PosMD')
        cmd.connectAttr(self.upperCtrl + '.doubleWave', PosMD + '.input1X')
        cmd.setAttr(PosMD + '.input2X', -1)

        cmd.connectAttr(PosMD + '.outputX', doubleWavePosCondition + '.colorIfTrueR')
        cmd.connectAttr(self.upperCtrl + '.doubleWave', doubleWavePosCondition + '.colorIfFalseR')

        # set up negative value operation:
        doubleWaveNegCondition = cmd.shadingNode('condition', asUtility=True, name='doubleWave_Neg_condition')
        cmd.connectAttr(self.upperCtrl + '.doubleWave', doubleWaveNegCondition + '.firstTerm')
        cmd.setAttr(doubleWaveNegCondition + '.operation', 2)  # greater than operation
        totalJntNum = len(self.joints)
        if totalJntNum == 5:
            factor = 1
        if totalJntNum == 7:
            factor = 2
        cmd.setAttr(doubleWaveNegCondition + '.colorIfTrueR', -factor)
        cmd.setAttr(doubleWaveNegCondition + '.colorIfFalseR', factor)  # keep output always negative

        NegMD = cmd.shadingNode('multiplyDivide', asUtility=True, name='doubleWave_NegMD')
        cmd.connectAttr(self.upperCtrl + '.doubleWave', NegMD + '.input1X')
        cmd.connectAttr(doubleWaveNegCondition + '.outColorR', NegMD + '.input2X')
        cmd.setAttr(NegMD + '.operation', 2)  # devide

        # connect the doubleWave stretching values
        cmd.connectAttr(doubleWavePosCondition + '.outColorR', doubleWaveCondition + '.colorIfTrueG')
        cmd.connectAttr(doubleWavePosCondition + '.outColorR', doubleWaveCondition + '.colorIfFalseR')

        cmd.connectAttr(NegMD + '.outputX', doubleWaveCondition + '.colorIfTrueR')
        cmd.connectAttr(NegMD + '.outputX', doubleWaveCondition + '.colorIfFalseG')

        # connect 2 joints at 2 ends: first joint and the second last joint in chain.(the last stretch joint)
        sideJnts = [self.stretchJnts[0], self.stretchJnts[-1]]
        for joint in sideJnts:
            jntPMAnode = self.jntPMAdict[joint]
            cmd.connectAttr(doubleWaveCondition + '.outColorR', jntPMAnode + '.input1D[2]')

        # conncet 2 joints in the middle of the whole chain
        middleJnts = [self.stretchJnts[middleNum - 1], self.stretchJnts[middleNum]]
        for joint in middleJnts:
            jntPMAnode = self.jntPMAdict[joint]
            cmd.connectAttr(doubleWaveCondition + '.outColorG', jntPMAnode + '.input1D[2]')

        # conncet 2 middle joints of upper section and lower section:
        restJnts = self.stretchJnts
        for joint in sideJnts + middleJnts:
            restJnts.remove(joint)
        for joint in restJnts:
            jntPMAnode = self.jntPMAdict[joint]
            cmd.connectAttr(NegMD + '.outputX', self.jntPMAdict[joint] + '.input1D[2]')

    def _drawCtrl(self, name, target):
        mel.eval(
            'curve -d 1 -p 0.5 0.5 0.5 -p 0.5 0.5 -0.5 -p -0.5 0.5 -0.5 -p -0.5 -0.5 -0.5 -p 0.5 -0.5 -0.5 -p 0.5 0.5 -0.5 -p -0.5 0.5 -0.5 -p -0.5 0.5 0.5 -p 0.5 0.5 0.5 -p 0.5 -0.5 0.5 -p 0.5 -0.5 -0.5 -p -0.5 -0.5 -0.5 -p -0.5 -0.5 0.5 -p 0.5 -0.5 0.5 -p -0.5 -0.5 0.5 -p -0.5 0.5 0.5 -k 0 -k 1 -k 2 -k 3 -k 4 -k 5 -k 6 -k 7 -k 8 -k 9 -k 10 -k 11 -k 12 -k 13 -k 14 -k 15 -n "_controller1" ;')
        cube = \
            cmd.polyCube(w=1, h=1, d=1, sx=1, sy=1, sz=1, ax=(0, 1, 0), constructionHistory=False,
                         n=name + '_warningBox')[
                0]
        cmd.scale(3, 1, 3, '_controller1')
        cmd.scale(2.7, 0.9, 2.7, cube)
        cmd.makeIdentity('_controller1', a=True, t=True, s=True, r=True)
        cmd.makeIdentity(cube, a=True, t=True, s=True, r=True)
        cubeShape = cmd.listRelatives(cube, shapes=True)[0]
        cmd.parent(cubeShape, '_controller1', s=True, r=True)
        cmd.delete(cube)
        cmd.rename('_controller1', name)
        general.moveToPosition(name, target, freeze=1)
        return name

    def _cleanUp(self):
        # ========================clean outliner=========================
        self.hideGrp = cmd.group(self.ikSpine[0], self.spineCurve, self.clusterGrp, n='spine_HideGrp')
        cmd.setAttr(self.hideGrp + '.v', 0)