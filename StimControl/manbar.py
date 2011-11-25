# Demo program using ManBar.
#
# Copyright (C) 2010-2011 Huang Xin
#
#
# Distributed under the terms of the BSD License.
# See LICENSE.TXT that came with this file.

from __future__ import division
from StimControl.LightStim.Core import DefaultScreen
from StimControl.LightStim.SweepSeque import dictattr
from StimControl.LightStim.FrameControl import FrameSweep
from StimControl.LightStim.ManBar import ManBar

DefaultScreen(['control','left','right'])

p = dictattr()

# bar brightness (0-1)
p.brightness = 1
# background brightness (0-1)
p.bgbrightness = 0
# antialiase the bar?
p.antialiase = True
# flash the bar?
p.flash = False
# duration of each on period (sec)
p.flashduration = 0.5
# duration of each off period (sec)
p.flashinterval = 0.3
# factor to chage bar width and height by left/right/up/down key
p.sizemultiplier = 1.02
# brightness step amount on +/- (0-1)
p.brightnessstep = 0.005
# orientation step size to snap to when scrolling mouse wheel (deg)
p.snapDeg = 12

stimulus_control = ManBar(disp_info=True, params=p, viewport='control')
stimulus_left = ManBar(params=p, viewport='left')
stimulus_right = ManBar(params=p, viewport='right')

if __name__ == "__main__":
    sweep = FrameSweep()
    sweep.add_stimulus(stimulus_control)
    sweep.add_stimulus(stimulus_left)
    sweep.add_stimulus(stimulus_right)
    sweep.go()
