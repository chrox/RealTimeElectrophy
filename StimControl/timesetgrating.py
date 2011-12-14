# Generate arbitrary onset and offset timing gratings.
#
# Copyright (C) 2010-2011 Huang Xin
#
# See LICENSE.TXT that came with this file.

from __future__ import division
import numpy as np
from StimControl.LightStim.SweepSeque import dictattr,TimingSeque
from StimControl.LightStim.FrameControl import FrameSweep
from StimControl.LightStim.Grating import TimingSetGrating
from StimControl.LightStim.Core import DefaultScreen

DefaultScreen(['left','right'])

p = dictattr()
p.ml = 0.5
p.tfreqCycSec = 0.0
p.bgbrightness = 0.0
p.phase0 = 0
p.contrast = 1

cycle_left = dictattr(duration=0.2, pre=np.linspace(0.0,0.0,1), stimulus=0.05)
cycle_right = dictattr(duration=0.2, pre=np.linspace(0.03,0.03,1), stimulus=0.05)
episode_left = dictattr(repeat=50, cycle=cycle_left, interval=1.0)
episode_right = dictattr(repeat=50, cycle=cycle_right, interval=1.0)
sequence_left = TimingSeque(repeat=10, episode=episode_left, shuffle=True)
sequence_right = TimingSeque(repeat=10, episode=episode_right, shuffle=True)

grating_left = TimingSetGrating(viewport='left', params=p, sweepseq=sequence_left)
p.phase0 = 180.0
grating_right = TimingSetGrating(viewport='right', params=p, sweepseq=sequence_right)
sweep = FrameSweep()
sweep.add_stimulus(grating_left)
sweep.add_stimulus(grating_right)
sweep.go()



