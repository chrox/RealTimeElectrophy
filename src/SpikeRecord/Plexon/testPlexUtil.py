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
            spikes = PlexUtil.GetSpikes(data)
            events = PlexUtil.GetExtEvents(data)
            events = {'start':events['start']}
            for i in range(spikes['num']):
                print "spike:DSP%d%c t=%f <--------------" % \
                      (spikes['channel'][i],\
                       spikes['unit'][i],\
                       spikes['timestamp'][i])
            for key,value in events.items():
                if key in ('first_strobe','second_strobe'):
                    for i in range(len(value['value'])):
                        print "event:%s,value:%d t=%f" % (key, value['value'][i], value['timestamp'][i])
                else:
                    for i in range(len(value)):
                        print "event:%s t=%f" % (key, value[i])
            time.sleep(0.04)

            #print h.heap()

