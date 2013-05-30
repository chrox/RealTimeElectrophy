#!/usr/bin/python
# Display movie on left and right viewport with arbitary inter-viewport delay with pyffmpeg.
#
# Copyright (C) 2010-2013 Huang Xin
#
# See LICENSE.TXT that came with this file.

from __future__ import division
import sys
import random
import pygame
import numpy as np

import threading
from threading import Thread 
from multiprocessing import Process

import time
import alsaaudio
from pyffmpeg import FFMpegReader, PixelFormats

from StimControl.LightStim.Core import DefaultScreen
from StimControl.LightStim.LightData import dictattr
from StimControl.LightStim.SweepSeque import TimingSeque
from StimControl.LightStim.FrameControl import FrameSweep
from StimControl.LightStim.SweepController import SweepSequeStimulusController
from StimControl.LightStim.Movie import BufferedTextureObject, TimingSetMovie
        
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

class AlsaSoundLazyPlayer:
    def __init__(self,rate=44100,channels=2,fps=25):
        self._rate=rate
        self._channels=channels
        self._d = alsaaudio.PCM()
        self._d.setchannels(channels)
        self._d.setformat(alsaaudio.PCM_FORMAT_S16_LE)
        self._d.setperiodsize(int((rate*channels)//fps))
        self._d.setrate(rate)
    def push_nowait(self,stamped_buffer):
        self._d.write(stamped_buffer[0].data)

class Player(threading.Thread):
    def run(self):
        global mp
        mp.run()
    def stop(self):
        global mp
        mp.close()
        
def render_to_buffer(frame):
    buffer = np.frombuffer(texture_object.buffer_data, 'B')
    frame = np.flipud(frame)
    frame = frame.reshape((1, -1))
    buffer[:] = frame
        
TS_VIDEO_RGB24={ 'video1':(0, -1, {'pixel_format':PixelFormats.PIX_FMT_RGB24}), 'audio1':(1,-1,{})}
## create the reader object
mp = FFMpegReader()
## open an audio-video file
mp.open(filename,TS_VIDEO_RGB24 )
tracks = mp.get_tracks()
width, height = tracks[0].get_size()

pygame_surface = pygame.surface.Surface((width,height))

texture_object = BufferedTextureObject(size=width*height*3, dimensions=2)

ap = AlsaSoundLazyPlayer(tracks[1].get_samplerate(),tracks[1].get_channels(),tracks[0].get_fps())

tracks[1].set_observer(ap.push_nowait)
tracks[0].set_observer(render_to_buffer)

p_left = dictattr()
p_left.layout = layout
p_left.bgbrightness = 0.0
p_left.contrast = 1.0

p_right = dictattr()
p_right.layout = layout
p_right.bgbrightness = 0.0
p_right.contrast = 0.5

cycle_left = dictattr(duration=0.016, pre=pre_left, stimulus=0.016)
cycle_right = dictattr(duration=0.016, pre=pre_right, stimulus=0.016)
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
    player = Player()
    sweep.add_quit_callback(player.stop)
    player.start()
    sweep.go()

