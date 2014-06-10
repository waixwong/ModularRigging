__author__ = 'WEI'

import modules.module as module


class Spine(module.Module):
    def __init__(self):
        super(Spine, self).__init__()

    def setup(self):
        print 'Setting up Spine'

    def install(self, joints=None):
        if joints is not None:
            self.joints = joints

        print 'installing Spine'

    @property
    def joints(self):
        return self._joints

    @joints.setter
    def joints(self, value):
        self._joints = value

