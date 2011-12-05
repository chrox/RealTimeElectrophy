# Base spike data.
#
# Copyright (C) 2010-2011 Huang Xin
# 
# See LICENSE.TXT that came with this file.

from SpikeRecord.Plexon.PlexClient import PlexClient
from SpikeRecord.Plexon.PlexFile import PlexFile
from SpikeRecord.Plexon.PlexUtil import PlexUtil

class PlexSpikeData(object):
    # Base class handling spike records online or offline from Plexon.
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

    def __del__(self):
        self.pc.CloseClient()
        
    def renew_data(self):
        pass
    
    def get_data(self):
        pass
    
    def _update_data(self):
        if self.read_from_server:
            self.data = self.pc.GetTimeStampArrays()
            self.online = True
        elif self.read_from_file and not self.file_has_read:
            self.data = self.pf.GetTimeStampArrays()
            self.online = False
            self.file_has_read = True
        elif self.file_has_read:
            self.data = self.pf.GetNullTimeStamp()
            self.online = False