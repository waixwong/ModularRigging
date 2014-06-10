__author__ = 'WEI'
import maya.cmds as cmd
import maya.mel as mel

import utilities.joints as j

reload(j)
import utilities.general as general

reload(general)


class IKSpine():
    def __init__(self, joints, upperCtrl=None, lowerCtrl=None):
        self.joints = joints
        self.upperCtrl = upperCtrl
        self.lowerCtrl = lowerCtrl

        self._setup()

    def _setup(self):
        sj = self.joints[0]
        ej = self.joints[-1]

        self.spineCurve = 'curve_bindSpine'
        # setup IK
        ikSpine = cmd.ikHandle(sj=sj, ee=ej, name='ikHandle_bindSpine', sol='ikSplineSolver', createCurve=True,
                               ns=2)
        cmd.rename(ikSpine[2], self.spineCurve)

        # clusters
        clusterReturn = general.clusterCurve(self.spineCurve, 'cluster_spineIK')
        clusters = clusterReturn[0]
        clusterGrp = clusterReturn[1]

        # ==================controllers setup=============================
        if self.upperCtrl == None:
            self.upperCtrl = self._drawCtrl('ctrl_upperTorso', self.joints[-2])
        if self.lowerCtrl == None:
            self.lowerCtrl = self._drawCtrl('ctrl_lowerTorso', self.joints[1])

        for i in [0, 1]:
            cmd.parentConstraint(self.lowerCtrl, clusters[i], mo=True)
        for i in [2, 3, 4]:
            cmd.parentConstraint(self.upperCtrl, clusters[i], mo=True)