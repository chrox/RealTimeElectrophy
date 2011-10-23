# V1 neuron adaptive response properties.
# Spike delay and instant firing rate of V1 neuron in response to two types of stimuli
# namely continuous stimulus and alternating stimulus are investigated in this experiment.
# We assume that when one eye is exposed to an continuous stimulus while the stimulation of
# the other eye is absent the stimulated eye will be adaptive.
#
# Copyright (C) 2010-2011 Huang Xin
#
#
# Distributed under the terms of the GNU Lesser General Public License
# (LGPL). See LICENSE.TXT that came with this file.

import numpy as np
from bisect import bisect_right
from collections import deque
from guppy import hpy; h = hpy()
from Plexon.PlexClient import PlexClient
from Plexon.PlexUtil import PlexUtil

# TODO # move these definition to stimulus space
ONSET_BIT = 0
OFFSET_BIT = 1
LEFT_STIM_BIT = 2
RIGHT_STIM_BIT = 3
ALT_STIM_BIT = 4
CON_STIM_BIT = 5

LATENCY_BOUNDARY = 0.2
INSTANT_RATE_SPAN = 0.1
RATE_BOUNDARY = 10.0
class TimeTorque(deque):
    """
    deque for event timestamp with timestamp tolerance.
    Occationally several sync events are sent successively in one stimulus onset.
    Tiny differences among these timestamps are torlerated in TimeTorque.
    """
    TIMESTAMP_TOLERANCE = 0.002
    def __contains__(self, time_stamp):
        for timestamp in self:
            if abs(timestamp-time_stamp) < TimeTorque.TIMESTAMP_TOLERANCE:
                return True
        return False

class AdaptiveResponse(object):
    def __init__(self):
        self.pc = PlexClient()
        self.pc.InitClient()

        self.onset_que = deque()
        self.offset_que = deque()
        self.left_stim_que = deque()
        self.right_stim_que = deque()
        self.alt_stim_que = deque()
        self.con_stim_que = deque()
        # and a dict for spike trains
        self.spike_trains = {}
        self.results = {}

    def close(self):
        self.pc.CloseClient()

    def _process_spike_response(self, channel, unit, lefty, continuity, response_type, onset_timestamp, spike_train):
        if channel not in self.results:
            self.results[channel] = {}
        if unit not in self.results[channel]:
            self.results[channel][unit] = {}
        if lefty not in self.results[channel][unit]:
            self.results[channel][unit][lefty] = {}
        if continuity not in self.results[channel][unit][lefty]:
            self.results[channel][unit][lefty][continuity] = {}
        if response_type not in self.results[channel][unit][lefty][continuity]:
            self.results[channel][unit][lefty][continuity][response_type] = []

        i = bisect_right(spike_train, onset_timestamp)
        if i != len(spike_train):
            if response_type is 'latency':
                latency = spike_train[i] - onset_timestamp
                if latency < LATENCY_BOUNDARY:
                    return latency
                return None
            if response_type is 'rate':
                j = bisect_right(spike_train, spike_train[i]+INSTANT_RATE_SPAN)
                if j != len(spike_train):
                    rate = (j - i)/INSTANT_RATE_SPAN
                    if rate > RATE_BOUNDARY:
                        return rate
                    return None
                return None
        return None

    def _update_data(self):
        data = self.pc.GetTimeStampArrays()
        self.onset_que.extend(PlexUtil.GetExtEvents(data, event='unstrobed_bit', bit=ONSET_BIT))
        self.offset_que.extend(PlexUtil.GetExtEvents(data, event='unstrobed_bit', bit=OFFSET_BIT))
        self.left_stim_que.extend(PlexUtil.GetExtEvents(data, event='unstrobed_bit', bit=LEFT_STIM_BIT))
        self.right_stim_que.extend(PlexUtil.GetExtEvents(data, event='unstrobed_bit', bit=RIGHT_STIM_BIT))
        self.alt_stim_que.extend(PlexUtil.GetExtEvents(data, event='unstrobed_bit', bit=ALT_STIM_BIT))
        self.con_stim_que.extend(PlexUtil.GetExtEvents(data, event='unstrobed_bit', bit=CON_STIM_BIT))
        # plexon should make sure that unstrobed bits will all arrive together in one GetTimeStampArrays call.
        # If this assert fails things will be much more complicated.
        if not len(self.onset_que):
            print "no configured stimulation."
            return
        if len(self.onset_que) != len(self.left_stim_que) + len(self.right_stim_que) or \
            len(self.onset_que) == len(self.alt_stim_que) + len(self.con_stim_que) or \
            (self.onset_que[0] in self.left_stim_que) == (self.onset_que[0] in self.right_stim_que) or \
            (self.onset_que[0] in self.alt_stim_que) != (self.onset_que[0] in self.con_stim_que):
            print "wrong stimulus configuration!"
            return

        new_spike_trains = PlexUtil.GetSpikeTrains(data)
        for channel,channel_trains in new_spike_trains.iteritems():
            if channel not in self.spike_trains:
                self.spike_trains[channel] = channel_trains
            else:
                for unit,unit_train in channel_trains.iteritems():
                    if unit not in self.spike_trains[channel]:
                        self.spike_trains[channel][unit] = unit_train
                    else:
                        self.spike_trains[channel][unit] = np.append(self.spike_trains[channel][unit], unit_train)

        while len(self.onset_que) > 1:
            if self.onset_que[0] in self.left_stim_que:
                lefty = 'left'
            else:
                lefty = 'right'
            if self.onset_que[0] in self.con_stim_que:
                continuity = 'continuous'
            else:
                continuity = 'alternating'
            for channel,channel_trains in self.spike_trains.iteritems():
                for unit,unit_train in channel_trains.iteritems():
                    latency = self._process_spike_response(channel, unit, lefty, continuity, 'latency', self.onset_que[0], unit_train)
                    rate = self._process_spike_response(channel, unit, lefty, continuity, 'rate', self.onset_que[0], unit_train)
                    if latency and rate:
                        self.results[channel][unit][lefty][continuity]['latency'].append(latency)
                        self.results[channel][unit][lefty][continuity]['rate'].append(rate)
                    self.onset_que.popleft()
                    if lefty is 'left':
                        self.left_stim_que.popleft()
                    else:
                        self.right_stim_que.popleft()
                    if continuity is 'continuous':
                        self.con_stim_que.popleft()
                    else:
                        self.alt_stim_que.popleft()

    def _analysis(self, data):
        results = {}
        for channel,channel_data in data.iteritems():
            results[channel] = {}
            for unit,unit_data in channel_data.iteritems():
                results[channel][unit] = {}
                for response_type in ('latency','rate'):
                    means = [np.mean(unit_data[lefty][continuity][response_type])\
                                for continuity in ('continuous','alternating')\
                                    for lefty in ('left','right')]
                    stds = [np.std(unit_data[lefty][continuity][response_type])\
                                for continuity in ('continuous','alternating')\
                                    for lefty in ('left','right')]
                    results[channel][unit][response_type] = np.nan_to_num(means), np.nan_to_num(stds)
        return results

    def get_results(self):
        self._update_data()
        return self._analysis(self.results)

    def get_demo_results(self):
        demo_data = {'1':{
                        'a':{
                             'left':{
                                     'continuous':{
                                                   'latency':[56.000,61.000,73.000,59.000],
                                                   'rate':[23.5294117647,35.2941176471,35.2941176471,47.0588235294]},
                                     'alternating':{
                                                    'latency':[49.000,78.000,53.000,47.000],
                                                   'rate':[23.5294117647,47.0588235294,47.0588235294,47.0588235294]}
                                     },
                              'right':{
                                     'continuous':{
                                                   'latency':[89.000,70.000,82.000,72.000],
                                                   'rate':[35.2941176471,23.5294117647,47.0588235294,23.5294117647]},
                                     'alternating':{
                                                    'latency':[60.000,63.000,63.000,60.000],
                                                   'rate':[23.5294117647,39.2941176471,35.2941176471,35.2941176471]}
                                     }
                            },
                        'b':{
                             'left':{
                                     'continuous':{
                                                   'latency':[54.000,61.000,73.000,55.000],
                                                   'rate':[29.5294117647,35.2941176471,35.2941176471,49.0588235294]},
                                     'alternating':{
                                                    'latency':[43.000,78.000,59.000,47.000],
                                                   'rate':[29.5294117647,44.0588235294,49.0588235294,44.0588235294]}
                                     },
                              'right':{
                                     'continuous':{
                                                   'latency':[89.000,75.000,80.000,72.000],
                                                   'rate':[35.2941176471,23.5294117647,47.0588235294,23.5294117647]},
                                     'alternating':{
                                                    'latency':[60.000,63.000,63.000,60.000],
                                                   'rate':[25.5294117647,35.2941176471,39.2941176471,39.2941176471]}
                                     }
                            }
                         }
                    }

        return self._analysis(demo_data)