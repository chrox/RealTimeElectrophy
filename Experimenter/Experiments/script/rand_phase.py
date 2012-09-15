# Generate random phase grating.
#
# Copyright (C) 2010-2011 Huang Xin
#
# See LICENSE.TXT that came with this file.

from __future__ import division
from StimControl.LightStim.SweepSeque import ParamSeque
from StimControl.LightStim.FrameControl import FrameSweep
from StimControl.LightStim.Grating import ParamsGrating
from StimControl.LightStim.LightData import dictattr

eye = 'left'

p = dictattr()
p.ml = 0.5
p.tfreqCycSec = 0.0
p.bgbrightness = 0.0
p.phase0 = 0
p.contrast = 1

phase_at_t0 = [0.0, 90.0, 180.0, 270.0]
param = ParamSeque(repeat=200, phase_at_t0=phase_at_t0, frame_duration=0.016, blank_duration=0.2)
grating = ParamsGrating(viewport=eye, params=p, sweepseq=param)

sweep = FrameSweep()
sweep.add_stimulus(grating)
sweep.go(prestim=5.0,poststim=5.0,RSTART=True)
