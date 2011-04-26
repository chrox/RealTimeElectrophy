#!/usr/bin/python
#coding:utf-8

###########################################################
### Utilities for Plexon data collection
### Written by Huangxin
###########################################################
import numpy as np
from .. import Plexon

class PlexUtil(object):
    """
    Utilities for data collection
    """
    @staticmethod
    def GetSpikes(data):
        """
        GetSpikes(data) -> spikes

        Return spikes in TimeStampArrays.
        Parameters
        ----------
        data: dict 
            {'type', 'channel', 'unit', 'timestamp'} dictionary from the return value of PlexClient.GetTimeStampArray().

        Returns
        -------
        spikes: dict
            {'channel', 'unit', 'timestamp', 'num'} dictionary of spikes data.
        """
        eventype   = data['type']
        channel   = data['channel']
        unit      = data['unit']
        timestamp = data['timestamp']
        sorted_spikes = (eventype == Plexon.PL_SingleWFType) & (unit > 0)
        spikes = {}
        spikes['channel'] = np.copy(channel[sorted_spikes])
        spikes['unit'] = np.copy(map(chr, unit[sorted_spikes] + (ord('a')-1)))
        spikes['timestamp'] = np.copy(timestamp[sorted_spikes])
        spikes['num'] = len(spikes['timestamp'])
        return spikes

    @staticmethod
    def GetExtEvents(data):
        """
        GetExtEvents(data) -> extevents

        Return external events.
        Parameters
        ----------
        data: dict
            {'type', 'channel', 'unit', 'timestamp'} dictionary from the return value of PlexClient.GetTimeStampArray().
        
        Returns
        -------
        extevents: dict
            {'first_strobe', 'second_strobe', 'start', 'stop', 'pause', 'resume'} dictionary of different external event as array. 
        """
        ext_event_type = (data['type'] == Plexon.PL_ExtEventType)
        #extevents = data['type'][ext_event_type]
        channel = data['channel'][ext_event_type]
        unit = data['unit'][ext_event_type]
        timestamp = data['timestamp'][ext_event_type]
        extevents = {}
        # for strobed word event
        strobed_events = (channel == Plexon.PL_StrobedExtChannel)
        strobed_unit = unit[strobed_events]
        strobed_timestamp = timestamp[strobed_events]
        first_strobe  = (strobed_unit & 0x8000) != 0
        second_strobe = (strobed_unit & 0x8000) == 0
        extevents['first_strobe']  = {'value':strobed_unit[first_strobe] & 0x7FFF , 'timestamp':strobed_timestamp[first_strobe]}
        extevents['second_strobe'] = {'value':strobed_unit[second_strobe]         , 'timestamp':strobed_timestamp[second_strobe]}
        # for start event 
        extevents['start'] = timestamp[channel == Plexon.PL_StartExtChannel]
        # for stop event
        extevents['stop'] = timestamp[channel == Plexon.PL_StopExtChannel]
        # for pause event
        extevents['pause'] = timestamp[channel == Plexon.PL_Pause]
        # for resume event 
        extevents['resume'] = timestamp[channel == Plexon.PL_Resume]
        
        return extevents

