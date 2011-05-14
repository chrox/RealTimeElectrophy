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
p.xorigDeg = -3.510392 # x coord of stimulus center anchor from screen center, in deg
p.yorigDeg = 2.73537 # y coord of stimulus center anchor from screen center, in deg
p.widthDeg = 15.146667 # stimulus width in deg. Width is the dimension || to ori
p.heightDeg = 12.266667 # stimulus width in deg. Height is the dim |_ to ORI
p.ori = 293 # orientation of manbar in deg from the positive x axis, counterclockwise, used as stimulus orientation offset
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

stimulus_with_info = ManBar(viewport='Viewport_control', params=p, disp_info=True)
stimulus_no_info = ManBar(viewport='Viewport_left', params=p, disp_info=False)
sweep = FrameSweep()
sweep.add_stimulus(stimulus_with_info)
sweep.add_stimulus(stimulus_no_info)
sweep.add_controllers()
sweep.attach_event_handlers()
sweep.go()
