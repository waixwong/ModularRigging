__author__ = 'WEI'

import maya.cmds as cmd
from limbs import module
from utilities import joints as j

reload(module)
reload(j)


class IKFK(module.Module):
    def _setup(self):
        # build binding chain:
        self.bindingChain = j.create_chain(self.locators, self.names, self.sao, self.oj)
        # create IK chain and FK chain:
        ikNames = []
        fkNames = []

        for jnt in self.bindingChain:
            ikName = jnt + '_ik'
            fkName = jnt + '_fk'

            ikNames.append(ikName)
            fkNames.append(fkName)

        ikChain = j.duplicate_chain(self.bindingChain[0], ikNames)
        fkChain = j.duplicate_chain(self.bindingChain[0], fkNames)

        self.setupFK(fkChain)

    def setupIK(self, ikChain):
        # setup IK:
        """
        setup an ik on the input list
        :param ikChain: list of joint chain to set an ik on
        """
        handle = cmd.ikHandle(n=ikChain[0] + '_ikHandle', sj=ikChain[0], ee=ikChain[-1], sol='ikRPsolver', s=0)
        # get pole vector location:

    def setupFK(self, fkChain):
        self.fkCtrls = []
        for i in range(0, len(fkChain)):
            ctrl = cmd.circle(n='ctrl_' + self.names[i], radius=1)
            self.fkCtrls.append(ctrl)

        print self.fkCtrls





