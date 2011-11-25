# Demo program using ManGrating.
#
# Copyright (C) 2010-2011 Huang Xin
#
#
# Distributed under the terms of the BSD License.
# See LICENSE.TXT that came with this file.

"""
USAGE:
        Move the mouse cursor to change the position of the grating.
        Scroll the mouse wheel to change the orientation.
        Press right arrow to increase the spatial frequency.
        Press left arrow to decrease the spatial frequency.
        Press up arrow to increase the temporal frequency.
        ...
"""
from __future__ import division
from StimControl.LightStim.Core import DefaultScreen
from StimControl.LightStim.SweepSeque import dictattr
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

if __name__ == "__main__":
    sweep = FrameSweep()
    sweep.add_stimulus(stimulus_control)
    sweep.add_stimulus(stimulus_left)
    sweep.add_stimulus(stimulus_right)
    sweep.go()