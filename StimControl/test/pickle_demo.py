# 
#
# Copyright (C) 2010-2011 Huang Xin
#
# See LICENSE.TXT that came with this file.

from StimControl.LightStim.SweepSeque import ParamSeque
from StimControl.LightStim.FrameControl import FrameSweep
from StimControl.LightStim.Grating import ParamsGrating
from StimControl.LightStim.Core import DefaultScreen
from StimControl.LightStim.LightData import dictattr,IndexedParam

DefaultScreen(['left','right'])

p = dictattr()
p.ml = 0.5
p.tfreqCycSec = 2.0
p.bgbrightness = 0.0
p.phase0 = 0
p.contrast = 1

orientation = IndexedParam('orientation')
spatial_freq = [None]
phase_at_t0 = [None]

param_sequence = ParamSeque(repeat=4, orientation=orientation, spatial_freq=spatial_freq, phase_at_t0=phase_at_t0, frame_duration=2.0, blank_duration=1.0)

random_grating = ParamsGrating(viewport='left', params=p, sweepseq=param_sequence)

import pickle
with open('test_pickle.pkl','w') as file:
    pickle.dump(random_grating,file,1)
with open('test_pickle.pkl','r') as file:
    unpckled_stim = pickle.load(file)
    
sweep = FrameSweep()
sweep.add_stimulus(unpckled_stim)

sweep.go()

