import maya.cmds as cmd
import utilities

reload(utilities)
import controller

reload(controller)

# ####################
# Isner spine Module
# number of joints
# must be an odd number
# end joint included.
# ####################

# 1. set up a spine IK
def isnerSpine(sj, ej, globalScale=1):
    # get the complete Chain:
    spineJnts = utilities.completeChain(sj, ej)
    # check the total joint num of the chain:
    totalJntNum = len(spineJnts)
    if totalJntNum not in [5, 7]:
        cmd.confirmDialog(title='Warning! Isner Spine Installation Failed',
                          message='Isner Spine can only be installed on a joint chain which consists of 5 or 7 joints.',
                          button='oK', defaultButton='OK', cancelButton='OK', icon='warning')
        return
    # create a curve based on jnt location
    points = []
    for joint in spineJnts:
        pos = cmd.xform(joint, q=True, t=True, ws=True)
        points.append(pos)

    # spineCurve = cmd.curve(n='curve_bindSpine', point = points, degree=3)
    spineCurve = 'curve_bindSpine'
    # setup IK
    ikSpine = cmd.ikHandle(sj=sj, ee=ej, name='ikHandle_bindSpine', sol='ikSplineSolver', createCurve=True,
                           ns=2)  # curve = spineCurve)
    cmd.rename(ikSpine[2], spineCurve)

    # clusters
    clusterReturn = utilities.clusterCurve(spineCurve, 'cluster_spineIK')
    clusters = clusterReturn[0]
    clusterGrp = clusterReturn[1]

    # ==================controllers setup=============================
    upperCtrl = controller.warningBox('ctrl_upperTorso', spineJnts[-3])[0]
    lowerCtrl = controller.warningBox('ctrl_lowerTorso', spineJnts[1])[0]
    ctrlGrps = [upperCtrl, lowerCtrl]

    for ctrl in [upperCtrl, lowerCtrl]:
        cmd.scale(1, 1.5, 3, ctrl)
        cmd.makeIdentity(ctrl, a=True, s=True)

    for i in [0, 1]:
        cmd.parentConstraint(lowerCtrl, clusters[i], mo=True)
    for i in [2, 3, 4]:
        cmd.parentConstraint(upperCtrl, clusters[i], mo=True)

    # ==================stretchSpine setup=============================
    # create a curveInfo node to get the curve length
    curveInfoNode = cmd.arclen(spineCurve, constructionHistory=True)
    curveInfoNode = cmd.rename(curveInfoNode, spineCurve + 'Info')

    # Calculate stretch factor
    stretchMDnode = cmd.shadingNode('multiplyDivide', asutilities=True, name='spineIKstretchy_MD')
    cmd.connectAttr(curveInfoNode + '.arcLength', stretchMDnode + '.input1.input1X')
    nonScaleLength = cmd.getAttr(curveInfoNode + '.arcLength')

    # original curve length = nonscale length * global scale
    originalLengthMD = cmd.shadingNode('multiplyDivide', asutilities=True, name='spineCurveOriginalLength_MD')
    cmd.setAttr(originalLengthMD + '.input1X', nonScaleLength)
    if globalScale == 1:
        cmd.setAttr(originalLengthMD + '.input2X', 1)
    else:
        cmd.connectAttr(globalScale, originalLengthMD + '.input2X')

    originalLength = originalLengthMD + '.outputX'
    cmd.connectAttr(originalLength, stretchMDnode + '.input2X')
    cmd.setAttr(stretchMDnode + '.operation', 2)

    # create a switch for stretch
    condition = cmd.shadingNode('condition', asutilities=True, name='stretch_condition')
    cmd.connectAttr(stretchMDnode + '.output.outputX', condition + '.colorIfTrue.colorIfTrueR')
    cmd.setAttr(condition + '.operation', 0)
    cmd.setAttr(condition + '.firstTerm', 1)  # this attr goes into the switch (stretchy ON/OFF)
    cmd.setAttr(condition + '.secondTerm', 1)

    # attributes: stretchSpine:
    cmd.addAttr(upperCtrl, ln='stretchSpine', at='bool', dv=1, keyable=True)
    cmd.connectAttr(upperCtrl + '.stretchSpine', condition + '.firstTerm')

    # ==================hook the output value from condition node to joints==================
    # end effector (end joint) no need to stretch, exclude from joint list
    stretchJnts = spineJnts[:len(spineJnts) - 1]
    jntPMAdict = {}
    for joint in stretchJnts:
        jntPMAnode = cmd.shadingNode('plusMinusAverage', asutilities=True, name=joint + '_spine_compression_PMA')
        cmd.connectAttr(condition + '.outColorR', jntPMAnode + '.input1D[0]', force=True)
        cmd.connectAttr(jntPMAnode + '.output1D', joint + '.sx', f=True)
        jntPMAdict[joint] = jntPMAnode

    ######### attributes: singleWave:
    singleWaveMD = cmd.shadingNode('multiplyDivide', asutilities=True, name='singleWave_MD')
    cmd.addAttr(upperCtrl, ln='singleWave', at='float', dv=0, minValue=-1, maxValue=1, keyable=True)
    cmd.connectAttr(upperCtrl + '.singleWave', singleWaveMD + '.input1X', force=True)
    cmd.setAttr(singleWaveMD + '.input2X', -1)

    # devide the joint chain:
    middleNum = len(stretchJnts) / 2  # note that the end joint should be excluded from the spineJnts list
    middleNum = int(middleNum)
    upperJnts = stretchJnts[middleNum:]
    lowerJnts = stretchJnts[:middleNum]

    for joint in upperJnts:
        jntPMAnode = jntPMAdict[joint]
        cmd.connectAttr(upperCtrl + '.singleWave', jntPMAnode + '.input1D[1]')
    for joint in lowerJnts:
        jntPMAnode = jntPMAdict[joint]
        cmd.connectAttr(singleWaveMD + '.outputX', jntPMAnode + '.input1D[1]')

    ######### attribute: doubleWave:
    # make a main condition node: this node will send compression/expansion data to joints at two end.
    cmd.addAttr(upperCtrl, ln='doubleWave', at='float', dv=0, minValue=-5, maxValue=5, keyable=True)
    doubleWaveCondition = cmd.shadingNode('condition', asutilities=True, name='doubleWave_condition')
    # if doubleWave attr > 0: middle joints expansion
    cmd.connectAttr(upperCtrl + '.doubleWave', doubleWaveCondition + '.firstTerm')
    cmd.setAttr(doubleWaveCondition + '.operation', 2)  # greater than operation

    # set up positive value operation:
    doubleWavePosCondition = cmd.shadingNode('condition', asutilities=True, name='doubleWave_Pos_condition')
    cmd.connectAttr(upperCtrl + '.doubleWave', doubleWavePosCondition + '.firstTerm')
    cmd.setAttr(doubleWavePosCondition + '.operation', 4)  # less than operation

    PosMD = cmd.shadingNode('multiplyDivide', asutilities=True, name='doubleWave_PosMD')
    cmd.connectAttr(upperCtrl + '.doubleWave', PosMD + '.input1X')
    cmd.setAttr(PosMD + '.input2X', -1)

    cmd.connectAttr(PosMD + '.outputX', doubleWavePosCondition + '.colorIfTrueR')
    cmd.connectAttr(upperCtrl + '.doubleWave', doubleWavePosCondition + '.colorIfFalseR')

    # set up negative value operation:
    doubleWaveNegCondition = cmd.shadingNode('condition', asutilities=True, name='doubleWave_Neg_condition')
    cmd.connectAttr(upperCtrl + '.doubleWave', doubleWaveNegCondition + '.firstTerm')
    cmd.setAttr(doubleWaveNegCondition + '.operation', 2)  # greater than operation
    if totalJntNum == 5:
        factor = 1
    if totalJntNum == 7:
        factor = 2
    cmd.setAttr(doubleWaveNegCondition + '.colorIfTrueR', -factor)
    cmd.setAttr(doubleWaveNegCondition + '.colorIfFalseR', factor)  # keep output always negative

    NegMD = cmd.shadingNode('multiplyDivide', asutilities=True, name='doubleWave_NegMD')
    cmd.connectAttr(upperCtrl + '.doubleWave', NegMD + '.input1X')
    cmd.connectAttr(doubleWaveNegCondition + '.outColorR', NegMD + '.input2X')
    cmd.setAttr(NegMD + '.operation', 2)  # devide

    # connect the doubleWave stretching values
    cmd.connectAttr(doubleWavePosCondition + '.outColorR', doubleWaveCondition + '.colorIfTrueG')
    cmd.connectAttr(doubleWavePosCondition + '.outColorR', doubleWaveCondition + '.colorIfFalseR')

    cmd.connectAttr(NegMD + '.outputX', doubleWaveCondition + '.colorIfTrueR')
    cmd.connectAttr(NegMD + '.outputX', doubleWaveCondition + '.colorIfFalseG')

    # connect 2 joints at 2 ends: first joint and the second last joint in chain.(the last stretch joint)
    sideJnts = [stretchJnts[0], stretchJnts[-1]]
    for joint in sideJnts:
        jntPMAnode = jntPMAdict[joint]
        cmd.connectAttr(doubleWaveCondition + '.outColorR', jntPMAnode + '.input1D[2]')

    # conncet 2 joints in the middle of the whole chain
    middleJnts = [stretchJnts[middleNum - 1], stretchJnts[middleNum]]
    for joint in middleJnts:
        jntPMAnode = jntPMAdict[joint]
        cmd.connectAttr(doubleWaveCondition + '.outColorG', jntPMAnode + '.input1D[2]')

    # conncet 2 middle joints of upper section and lower section:
    restJnts = stretchJnts
    for joint in sideJnts + middleJnts:
        restJnts.remove(joint)
    for joint in restJnts:
        jntPMAnode = jntPMAdict[joint]
        cmd.connectAttr(NegMD + '.outputX', jntPMAdict[joint] + '.input1D[2]')

    #=========================twist fix=============================
    ikHandle = ikSpine[0]
    cmd.setAttr(ikHandle + '.dTwistControlEnable', 1)
    cmd.setAttr(ikHandle + '.dWorldUpType', 4)
    cmd.setAttr(ikHandle + '.dWorldUpVectorX', 1)
    cmd.setAttr(ikHandle + '.dWorldUpVectorY', 0)
    cmd.setAttr(ikHandle + '.dWorldUpVectorEndX', 1)
    cmd.setAttr(ikHandle + '.dWorldUpVectorEndY', 0)
    cmd.connectAttr(lowerCtrl + '.xformMatrix', ikHandle + '.dWorldUpMatrix', f=True)
    cmd.connectAttr(upperCtrl + '.xformMatrix', ikHandle + '.dWorldUpMatrixEnd', f=True)

    cmd.makeIdentity(sj, apply=True, r=True)

    #==========================warning box==========================
    # create warning box material:
    warningLambert = cmd.shadingNode('lambert', asShader=True, name='warningBox_material')
    sg = cmd.sets(renderable=True, noSurfaceShader=True, empty=True, name=warningLambert + 'SG')
    cmd.connectAttr(warningLambert + '.outColor', sg + '.surfaceShader', f=True)
    cmd.setAttr(warningLambert + '.transparency', 0.6, 0.6, 0.6)

    # set color change:
    cmd.addAttr(upperCtrl, ln='scaleFactor', at='float', dv=0, keyable=False)

    cmd.setAttr(upperCtrl + '.scaleFactor', 1.5)
    cmd.setAttr(warningLambert + '.color', 1, 0, 0, type='double3')
    cmd.setDrivenKeyframe(warningLambert + '.colorR', currentDriver=upperCtrl + '.scaleFactor')
    cmd.setDrivenKeyframe(warningLambert + '.colorG', currentDriver=upperCtrl + '.scaleFactor')
    cmd.setDrivenKeyframe(warningLambert + '.colorB', currentDriver=upperCtrl + '.scaleFactor')

    cmd.setAttr(upperCtrl + '.scaleFactor', 0.8)
    cmd.setDrivenKeyframe(warningLambert + '.colorR', currentDriver=upperCtrl + '.scaleFactor')
    cmd.setDrivenKeyframe(warningLambert + '.colorG', currentDriver=upperCtrl + '.scaleFactor')
    cmd.setDrivenKeyframe(warningLambert + '.colorB', currentDriver=upperCtrl + '.scaleFactor')

    cmd.setAttr(upperCtrl + '.scaleFactor', 1)
    cmd.setAttr(warningLambert + '.color', 0, 1, 0, type='double3')
    cmd.setDrivenKeyframe(warningLambert + '.colorR', cd=upperCtrl + '.scaleFactor')
    cmd.setDrivenKeyframe(warningLambert + '.colorG', cd=upperCtrl + '.scaleFactor')
    cmd.setDrivenKeyframe(warningLambert + '.colorB', cd=upperCtrl + '.scaleFactor')

    cmd.connectAttr(stretchMDnode + '.outputX', upperCtrl + '.scaleFactor')

    # assign material to warningbox


    for ctrl in [upperCtrl, lowerCtrl]:
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
                cmd.connectAttr(upperCtrl + '.stretchSpine', box + '.visibility')
    #========================clean outliner=========================
    hideGrp = cmd.group(ikHandle, spineCurve, clusterGrp, n='spine_HideGrp')
    cmd.setAttr(hideGrp + '.v', 0)

    #=========================return value==========================
    returnTuple = (ctrlGrps, hideGrp)
    return returnTuple

# ####################################
# ########### module entry ###########
# ####################################
'''
sj = cmd.ls(selection = True)[0]
jntList = cmd.listRelatives(cmd.ls(selection = True),children = True, ad = True)
ej = jntList[0]

isnerSpine(sj,ej)
'''
