# ##############################################################
# ################## Sparky Controllers Setup ##################
# #################### by Wei Wang #####################
# ##############################################################

import maya.cmds as cmd
import sys
import maya.mel as mel


class Dynamic_chain:
    def __init__(self):
        info = cmd.confirmDialog(button=['Do it', 'Cancel'], defaultButton='Do it', icn=
        'warning', t='Select the start joint of the chain you want make dynamic, then press "Do it" ',
                                 message='Make sure you don\'t have a curve named "Curve1"', dismissString='dismiss', )
        if info == 'Do it':
            self.do()

    def do(self):
        if self.complete_joint_list():
            # create control curve
            positions = []
            # query joint positions:
            for jnt in self.joint_list:
                positions.append(cmd.xform(jnt, q=True, t=True, ws=True))

            init_curve = cmd.curve(n='init_curve', p=positions, ws=True)

            # make curve dynamic
            cmd.select(init_curve, r=True)

            mel.eval('makeCurvesDynamicHairs 1 0 1;')
            cmd.rename('follicle1', 'follicle')
            cmd.rename('curve1', 'outputCurve')

            output_curve = 'outputCurve'

            # create a spline IK on result curve;
            cmd.ikHandle(n='dynIK', sj=self.sj, ee=self.ej, c=output_curve, ccv=False, pcv=False,
                         sol='ikSplineSolver', )

    def complete_joint_list(self):
        selection = cmd.ls(selection=True)

        if len(selection) < 1 or cmd.objectType(selection[0]) != 'joint':
            cmd.confirmDialog(button='OK', defaultButton='OK', icn=
            'warning', t='What are you doing ??', message='Your selection must be a joint!')
            return 0

        else:
            self.sj = selection[0]
            self.joint_list = cmd.listRelatives(cmd.ls(selection=True), children=True, ad=True)
            self.ej = self.joint_list[0]
            # add sj to list:
            self.joint_list.append(self.sj)
            # inverse joint list:
            self.joint_list.reverse()
            return 1

    def blend_fk(self):
        pass