#!/usr/bin/python
# Display movie on left and right viewport with arbitary inter-viewport delay with pyffmpeg.
#
# Copyright (C) 2010-2013 Huang Xin
#
# See LICENSE.TXT that came with this file.

from __future__ import division
import os
import sys
import random
import pygame
import numpy as np
import multiprocessing.sharedctypes

from StimControl.LightStim.Core import DefaultScreen
from StimControl.LightStim.LightData import dictattr
from StimControl.LightStim.SweepSeque import TimingSeque
from StimControl.LightStim.FrameControl import FrameSweep
from StimControl.LightStim.SweepController import SweepSequeStimulusController
from StimControl.LightStim.Movie import BufferedTextureObject, TimingSetMovie, MoviePlayer
        
DefaultScreen(['left','right'], bgcolor=(0.0,0.0,0.0))

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

layout = None
if len(argv) >= 4:
    layout = argv[3]
if layout not in ("LR","RL","TB","BT"):
    layout = "2D"
    
try:
    seek = int(argv[4])
except:
    seek = None

p_left = dictattr()
p_left.layout = layout
p_left.bgbrightness = 0.0
p_left.contrast = 1.0

p_right = dictattr()
p_right.layout = layout
p_right.bgbrightness = 0.0
p_right.contrast = 1.0

cycle_left = dictattr(duration=0.016, pre=pre_left, stimulus=0.016)
cycle_right = dictattr(duration=0.016, pre=pre_right, stimulus=0.016)
block_left = dictattr(repeat=None, cycle=cycle_left, interval=0.0)
block_right = dictattr(repeat=None, cycle=cycle_right, interval=0.0)
sequence_left = TimingSeque(repeat=1, block=block_left, shuffle=True)
sequence_right = TimingSeque(repeat=1, block=block_right, shuffle=True)

if __name__ == '__main__':
    player = MoviePlayer(argv[-1])
    width, height = player.get_size()
    buffer_data = multiprocessing.sharedctypes.RawArray('B', width*height*3)
    player.set_buffer(buffer_data)
    
    sweep = FrameSweep()
    pygame_surface = pygame.surface.Surface((width,height))
    movie_left = TimingSetMovie(viewport='left', 
                                surface=pygame_surface,
                                texture_obj=BufferedTextureObject(buffer_data, dimensions=2),
                                params=p_left, subject=subject, sweepseq=sequence_left)
    movie_right = TimingSetMovie(viewport='right',
                                 surface=pygame_surface,
                                 texture_obj=BufferedTextureObject(buffer_data, dimensions=2),
                                 params=p_right, subject=subject, sweepseq=sequence_right)
    sweep.add_stimulus(movie_left)
    sweep.add_stimulus(movie_right)
    sweep.add_quit_callback(player.stop)
    player.seek(seek)
    player.start()
    sweep.go()
