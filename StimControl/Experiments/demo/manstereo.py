# Demo program using Manstereo.
#
# Copyright (C) 2010-2013 Huang Xin
#
# See LICENSE.TXT that came with this file.

from __future__ import division
import sys
from StimControl.LightStim.Core import DefaultScreen
from StimControl.LightStim.LightData import dictattr
from StimControl.LightStim.FrameControl import FrameSweep
from StimControl.LightStim.ManStereo import ManStereo
# Manual Grating experiment parameters, all must be scalars

p = dictattr()
p.bgbrightness = 0.5
p.antialiase = True

p.dotsNumber = 2000
p.dotSquareWidth = 7.5
p.randomSeed = 0
p.discDistDeg = 2.5
p.discDiameter = 1.25
p.disparity = 0

p.snapDeg = 45.0
p.disparityStep = 0.02

if __name__ == '__main__':
    DefaultScreen(['control','left','right'])
    subject = None
    argv = list(sys.argv)
    if len(argv) >= 2:
        subject = argv[1]
    while subject is None:
        sys.stdout.write('Please input lowercase initials of subject name: ')
        subject = raw_input()
    
    stimulus_control = ManStereo(disp_info=False, subject=subject, params=p, viewport='control')
    stimulus_left = ManStereo(disp_info=False, subject=subject, params=p, viewport='left')
    p.disparity = 0.3
    stimulus_right = ManStereo(disp_info=False, subject=subject, params=p, viewport='right')
    
    sweep = FrameSweep()
    sweep.add_stimulus(stimulus_control)
    sweep.add_stimulus(stimulus_left)
    sweep.add_stimulus(stimulus_right)
    sweep.go()
