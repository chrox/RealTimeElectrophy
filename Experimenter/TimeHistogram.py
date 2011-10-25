# Neuron PSTH data.
#
# Copyright (C) 2010-2011 Huang Xin
# 
#
# Distributed under the terms of the GNU Lesser General Public License
# (LGPL). See LICENSE.TXT that came with this file.
import numpy as np
from Plexon.PlexClient import PlexClient
from Plexon.PlexUtil import PlexUtil

class PSTH:
    def __init__(self):
        self.pc = PlexClient()
        self.pc.InitClient()
        self.pu = PlexUtil()

        # and a dict for spike trains
        self.spike_trains = {}
        self.histogram_data = {}

    def __close__(self):
        self.pc.CloseClient()
        
    def get_data(self):
        self._update_data()
        self._get_psth_data()
        return self.histogram_data
    
    def _update_data(self):
        data = self.pc.GetTimeStampArrays()
        new_spike_trains = self.pu.GetSpikeTrains(data)
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
        history = 2.0
        baseline_duration = 0.32
        binsize = 0.01 #binsize 10 ms
        bins = np.arange(0.,baseline_duration,binsize)
        trials = int(history // baseline_duration)
        spike_times_trials = {}
        for channel,channel_trains in self.spike_trains.iteritems():
            if channel not in self.histogram_data:
                self.histogram_data[channel] = {}
            for unit,unit_train in channel_trains.iteritems():
                for trial in range(trials):
                    take = ((unit_train >= unit_train[-1]-baseline_duration*(trial+1)) & (unit_train<unit_train[-1]-baseline_duration*trial))
                    spike_times_trials[trial] = unit_train[take] - (unit_train[-1]-baseline_duration*(trial+1))
                spike_times = np.array([spike for spike_train in spike_times_trials.itervalues() for spike in spike_train])
                spike_times.sort()
                #psth = np.array(np.histogram(spike_times, bins=bins)[0],dtype='float')
                hist_data = np.array(np.histogram(spike_times, bins=bins)[0],dtype='float') / (trials*binsize)
                self.histogram_data[channel][unit] = (spike_times, hist_data, bins)
        #smooth_psth = nd.gaussian_filter1d(psth, kernel_width)
        #return pylab.mean(smooth_psth), pylab.std(smooth_psth)  