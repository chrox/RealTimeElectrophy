# Demo program using ManGrating.
#
# Copyright (C) 2010-2011 Huang Xin
# 
#
# Distributed under the terms of the GNU Lesser General Public License
# (LGPL). See LICENSE.TXT that came with this file.
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
from LightStim.SweepTable import StaticParams
from LightStim.FrameControl import FrameSweep
from LightStim.ManGrating import ManGrating
# Manual Grating experiment parameters, all must be scalars

p = StaticParams()
# grating width (deg)
p.widthDeg = 20
# grating height (deg)
p.heightDeg = 20
# mask, one of:  None, 'gaussian', or 'circle'
p.mask = None
p.maskDiameterDeg = 5
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
# rate of change of size during buttonpress (deg/sec)
p.sizerateDegSec = 25
# rate of change of orientation during mouse button press (deg/sec)
p.orirateDegSec = 18
# factor to change temporal freq by on up/down
p.tfreqmultiplier = 1.01
# factor to change spatial freq by on left/right
p.sfreqmultiplier = 1.01
# factor to change contrast by on +/-
p.contrastmultiplier = 1.005
# orientation step size to snap to when scrolling mouse wheel (deg)
p.snapDeg = 18

stimulus_control = ManGrating(disp_info=True, params=p, viewport='control')
stimulus_primary = ManGrating(disp_info=False, params=p, viewport='primary')
stimulus_left = ManGrating(disp_info=False, params=p, viewport='left')
stimulus_right = ManGrating(disp_info=False, params=p, viewport='right')

if __name__ == "__main__":
    sweep = FrameSweep()
    sweep.add_stimulus(stimulus_control)
    sweep.add_stimulus(stimulus_primary)
    sweep.add_stimulus(stimulus_left)
    sweep.add_stimulus(stimulus_right)
    sweep.go()