#!/usr/bin/pyhton
#from guppy import hpy; h = hpy()
import cProfile,pstats
from PlexFile import PlexFile
from PlexUtil import PlexUtil

def run():
    with PlexFile('../../data/sparse-noise.plx') as pf:
        pu = PlexUtil()
        #print "reading from file"
        data = pf.GetTimeStampArrays()
        print "found %d events." %pu.GetEventsNum(data)
        # get spike trains altogether
        spike_trains = pu.GetSpikeTrains(data)
        for channel,channel_trains in spike_trains.iteritems():
            print 'found spike trains of channel:%c' % channel
            #print '  ' + ', '.join(str(spike) for unit_train in channel_trains.itervalues() for spike in unit_train)
        # get spike trian of specific channel and unit
        spike_info = pu.GetSpikesInfo(data)
        for channel,units in spike_info:
            print 'found spikes in channel:%d unit:%s' % (channel, ', '.join(unit for unit in units))
            for unit in units:
                spikes = pu.GetSpikeTrain(data, channel=channel, unit=unit)
                print "found %d spikes in unit %c. last 5 spikes are:" %(len(spikes),unit)
                for timestamp in spikes[-5:]:
                    print "spike:DSP%d%c t=%f" % (channel, unit, timestamp)
        
        bit_2_events = pu.GetExtEvents(data, event='unstrobed_bit', bit=2)
        bit_3_events = pu.GetExtEvents(data, event='unstrobed_bit', bit=3)
        print "found %d bit 2 events. Last 5 events are:" %(len(bit_2_events))
        for timestamp in bit_2_events[-5:]:
            print "unstrobed bit 2 t=%f" % timestamp
        print "found %d bit 3 events. Last 5 events are:" %(len(bit_3_events))
        for timestamp in bit_3_events[-5:]:
            print "unstrobed bit 3 t=%f" % timestamp
        
        unstrobed_word = pu.GetExtEvents(data, event='unstrobed_word', online=False)
        print "found %d unstrobed word events. Last 5 events are:" %(len(unstrobed_word['value']))
        for value,timestamp in zip(unstrobed_word['value'][-5:],unstrobed_word['timestamp'][-5:]) :
            print "unstrobed word:%d t=%f" % (value,timestamp)

if __name__ == "__main__":
        run()
        #cProfile.run('run()','PlexFile_profile')
        #p = pstats.Stats('PlexFile_profile')
        #p.sort_stats('cumulative')
        #p.print_stats()
        
        #print h.heap()

