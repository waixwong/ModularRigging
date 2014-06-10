__author__ = 'WEI'

import maya.cmds as cmd
import modules.spine.isner as spine

reload(spine)

import utilities.joints as j

reload(j)

dir = '/Users/WEI/Dropbox/girl/'


class Girl:
    def __init__(self):
        self.ns = 'gril:'
        self.dir = dir
        self.model = self.dir + 'girl.ma'

        # import model into current scene:
        model = self.dir + 'girl.ma'
        cmd.file(model, i=True, lrd='none', type='mayaAscii')

        # import locators and controllers:
        locators = self.dir + 'info.ma'
        cmd.file(locators, i=True, lrd='none', type='mayaAscii')

        self._createSkeleton()
        self.setup()

        # self.addNameSpace()

    def _createSkeleton(self):
        # root:
        root = ['root']
        rootJoint = j.create_chain(root)

        # spine:
        spine_locators = ['spine_root', 'spine_waist', 'spine_mid', 'spine_chest', 'spine_end']
        self.spineJoints = j.create_chain(spine_locators, m_sao='zup', radius=0.6)

        # legs:
        leg_locators = ['hip', 'knee', 'ankle', 'ball', 'toe']
        l_legJoints = j.create_chain(leg_locators, side=1, m_sao='xup', radius=0.7)
        r_legJoints = cmd.mirrorJoint(l_legJoints[0], mirrorBehavior=1, mirrorYZ=1, searchReplace=['L_', 'R_'])

        # arms:
        arm_locators = ['shoulder', 'elbow', 'wrist']
        l_armJoints = j.create_chain(arm_locators, side=1)
        r_armJoints = cmd.mirrorJoint(l_armJoints[0], mirrorBehavior=1, mirrorYZ=1, searchReplace=['L_', 'R_'])

        # fingers:
        fingers = ['index', 'mid', 'ring', 'pinky']
        for finger in fingers:
            finger_locators = [finger + '_1', finger + '_2', finger + '_3', finger + '_end']
            l_fingerJoints = j.create_chain(finger_locators, side=1, radius=0.2)
            r_fingerJoints = cmd.mirrorJoint(l_fingerJoints[0], mirrorBehavior=1, mirrorYZ=1,
                                             searchReplace=['L_', 'R_'])

    def setup(self):
        """
        character setup, do this after skeleton is complete.
        :type self: object
        """
        # setup spine: Isner spine:
        self.spine = spine.IsnerSpine(self.spineJoints, 'ctrl_upperTorso')


    def _setup_legs(self, prefix, leg_locators):
        # setup IK/FK leg with floating foot pivot:
        names = []
        # leg locations:
        for locator in leg_locators:
            name = prefix + locator
            names.append(name)

        ikfk.IKFK(names, leg_locators)
