# Generate random orientation and spatial frequency gratings.
#
# Copyright (C) 2010-2011 Huang Xin
#
# See LICENSE.TXT that came with this file.

from __future__ import division
from StimControl.LightStim.SweepSeque import ParamSeque
from StimControl.LightStim.FrameControl import FrameSweep
from StimControl.LightStim.Grating import ParamsGrating, MonocularGrating
from StimControl.LightStim.Core import DefaultScreen
from StimControl.LightStim.LightData import dictattr,IndexedParam

DefaultScreen(['left','right'])

p = dictattr()
p.ml = 0.5
p.tfreqCycSec = 2.0
p.bgbrightness = 0.5
p.phase0 = 0
p.contrast = 1

#Monocular stimuli
phase_at_t0 = [0]
monocular_param_left = ParamSeque(repeat=1, phase_at_t0=phase_at_t0, frame_duration=2.0, blank_duration=1.0)
monocular_param_right = ParamSeque(repeat=1, phase_at_t0=phase_at_t0, frame_duration=2.0, blank_duration=1.0)
monocular_grating_left = MonocularGrating(viewport='left', params=p, sweepseq=monocular_param_left)
monocular_grating_right = MonocularGrating(viewport='right', params=p, sweepseq=monocular_param_right)

#Binocular stimuli
phase_at_t0 = [0]*16
param_left = ParamSeque(repeat=4, phase_at_t0=phase_at_t0, frame_duration=2.0, blank_duration=1.0)

phase_at_t0 = IndexedParam('phase_at_t0')
param_right = ParamSeque(repeat=4, phase_at_t0=phase_at_t0, frame_duration=2.0, blank_duration=1.0)

grating_left = ParamsGrating(viewport='left', params=p, sweepseq=param_left, trigger=False)
grating_right = ParamsGrating(viewport='right', params=p, sweepseq=param_right)

sweep = FrameSweep()
sweep.add_stimulus(monocular_grating_left)
sweep.go()
sweep.add_stimulus(monocular_grating_right)
sweep.go()
sweep.add_stimulus(grating_left)
sweep.add_stimulus(grating_right)
sweep.go()
