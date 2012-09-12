# Display blank screen.
#
# Copyright (C) 2010-2012 Huang Xin
#
# See LICENSE.TXT that came with this file.

from __future__ import division
from StimControl.LightStim.FrameControl import FrameSweep
from StimControl.LightStim.Core import Dummy_Stimulus

duration = 15.0

dummy_stimulus = Dummy_Stimulus()

sweep = FrameSweep()
sweep.add_stimulus(dummy_stimulus)
sweep.parameters.go_duration = (duration, 'seconds')
sweep.go(prestim=5.0,poststim=5.0,RSTART=False)