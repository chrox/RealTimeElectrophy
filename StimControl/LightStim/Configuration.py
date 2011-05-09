# This module contains the hardware configuration of LightStim.
#
# Copyright (C) 2010-2011 Huang Xin
# 
#
# Distributed under the terms of the GNU Lesser General Public License
# (LGPL). See LICENSE.TXT that came with this file.

import os
import ConfigParser

default_dict = {
    'DTBoard' : {
                'INSTALLED': False
                },
    'Screen' : {
                 'WIDTH':    38.6,
                 'HEIGHT':   29.0,
                 'DISTANCE': 57.0,
                 'GAMMA':    1.0
                 },
    'Eye' :     {
                'OPEN':     'right'
                }
    }

class Config:
    """Reads and writes the config file, adds an update function"""
    def __init__(self):
        cfg = ConfigParser.ConfigParser()
        
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
            cfg.read(configFile)
        else:
            # pretend we have a config file
            for section_name,section in default_dict.iteritems():
                cfg.add_section(section_name)
                for key,value in section.iteritems():
                    cfg.set(section_name,key,str(value))

        # Get the values from the configFile
        for section_name,section in default_dict.iteritems():
            for option in cfg.options(section_name):
                name = option.upper()
                value = cfg.get(section_name,option)
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
