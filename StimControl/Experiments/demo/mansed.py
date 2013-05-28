#!/usr/bin/python
# Adjust SED gratings.
#
# Copyright (C) 2010-2011 Huang Xin
#
# See LICENSE.TXT that came with this file.

from __future__ import division
import sys
from StimControl.LightStim.Core import DefaultScreen
from StimControl.LightStim.LightData import dictattr
from StimControl.LightStim.FrameControl import FrameSweep
from StimControl.LightStim.ManSED import ManSED
# Manual Grating experiment parameters, all must be scalars

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
p.tfreqmultiplier = 0.0
# factor to change spatial freq by on left/right
p.sfreqmultiplier = 1.01
# factor to change contrast by on +/-
p.contrastmultiplier = 1.005
# orientation step size to snap to when scrolling mouse wheel (deg)
p.snapDeg = 45.0
p.radius = 2.0
p.maskDiameterDeg = 1.5
p.sfreqCycDeg = 3.0
p.tfreqCycSec = 0.0
p.ori = 0.0

if __name__ == '__main__':
    DefaultScreen(['control','left','right'])
    subject = None
    argv = list(sys.argv)
    if len(argv) >= 2:
        subject = argv[1]
    while subject is None:
        sys.stdout.write('Please input lowercase initials of subject name: ')
        subject = raw_input()

    stimulus_control = ManSED(disp_info=True, subject=subject, params=p, viewport='control')
    stimulus_left = ManSED(disp_info=True, subject=subject, params=p, viewport='left')
    p.ori = 90.0
    stimulus_right = ManSED(disp_info=True, subject=subject, params=p, viewport='right')

    sweep = FrameSweep()
    sweep.add_stimulus(stimulus_control)
    sweep.add_stimulus(stimulus_left)
    sweep.add_stimulus(stimulus_right)
    sweep.go()
