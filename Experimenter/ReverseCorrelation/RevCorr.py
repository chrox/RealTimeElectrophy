# Reverse Correlation Model
#
# Copyright (C) 2010-2011 Huang Xin
# 
# See LICENSE.TXT that came with this file.

import numpy as np
from SpikeRecord.Plexon.PlexClient import PlexClient
from SpikeRecord.Plexon.PlexFile import PlexFile
from SpikeRecord.Plexon.PlexUtil import PlexUtil

class RevCorrData(object):
    def __init__(self, file=None):
        
        self.read_from_server = True
        self.read_from_file = False
        self.file_has_read = False
        
        if file is None:
            self.pc = PlexClient()
            self.pc.InitClient()
        else:
            self.read_from_server = False
            self.read_from_file = True
            self.pf = PlexFile(file)
            
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
        if self.read_from_server:
            data = self.pc.GetTimeStampArrays()
        elif self.read_from_file and not self.file_has_read:
            data = self.pf.GetTimeStampArrays()
            self.file_has_read = True
        elif self.file_has_read:
            data = self.pf.GetNullTimeStamp()
            
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
    
    def get_img(self, data, channel, unit, dimension, tau, format, cmap):
        if format == 'rgb':
            return RevCorrImg.get_rgb_img(data, channel, unit, dimension, tau, cmap)
        elif format == 'float':
            return RevCorrImg.get_float_img(data, channel, unit, dimension, tau, cmap)
    
    def float_to_rgb(self, float_img, cmap='jet'):
        return RevCorrImg._process_img(float_img, cmap)
        
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
    def get_float_img(data,channel,unit,dimension,tau,cmap):
        raise RuntimeError("%s: Definition of get_float_img() in base class RevCorrImg must be overriden."%(str(self),))

    @staticmethod
    def get_rgb_img(data,channel,unit,dimension,tau,cmap):
        img = RevCorrImg.get_float_img(data,channel,unit,dimension,tau,cmap)
        return RevCorrImg._process_img(img, cmap)
    
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
        for row in range(img.shape[0]):
            for col in range(img.shape[1]):
                rgb_img[row][col] = np.array(RevCorrImg._colormap(img[row][col],cmap))
        return rgb_img

class STAData(RevCorrData):
    """ Spike triggered average(STA) analysis
    """
    def __init__(self,file=None):
        super(STAData, self).__init__(file)
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
    
    def get_img(self, data, channel, unit, dimension=(32,32), tau=0.085, format='rgb', cmap='jet'):
        if format == 'rgb':
            return STAImg.get_rgb_img(data, channel, unit, dimension, tau, cmap)
        elif format == 'float':
            return STAImg.get_float_img(data, channel, unit, dimension, tau, cmap)
        
class STAImg(RevCorrImg):
    @staticmethod
    def get_float_img(data,channel,unit,dimension,tau,cmap='jet'):
        """ Take the time offset between spikes and the triggered stimulus.
        """
        spike_trains = data['spikes']
        cols = data['x_indices']
        rows = data['y_indices']
        contrast = data['contrast']
        timestamps = data['timestamps']
        
        img = np.zeros(dimension)
        if len(timestamps)>1:
            spikes = spike_trains[channel][unit]
            triggered_stim = spikes - tau
            
            stim_times, _bins = np.histogram(triggered_stim, timestamps)
            take = stim_times > 0
            triggered_times = stim_times[take] 
            col = cols[take]
            row = rows[take]
            contrast = contrast[take]
            contrast[contrast==0] = -1
            for index,times in enumerate(triggered_times):
                col_index = col[index]
                row_index = row[index]
                if row_index < dimension[0] and col_index < dimension[1]:
                    img[row_index][col_index] += times*contrast[index]
        return img
    
    @staticmethod
    def get_rgb_img(data,channel,unit,dimension,tau,cmap='jet'):
        img = STAImg.get_float_img(data,channel,unit,dimension,tau,cmap)
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
    def get_img(self, data, channel, unit, dimension=(16,16), tau=0.085, format='rgb', cmap='jet'):
        if format == 'rgb':
            return ParamMapIMG.get_rgb_img(data, channel, unit, dimension, tau, cmap)
        elif format == 'float':
            return ParamMapIMG.get_float_img(data, channel, unit, dimension, tau, cmap)

class ParamMapIMG(RevCorrImg):
    @staticmethod
    def get_float_img(data,channel,unit,dimension,tau,cmap='gbr'):
        spike_trains = data['spikes']
        cols = data['x_indices']
        rows = data['y_indices']
        timestamps = data['timestamps']
        img = np.zeros(dimension)
        
        if len(timestamps)>1:
            spikes = spike_trains[channel][unit]
            triggered_stim = spikes - tau
            stim_times, _bins = np.histogram(triggered_stim, timestamps)
            take = stim_times > 0
            triggered_times = stim_times[take]
            
            col = cols[take]
            row = rows[take]
            for index,times in enumerate(triggered_times):
                col_index = col[index]
                row_index = row[index]
                if row_index < dimension[0] and col_index < dimension[1]:
                    img[row_index][col_index] += times
        return img

    @staticmethod
    def get_rgb_img(data,channel,unit,dimension,tau,cmap='gbr'):
        img = ParamMapIMG.get_float_img(data,channel,unit,dimension,tau,cmap)
        return ParamMapIMG._process_img(img, cmap)