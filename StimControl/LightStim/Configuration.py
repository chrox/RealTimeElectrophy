# This module contains the hardware configuration of LightStim.
#
# Copyright (C) 2010-2011 Huang Xin
# 
#
# Distributed under the terms of the GNU Lesser General Public License
# (LGPL). See LICENSE.TXT that came with this file.

import os
import ConfigParser

default_conf = {
    'DTBoard' : {
                'INSTALLED': False
                },
    'Screen_common' : {
                       'WIDTH':    800,
                       'HEIGHT':   600
                       },
    'Viewport_control' : {
                        'WIDTH':    38.6,
                        'HEIGHT':   29.0,
                        'DISTANCE': 57.0,
                        'GAMMA':    1.0,
                        'OFFSET':   0,
                        'MIRRORED': False,
                        'REFRESH_RATE': 60.0
                        },
    'Viewport_primary' : {
                        'WIDTH':    38.6,
                        'HEIGHT':   29.0,
                        'DISTANCE': 57.0,
                        'GAMMA':    1.0,
                        'OFFSET':   1,
                        'MIRRORED': False,
                        'REFRESH_RATE': 120.0
                        },
    'Viewport_left' : {
                        'WIDTH':    42.6,
                        'HEIGHT':   32.0,
                        'DISTANCE': 57.0,
                        'GAMMA':    1.0,
                        'OFFSET':   2,
                        'MIRRORED': True,
                        'REFRESH_RATE': 120.0
                        },
    'Viewport_right' : {
                        'WIDTH':    42.6,
                        'HEIGHT':   32.0,
                        'DISTANCE': 57.0,
                        'GAMMA':    1.0,
                        'OFFSET':   3,
                        'MIRRORED': True,
                        'REFRESH_RATE': 120.0
                        },
    }

class Config:
    """Reads and writes the config file, adds an update function"""
    def __init__(self):
        self.cfg = ConfigParser.ConfigParser()
        
        self.LIGHTSTIM_SYSTEM_DIR = os.path.split(__file__)[0]
        user_dir = os.path.expanduser("~")
        self.LIGHTSTIM_USER_DIR = os.path.join(user_dir,"LightStim")
        # Is there one in LIGHTSTIM_USER_DIR?
        configFile = os.path.join(self.LIGHTSTIM_USER_DIR,"LightStim.cfg")
        if not os.path.isfile(configFile):
            configFile = os.path.join(self.LIGHTSTIM_SYSTEM_DIR,"LightStim.cfg")
            if not os.path.isfile(configFile):
                configFile = None # No file, use defaults specified in environment variables then here
        if configFile:
            self.cfg.read(configFile)
        else:
            # pretend we have a config file
            for section_name,section in default_conf.iteritems():
                self.cfg.add_section(section_name)
                for key,value in section.iteritems():
                    self.cfg.set(section_name,key,str(value))

        # Get the values from the configFile
        for section_name,section in default_conf.iteritems():
            for option in self.cfg.options(section_name):
                name = option.upper()
                value = self.cfg.get(section_name,option)
                if value == 'False' or value == 'false':
                    value = False
                elif value == 'True' or value == 'true':
                    value = True
                if isinstance(section[name], int):
                    if isinstance(section[name], bool):
                        value = bool(value)
                    else:
                        value = int(value)
                elif isinstance(section[name], float):
                    value = float(value)
                setattr(self,'LIGHTSTIM_'+section_name.upper()+'_'+name,value)

    def get_screen_width_pix(self):
        return self.LIGHTSTIM_SCREEN_COMMON_WIDTH
    def get_screen_height_pix(self):
        return self.LIGHTSTIM_SCREEN_COMMON_HEIGHT
    def get_viewport_width_pix(self,name):
        return self.LIGHTSTIM_SCREEN_COMMON_WIDTH
    def get_viewport_height_pix(self,name):
        return self.LIGHTSTIM_SCREEN_COMMON_HEIGHT
    def get_viewport_width_cm(self,name):
        return getattr(self, 'LIGHTSTIM_'+name.upper()+'_'+'WIDTH')
    def get_viewport_height_cm(self,name):
        return getattr(self, 'LIGHTSTIM_'+name.upper()+'_'+'HEIGHT')
    def get_viewport_distance_cm(self,name):
        return getattr(self, 'LIGHTSTIM_'+name.upper()+'_'+'DISTANCE')
    def get_viewport_offset_pix(self,name):
        return getattr(self, 'LIGHTSTIM_'+name.upper()+'_'+'OFFSET') * self.get_screen_width_pix()
    def get_viewport_mirrored(self,name):
        return getattr(self, 'LIGHTSTIM_'+name.upper()+'_'+'MIRRORED')
    def get_viewport_refresh_rate(self,name):
        return getattr(self, 'LIGHTSTIM_'+name.upper()+'_'+'REFRESH_RATE')
    def get_viewport_gamma(self,name):
        return getattr(self, 'LIGHTSTIM_'+name.upper()+'_'+'GAMMA')
    def is_viewport_mirrored(self,name):
        return getattr(self, 'LIGHTSTIM_'+name.upper()+'_'+'MIRRORED')
        
        
