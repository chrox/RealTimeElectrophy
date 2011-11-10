# Generate random orientation and spatial frequency gratings.
#
# Copyright (C) 2010-2011 Huang Xin
#
#
# Distributed under the terms of the BSD License.
# See LICENSE.TXT that came with this file.

from __future__ import division
from LightStim.SweepSeque import dictattr,ParamSeque
from LightStim.FrameControl import FrameSweep
from LightStim.Grating import Grating,IndexedParam

p = dictattr()
p.ml = 0.5
p.tfreqCycSec = 2.0
p.bgbrightness = 0.0
p.phase0 = 0
p.contrast = 1

orientation = [None]
spatial_freq = [None]
phase_at_t0 = [0]*16
param_left = ParamSeque(repeat=4, orientation=orientation, spatial_freq=spatial_freq, phase_at_t0=phase_at_t0, frame_duration=2.0, blank_duration=1.0)

phase_at_t0 = IndexedParam('phase_at_t0')
param_right = ParamSeque(repeat=4, orientation=orientation, spatial_freq=spatial_freq, phase_at_t0=phase_at_t0, frame_duration=2.0, blank_duration=1.0)

grating_left = Grating(viewport='left', params=p, sweepseq=param_left, trigger=False)
grating_right = Grating(viewport='right', params=p, sweepseq=param_right)

sweep = FrameSweep()
sweep.add_stimulus(grating_left)
sweep.add_stimulus(grating_right)
sweep.go()
