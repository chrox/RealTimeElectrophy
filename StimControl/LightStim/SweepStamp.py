# This module contains the constants of SweepStamp.
#
# Copyright (C) 2010-2011 Huang Xin
#
# See LICENSE.TXT that came with this file.
import sys
import VisionEgg.Daq
import VisionEgg.ParameterTypes as ve_types

from .. import LightStim

COMEDI_INSTALLED = LightStim.config.LIGHTSTIM_DAQBOARD_COMEDI_INSTALLED
DT340_INSTALLED = LightStim.config.LIGHTSTIM_DAQBOARD_DT340_INSTALLED

if COMEDI_INSTALLED:
    if not sys.platform.startswith('linux'):
        raise RuntimeError('Comedi driver not supported on this platform.')
    try:
        import comedi
    except ImportError:
        raise RuntimeError('Cannot import comedi module.')
    
if DT340_INSTALLED:
    if sys.platform != 'win32':
        raise RuntimeError('DT340 driver not supported on this platform.')
    try:
        import DT # only importable if DT board is installed
    except ImportError:
        raise RuntimeError('Cannot import DT module.')
    else:
        DT = None

# If DTboard pin C1 is connected to Omniplex pin A24, this post signal will trigger remote START recording.
RSTART_EVT = 0x00020000
# use single bit event to trigger START/STOP recording
START_REC = 1 << 14
STOP_REC = 1 << 15
# Maximum postable integer, 65535 for 16 digital lines. 
MAXPOSTABLEINT = 0x0000ffff
 

class ComediFunctionality(VisionEgg.Daq.Functionality):
    def __init__(self,**kw):
        VisionEgg.Daq.Functionality.__init__(self,**kw)
        self.device = None
        self.subdevice = None
        self.write_mask = None
        self.bits = None
        self.base_channel = None
    def get_data(self):
        raise RuntimeError("Must override get_data method with daq implementation!")
    def put_data(self,data):
        raise RuntimeError("Must override put_data method with daq implementation!")

class ComediInput(ComediFunctionality):
    def __init__(self,**kw):
        ComediFunctionality.__init__(self,**kw)
        self.io_direction = comedi.COMEDI_INPUT
    def get_data(self):
        return comedi.comedi_dio_bitfield2(self.device, self.subdevice, self.write_mask, 0, self.base_channel)

class ComediOutput(ComediFunctionality):
    def __init__(self,**kw):
        ComediFunctionality.__init__(self,**kw)
        self.io_direction = comedi.COMEDI_OUTPUT
    def put_data(self,data):
        comedi.comedi_dio_bitfield2(self.device, self.subdevice, self.write_mask, data, self.base_channel)
    def __del__(self):
        """Set output bits low when closing."""
        comedi.comedi_dio_bitfield2(self.device, self.subdevice, self.write_mask, 0, self.base_channel)

class ComediChannel(VisionEgg.Daq.Channel):
    """A data acquisition channel using a comedi device."""
    constant_parameters_and_defaults = {
        'first_channel' : (0, ve_types.UnsignedInteger),
        'num_channels' : (16,ve_types.UnsignedInteger),
        }
    def __init__(self,**kw):
        if not 'comedi' in globals().keys():
            raise RuntimeError("Comedi input/output not supported on this platform.")
        VisionEgg.Daq.Channel.__init__(self,**kw)
        
        base_channel = self.constant_parameters.base_channel
        if not isinstance(base_channel, int) or base_channel < 0:
            raise ValueError("Base channel must be nonnegative integer.")
        num_channels = self.constant_parameters.num_channels
        if not isinstance(num_channels, int) or num_channels < 0:
            raise ValueError("Number of channels must be nonnegative integer.")
        signal_type = self.constant_parameters.signal_type
        if not isinstance(signal_type,VisionEgg.Daq.Digital):
            raise ValueError("Channel must be digital.")
        daq_mode = self.constant_parameters.daq_mode
        if not isinstance(daq_mode,VisionEgg.Daq.Immediate):
            raise ValueError("Channel must be immediate mode.")
        functionality = self.constant_parameters.functionality
        if not isinstance(functionality,ComediInput):
            if not isinstance(functionality,ComediOutput):
                raise ValueError("Channel functionality must be instance of ComediInput or ComediOutput.")
        
class ComediDevice(VisionEgg.Daq.Device):
    """ Comedi provides a common data acquisition interface for a varity of DAQ hardware on Linux Platform.
        See http://www.comedi.org/.
    """
    def __init__(self,dev_file='/dev/comedi0',**kw):
        if not 'comedi' in globals().keys():
            raise RuntimeError("Comedi input/output not supported on this platform.")
        VisionEgg.Daq.Device.__init__(self,**kw)
        self.dev = comedi.comedi_open(dev_file)
        if not self.dev:
            raise RuntimeError("Error openning Comedi device")
        for channel in self.channels:
            if not isinstance(channel,ComediChannel):
                raise ValueError("ComediDevice only has ComediChannel.")
    
    def __del__(self):
        self.dev.close()
    
    def add_channel(self,channel):
        if not isinstance(channel,ComediChannel):
            raise ValueError("ComediDevice only has ComediChannel.")
        VisionEgg.Daq.Device.add_channel(self,channel)
        
        first_channel = channel.constant_parameters.first_channel
        num_channels = channel.constant_parameters.num_channels
        n_subdevs = comedi.comedi_get_n_subdevices(self.dev)
        nchannels = 0
        for subdevind in range(n_subdevs):
            subdevchans = comedi.comedi_get_n_channels(self.dev, subdevind)
            nchannels += subdevchans
            if first_channel + num_channels <= nchannels:
                subdevice = subdevind
                base_channel = first_channel - (nchannels - subdevchans)
                if base_channel < 0:
                    raise RuntimeError("All channels are not in one port. " 
                                     "You may need to try another first channel in the configuration file.")
                channel_io_dir = channel.constant_parameters.functionality.io_direction
                if comedi.comedi_find_subdevice_by_type(self.dev, channel_io_dir, subdevice) != subdevice:
                    raise RuntimeError("The port is not capable of the functionality as you request.")
                for channel in range(base_channel+num_channels):
                    comedi.comedi_dio_config(self.dev,subdevice,channel,channel_io_dir)
                    
                channel.constant_parameters.functionality.device = self.dev
                channel.constant_parameters.functionality.subdevice = subdevice
                channel.constant_parameters.functionality.write_mask = 2**num_channels - 1
                channel.constant_parameters.functionality.base_channel = base_channel
                return
        raise RuntimeError("Cannot allocate a port as you request.")
        
class DAQTrigger:
    def __init__(self,**kw):
        if self.__class__ == DAQTrigger:
            raise RuntimeError("Trying to instantiate abstract base class.")
    def trigger_out(self, value):
        raise RuntimeError("Must override trigger_out method with daq implementation!")
    def trigger_in(self):
        raise RuntimeError("Must override trigger_in method with daq implementation!")
    
class ComediDAQOUT(DAQTrigger):
    def __init__(self):
        self.device = ComediDevice('/dev/comedi0')
        first_channel = LightStim.config.LIGHTSTIM_DAQBOARD_COMEDI_BASE_CHAN
        num_channels = LightStim.config.LIGHTSTIM_DAQBOARD_COMEDI_NUM_CHANS
        self.trigger_out_channel = ComediChannel(first_channel = first_channel,
                                                 num_channels = num_channels,
                                                 signal_type = VisionEgg.Daq.Digital(),
                                                 daq_mode = VisionEgg.Daq.Immediate(),
                                                 functionality = ComediOutput())
        self.device.add_channel(self.trigger_in_channel)
    
    def trigger_out(self, value):
        self.trigger_out_channel.constant_parameters.functionality.put_data(value)
    
class DT340DAQOUT(DAQTrigger):
    def __init__(self):
        DT.initBoard()
        
    def trigger_out(self, value):
        DT.postInt16NoDelay(value)
        DT.clearBitsNoDelay(value)
    
class DAQStampTrigger:
    """ Digital trigger via DAQ device.
    """
    def __init__(self):
        if COMEDI_INSTALLED:
            self.trigger_out_daq = ComediDAQOUT()
        elif DT340_INSTALLED:
            self.trigger_out_daq = DT340DAQOUT()
    
    def post_stamp(self, postval):
        if COMEDI_INSTALLED or DT340_INSTALLED:
            self.trigger_out_daq.trigger_out(postval)
            
class SoftStampTrigger:
    """ Software trigger for test only. Implemented in Pyro.
    """
    def __init__(self,host,port):
        import Pyro.core
        URI = "PYROLOC://%s:%d/%s" % (host,port,'trigger_receiver')
        Pyro.core.initClient()
        self.trigger_receiver = Pyro.core.getProxyForURI(URI)
        
    def post_stamp(self, postval):
        print "Post soft triggered word: %d" %postval
        try:
            self.trigger_receiver.put_stamp(postval)
        except:
            print "Cannot post stamp to trigger receiver."
    