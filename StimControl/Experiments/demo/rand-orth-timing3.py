# Generate arbitrary onset and offset timing gratings.
#
# Copyright (C) 2010-2011 Huang Xin
#
# See LICENSE.TXT that came with this file.

from __future__ import division
import sys
import random
import numpy as np
from StimControl.LightStim.SweepSeque import TimingSeque
from StimControl.LightStim.LightData import dictattr
from StimControl.LightStim.FrameControl import FrameSweep
from StimControl.LightStim.Grating import TimingController,RandPhaseController
from StimControl.LightStim.SweepController import SweepSequeStimulusController
from StimControl.LightStim.SEDGrating import SEDGrating
from StimControl.LightStim.Target import Fixation
from StimControl.LightStim.Core import DefaultScreen

class RandOriController(SweepSequeStimulusController):
    def __init__(self,*args,**kwargs):
        super(RandOriController, self).__init__(*args,**kwargs)
        self.gp = self.stimulus.gp
        self.ori = np.linspace(0.0, 360.0, 16, endpoint=False)
        self.index = 0
    def during_go_eval(self):
        self.index = self.index + 1
        random.seed(self.index)
        self.gp.orientation = random.choice(self.ori)

class OrthOriController(RandOriController):
    def __init__(self,*args,**kwargs):
        super(OrthOriController, self).__init__(*args,**kwargs)
    def during_go_eval(self):
        super(OrthOriController, self).during_go_eval()
        self.gp.orientation = self.gp.orientation + 90
        
class TimingSetGrating(SEDGrating):
    def register_controllers(self):
        super(TimingSetGrating, self).register_controllers()
        self.logger.info('Register TimingController.')
        self.controllers.append(TimingController(self))
        self.controllers.append(OrthOriController(self))
        
class RandPhaseTimingSetGrating(SEDGrating):
    def register_controllers(self):
        super(RandPhaseTimingSetGrating, self).register_controllers()
        self.logger.info('Register TimingController.')
        self.controllers.append(TimingController(self))
        self.controllers.append(RandPhaseController(self))
        self.controllers.append(OrthOriController(self))
        
class RandOriTimingSetGrating(SEDGrating):
    def register_controllers(self):
        super(RandOriTimingSetGrating, self).register_controllers()
        self.logger.info('Register TimingController.')
        self.controllers.append(TimingController(self))
        self.controllers.append(RandPhaseController(self))
        self.controllers.append(RandOriController(self))

class OrthOriTimingSetGrating(SEDGrating):
    def register_controllers(self):
        super(OrthOriTimingSetGrating, self).register_controllers()
        self.logger.info('Register TimingController.')
        self.controllers.append(TimingController(self))
        self.controllers.append(RandPhaseController(self))
        self.controllers.append(OrthOriController(self))
        
DefaultScreen(['left','right'], bgcolor=(0.5,0.5,0.5))

p_left = dictattr()
p_left.ml = 0.5
p_left.tfreqCycSec = 0.0
p_left.bgbrightness = 0.5
p_left.contrast = 1
p_left.phase0 = 0

p_right = dictattr()
p_right.ml = 0.5
p_right.tfreqCycSec = 0.0
p_right.bgbrightness = 0.5
p_right.contrast = 1
p_right.phase0 = 0

argv = list(sys.argv)

subject = None
if len(argv) >= 2:
    subject = argv[1]
while subject is None:
    sys.stdout.write('Please input lowercase initials of subject name: ')
    subject = raw_input()
    
interval = None
if len(argv) >= 3:
    interval = int(argv[2]) / 1000
while interval is None:
    sys.stdout.write('Please input stimulus interval in miliseconds: ')
    interval = int(raw_input()) / 1000
    
stim_interval = interval

pre_left = 0.0 if stim_interval > 0 else abs(stim_interval)
pre_right = 0.0 if stim_interval <= 0 else stim_interval

repeats = 1000
rand_phase = True

cycle_left = dictattr(duration=0.132, pre=pre_left, stimulus=0.016)
cycle_right = dictattr(duration=0.132, pre=pre_right, stimulus=0.016)
block_left = dictattr(repeat=repeats, cycle=cycle_left, interval=0.0)
block_right = dictattr(repeat=repeats, cycle=cycle_right, interval=0.0)
sequence_left = TimingSeque(repeat=1, block=block_left, shuffle=True)
sequence_right = TimingSeque(repeat=1, block=block_right, shuffle=True)

fp = dictattr()
fp.color = (1.0, 0.0, 0.0, 1.0)
fp.width = 0.25

fixation_left = Fixation(viewport='left', subject=subject, params=fp)
fixation_right = Fixation(viewport='right', subject=subject, params=fp)

for i in range(6):
    sweep = FrameSweep()
    grating_left = RandOriTimingSetGrating(viewport='left', params=p_left, subject=subject, sweepseq=sequence_left)
    grating_right = OrthOriTimingSetGrating(viewport='right', params=p_right, subject=subject, sweepseq=sequence_right)
    sweep.add_stimulus(grating_left)
    sweep.add_stimulus(grating_right)
    sweep.add_stimulus(fixation_left)
    sweep.add_stimulus(fixation_right)
    sweep.go(prestim=5.0,poststim=5.0,duration=(150.0,'seconds'))
