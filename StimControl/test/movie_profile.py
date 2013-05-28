# Display movie on left and right viewport with arbitary inter-viewport delay.
#
# Copyright (C) 2010-2013 Huang Xin
#
# See LICENSE.TXT that came with this file.

from __future__ import division
import sys
import random
import pygame
import numpy as np

from StimControl.LightStim.Core import DefaultScreen
from StimControl.LightStim.LightData import dictattr
from StimControl.LightStim.SweepSeque import TimingSeque
from StimControl.LightStim.FrameControl import FrameSweep
from StimControl.LightStim.SweepController import SweepSequeStimulusController
from StimControl.LightStim.Movie import SurfaceTextureObject, TimingSetMovie
        
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
if layout not in ("LR", "TB"):
    layout = "2D"

filename = argv[-1]
movie = pygame.movie.Movie(filename)
width, height = movie.get_size()
pygame_surface = pygame.surface.Surface((width,height))
movie.set_display(pygame_surface)

texture_object = SurfaceTextureObject(dimensions=2)

p_left = dictattr()
p_left.layout = layout
p_left.bgbrightness = 0.0
p_left.contrast = 1.0

p_right = dictattr()
p_right.layout = layout
p_right.bgbrightness = 0.0
p_right.contrast = 0.5

cycle_left = dictattr(duration=0.04, pre=pre_left, stimulus=0.016)
cycle_right = dictattr(duration=0.04, pre=pre_right, stimulus=0.016)
block_left = dictattr(repeat=None, cycle=cycle_left, interval=0.0)
block_right = dictattr(repeat=None, cycle=cycle_right, interval=0.0)
sequence_left = TimingSeque(repeat=1, block=block_left, shuffle=True)
sequence_right = TimingSeque(repeat=1, block=block_right, shuffle=True)

if __name__ == '__main__':
    sweep = FrameSweep()
    movie_left = TimingSetMovie(viewport='left', 
                                surface=pygame_surface, texture_obj=texture_object,
                                params=p_left, subject=subject, sweepseq=sequence_left)
    movie_right = TimingSetMovie(viewport='right',
                                 surface=pygame_surface, texture_obj=texture_object,
                                 params=p_right, subject=subject, sweepseq=sequence_right)
    sweep.add_stimulus(movie_left)
    sweep.add_stimulus(movie_right)
    sweep.add_quit_callback(movie.stop)
    
    movie.play()
    #sweep.go(prestim=0.5,poststim=0.5)
    import cProfile,pstats
    cProfile.run('sweep.go()','movie_profile')
    p = pstats.Stats('movie_profile')
    p.sort_stats('cumulative')
    p.print_stats()
