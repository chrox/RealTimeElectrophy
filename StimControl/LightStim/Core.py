# Screen and Viewport class for multiply displays stimulation.
#
# Copyright (C) 2010-2011 Huang Xin
#
# See LICENSE.TXT that came with this file.

"""

This module contains classes for multiply displays stimulation.

"""
from __future__ import division
import os
import sys
import math
import pickle
import logging
import numpy as np
#import logging
import OpenGL
# Suppress known PyOpenGL bug ID:2817196 and a performance improvement
OpenGL.ERROR_CHECKING = False
# performance improvement 
OpenGL.ERROR_LOGGING = False
import VisionEgg
VisionEgg.start_default_logging(); VisionEgg.watch_exceptions()
import VisionEgg.GL as gl
import VisionEgg.Core
from .. import LightStim

from LightData import dictattr

class Screen(VisionEgg.Core.Screen):
    """ Large screen occupies multiply displays
    """
    def __init__(self, viewports_list, bgcolor, frameless=True, hide_mouse=True, alpha_bits=8, **kw):
        # Make sure that SDL_VIDEO_WINDOW_POS takes effect.
        VisionEgg.config.VISIONEGG_FRAMELESS_WINDOW = 0
        screen_offset = min([LightStim.config.get_viewport_offset(viewport) for viewport in LightStim.config.get_known_viewports() if viewport in viewports_list])
        os.environ['SDL_VIDEO_WINDOW_POS']="%d,%d" %(screen_offset,0)
        if sys.platform == 'win32':
            # Suppress known bug "pygame.error: No available video device" when initiating display in pygame
            os.environ['SDL_VIDEODRIVER']='windib'
        self.screen_width = LightStim.config.get_screen_width_pix(viewports_list)
        self.screen_height = LightStim.config.get_screen_height_pix(viewports_list)
        super(Screen,self).__init__(size=(self.screen_width, self.screen_height), bgcolor=bgcolor, frameless=True, hide_mouse=True, alpha_bits=8, **kw)

class DefaultScreen(Screen):
    """ Specified before stimulus definition.
    """
    screen = None
    viewports = None
    def __init__(self,viewports_list,bgcolor=(0.0,0.0,0.0)):
        DefaultScreen.screen = Screen(viewports_list,bgcolor)
        DefaultScreen.viewports = viewports_list

class Stimulus(VisionEgg.Core.Stimulus):
    """ One stimulus has one and only one viewport to make things not so hard."""
    # __slot__ specifies which attributes are copied when copy.copy is called.
    __slots__ = ('controllers','sweep_completed')
    def __init__(self, subject=None, params=None, viewport=None, **kwargs):
        super(Stimulus, self).__init__(**kwargs)
        self.name = "stimulus"
        self.logger = logging.getLogger('LightStim.Stimulus')
        self.param_names = []
        self.defalut_parameters = {}
        
        if subject is not None:
            self.param_file = "stimulus_params." + subject + ".pkl"
        else:
            self.param_file = "stimulus_params.pkl"
            
        if hasattr(params,'bgbrightness'):
            self.bgcolor = (params.bgbrightness, params.bgbrightness, params.bgbrightness)
        else:
            self.bgcolor = (0.0,0.0,0.0)
        if viewport:
            self.viewport = Viewport(name=viewport, bgcolor=self.bgcolor)
            
        """ store stimulus parameters """
        self.parameters = dictattr()
        
        self.sweep_completed = False
        self.stimuli = []
        self.controllers = []
        self.event_handlers = []
    def get_parameters(self, params, param_names):
        return dict((paramname,getattr(params,paramname)) for paramname in param_names)
    def set_parameters(self, dest_params, source_params):
        for paramname, paramval in source_params.items():
            setattr(dest_params, paramname, paramval)
    def draw(self):
        for stimulus in self.stimuli:
            stimulus.draw()
    def make_stimuli(self):
        raise RuntimeError("Must override make_stimuli method with stimulus implementation!")    
    def register_controllers(self):
        raise RuntimeError("Must override register_controllers method with stimulus implementation!")
    def register_event_handlers(self):
        raise RuntimeError("Must override register_event_handlers method with stimulus implementation!")
    
    def load_params(self, index=0):
        name = self.viewport.name
        info = self.name + str(index) + ' in ' + name + ' viewport.'
        if self.viewport.get_name() != 'control':   # make control viewport like a passive viewport
            self.logger.info('Load parameters for ' + info)
        try:
            with open(self.param_file,'rb') as pkl_input:
                params_dict = pickle.load(pkl_input)[name][index]
                for key in params_dict:
                    if key in self.defalut_parameters and \
                              type(params_dict[key]) != type(self.defalut_parameters[key]):
                        params_dict[key] = self.defalut_parameters[key]
                        self.logger.warning("Found corrupted parameter '%s' for " %key + info + 
                                       ' Use the default value %s.'%str(self.defalut_parameters[key]))
                self.defalut_parameters.update(params_dict)
        except:
            if self.viewport.get_name() != 'control':
                self.logger.warning('Cannot load parameters for ' + info + ' Use the default parameter.')
        
        self.set_parameters(self.parameters, self.defalut_parameters)
    
    def save_params(self, index):
        name = self.viewport.name
        info = self.name + str(index) + ' in ' + name + ' viewport.'
        self.logger.info('Save preference for ' + info)
        params_dict = {}
        try:
            try:
                with open(self.param_file,'rb') as pkl_input:
                    params_dict = pickle.load(pkl_input)
            except:
                self.logger.warning('Cannot load params.'+ ' Use the default preference.')
            if name not in params_dict:
                params_dict[name] = [self.defalut_preference] * 2
            with open(self.param_file,'wb') as pkl_output:
                params_dict[name][index].update(self.get_parameters(self.parameters, self.param_names))
                pickle.dump(params_dict, pkl_output)
            self.logger.info('Saved parameters:\n' + str(self.get_parameters(self.parameters, self.param_names)))
        except:
            self.logger.warning('Cannot save preference ' + info)
    
class Dummy_Stimulus(Stimulus):
    """ To keep the framesweep running """
    def __init__(self, viewport='left', **kwargs):
        super(Dummy_Stimulus, self).__init__(viewport,**kwargs)
    def draw(self):
        pass

class HorizontalMirrorView(VisionEgg.Core.ModelView):
    def __init__(self,width):
        gl.glMatrixMode(gl.GL_MODELVIEW) # Set OpenGL matrix state to modify the modelview matrix
        gl.glPushMatrix()
        gl.glLoadIdentity() # Clear the modelview matrix
        gl.glTranslate(width,0,0)
        gl.glRotate(180, 0, 1, 0)
        matrix = gl.glGetFloatv(gl.GL_MODELVIEW_MATRIX)
        gl.glPopMatrix()
        if matrix is None:
            # OpenGL wasn't started
            raise RuntimeError("OpenGL matrix operations can only take place once OpenGL context started.")
        matrix = np.asarray(matrix) # make sure it's numpy array
        VisionEgg.Core.ModelView.__init__(self,**{'matrix':matrix})               

class Viewport(VisionEgg.Core.Viewport):
    """ Named viewport in hardware configuration file LightStim.cfg
        Register this viewport in viewport list when .
    """
    defined_viewports = []    # defined viewports in stimulus. Updated when stimulus is defined.
    registered_viewports = [] # registered viewports in screen. Updated when stimulus is added. And viewport is deleted.
    def __init__(self, name, bgcolor=None, **kw):
        if name not in Viewport.defined_viewports:
            Viewport.defined_viewports.append(name)
        self.name = name
        self.width_pix = LightStim.config.get_viewport_width_pix(name)
        self.height_pix = LightStim.config.get_viewport_height_pix(name)
        self.width_cm = LightStim.config.get_viewport_width_cm(name)
        self.height_cm = LightStim.config.get_viewport_height_cm(name)
        self.distance_cm = LightStim.config.get_viewport_distance_cm(name)
        self.mirrored = LightStim.config.is_viewport_mirrored(name)
        self.refresh_rate = LightStim.config.get_viewport_refresh_rate(name)
        self.pix_per_cm = (self.width_pix/self.width_cm + self.height_pix/self.height_cm)/2
        self.size = (self.width_pix, self.height_pix)
        
        self.x_rectification_deg = LightStim.config.get_viewport_x_rectification_deg(name)
        self.y_rectification_deg = LightStim.config.get_viewport_y_rectification_deg(name)
        
        self.xorig = self.width_pix / 2 + self.x_rectification_deg * math.pi / 180 * self.distance_cm * self.pix_per_cm
        self.yorig = self.height_pix / 2 + self.y_rectification_deg * math.pi / 180 * self.distance_cm * self.pix_per_cm
        # Pythonic ternary operator
        mirror_view = HorizontalMirrorView(width=self.width_pix) if self.mirrored else None
        
        screen = DefaultScreen.screen if DefaultScreen.screen is not None else Screen(Viewport.defined_viewports)
        if bgcolor is not None:
            screen.parameters.bgcolor = bgcolor
        super(Viewport,self).__init__(anchor='upperleft', size=self.size, camera_matrix=mirror_view, screen=screen, **kw)
    
    def update_viewport(self):
        # update viewport position
        known_viewports = LightStim.config.get_known_viewports()
        min_viewport_order = min([LightStim.config.get_viewport_index(viewport_name) for viewport_name in Viewport.defined_viewports])
        max_viewport_order = max([LightStim.config.get_viewport_index(viewport_name) for viewport_name in Viewport.defined_viewports])
        if DefaultScreen.viewports is not None:
            screen_viewports = DefaultScreen.viewports
        else:
            screen_viewports = known_viewports[min_viewport_order:max_viewport_order+1]
        offset = sum([LightStim.config.get_viewport_width_pix(viewport_name) for viewport_name in screen_viewports[:screen_viewports.index(self.name)]])
        height = LightStim.config.get_screen_height_pix(Viewport.defined_viewports)
        self.parameters.position = offset, height
       
    def get_name(self):
        return self.name
    def get_size(self):
        return self.size
    ############# Some spatial utilities #############
    def deg2pix(self, deg):
        """Convert from degrees of visual space to pixels"""
        # shouldn't I be using opp = 2.0 * distance * tan(deg/2), ie trig instead of solid angle of a circle ???!!
        # make it a one-liner, break it up into multiple lines in the docstring
        if deg == None:
            deg = 0 # convert to an int
        rad = deg * math.pi / 180 # float, angle in radians
        s = self.distance_cm * rad # arc length in cm
        return s * self.pix_per_cm # float, arc length in pixels
    
    def deg2truepix(self, deg):
        return 2.0 * self.distance_cm * self.pix_per_cm * math.tan(deg*math.pi/90)
    
    def pix2deg(self, pix):
        """Convert from pixels to degrees of visual space"""
        # shouldn't we be using arctan?????!!!!!!!
        if pix == None:
            pix = 0 # convert to an int
        s = pix / self.pix_per_cm # arc length in cm
        rad = s / self.distance_cm # angle in radians
        return rad * 180 / math.pi # float, angle in degrees
    
    ############# Some temporal utilities #############    
    def intround(self, n):
        """Round to the nearest integer, return an integer"""
        return int(round(n))
    
    def sec2vsync(self, sec):
        """Convert from sec to number of vsyncs"""
        return sec * self.refresh_rate # float
    
    def msec2vsync(self, msec):
        """Convert from msec to number of vsyncs"""
        return self.sec2vsync(msec / 1000) # float
    
    def sec2intvsync(self, sec):
        """Convert from sec to an integer number of vsyncs"""
        vsync = self.intround(self.sec2vsync(sec))
        # prevent rounding down to 0 vsyncs. This way, even the shortest time interval in sec will get you at least 1 vsync
        if vsync == 0 and sec != 0:
            vsync = 1
        return vsync # int
    
    def msec2intvsync(self, msec):
        """Convert from msec to an integer number of vsyncs"""
        vsync = self.intround(self.msec2vsync(msec))
        # prevent rounding down to 0 vsyncs. This way, even the shortest time interval in msec will get you at least 1 vsync
        if vsync == 0 and msec != 0:
            vsync = 1
        return vsync # int
    
    def vsync2sec(self, vsync):
        """Convert from number of vsyncs to sec"""
        return vsync / self.refresh_rate # float
    
    def vsync2msec(self, vsync):
        """Convert from number of vsyncs to msec"""
        return self.vsync2sec(vsync) * 1000.0 # float
    
    ############# Some spatial-temporal utilities #############
    def degSec2pixVsync(self, degSec):
        """Convert speed from degress of visual space per sec to pixels per vsync"""
        try:
            pixSec = self.deg2pix(degSec)
            secPix = 1 / pixSec
            vsyncPix = self.sec2vsync(secPix) # float
            return 1 / vsyncPix # float
        except (ZeroDivisionError, FloatingPointError):
            return 0.0 # float
    
    def cycSec2cycVsync(self, cycSec):
        """Convert temporal frequency from cycles per sec to cycles per vsync"""
        try:
            secCyc = 1 / cycSec
            vsyncCyc = self.sec2vsync(secCyc) # float
            return 1 / vsyncCyc # float
        except (ZeroDivisionError, FloatingPointError):
            return 0.0 # float
    
    def cycDeg2cycPix(self, cycDeg):
        """Convert spatial frequency from cycles per degree of visual space to cycles per pixel"""
        try:
            degCyc = 1 / cycDeg
            pixCyc = self.deg2pix(degCyc) # float
            return 1 / pixCyc # float
        except (ZeroDivisionError, FloatingPointError):
            return 0.0 # float
