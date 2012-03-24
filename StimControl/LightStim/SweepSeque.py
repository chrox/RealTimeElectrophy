# SweepSeque is another frame-by-frame stimulus controller.
#
# Copyright (C) 2010-2011 Huang Xin
#
# See LICENSE.TXT that came with this file.

from __future__ import division
import numpy as np
import itertools
import random
import logging
from .. import LightStim

class SweepSeque(object):
    def __init__(self):
        assumed_refresh_rate = LightStim.config.assume_viewport_refresh_rate()
        self.sweep_duration = 1/assumed_refresh_rate

class TimingSeque(SweepSeque):
    """ stimulus sequence with arbitrary onset and offset timing."""
    def __init__(self, repeat, block, shuffle):
        super(TimingSeque, self).__init__()
        logger = logging.getLogger('LightStim.SweepSeque')
        self.block = block
        self.cycle = self.block.cycle
        
        pre_sweep_counts = np.round(self.cycle.pre / self.sweep_duration)
        stim_sweep_counts = np.round(self.cycle.stimulus / self.sweep_duration)
        post_sweep_counts = np.round(self.cycle.duration / self.sweep_duration) - pre_sweep_counts - stim_sweep_counts
        
        logger.info( "Actual sweep duration(sec) :\npre-stimulus :  %s\nstimulus :      %s\npost-stimulus : %s" \
                     %('\t%.4f' %(pre_sweep_counts*self.sweep_duration),
                       '\t%.4f' %(stim_sweep_counts*self.sweep_duration),
                       '\t%.4f' %(post_sweep_counts*self.sweep_duration)))
        if np.any(post_sweep_counts < 0):
            raise RuntimeError('Wrong settings of sweep timing. It seems that sweep duration is too short.')
        pre_sweep_counts_rational = self.cycle.pre / self.sweep_duration
        warned_sweep = (pre_sweep_counts - pre_sweep_counts_rational) > 0.25
        if warned_sweep:
            warned_duration = self.cycle.pre
            actual_duration = pre_sweep_counts * self.sweep_duration
            logger.warning("Sweep delays(sec) %s is not supported by current monitor refresh rate. "
                           "They will be set to nearest supported value: %s." \
                           %(' %.4f' %warned_duration, ' %.4f' %actual_duration))
        
        interval = [0]*int(self.block.interval // self.sweep_duration)
        cycles = [[0]*pre_sweep_counts+[1]*stim_sweep_counts+[0]*post_sweep_counts] * repeat
        random.shuffle(cycles)
        self.sequence_list = [cycle * self.block.repeat + interval for cycle in cycles]
        #self.sequence = itertools.chain.from_iterable(self.sequence_list)

class RandParam(SweepSeque):
    """ base class for generating random parameter sequence from input """
    def __init__(self, repeat, frame_duration, blank_duration, *args):
        super(RandParam, self).__init__()
        frame_sweeps = int(round(frame_duration / self.sweep_duration))
        blank_sweeps = int(round(blank_duration / self.sweep_duration))
        blank_sweep = (float('nan'),float('nan'),float('nan')) # will be checked in paramseque controller.
        params = itertools.product(*args)
        param_sequence = np.random.permutation(list(params) * repeat)
        self.sequence_list = [[param]*frame_sweeps + [blank_sweep]*blank_sweeps for param in param_sequence]
        
        logger = logging.getLogger('LightStim.SweepSeque')
        logger.info( "Actual frame duration: %.4f sec." %(frame_sweeps*self.sweep_duration))
        frame_sweeps_rational = frame_duration / self.sweep_duration
        if abs(frame_sweeps-frame_sweeps_rational) > 0.25:
            logger.warning("Frame duration %.4fs are not support by current monitor refresh rate. "
                           "It will be set to nearest supported duration: %.4fs." \
                           %(frame_sweeps_rational*self.sweep_duration, frame_sweeps*self.sweep_duration))
                           
class ParamSeque(RandParam):
    """ stimulus sequence of random orientation and spatial frequency parameters."""
    def __init__(self, repeat, frame_duration, blank_duration, orientation=[None], spatial_freq=[None], phase_at_t0=[None]):
        super(ParamSeque, self).__init__(repeat, frame_duration, blank_duration, orientation, spatial_freq, phase_at_t0)

class SparseNoiseSeque(RandParam):
    """ stimulus sequence of sparse noise with bar stimulus display in random position and of random brightness. """
    def __init__(self, repeat, x_index, y_index, contrast, frame_duration, blank_duration):
        super(SparseNoiseSeque, self).__init__(repeat, frame_duration, blank_duration, x_index, y_index , contrast)


