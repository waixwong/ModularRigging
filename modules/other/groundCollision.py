import maya.cmds as cmd

'''
ground collision func.
input gound mesh, constrainted object
2 locators will be generated: a controller and a collision locator
put collision locator at the collision point on the object.

'''


def groundConstraint(mesh, obj):
    name = mesh + '_' + obj

    # 1 create a CPOM node and connect input
    # ############################################################
    # create input position locator and closest point locator:
    pos = cmd.xform(obj, q=True, translation=True, ws=True)
    colLoc = cmd.spaceLocator(n=name + '_collisionLoc')[0]
    cmd.xform(colLoc, translation=pos, ws=True)
    ctrlLoc = cmd.spaceLocator(n=name + '_ctrlLoc', p=pos)[0]
    cmd.xform(ctrlLoc, cp=True)

    cmd.parent(colLoc, ctrlLoc)

    # closest point on mesh node:
    CPOM = cmd.shadingNode('closestPointOnMesh', asUtility=True, n=name + '_CPOM')

    # connect ground mesh to CPOM
    meshShape = cmd.listRelatives(mesh, shapes=True)[0]
    cmd.connectAttr(meshShape + '.worldMesh[0]', CPOM + '.inMesh')
    cmd.connectAttr(meshShape + '.worldMatrix[0]', CPOM + '.inputMatrix')

    # connect ctrl locator and collision locator to CPOM
    # decompose ctrlLoc
    if cmd.pluginInfo('decomposeMatrix', q=True, loaded=True) == False:
        cmd.loadPlugin('decomposeMatrix')

    colLocDM = cmd.shadingNode('decomposeMatrix', asUtility=True, n=colLoc + '_decomposeMatrix')
    cmd.connectAttr(colLoc + '.worldMatrix', colLocDM + '.inputMatrix')
    cmd.connectAttr(colLocDM + '.outputTranslate', CPOM + '.inPosition')
    # ############################################################

    # 2, fix rotation: make obj rotates on surface: normal constraint 
    #############################################################
    # create vector product nodes:
    ax_x = cmd.shadingNode('vectorProduct', asUtility=True, n=name + 'ax_x')
    ax_z = cmd.shadingNode('vectorProduct', asUtility=True, n=name + 'ax_z')
    for node in [ax_x, ax_z]:
        cmd.setAttr(node + '.operation', 2)  #cross product
        cmd.setAttr(node + '.normalizeOutput', 1)  #normalize output

    # normal from CPOM --> vector product nodes
    cmd.setAttr(ax_z + '.input1X', 1)
    cmd.connectAttr(CPOM + '.result.normal', ax_z + '.input2')

    cmd.connectAttr(CPOM + '.result.normal', ax_x + '.input1')
    cmd.connectAttr(ax_z + '.output', ax_x + '.input2')

    # create a 4X4 matrix
    fourbyfour = cmd.shadingNode('fourByFourMatrix', asUtility=True, n=name + '_fourByFourMatrix')

    # connect translate/rotate output to matrix
    cmd.connectAttr(ax_x + '.outputX', fourbyfour + '.in00')
    cmd.connectAttr(ax_x + '.outputY', fourbyfour + '.in01')
    cmd.connectAttr(ax_x + '.outputZ', fourbyfour + '.in02')

    cmd.connectAttr(CPOM + '.result.normalX', fourbyfour + '.in10')
    cmd.connectAttr(CPOM + '.result.normalY', fourbyfour + '.in11')
    cmd.connectAttr(CPOM + '.result.normalZ', fourbyfour + '.in12')

    cmd.connectAttr(ax_z + '.outputX', fourbyfour + '.in20')
    cmd.connectAttr(ax_z + '.outputY', fourbyfour + '.in21')
    cmd.connectAttr(ax_z + '.outputZ', fourbyfour + '.in22')

    cmd.connectAttr(CPOM + '.result.positionX', fourbyfour + '.in30')
    cmd.connectAttr(CPOM + '.result.positionY', fourbyfour + '.in31')
    cmd.connectAttr(CPOM + '.result.positionZ', fourbyfour + '.in32')
    #############################################################

    # 3, detect if collision is happening
    #############################################################
    # create the difference matrix
    diffMatrix = cmd.shadingNode('multMatrix', asUtility=True, n=name + '_diffMatrix')
    # connect output from 4X4 and colLoc inverse worldMatrix to diffMatrix
    cmd.connectAttr(fourbyfour + '.output', diffMatrix + '.matrixIn[0]')
    cmd.connectAttr(colLoc + '.worldInverseMatrix[0]', diffMatrix + '.matrixIn[1]')

    # decompose diffMatrix and create a condition node
    diffMatrixDM = cmd.shadingNode('decomposeMatrix', asUtility=True, n=diffMatrix + '_decomposeMatrix')
    cmd.connectAttr(diffMatrix + '.matrixSum', diffMatrixDM + '.inputMatrix')

    # condition: if diffMatrixDM.ty<0, then collision not happen (true=happe, false = not happen)
    condition = cmd.shadingNode('condition', asUtility=True, n=name + '_condition')
    cmd.setAttr(condition + '.operation', 2)  #greater than
    cmd.setAttr(condition + '.colorIfTrueR', 1)
    cmd.setAttr(condition + '.colorIfFalseR', 0)

    cmd.connectAttr(diffMatrixDM + '.outputTranslate.outputTranslateY', condition + '.firstTerm')

    # blending: collision happen----> collide weight =1, collision not happen---> collide weight =0:
    blend = cmd.shadingNode('pairBlend', asUtility=True, n=name + '_blend')
    cmd.connectAttr(condition + '.outColorR', blend + '.weight')

    # blend ctrl loc and collision loc:
    # decompose ctrlLoc
    ctrlLocDM = cmd.shadingNode('decomposeMatrix', asUtility=True, n=ctrlLoc + '_decomposeMatrix')
    cmd.connectAttr(ctrlLoc + '.worldMatrix', ctrlLocDM + '.inputMatrix')

    # decompose 4X4
    fourbyfourDM = cmd.shadingNode('decomposeMatrix', asUtility=True, n=fourbyfour + '_decomposeMatrix')
    cmd.connectAttr(fourbyfour + '.output', fourbyfourDM + '.inputMatrix')

    # blend:
    cmd.connectAttr(ctrlLocDM + '.outputTranslate', blend + '.inTranslate1')
    cmd.connectAttr(ctrlLocDM + '.outputRotate', blend + '.inRotate1')
    cmd.connectAttr(fourbyfourDM + '.outputTranslate', blend + '.inTranslate2')
    cmd.connectAttr(fourbyfourDM + '.outputRotate', blend + '.inRotate2')
    ########################################################################

    # 5. offset obj position(contact)
    ########################################################################
    offsetMatrix = cmd.shadingNode('multMatrix', asUtility=True, n=name + 'offsetMatrix')
    cmd.connectAttr(diffMatrix + '.matrixSum', offsetMatrix + '.matrixIn[0]')
    cmd.connectAttr(ctrlLoc + '.worldMatrix[0]', offsetMatrix + '.matrixIn[1]')

    cmd.connectAttr(offsetMatrix + '.matrixSum', fourbyfourDM + '.inputMatrix', force=True)

    # 5. connect result to obj
    ########################################################################
    objGrp = cmd.group(obj, n=obj + '_collision_Grp', r=True)
    cmd.connectAttr(blend + '.outTranslate', objGrp + '.translate')
    cmd.connectAttr(blend + '.outRotate', objGrp + '.rotate')

    return (ctrlLoc, colLoc, objGrp)