__author__ = 'WEI'


class Module(object):
    def __init__(self, joints=None):
        self._joints = joints

        # groups
        self.non_xform = None
        self.xform = None
        self.deformation = None
        self.invisible = None

    def setup(self):
        print 'setting up module'

    def install(self):
        print 'installing module'

