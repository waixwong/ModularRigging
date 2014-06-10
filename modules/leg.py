__author__ = 'WEI'

from modules.module import Module
from utilities import joints, general
import pymel.core as pm
import maya.cmds as cmds

reload(joints)


class Leg(Module):
    def __init__(self, joints):
        super(Leg, self).__init__(joints=joints)
        self._root = self._joints[0]
        self._end = self._joints[-1]
        self._ik_chain = None
        self._fk_chain = None

        self.switch = None

    def setup(self):
        print 'setting up leg'

    def install(self):
        self._setup_ikfk()

    def _setup_ikfk(self):
        ik_jnt_names = [x + '_ik' for x in self._joints]
        fk_jnt_names = [x + '_fk' for x in self._joints]

        # duplicate command will also duplicate children nodes, including constraint nodes
        # thus must duplicate before setting up any connections/ constraints.
        ik_chain = joints.duplicate_chain(self._root, ik_jnt_names)
        fk_chain = joints.duplicate_chain(self._root, fk_jnt_names)

        # constraint deformation chain:
        ik_weight_attrs = []
        for index, jnt in enumerate(ik_chain):
            constraint = pm.parentConstraint(jnt, self._joints[index])
            alias = constraint.getWeightAliasList()
            ik_weight_attrs.append(alias)

        fk_weight_attrs = []
        for index, jnt in enumerate(fk_chain):
            constraint = pm.parentConstraint(jnt, self._joints[index])
            alias = constraint.getWeightAliasList()
            fk_weight_attrs.append(alias)

        # flatten the lists
        ik_weight_attrs = general.flatten_list(ik_weight_attrs)
        fk_weight_attrs = general.flatten_list(fk_weight_attrs)
        fk_weight_attrs = [x for x in fk_weight_attrs if x not in ik_weight_attrs]

        # setup blend switch
        # create a switch object, if no specified.
        # fixme: if switch object specified

        switch_transform = pm.createNode('transform')
        attr_name = 'IK_FK'
        switch_transform.addAttr(attr_name, attributeType='double', min=0, max=1, dv=0, k=1)
        switch_attr = switch_transform.attr(attr_name)

        # use a plusMinusAverage node to control the blending:
        plus_minus_node = pm.createNode('plusMinusAverage')
        plus_minus_node.operation.set(2)
        plus_minus_node.input1D[0].set(1)

        switch_attr.connect(plus_minus_node.input1D[1])

        for ik_attr in ik_weight_attrs:
            plus_minus_node.output1D.connect(ik_attr)
        for fk_attr in fk_weight_attrs:
            switch_attr.connect(fk_attr)

        # setup IK
        ik = pm.ikHandle(n=ik_chain[0] + '_ikHandle', sj=ik_chain[0], ee=ik_chain[-1], sol='ikRPsolver', s=0)
        ik_handle = ik[0]