# Generate random orientation and spatial frequency gratings.
#
# Copyright (C) 2010-2011 Huang Xin
#
# See LICENSE.TXT that came with this file.

from __future__ import division
from StimControl.LightStim.SweepSeque import ParamSeque
from StimControl.LightStim.FrameControl import FrameSweep
from StimControl.LightStim.Grating import ParamMapGrating
from StimControl.LightStim.Core import DefaultScreen
from StimControl.LightStim.LightData import dictattr,IndexedParam

DefaultScreen(['left'])

p = dictattr()
p.ml = 0.5
p.tfreqCycSec = 2.0
p.bgbrightness = 0.5
p.phase0 = 0
p.contrast = 1

orientation = IndexedParam('orientation_180')
spatial_freq = IndexedParam('spatial_freq')
phase_at_t0 = [None]

param_sequence = ParamSeque(repeat=4, orientation=orientation, spatial_freq=spatial_freq, phase_at_t0=phase_at_t0, frame_duration=0.1, blank_duration=0.0)

random_grating = ParamMapGrating(viewport='left', params=p, sweepseq=param_sequence)
sweep = FrameSweep()
sweep.add_stimulus(random_grating)
sweep.go()