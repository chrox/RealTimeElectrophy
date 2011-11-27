# This module contains the hardware configuration of LightStim.
#
# Copyright (C) 2010-2011 Huang Xin
#
# See LICENSE.TXT that came with this file.

import os
import logging
import ConfigParser

class Config:
    """Reads and writes the config file, adds an update function"""
    template = {
    'DTBoard' : {
                'INSTALLED': False
                },
    'Viewport' : {
                        'WIDTH_PIX': 1280,
                        'HEIGHT_PIX': 800,
                        'WIDTH_CM':    38.6,
                        'HEIGHT_CM':   29.0,
                        'DISTANCE': 57.0,
                        'GAMMA':    1.0,
                        'INDEX':   0,
                        'MIRRORED': False,
                        'REFRESH_RATE': 60.0,
                        'X_RECTIFICATION': 0.0,
                        'Y_RECTIFICATION': 0.0
                        }
    }
    viewport_prefix = 'LIGHTSTIM_VIEWPORT_'
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
            raise RuntimeError('No hardware configuration file was found.')

        # Get the values from the configFile
        self.sections = self.cfg.sections()
        for section in self.sections:
            for template_section in Config.template.iterkeys():
                if section.startswith(template_section):
                    section_template = Config.template[template_section]
            for option in self.cfg.options(section):
                name = option.upper()
                value = self.cfg.get(section,option)
                if value == 'False' or value == 'false':
                    value = False
                elif value == 'True' or value == 'true':
                    value = True
                if isinstance(section_template[name], bool):
                    value = self.cfg.getboolean(section, option)
                elif isinstance(section_template[name], int):
                    value = self.cfg.getint(section, option)
                elif isinstance(section_template[name], float):
                    value = self.cfg.getfloat(section, option)
                setattr(self,'LIGHTSTIM_'+section.upper()+'_'+name,value)

    def get_screen_width_pix(self,viewports_list):
        known_viewports = self.get_known_viewports()
        min_viewport_order = min([self.get_viewport_index(viewport_name) for viewport_name in viewports_list])
        max_viewport_order = max([self.get_viewport_index(viewport_name) for viewport_name in viewports_list])
        screen_viewports = known_viewports[min_viewport_order:max_viewport_order+1]
        return sum([self.get_viewport_width_pix(viewport_name) for viewport_name in screen_viewports])
    def get_screen_height_pix(self,viewports_list):
        return max([self.get_viewport_height_pix(viewport_name) for viewport_name in viewports_list])
    def get_known_viewports(self):
        viewports = [section[len('Viewport_'):] for section in self.sections if section.startswith('Viewport_')]
        # sorted from viewport index
        return sorted(viewports,key=self.get_viewport_index)
    def get_viewport_width_pix(self,viewport_name):
        return getattr(self, Config.viewport_prefix+viewport_name.upper()+'_'+'WIDTH_PIX')
    def get_viewport_height_pix(self,viewport_name):
        return getattr(self, Config.viewport_prefix+viewport_name.upper()+'_'+'HEIGHT_PIX')
    def get_viewport_width_cm(self,viewport_name):
        return getattr(self, Config.viewport_prefix+viewport_name.upper()+'_'+'WIDTH_CM')
    def get_viewport_height_cm(self,viewport_name):
        return getattr(self, Config.viewport_prefix+viewport_name.upper()+'_'+'HEIGHT_CM')
    def get_viewport_distance_cm(self,viewport_name):
        return getattr(self, Config.viewport_prefix+viewport_name.upper()+'_'+'DISTANCE')
    def get_viewport_index(self,viewport_name):
        return getattr(self, Config.viewport_prefix+viewport_name.upper()+'_'+'INDEX')
    def get_viewport_offset(self,viewport_name):
        known_viewports = self.get_known_viewports()
        left_viewports = known_viewports[:self.get_viewport_index(viewport_name)]
        return sum([self.get_viewport_width_pix(viewport_name) for viewport_name in left_viewports])
    def get_viewport_mirrored(self,viewport_name):
        return getattr(self, Config.viewport_prefix+viewport_name.upper()+'_'+'MIRRORED')
    def get_viewport_refresh_rate(self,viewport_name):
        return getattr(self, Config.viewport_prefix+viewport_name.upper()+'_'+'REFRESH_RATE')
    def get_viewport_gamma(self,viewport_name):
        return getattr(self, Config.viewport_prefix+viewport_name.upper()+'_'+'GAMMA')
    def is_viewport_mirrored(self,viewport_name):
        return getattr(self, Config.viewport_prefix+viewport_name.upper()+'_'+'MIRRORED')
    def get_viewport_x_rectification_deg(self,viewport_name):
        return getattr(self, Config.viewport_prefix+viewport_name.upper()+'_'+'X_RECTIFICATION')
    def get_viewport_y_rectification_deg(self,viewport_name):
        return getattr(self, Config.viewport_prefix+viewport_name.upper()+'_'+'Y_RECTIFICATION')
    
    def assume_viewport_refresh_rate(self):
        stim_viewport_refresh_rates = [self.get_viewport_refresh_rate(viewport) \
                                       for viewport in self.get_known_viewports() if viewport != 'control']
        refresh_rate = stim_viewport_refresh_rates[0] if len(stim_viewport_refresh_rates)>0 \
                                                      else self.get_viewport_refresh_rate('control')
        return refresh_rate
    
    def check_configuration(self):
        self.check_viewport_size()
        self.check_viewport_refresh_rate()
        
    def check_viewport_size(self):
        logger = logging.getLogger('LightStim.Configuration')
        stim_viewports = [viewport for viewport in self.get_known_viewports() if viewport != 'control']
        stim_viewport_sizes = [(self.get_viewport_width_pix(viewport), self.get_viewport_height_pix(viewport)) \
                               for viewport in stim_viewports]
        unique_sizes = set(stim_viewport_sizes)
        if len(unique_sizes)>1:
            logger.warning('Sizes of stimulus viewports are not the same in configuration file.')
        control_viewport_size = self.get_viewport_width_pix('control'), self.get_viewport_height_pix('control')
        for size in unique_sizes:
            if size[0]>control_viewport_size[0] or size[1]>control_viewport_size[1]:
                viewport_index = stim_viewport_sizes.index(size)
                logger.warning('Size of stimulus viewport \"%s\" is larger than that of control '
                               'viewport in configuration file.' %stim_viewports[viewport_index])
                
    def check_viewport_refresh_rate(self):
        logger = logging.getLogger('LightStim.Configuration')
        stim_viewport_refresh_rates = [self.get_viewport_refresh_rate(viewport) \
                                      for viewport in self.get_known_viewports() if viewport != 'control']
        unique_rates = set(stim_viewport_refresh_rates)
        if len(unique_rates)>1:
            logger.warning('Refresh rates of stimulus viewports are not the same in configuration file. Severe problems could happen '
                           'in subsequent stimulus presentation relating to temporal properties.')
