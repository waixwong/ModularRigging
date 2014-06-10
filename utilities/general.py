__author__ = 'WEI'

import maya.cmds as cmd
import itertools


def moveToPosition(obj, target, freeze=False):
    position = cmd.xform(target, q=True, translation=True, ws=True)
    cmd.xform(obj, translation=position, ws=True)
    if freeze:
        cmd.makeIdentity(obj, t=True, s=True, r=True, a=True)


# make clusters on an input curve, name the clusters as prefix_num, and put all clusters into a grp named prefix_grp.
def clusterCurve(curveName, namePrefix, grpSuffix='_grp'):
    cmd.select(d=True)
    cmd.select(curveName)
    cmd.ClusterCurve()
    scList = cmd.listRelatives(cmd.listRelatives(cmd.ls('cluster*', tr=1), shapes=1, type='clusterHandle'), parent=1)
    groupName = cmd.group(scList, n=namePrefix + grpSuffix)
    for obj in scList:
        cmd.rename(obj, namePrefix + '_1')

    clusterList = cmd.listRelatives(groupName, children=True)
    return (clusterList, groupName)


def makeCtrlLayer(obj, suffix='_grp'):
    grp = cmd.group(empty=True, n=obj + suffix)
    constraint = cmd.parentConstraint(obj, grp, mo=False)
    cmd.delete(constraint)
    cmd.parent(obj, grp)


def snap(ctrlName, target):
    cmd.rename('controller1', ctrlName)
    # move it to pos
    ctrlGrp = cmd.group(empty=True, n=ctrlName + '_grp')
    cmd.parent(ctrlName, ctrlGrp)
    cmd.parentConstraint(target, ctrlGrp, mo=False)
    cmd.delete(ctrlGrp + '_parentConstraint1')
    return ctrlGrp


def flatten_list(the_list):
    """
    Make a flat list out of list of lists in Python
    @param the_list: the list to flat
    @return: the flattened list
    """
    flat_list = list(itertools.chain.from_iterable(the_list))
    return flat_list