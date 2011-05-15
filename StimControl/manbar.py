# Demo program using WhiteNoise.
#
# Copyright (C) 2010-2011 Huang Xin
# 
#
# Distributed under the terms of the GNU Lesser General Public License
# (LGPL). See LICENSE.TXT that came with this file.
from __future__ import division

from LightStim.SweepTable import StaticParams
from LightStim.FrameControl import FrameSweep
from LightStim.ManBar import ManBar

p = StaticParams()

# Manual Bar experiment parameters, all must be scalars

# bar brightness (0-1)
p.brightness = 1
# background brightness (0-1)
p.bgbrightness = 0
# antialiase the bar?
p.antialiase = True
# flash the bar?
p.flash = False
# duration of each flash cycle (on and off) (sec)
p.flashSec = 1
# rate of change of size during buttonpress (deg/sec)
p.sizerateDegSec = 4
# rate of change of orientation during mouse button press (deg/sec)
p.orirateDegSec = 18
# brightness step amount on +/- (0-1)
p.brightnessstep = 0.005
# orientation step size to snap to when scrolling mouse wheel (deg)
p.snapDeg = 18
# print vsync histogram?
p.printhistogram = False
# display on how many screens?
p.nscreens = 2

stimulus_control = ManBar(viewport='Viewport_control', params=p, disp_info=True)
stimulus_primary = ManBar(viewport='Viewport_primary', params=p, disp_info=False)
stimulus_left = ManBar(viewport='Viewport_left', params=p, disp_info=False)
stimulus_right = ManBar(viewport='Viewport_right', params=p, disp_info=False)
sweep = FrameSweep()
sweep.add_stimulus(stimulus_control)
sweep.add_stimulus(stimulus_primary)
sweep.add_stimulus(stimulus_left)
sweep.add_stimulus(stimulus_right)
sweep.add_controllers()
sweep.attach_event_handlers()
sweep.go()
