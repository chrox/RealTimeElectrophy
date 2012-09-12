# Generate random orientation and spatial frequency gratings.
#
# Copyright (C) 2010-2011 Huang Xin
#
# See LICENSE.TXT that came with this file.

from __future__ import division
from StimControl.LightStim.SweepSeque import ParamSeque
from StimControl.LightStim.FrameControl import FrameSweep
from StimControl.LightStim.Grating import ParamsGrating
from StimControl.LightStim.LightData import dictattr,IndexedParam

eye = 'left'

p = dictattr()
p.ml = 0.5
p.tfreqCycSec = 2.0
p.bgbrightness = 0.5
p.phase0 = 0
p.contrast = 1

orientation = IndexedParam('orientation')
param_sequence = ParamSeque(repeat=4, orientation=orientation, frame_duration=2.0, blank_duration=1.0)

random_grating = ParamsGrating(viewport=eye, params=p, sweepseq=param_sequence)
sweep = FrameSweep()
sweep.add_stimulus(random_grating)
sweep.go(prestim=5.0,poststim=5.0,RSTART=True)