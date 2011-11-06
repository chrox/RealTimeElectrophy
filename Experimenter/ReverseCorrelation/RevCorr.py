# Reverse Correlation Model
#
# Copyright (C) 2010-2011 Huang Xin
# 
#
# Distributed under the terms of the GNU Lesser General Public License
# (LGPL). See LICENSE.TXT that came with this file.
import numpy as np
from Plexon.PlexClient import PlexClient
from Plexon.PlexUtil import PlexUtil

X_INDEX = 0B111111
Y_INDEX = 0B111111 << 6
CONTRAST = 0B1 << 12

class STAData:
    """ Spike triggered average(STA) analysis
    """
    def __init__(self):
        self.pc = PlexClient()
        self.pc.InitClient()
        self.pu = PlexUtil()
        
        # and a dict for spike trains
        self.x_indices = np.empty(0,dtype=np.int16)
        self.y_indices = np.empty(0,dtype=np.int16)
        self.contrast = np.empty(0,dtype=np.int16)
        self.timestamps = np.empty(0)
        self.spike_trains = {}

    def __close__(self):
        self.pc.CloseClient()
       
    def _update_data(self):
        data = self.pc.GetTimeStampArrays()
        new_triggers = self.pu.GetExtEvents(data, event='unstrobed_word')
        trigger_values = new_triggers['value']
        trigger_timestamps = new_triggers['timestamp']
        x_index = trigger_values & X_INDEX
        y_index = (trigger_values & Y_INDEX)>>6
        contrast = (trigger_values & CONTRAST)>>12
        self.x_indices = np.append(self.x_indices, x_index)
        self.y_indices = np.append(self.y_indices, y_index)
        self.contrast = np.append(self.contrast, contrast)
        self.timestamps = np.append(self.timestamps, trigger_timestamps)
        
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

    def get_data(self):
        self._update_data()
        data = {'spikes':self.spike_trains, 'x_indices':self.x_indices,'y_indices':self.y_indices,\
                'contrast':self.contrast, 'timestamps':self.timestamps}
        return data
        
class STAImg(object):
    @staticmethod
    def _colormap(value, color='jet'):
        def clamp(x): return max(0.0, min(x, 1.0))
        if color == 'jet':
            #code from Matt Stine's Blog
            fourValue = 4 * value;
            red   = min(fourValue - 1.5, -fourValue + 4.5)
            green = min(fourValue - 0.5, -fourValue + 3.5)
            blue  = min(fourValue + 0.5, -fourValue + 2.5)
            return map(clamp,(red,green,blue))
        if color == 'gbr':
            #green black red
            red   = 2 * value - 1
            green = 1 - 2 * value
            blue  = 0.0
            return map(clamp,(red,green,blue))
            #return map(lambda x: max(0.0,min(x, 1.0)),(red,green,blue))
        if color == 'bbr':
            #blue black red
            red   = 2 * value - 1
            green = 0.0
            blue  = 1 - 2 * value
            return map(clamp,(red,green,blue))
        if color == 'ggr':
            #green gray red
            red   = max(0.5,value)
            green = max(0.5,1 - value)
            blue  = 1 - (red + green)/2.0
            red   = red + 0.5 - green
            green = green + 0.5 - red
            return map(clamp,(red,green,blue))
        else:
            return (0.0,0.0,0.0)

    @staticmethod
    def _get_dimention(x_index,y_index):
        def is_power_of_2(v):
            return (v & (v - 1)) == 0
        def next_power_of_2(v):
            v -= 1
            v |= v >> 1
            v |= v >> 2
            v |= v >> 4
            v |= v >> 8
            v |= v >> 16
            return v + 1
        def get_next_power(v):
            if is_power_of_2(v):
                return v
            else:
                return next_power_of_2(v)
        x_dim = get_next_power(max(x_index)+1)
        y_dim = get_next_power(max(y_index)+1)
        return (x_dim, y_dim)

    @staticmethod
    def get_img(data,channel,unit,tau=0.085,cmap='jet'):
        """ Take the time offset between spikes and the triggered stimulus.
        """
        spike_trains = data['spikes']
        x_indices = data['x_indices']
        y_indices = data['y_indices']
        contrast = data['contrast']
        timestamps = data['timestamps']
        
        img = np.zeros((64,64))
        rgb_img = np.zeros((64,64,3))
        spikes = spike_trains[channel][unit]
        triggered_stim = spikes - tau
        stim_times, _bins = np.histogram(triggered_stim, timestamps)
        take = stim_times > 0
        triggered_times = stim_times[take] 
        x_index = x_indices[take]
        y_index = y_indices[take]
        contrast = contrast[take]
        contrast[contrast==0] = -1
        for index,times in enumerate(triggered_times):
            img[x_index[index]][y_index[index]] += times*contrast[index]
        #trim img
        x_dim,y_dim = STAImg._get_dimention(x_index,y_index)
        print max(x_index),max(y_index)
        print x_dim,y_dim
        img = img[:x_dim,:y_dim]
        rgb_img = rgb_img[:x_dim,:y_dim]
        #normalize image
        vmax = img.max()
        vmin = img.min()
        factor = 1.0/(vmax-vmin)/2.0 if vmax != vmin else 0
        img = img*factor + 0.5
        #use customized colormap
        #more efficient way?
        for col in range(img.shape[0]):
            for row in range(img.shape[1]):
                rgb_img[col][row] = np.array(STAImg._colormap(img[col][row],cmap))
        return rgb_img
        