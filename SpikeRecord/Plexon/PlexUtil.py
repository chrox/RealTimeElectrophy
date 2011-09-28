#!/usr/bin/python
#coding:utf-8

###########################################################
### Utilities for Plexon data collection
### Written by Huangxin
###########################################################
from operator import add
import numpy as np
import Plexon

class PlexUtil(object):
    """
    Utilities for data collection
    """
    def __init__(self):
        self.last_word = None
        self.last_timestamp = None
        
    def GetSpikesInfo(self,data):
        """
        GetSpikesInfo(data) -> info

        Return spike units collected in this period of time.
        Parameters
        ----------
        data: dict 
            {'type', 'channel', 'unit', 'timestamp'} dictionary from the return value of PlexClient.GetTimeStampArray().

        Returns
        info: list of units for every spikes occurring channels
            [(channel, units)]
        """
        sorted_spikes = (data['type'] == Plexon.PL_SingleWFType) & (data['unit'] > 0)
        info = []
        for channel in np.unique(data['channel'][sorted_spikes]):
            channel_units = map(chr, np.unique(data['unit'][sorted_spikes & (data['channel'] == channel)]) + (ord('a')-1))
            info.append((channel, channel_units))
        return info
        
    def GetSpikeTrains(self,data):
        spike_trains = {}
        sorted_spikes = (data['type'] == Plexon.PL_SingleWFType) & (data['unit'] > 0)
        for channel in np.unique(data['channel'][sorted_spikes]):
            spike_trains[str(channel)] = {}
            for unit in map(chr,np.unique(data['unit'][sorted_spikes & data['channel'] == channel]) + (ord('a')-1)):
                spike_trains[str(channel)][unit] = PlexUtil.GetSpikeTrain(data, channel=channel, unit=unit)
        return spike_trains
            
    def GetSpikeTrain(self, data, channel, unit):
        """
        GetSpikeTrain(data) -> spike_train

        Return sorted spikes of the specific unit in one channel.
        Parameters
        ----------
        data: dict 
            {'type', 'channel', 'unit', 'timestamp'} dictionary from the return value of PlexClient.GetTimeStampArray().
        channel: int 
            currently 1-128
        unit: str 
            a-z

        Returns
        -------
        spiketrain: array 
            timestamp array of the specific unit
        """
        unit_spikes = (data['type'] == Plexon.PL_SingleWFType) & \
                      (data['channel'] == channel) & \
                      (data['unit'] == ord(unit)-ord('a')+1)

        return np.copy(data['timestamp'][unit_spikes])
    
    def GetExtEvents(self, data, event, bit=None):
        """
        GetExtEvents(data) -> extevents

        Return external events.
        Parameters
        ----------
        data: dict
            {'type', 'channel', 'unit', 'timestamp'} dictionary from the return value of PlexClient.GetTimeStampArray().
        event: string
            event types: 'first_strobe_word','second_strobe_word','start','stop','pause','resume','unstrobed_bit'
        bit: int
            currently 1-32, used only in unstrobed_bit event 
        Returns
        -------
        extevents: timestamp array of 'first_strobe', 'second_strobe', 'start', 'stop', 'pause', 'resume' events. for strobe_word events 
        the array is contained in a dictionary which take the key 'value' as the strobed word and the key 'timestamp' as event stamp.
        """
        ext_event_type = (data['type'] == Plexon.PL_ExtEventType)
        #extevents = data['type'][ext_event_type]
        channel = data['channel'][ext_event_type]
        unit = data['unit'][ext_event_type]
        timestamp = data['timestamp'][ext_event_type]
        # for strobed word event
        if event in ('first_strobe_word','second_strobe_word'):
            strobed_events = (channel == Plexon.PL_StrobedExtChannel)
            strobed_unit = unit[strobed_events]
            strobed_timestamp = timestamp[strobed_events]
            first_strobe  = (strobed_unit & 0x8000) != 0
            second_strobe = (strobed_unit & 0x8000) == 0
            if event is 'first_strobe_word':
                return {'value':strobed_unit[first_strobe] & 0x7FFF , 'timestamp':strobed_timestamp[first_strobe]}
            else:
                return {'value':strobed_unit[second_strobe]         , 'timestamp':strobed_timestamp[second_strobe]}
        # for start event 
        if event is 'start':
            return timestamp[channel == Plexon.PL_StartExtChannel]
        # for stop event
        if event is 'stop':
            return timestamp[channel == Plexon.PL_StopExtChannel]
        # for pause event
        if event is 'pause':
            return timestamp[channel == Plexon.PL_Pause]
        # for resume event 
        if event is 'resume':
            return timestamp[channel == Plexon.PL_Resume]
        # for unstrobed events
        if event is 'unstrobed_bit':
            return timestamp[channel == bit + 1 ]
        # reconstruct unstrobed word from unstrobed bits
        if event is 'unstrobed_word':
            word_list = []
            timestamp_list = []
            WORD_BITS = 32
            unstrobed_bits = [timestamp[channel == bit + 1 ] for bit in range(WORD_BITS)]
            bits_num = reduce(add, [len(unstrobed_bits[bit]) for bit in range(WORD_BITS)])
            bits_indices = np.array([0]*WORD_BITS)
            while reduce(add, bits_indices) < bits_num:
                bit_oldest_timestamps = [unstrobed_bits[bit][index] if index<len(unstrobed_bits[bit]) else float("inf") for bit,index in enumerate(bits_indices)]
                assert len(bit_oldest_timestamps) == WORD_BITS
                timestamp = min(bit_oldest_timestamps)
                timestamp_list.append(timestamp)
                word_bits = [bit for bit,bit_timestamp in enumerate(bit_oldest_timestamps) if bit_timestamp==timestamp]
                word = reduce(add, [1<<bit for bit in word_bits])
                word_list.append(word)
                bits_indices[word_bits] += 1
            if len(timestamp_list) and self.last_timestamp == timestamp_list[0]:
                word_list[0] += self.last_word
            elif self.last_word is not None:
                word_list.insert(0,self.last_word)
                timestamp_list.insert(0,self.last_timestamp)
                if len(timestamp_list)==1: 
                    self.last_word = None
                    self.last_timestamp = None
                    return {'value': np.array(word_list), 'timestamp': np.array(timestamp_list)}
            if len(timestamp_list):
                self.last_word = word_list[-1]
                self.last_timestamp = timestamp_list[-1]
            return {'value': np.array(word_list[:-1]), 'timestamp': np.array(timestamp_list[:-1])}
            
            
            

