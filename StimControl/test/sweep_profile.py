# Profile the sweep
#
# Copyright (C) 2010-2011 Huang Xin
#
# See LICENSE.TXT that came with this file.

from __future__ import division
from StimControl.LightStim.Core import DefaultScreen
from StimControl.LightStim.LightData import dictattr
from StimControl.LightStim.FrameControl import FrameSweep
from StimControl.LightStim.ManGrating import ManGrating
# Manual Grating experiment parameters, all must be scalars

DefaultScreen(['control','left','right'])

p = dictattr()
# mask, one of:  None, 'gaussian', or 'circle'
p.mask = 'circle'
p.maskSizeStepDeg = 0.5
# initial grating phase
p.phase0 = 0
# grating mean luminance (0-1)
p.ml = 0.5
# grating contrast (0-1)
p.contrast = 1
# background brightness (0-1)
p.bgbrightness = 0.5
# antialiase the bar?
p.antialiase = True
# flash the grating?
p.flash = False
# duration of each on period (sec)
p.flashduration = 0.5
# duration of each off period (sec)
p.flashinterval = 0.3
# factor to chage bar width and height by left/right/up/down key
p.sizemultiplier = 1.02
# factor to change temporal freq by on up/down
p.tfreqmultiplier = 1.01
# factor to change spatial freq by on left/right
p.sfreqmultiplier = 1.01
# factor to change contrast by on +/-
p.contrastmultiplier = 1.005
# orientation step size to snap to when scrolling mouse wheel (deg)
p.snapDeg = 12

stimulus_control = ManGrating(disp_info=True, params=p, viewport='control')
stimulus_left = ManGrating(disp_info=False, params=p, viewport='left')
stimulus_right = ManGrating(disp_info=False, params=p, viewport='right')

sweep = FrameSweep()
sweep.add_stimulus(stimulus_control)
sweep.add_stimulus(stimulus_left)
sweep.add_stimulus(stimulus_right)
import cProfile,pstats
cProfile.run('sweep.go()','mangrating_profile')
p = pstats.Stats('mangrating_profile')
p.sort_stats('cumulative')
p.print_stats()