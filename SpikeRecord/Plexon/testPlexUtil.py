#!/usr/bin/pyhton
import time
from guppy import hpy; h = hpy()
from PlexClient import PlexClient
from PlexUtil import PlexUtil

if __name__ == "__main__":
    with PlexClient() as pc:
        while True:
            #print "reading from server"
            data = pc.GetTimeStampArrays()
            spike_info = PlexUtil.GetSpikesInfo(data)
            for channel,units in spike_info:
                print 'found spikes in channel:%d unit:%s' % (channel, ', '.join(unit for unit in units))
                for unit in units:
                    spikes = PlexUtil.GetSpikeTrain(data, channel=channel, unit=unit)
                    for timestamp in spikes:
                        print "spike:DSP%d%c t=%f" % (channel, unit, timestamp)
            
            bit_2_events = PlexUtil.GetExtEvents(data, event='unstrobed_bit', bit=2)
            bit_3_events = PlexUtil.GetExtEvents(data, event='unstrobed_bit', bit=3)
            for timestamp in bit_2_events:
                print "event:unstrobed bit 2 t=%f" % timestamp
            for timestamp in bit_3_events:
                print "event:unstrobed bit 3 t=%f" % timestamp
            
            unstrobed_word = PlexUtil.GetExtEvents(data, event='unstrobed_word')
            for value,timestamp in zip(unstrobed_word['value'],unstrobed_word['timestamp']) :
                print "event:unstrobed word:%d t=%f" % (value,timestamp)
            
            time.sleep(1.0)

            #print h.heap()

