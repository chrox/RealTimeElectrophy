# Generate arbitrary onset and offset timing gratings.
#
# Copyright (C) 2010-2011 Huang Xin
# 
#
# Distributed under the terms of the GNU Lesser General Public License
# (LGPL). See LICENSE.TXT that came with this file.

from __future__ import division
import numpy as np
from LightStim.SweepSeque import dictattr,TimingSeque
from LightStim.FrameControl import FrameSweep
from LightStim.Grating import Grating

p = dictattr()
p.ml = 0.5
p.tfreqCycSec = 0.0
p.bgbrightness = 0.0
p.phase0 = 0
p.contrast = 1

cycle_left = dictattr(duration=0.3, pre=np.linspace(0.0,0.0,10), stimulus=0.05)
cycle_right = dictattr(duration=0.3, pre=np.linspace(0.0,0.1,10), stimulus=0.05)
episode_left = dictattr(repeat=5, cycle=cycle_left, interval=1.0)
episode_right = dictattr(repeat=5, cycle=cycle_right, interval=1.0)
sequence_left = TimingSeque(repeat=1, episode=episode_left, shuffle=True)
sequence_right = TimingSeque(repeat=1, episode=episode_right, shuffle=True)

grating_left = Grating(viewport='left', params=p, sweepseq=sequence_left)
grating_right = Grating(viewport='right', params=p, sweepseq=sequence_right)
sweep = FrameSweep()
sweep.add_stimulus(grating_left)
sweep.add_stimulus(grating_right)
sweep.go()



