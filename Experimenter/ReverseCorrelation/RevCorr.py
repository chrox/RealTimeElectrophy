# Reverse Correlation Model
#
# Copyright (C) 2010-2011 Huang Xin
# 
#
# Distributed under the terms of the BSD License.
# See LICENSE.TXT that came with this file.

import numpy as np
from SpikeRecord.Plexon.PlexClient import PlexClient
from SpikeRecord.Plexon.PlexUtil import PlexUtil

class RevCorrData(object):
    def __init__(self):
        self.pc = PlexClient()
        self.pc.InitClient()
        self.pu = PlexUtil()
        
        self.renew_data()
        
    def __close__(self):
        self.pc.CloseClient()

    def renew_data(self):
        self.spike_trains = {}
        self.x_indices = np.empty(0,dtype=np.int16)
        self.y_indices = np.empty(0,dtype=np.int16)
        self.timestamps = np.empty(0)

    def _update_data(self):
        data = self.pc.GetTimeStampArrays()
        self.new_triggers = self.pu.GetExtEvents(data, event='unstrobed_word')
        
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
        data = {'spikes':self.spike_trains, 
                'x_indices':self.x_indices,'y_indices':self.y_indices,'timestamps':self.timestamps}
        return data
        
class RevCorrImg(object):
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
        pass
    
    @staticmethod        
    def _process_img(img,cmap):
        rgb_img = np.zeros(list(img.shape)+[3])
        #normalize image
        vmax = img.max()
        vmin = img.min()
        factor = 1.0/(vmax-vmin)/2.0 if vmax != vmin else 0
        img = img*factor + 0.5
        #use customized colormap
        #more efficient way?
        for col in range(img.shape[0]):
            for row in range(img.shape[1]):
                rgb_img[col][row] = np.array(RevCorrImg._colormap(img[col][row],cmap))
        return rgb_img

class STAData(RevCorrData):
    """ Spike triggered average(STA) analysis
    """
    def __init__(self):
        super(STAData, self).__init__()
        self.X_INDEX = 0B111111
        self.X_BIT_SHIFT = 0
        self.Y_INDEX = 0B111111
        self.Y_BIT_SHIFT = 6
        self.CONTRAST = 0B1
        self.CONTRAST_BIT_SHIFT = 12

    def renew_data(self):
        super(STAData, self).renew_data()
        self.contrast = np.empty(0,dtype=np.int16)

    def _update_data(self):
        super(STAData,self)._update_data()
        trigger_values = self.new_triggers['value']
        trigger_timestamps = self.new_triggers['timestamp']
        x_index = (trigger_values & self.X_INDEX<<self.X_BIT_SHIFT)>>self.X_BIT_SHIFT
        y_index = (trigger_values & self.Y_INDEX<<self.Y_BIT_SHIFT)>>self.Y_BIT_SHIFT
        contrast = (trigger_values & self.CONTRAST<<self.CONTRAST_BIT_SHIFT)>>self.CONTRAST_BIT_SHIFT
        self.x_indices = np.append(self.x_indices, x_index)
        self.y_indices = np.append(self.y_indices, y_index)
        self.contrast = np.append(self.contrast, contrast)
        self.timestamps = np.append(self.timestamps, trigger_timestamps)

    def get_data(self):
        data = super(STAData,self).get_data()
        data['contrast'] = self.contrast
        return data
    
    def get_rgb_img(self, data, channel, unit, dimension=(32,32), tau=0.085, cmap='jet'):
        return STAImg.get_rgb_img(data, channel, unit, dimension, tau, cmap)
        
class STAImg(RevCorrImg):
    @staticmethod
    def get_rgb_img(data,channel,unit,dimension,tau,cmap='jet'):
        """ Take the time offset between spikes and the triggered stimulus.
        """
        spike_trains = data['spikes']
        x_indices = data['x_indices']
        y_indices = data['y_indices']
        contrast = data['contrast']
        timestamps = data['timestamps']
        
        img = np.zeros(dimension)
        if len(timestamps)>1:
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
                pixel_index_x = x_index[index]
                pixel_index_y = y_index[index]
                if pixel_index_x < dimension[0] and pixel_index_y < dimension[1]:
                    img[pixel_index_x][pixel_index_y] += times*contrast[index]
        return STAImg._process_img(img, cmap)

class ParamMapData(RevCorrData):
    def __init__(self):
        super(ParamMapData,self).__init__()
        self.X_INDEX = 0B1111
        self.X_BIT_SHIFT = 0
        self.Y_INDEX = 0B1111
        self.Y_BIT_SHIFT = 4
    def renew_data(self):
        super(ParamMapData,self).renew_data()
    def _update_data(self):
        super(ParamMapData,self)._update_data()
        trigger_values = self.new_triggers['value']
        trigger_timestamps = self.new_triggers['timestamp']
        x_index = (trigger_values & self.X_INDEX<<self.X_BIT_SHIFT)>>self.X_BIT_SHIFT
        y_index = (trigger_values & self.Y_INDEX<<self.Y_BIT_SHIFT)>>self.Y_BIT_SHIFT
        self.x_indices = np.append(self.x_indices, x_index)
        self.y_indices = np.append(self.y_indices, y_index)
        self.timestamps = np.append(self.timestamps, trigger_timestamps)
    def get_data(self):
        data = super(ParamMapData,self).get_data()
        return data
    def get_rgb_img(self, data, channel, unit, dimension=(16,16), tau=0.085, cmap='jet'):
        return ParamMapIMG.get_rgb_img(data, channel, unit, dimension, tau, cmap)

class ParamMapIMG(RevCorrImg):
    @staticmethod
    def get_rgb_img(data,channel,unit,dimension,tau,cmap='gbr'):
        spike_trains = data['spikes']
        x_indices = data['x_indices']
        y_indices = data['y_indices']
        timestamps = data['timestamps']
        img = np.zeros(dimension)
        
        if len(timestamps)>1:
            spikes = spike_trains[channel][unit]
            triggered_stim = spikes - tau
            stim_times, _bins = np.histogram(triggered_stim, timestamps)
            take = stim_times > 0
            triggered_times = stim_times[take] 
            x_index = x_indices[take]
            y_index = y_indices[take]
            for index,times in enumerate(triggered_times):
                pixel_index_x = x_index[index]
                pixel_index_y = y_index[index]
                if pixel_index_x < dimension[0] and pixel_index_y < dimension[1]:
                    img[pixel_index_x][pixel_index_y] += times
        return ParamMapIMG._process_img(img, cmap)
