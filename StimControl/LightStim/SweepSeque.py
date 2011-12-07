# SweepSeque is another frame-by-frame stimulus controller.
#
# Copyright (C) 2010-2011 Huang Xin
#
# See LICENSE.TXT that came with this file.

from __future__ import division
import numpy as np
import itertools
import random
from .. import LightStim

class dictattr(dict):
    """ Dictionary with attribute access"""
    def __init__(self, *args, **kwargs):
        super(dictattr, self).__init__(*args, **kwargs)
        for k, v in kwargs.iteritems():
            self.__setitem__(k, v) # call our own __setitem__ so we get keys as attribs even on kwarg init
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError, '%r object has no attribute %r' % ('dictattr', key)
    def __setattr__(self, key, val):
        self[key] = val
    def __setitem__(self, key, val):
        super(dictattr, self).__setitem__(key, val)
        if key.__class__ == str and not key[0].isdigit(): # key isn't a number or a string starting with a number
            key = key.replace(' ', '_') # get rid of any spaces
            self.__dict__[key] = val # make the key show up as an attrib upon dir()

class SweepSeque(object):
    def __init__(self):
        assumed_refresh_rate = LightStim.config.assume_viewport_refresh_rate()
        self.sweep_duration = 1/assumed_refresh_rate

class TimingSeque(SweepSeque):
    """ stimulus sequence with arbitrary onset and offset timing."""
    def __init__(self, repeat, episode, shuffle):
        super(TimingSeque, self).__init__()
        self.episode = episode
        self.cycle = self.episode.cycle
        
        pre_sweep_counts = (self.cycle.pre + self.cycle.stimulus - self.cycle.stimulus) // self.sweep_duration
        stim_sweep_counts = (self.cycle.stimulus + self.cycle.pre - self.cycle.pre) // self.sweep_duration
        post_sweep_counts = (self.cycle.duration // self.sweep_duration) - pre_sweep_counts - stim_sweep_counts
        
        interval = [0]*int(self.episode.interval // self.sweep_duration)
        cycles = [[0]*pre_sweep_counts[i]+[1]*stim_sweep_counts[i]+[0]*post_sweep_counts[i] for i in range(len(stim_sweep_counts))] * repeat
        random.shuffle(cycles)
        self.sequence_list = [cycle * self.episode.repeat + interval for cycle in cycles]
        #self.sequence = itertools.chain.from_iterable(self.sequence_list)

class RandParam(SweepSeque):
    """ base class for generating random parameter sequence from input """
    def __init__(self, repeat, frame_duration, blank_duration, *args):
        super(RandParam, self).__init__()
        frame_sweeps = int(frame_duration // self.sweep_duration)
        blank_sweeps = int(blank_duration // self.sweep_duration)
        blank_sweep = (float('nan'),float('nan'),float('nan')) # will be checked in paramseque controller.
        params = itertools.product(*args)
        param_sequence = np.random.permutation(list(params) * repeat)
        self.sequence_list = [[param]*frame_sweeps + [blank_sweep]*blank_sweeps for param in param_sequence]

class ParamSeque(RandParam):
    """ stimulus sequence of random orientation and spatial frequency parameters."""
    def __init__(self, repeat, orientation, spatial_freq, phase_at_t0, frame_duration, blank_duration):
        super(ParamSeque, self).__init__(repeat, frame_duration, blank_duration, orientation, spatial_freq, phase_at_t0)

class SparseNoiseSeque(RandParam):
    """ stimulus sequence of sparse noise with bar stimulus display in random position and of random brightness. """
    def __init__(self, repeat, x_index, y_index, contrast, frame_duration, blank_duration):
        super(SparseNoiseSeque, self).__init__(repeat, frame_duration, blank_duration, x_index, y_index , contrast)


