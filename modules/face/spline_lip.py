__author__ = 'WEI'
import maya.cmds as cmd

import sys
import joints as jnt


reload(jnt)


class Spline_lip:
    def __init__(self):
        self.initlocPos = [(0, 1, 0), (1, 1, 0), (2, 0.9, 0), (3, 0.7, 0), (4, 0, 0), (0, -1, 0), (1, -1, 0),
                           (2, -0.9, 0),
                           (3, -0.7, 0)]
        self.locators = ['upper_mid', 'upper1', 'upper2', 'upper3', 'corner', 'lower_mid', 'lower1', 'lower2', 'lower3']
        info = cmd.confirmDialog(button=['Place locators', 'Create rig!', 'Cancel'], defaultButton='cancel', icn=
        'information', t='Select the start joint of the chain you want make dynamic, then press "Do it" ',
                                 message='Make sure you don\'t have a curve named "Curve1"', dismissString='dismiss', )
        if info == 'Place locators':
            self.setup_locators()
        if info == 'Create rig!':
            self.create_rig()

    def setup_locators(self):
        """
        set up initial locators for placement.
        """
        for i in range(0, 9):
            locator = cmd.spaceLocator(n=self.locators[i], a=True)[0]
            self.locators.append(locator)
            cmd.xform(locator, t=self.initlocPos[i], ws=True)
            cmd.select(clear=True)

    def create_rig(self):
        # create deformation chain
        chain = jnt.create_floating_jnts(self.locators, radius=0.4)
        rotation_chain = []
        deformation_chain = []
        for joint in chain:
            joint = cmd.rename(joint, joint + '_deformation')
            deformation_chain.append(joint)
            # duplicate deformation chain to create rotation chain
            rj = cmd.duplicate(joint, n=joint + '_rotation')[0]
            rotation_chain.append(rj)
            cmd.joint(rj, e=True, radius=0.6)

            # create spline chain.



