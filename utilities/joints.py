import maya.cmds as cmd
import pymel.core as pm


def create_chain(locators, side=0, m_sao='yup', m_oj='xyz', prefix='jnt_', radius=1.0):
    positions = get_position(locators)
    joints = []

    if side == 0:
        LR = ''
    elif side == 1:
        LR = 'L_'
    else:
        LR = 'R_'

    cmd.select(clear=True)
    for index in range(0, len(positions)):
        jnt = cmd.joint(n=(LR + prefix + locators[index]), p=tuple(positions[index]), rad=radius)
        joints.append(jnt)

    cmd.joint(joints, e=True, zso=True, oj=m_oj, sao=m_sao)

    return joints


def get_position(locators):
    positionList = []

    for obj in locators:
        shapeNode = cmd.listRelatives(obj, shapes=True)[0]
        location = cmd.getAttr(shapeNode + '.worldPosition')[0]
        positionList.append(location)
    return positionList


def create_floating_jnts(indicators, radius=1):
    positions = get_position(indicators)
    joints = []

    for index in range(0, len(positions)):
        jnt = cmd.joint(n="jnt_" + (indicators[index]), p=tuple(positions[index]), rad=radius)
        joints.append(jnt)
        cmd.select(clear=True)

    return joints


def duplicate_chain(root, names):
    # duplicate input chain
    """
    create a copy of a joint chain
    :param root: root joint of the chain to duplicate
    :param names: list of names of duplicated chain
    """
    duplicatedChain = cmd.duplicate(root, renameChildren=True, inputConnections=False, returnRootsOnly=False)
    print duplicatedChain
    # rename duplicated chain:
    for i in range(0, len(duplicatedChain)):
        duplicatedChain[i] = cmd.rename(duplicatedChain[i], names[i])

    return duplicatedChain


def completeChain(sj):
    # get the complete chain:
    completeJnts = cmd.listRelatives(sj, children=True, allDescendents=True, type='joint')
    completeJnts.append(sj)
    # joints order in spineJnt list is reversed. [ej,....,sj]
    completeJnts.reverse()

    return completeJnts