# Generate arbitrary onset and offset timing gratings.
#
# Copyright (C) 2010-2011 Huang Xin
#
# See LICENSE.TXT that came with this file.

from __future__ import division
from StimControl.LightStim.SweepSeque import TimingSeque
from StimControl.LightStim.LightData import dictattr
from StimControl.LightStim.FrameControl import FrameSweep
from StimControl.LightStim.Grating import TimingSetGrating
from StimControl.LightStim.Core import DefaultScreen

DefaultScreen(['left','right'])

p_left = dictattr()
p_left.ml = 0.5
p_left.tfreqCycSec = 0.0
p_left.bgbrightness = 0.0
p_left.contrast = 1
p_left.phase0 = 0

p_right = dictattr()
p_right.ml = 0.5
p_right.tfreqCycSec = 0.0
p_right.bgbrightness = 0.0
p_right.contrast = 1
p_right.phase0 = 0

stim_interval = 0.0

pre_left = 0.0 if stim_interval > 0 else stim_interval
pre_right = 0.0 if stim_interval <= 0 else stim_interval

repeats = 1600

cycle_left = dictattr(duration=0.132, pre=pre_left, stimulus=0.016)
cycle_right = dictattr(duration=0.132, pre=pre_right, stimulus=0.016)
block_left = dictattr(repeat=repeats, cycle=cycle_left, interval=0.0)
block_right = dictattr(repeat=repeats, cycle=cycle_right, interval=0.0)
sequence_left = TimingSeque(repeat=1, block=block_left, shuffle=True)
sequence_right = TimingSeque(repeat=1, block=block_right, shuffle=True)

grating_left = TimingSetGrating(viewport='left', params=p_left, sweepseq=sequence_left)
grating_right = TimingSetGrating(viewport='right', params=p_right, sweepseq=sequence_right)
sweep = FrameSweep()
sweep.add_stimulus(grating_left)
sweep.add_stimulus(grating_right)
sweep.go(prestim=5.0,poststim=5.0,RSTART=True)



