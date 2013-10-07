# Neuron PSTH data.
#
# Copyright (C) 2010-2011 Huang Xin
# 
# See LICENSE.TXT that came with this file.

import logging
import numpy as np
import scipy.ndimage as nd
from PlexSpikeData import PlexSpikeData

class PSTHTuning(PlexSpikeData):
    ORI_MASK = 0xF<<0
    SPF_MASK = 0xF<<4
    PHA_MASK = 0xF<<8
    ONSET_MASK = 1<<12
    MONO_MASK = 3<<12
    MONO_LEFT_MASK = 3<<12 | ORI_MASK
    MONO_RIGHT_MASK = 3<<12 | SPF_MASK
    def __init__(self, *args,**kwargs):
        super(PSTHTuning, self).__init__(*args,**kwargs)
        self.data_type = 'psth_tuning'
        self.param_indices = np.empty(0,dtype=np.int16)
        self.timestamps = np.empty(0)
        self.parameter = None
        self.spike_trains = {}
        self.histogram_data = {}
        
    def renew_data(self):
        self.param_indices = np.empty(0,dtype=np.int16)
        self.timestamps = np.empty(0)
        self.spike_trains = {}
        self.histogram_data = {}
    
    def get_data(self,callback=None):
        self._update_data(callback)
        self._get_psth_data()
        return self.histogram_data
    
    def _update_data(self,callback=None):
        super(PSTHTuning, self)._update_data(callback)
            
        new_triggers = self.pu.GetExtEvents(self.data, event='first_strobe_word')
        if len(new_triggers['value']) == 0:
            new_triggers = self.pu.GetExtEvents(self.data, event='unstrobed_word', online=self.online)
        trigger_values = new_triggers['value']
        
        take_mono = trigger_values & PSTHTuning.MONO_MASK == PSTHTuning.MONO_MASK
        take_mono_left  = trigger_values & PSTHTuning.MONO_LEFT_MASK == PSTHTuning.MONO_LEFT_MASK
        take_mono_right  = trigger_values & PSTHTuning.MONO_RIGHT_MASK == PSTHTuning.MONO_RIGHT_MASK
        
        ori_index = trigger_values & PSTHTuning.ORI_MASK
        ori_index[take_mono] = 0
        spf_index = (trigger_values & PSTHTuning.SPF_MASK)>>4
        spf_index[take_mono] = 0
        pha_index = (trigger_values & PSTHTuning.PHA_MASK)>>8
        pha_index[take_mono] = 0
        
        if np.any(ori_index):
            self.parameter = 'orientation'
        elif np.any(spf_index):
            self.parameter = 'spatial_frequency'
        elif np.any(pha_index):
            self.parameter = 'disparity'
        param_indices = np.array((ori_index + spf_index + pha_index), np.int)
        take_offset = (trigger_values & PSTHTuning.ONSET_MASK) == 0
        param_indices[take_offset] = -1
        param_indices[take_mono_left] = 16
        param_indices[take_mono_right] = 17
        
        # param_index_que typically has values in the range of [-1,17]
        # That's enough to describe the stimuli, isn't it?
        # -1 for stimulus off
        # [0, 15] for tuning stimulus parameters
        # 16 for monocular right stimulus
        # 17 for monocular right stimulus
        self.param_indices = np.append(self.param_indices, param_indices)
        self.timestamps = np.append(self.timestamps, new_triggers['timestamp'])
        
        new_spike_trains = self.pu.GetSpikeTrains(self.data)
        for channel,channel_trains in new_spike_trains.iteritems():
            if channel not in self.spike_trains:
                self.spike_trains[channel] = channel_trains
            else:
                for unit,unit_train in channel_trains.iteritems():
                    if unit not in self.spike_trains[channel]:
                        self.spike_trains[channel][unit] = unit_train
                    else:
                        self.spike_trains[channel][unit] = np.append(self.spike_trains[channel][unit], unit_train)
    
    def _get_psth_data(self):
        logger = logging.getLogger('Experimenter.TimeHistogram')
        # process all on segments before the off segments in the timestamp queue
        off_indices = np.nonzero(self.param_indices == -1)
        while np.any(off_indices[0]):     # have any stimulus on segment
            if self.param_indices[0] < 0: # remove the beginning off segment
                index = self.param_indices[0]
                off_begin = self.timestamps[off_indices[0][0]]
                off_end = self.timestamps[off_indices[0][-1]]
                if off_end > off_begin:
                    logger.info('Processing background activity at duration %.2f:%.2f' %(off_begin, off_end))
                    self._process_psth_data(off_begin, off_end, index)
                on_indices = np.nonzero(self.param_indices >= 0)
                if any(on_indices[0]):
                    self.param_indices = self.param_indices[on_indices[0][0]:]
                    self.timestamps = self.timestamps[on_indices[0][0]:]
                else:
                    self.param_indices = np.empty(0,dtype=np.int16)
                    self.timestamps = np.empty(0)
            else:
                if np.any(self.param_indices[1:off_indices[0][0]] != self.param_indices[:off_indices[0][0]-1]):
                    logger.warning('Bad stimulation trigger: stimulus parameter are not the same between two off segments.')
                on_begin = self.timestamps[0]
                on_end = self.timestamps[off_indices[0][0]-1]
                index = self.param_indices[0]
                if index not in range(18):
                    logger.warning('Bad stimulation trigger: stimulus parameter index exceeded defined range [0,17].')
                if on_end > on_begin and index in range(18):
                    logger.info('Processing psth data for %s index: %d at duration %.2f:%.2f'
                                %(self.parameter,index, on_begin, on_end))
                    self._process_psth_data(on_begin, on_end, index) # psth processing of on segment
                self.param_indices = self.param_indices[off_indices[0][0]:] # remove processed on segment
                self.timestamps = self.timestamps[off_indices[0][0]:]
            off_indices = np.nonzero(self.param_indices == -1)
                
    def _process_psth_data(self,begin,end,param_index):
        duration = 2.0
        binsize = 0.01 #binsize 10 ms
        bins = np.arange(0.,duration,binsize)
        for channel,channel_trains in self.spike_trains.iteritems():
            if channel not in self.histogram_data:
                self.histogram_data[channel] = {}
            for unit,unit_train in channel_trains.iteritems():
                if unit not in self.histogram_data[channel]:
                    self.histogram_data[channel][unit] = {}
                if param_index not in self.histogram_data[channel][unit]:
                    self.histogram_data[channel][unit][param_index] = {}
                    self.histogram_data[channel][unit][param_index]['trials'] = 0
                    self.histogram_data[channel][unit][param_index]['spikes'] = []
                    self.histogram_data[channel][unit][param_index]['means'] = []
                take = ((unit_train >= begin) & (unit_train < begin + duration) & (unit_train< end))
                trial_spikes = unit_train[take] - begin
                trial_mean = np.mean(np.array(np.histogram(trial_spikes, bins=bins)[0],dtype='float') / binsize)
                spikes = np.append(self.histogram_data[channel][unit][param_index]['spikes'], trial_spikes)
                trials = self.histogram_data[channel][unit][param_index]['trials'] + 1
                psth_data = np.array(np.histogram(spikes, bins=bins)[0],dtype='float') / (binsize*trials)
                smooth_psth = nd.gaussian_filter1d(psth_data, sigma=5)
                mean = np.mean(smooth_psth)
                self.histogram_data[channel][unit][param_index]['spikes'] = spikes
                self.histogram_data[channel][unit][param_index]['trials'] = trials
                self.histogram_data[channel][unit][param_index]['psth_data'] = psth_data
                self.histogram_data[channel][unit][param_index]['smooth_psth'] = smooth_psth
                self.histogram_data[channel][unit][param_index]['bins'] = bins
                self.histogram_data[channel][unit][param_index]['mean'] = mean
                self.histogram_data[channel][unit][param_index]['means'].append(trial_mean)
                self.histogram_data[channel][unit][param_index]['std'] = np.std(self.histogram_data[channel][unit][param_index]['means'])
                
class PSTHAverage(PlexSpikeData):
    ONSET_MASK = 1<<12
    def __init__(self, *args,**kwargs):
        super(PSTHAverage, self).__init__(*args,**kwargs)
        self.data_type = 'psth_average'
        self.timestamps = np.empty(0)
        self.onset_timestamps = np.empty(0)
        self.spike_trains = {}
        self.histogram_data = {}
        
    def renew_data(self):
        self.timestamps = np.empty(0)
        self.spike_trains = {}
        self.histogram_data = {}
    
    def get_data(self,callback=None):
        self._update_data(callback)
        self._get_psth_data()
        return self.histogram_data
    
    def _update_data(self,callback=None):
        super(PSTHAverage, self)._update_data(callback)
        new_triggers = self.pu.GetExtEvents(self.data, event='first_strobe_word')
        if len(new_triggers['value']) == 0:
            new_triggers = self.pu.GetExtEvents(self.data, event='unstrobed_word', online=self.online)
        trigger_values = new_triggers['value']
        is_onset_trigger = (trigger_values & PSTHTuning.ONSET_MASK) != 0
        onset_timestamps = new_triggers['timestamp'][is_onset_trigger]
        self.onset_timestamps = np.append(self.onset_timestamps, onset_timestamps)
        self.timestamps = np.append(self.timestamps, new_triggers['timestamp'])
                
        new_spike_trains = self.pu.GetSpikeTrains(self.data)
        for channel,channel_trains in new_spike_trains.iteritems():
            if channel not in self.spike_trains:
                self.spike_trains[channel] = channel_trains
            else:
                for unit,unit_train in channel_trains.iteritems():
                    if unit not in self.spike_trains[channel]:
                        self.spike_trains[channel][unit] = unit_train
                    else:
                        self.spike_trains[channel][unit] = np.append(self.spike_trains[channel][unit], unit_train)
            
    def _get_psth_data(self):
        for channel,channel_trains in self.spike_trains.iteritems():
            if channel not in self.histogram_data:
                self.histogram_data[channel] = {}
            for unit,_unit_train in channel_trains.iteritems():
                if unit not in self.histogram_data[channel]:
                    self.histogram_data[channel][unit] = {}
                    self.histogram_data[channel][unit]['trials'] = 0
                    self.histogram_data[channel][unit]['spikes'] = []
                    self.histogram_data[channel][unit]['means'] = []
                self._process_unit(channel,unit)
                    
    def _process_unit(self,channel,unit):
        duration = 0.152
        binsize = 0.001 #binsize 1 ms
        bins = np.arange(0.,duration,binsize)
        self.histogram_data[channel][unit]['bins'] = bins[:-1]*1000
        stimulus_on = self.onset_timestamps
        unit_train = self.spike_trains[channel][unit]
        spikes = []
        trials = 0
        for begin in stimulus_on:
            take = ((unit_train >= begin) & (unit_train < begin + duration))
            trial_spikes = unit_train[take] - begin
            spikes = np.append(spikes, trial_spikes)
            trials = trials + 1
        print trials
        psth_data = np.array(np.histogram(spikes, bins=bins)[0],dtype='float') / (binsize*trials)
        smoothed_psth = nd.gaussian_filter1d(psth_data, sigma=10)
        maxima_indices = (np.diff(np.sign(np.diff(smoothed_psth))) < 0).nonzero()[0] + 1
        minima_indices = (np.diff(np.sign(np.diff(smoothed_psth))) > 0).nonzero()[0] + 1
        maxima = smoothed_psth[maxima_indices]
        time = self.histogram_data[channel][unit]['bins']
        try:
            peak_time = time[maxima_indices[maxima.argmax()]]
        except:
            peak_time = None
        
        self.histogram_data[channel][unit]['spikes'] = spikes
        self.histogram_data[channel][unit]['trials'] = trials
        self.histogram_data[channel][unit]['psth_data'] = psth_data
        self.histogram_data[channel][unit]['smoothed_psth'] = smoothed_psth
        self.histogram_data[channel][unit]['maxima'] = smoothed_psth[maxima_indices]
        self.histogram_data[channel][unit]['minima'] = smoothed_psth[minima_indices]
        self.histogram_data[channel][unit]['maxima_indices'] = maxima_indices
        self.histogram_data[channel][unit]['minima_indices'] = minima_indices
        self.histogram_data[channel][unit]['peak_time'] = peak_time
            