# SweepSeque is another frame-by-frame stimulus controller.
#
# Copyright (C) 2010-2011 Huang Xin
# 
#
# Distributed under the terms of the GNU Lesser General Public License
# (LGPL). See LICENSE.TXT that came with this file.
from __future__ import division
import numpy as np
import itertools
import numpy.random

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
    def __init__(self, sweep_duration=1/120.0):
        self.sweep_duration = sweep_duration
        
    def update_sweep_duration(self, sweep_duration):
        pass
    def next(self):
        raise RuntimeError("%s: Definition of next() in abstract base class SweepSeque must be overriden."%(str(self),))
    def last(self):
        raise RuntimeError("%s: Definition of last() in abstract base class SweepSeque must be overriden."%(str(self),))

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
        numpy.random.shuffle(cycles)
        sweep_sequence = [cycle * self.episode.repeat + interval for cycle in cycles]
        self.sequence = itertools.chain.from_iterable(sweep_sequence)
        self._last = None
    def next(self):
        try:
            next = self.sequence.next()
            self._last = next
            return next
        except StopIteration:
            self._last = None
            return None
    
    def last(self):
        return self._last
        
class ParamSeque(SweepSeque):
    """ stimulus sequence of random orientation and spatial frequency parameters."""
    def __init__(self, repeat, orientation, spatial_freq, frame_duration, interval):
        super(ParamSeque, self).__init__()
        nsweep = int(frame_duration // self.sweep_duration)
        params = itertools.product(orientation, spatial_freq)
        param_sequence = np.random.permutation(list(params) * repeat)
        sweep_sequence = [[param] * nsweep for param in param_sequence]
        self.sequence = itertools.chain.from_iterable(sweep_sequence)
        
    def next(self):
        try:
            next = self.sequence.next()
            self._last = next
            return self._last
        except StopIteration:
            self._last = (None,None)
            return self._last
    
    def last(self):
        return self._last
        
        
        
        
        
        
        