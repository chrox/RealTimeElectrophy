# Generate random orientation and spatial frequency gratings.
#
# Copyright (C) 2010-2011 Huang Xin
#
# See LICENSE.TXT that came with this file.

from __future__ import division
from StimControl.LightStim.SweepSeque import dictattr,ParamSeque
from StimControl.LightStim.FrameControl import FrameSweep
from StimControl.LightStim.Grating import ParamsGrating,IndexedParam
from StimControl.LightStim.Core import DefaultScreen

DefaultScreen(['left','right'])

p = dictattr()
p.ml = 0.5
p.tfreqCycSec = 2.0
p.bgbrightness = 0.0
p.phase0 = 0
p.contrast = 1

orientation = [None]
spatial_freq = IndexedParam('spatial_freq')
phase_at_t0 = [None]

param_sequence = ParamSeque(repeat=4, orientation=orientation, spatial_freq=spatial_freq, phase_at_t0=phase_at_t0, frame_duration=2.0, blank_duration=1.0)

random_grating = ParamsGrating(viewport='left', params=p, sweepseq=param_sequence)
sweep = FrameSweep()
sweep.add_stimulus(random_grating)
sweep.go()