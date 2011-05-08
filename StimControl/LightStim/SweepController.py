# This module contains the base class of SweepTableController.
#
# Copyright (C) 2010-2011 Huang Xin
# 
#
# Distributed under the terms of the GNU Lesser General Public License
# (LGPL). See LICENSE.TXT that came with this file.

import itertools
import VisionEgg.FlowControl
import VisionEgg.ParameterTypes as ve_types

from LightStim import sec2intvsync
    
class SweepTableController(VisionEgg.FlowControl.Controller):
    """Base class for realtime stimulus parameter controller.
    All stimulus parameters come from sweeptable. 
    """
    def __init__(self,sweeptable=None):
        VisionEgg.FlowControl.Controller.__init__(self,
                                           return_type=ve_types.NoneType,
                                           eval_frequency=VisionEgg.FlowControl.Controller.EVERY_FRAME)
        self.st = sweeptable.data
        self.static = sweeptable.static #shorthand
        # multiply the sweeptable index with n vsync for every frame sweep
        nvsync = sec2intvsync(self.static.sweepSec)
        vsynctable = [vsync for sweep in sweeptable.i for vsync in itertools.repeat(sweep,nvsync)]
        # iterator for every vsync sweep
        self.tableindex = iter(vsynctable)
    def next_index(self):
        """Return next vsync sweep index
        """
        try:
            return self.tableindex.next()
        except StopIteration:
            return None
    def during_go_eval(self):
        pass
    def between_go_eval(self):
        pass
    
