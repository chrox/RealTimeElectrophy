"""Modified from dimstim Movie experiment"""

from __future__ import division

import numpy as np
np.seterr(all='raise') # raise all numpy errors (like 1/0), don't just warn
import pygame
import OpenGL.GL as gl

import VisionEgg
import VisionEgg.FlowControl
import VisionEgg.ParameterTypes as ve_types
from VisionEgg.MoreStimuli import Target2D
from VisionEgg.Core import FixationSpot

from LightStim import SCREENWIDTH,SCREENHEIGHT,sec2vsync,deg2pix
from LightStim.FrameControl import FrameControl,DT
from LightStim.SweepStamp import DTBOARDINSTALLED,MAXPOSTABLEINT,SWEEP
from LightStim.stimuli.CheckBoard import CheckBoard

from LightStim.FrameController import SweepStampController,SweepTableController


class RFModel(object):
    """LNP receptive field model for simulation"""
    #Gabor function for the simplest spatial receptive field
    def gabor_func(self, x,y,dx=1,dy=1,phi=np.pi/4,k=2):
        return 1/(2*np.pi*dx*dy)*np.exp(-x**2/2/dx**2-y**2/2/dy**2)*np.cos(k*x-phi)
    #response to color increment. contrast:{-1,1}
    def response(self, xpos, ypos, contrast):
        if contrast == 1:
            return max(0,self.gabor_func(xpos,ypos))
        else:
            return min(0,self.gabor_func(xpos,ypos)) 

class DTSweepStampController(SweepStampController):
    """Digital output for triggering and frame timing verification 
    """
    def __init__(self,sweeptable):
        VisionEgg.FlowControl.Controller.__init__(self,
                                           return_type=ve_types.NoneType,
                                           eval_frequency=VisionEgg.FlowControl.Controller.EVERY_FRAME)
        if DTBOARDINSTALLED: DT.initBoard()
        self.st = sweeptable.data
        self.st_iterator = iter(sweeptable.i)
    def during_go_eval(self):
        if DTBOARDINSTALLED: DT.setBitsNoDelay(SWEEP)
        index = self.st_iterator.next()
        """ 
            16-bits stimuli representation code will be posted to DT port
                000 1 111111 111111
                 |  |    |      |-----y index  
                 |  |    |------------x index
                 |  |-----------------contrast
                 |--------------------reserved 
        """
        postval = (self.st.contrast[index]<<12) + (self.st.posindex[index][0]<<6) + self.st.posindex[index][1]
        if DTBOARDINSTALLED: DT.postInt16NoDelay(postval) # post value to port, no delay
        
class PositionController(SweepTableController):
    def __init__(self,sweeptable):
        VisionEgg.FlowControl.Controller.__init__(self,
                                           return_type=ve_types.Sequence2,
                                           eval_frequency=VisionEgg.FlowControl.Controller.EVERY_FRAME)
        self.st = sweeptable.data
        self.st_iterator = iter(sweeptable.i)
        self.static = sweeptable.static #shorthand
    def during_go_eval(self):
        """Update target position, given sweep table index index"""
        index = self.st_iterator.next()
        """
        grid index diagram posindex
             ___________
            |0,0|1,0|2,0|
            |___|___|___|
            |0,1|1,1|2,1|
            |___|___|___|
            |0,2|1,2|2,2|
            |___|___|___|
        """
        #print self.st.posindex[index][0], self.st.posindex[index][1]
        xposdeg = self.static.center[0]-self.static.size[0]/2 + \
                    self.st.posindex[index][1]*self.static.gridcell[0]+self.static.widthDeg/2
        yposdeg = self.static.center[1]+self.static.size[1]/2 - \
                    self.st.posindex[index][0]*self.static.gridcell[1]-self.static.heightDeg/2
        xorig = deg2pix(self.static.origDeg[0]) + SCREENWIDTH / 2 
        yorig = deg2pix(self.static.origDeg[1]) + SCREENHEIGHT / 2
        return (xorig+deg2pix(xposdeg),yorig+deg2pix(yposdeg))
    
class ContrastController(SweepTableController):
    def __init__(self,sweeptable):
        VisionEgg.FlowControl.Controller.__init__(self,
                                           return_type=ve_types.Sequence4,
                                           eval_frequency=VisionEgg.FlowControl.Controller.EVERY_FRAME)
        self.st = sweeptable.data
        self.st_iterator = iter(sweeptable.i)
        self.static = sweeptable.static #shorthand
    def during_go_eval(self):
        """Update target contrast, given sweep table index index"""
        index = self.st_iterator.next()
        if self.st.contrast[index] == 0:
            return (0.0, 0.0, 0.0, 1.0)
        else:
            return (1.0, 1.0, 1.0, 1.0)

class CBColorController(SweepTableController):
    def __init__(self,cbp,sweeptable):
        VisionEgg.FlowControl.Controller.__init__(self,
                                           return_type=ve_types.NoneType,
                                           eval_frequency=VisionEgg.FlowControl.Controller.EVERY_FRAME)
        self.st = sweeptable.data
        self.st_iterator = iter(sweeptable.i)
        self.static = sweeptable.static #shorthand
        self.cbp = cbp
        self.receptive_field = RFModel()
    def during_go_eval(self): 
        """update checkboard color index"""
        index = self.st_iterator.next()
        xindex, yindex = self.st.posindex[index][0], self.st.posindex[index][1]
        m, n = self.static.griddim[0], self.static.griddim[1]
        xpos = xindex/m*8 - 4
        ypos = 4 - yindex/n*8
        color_increment = self.receptive_field.response(xpos,ypos,self.st.contrast[index])
        self.cbp.colorindex[self.st.posindex[index][0],self.st.posindex[index][1]] += color_increment

class WhiteNoise(FrameControl):
    """WhiteNoise experiment"""
    def __init__(self, *args, **kwargs):
        super(WhiteNoise, self).__init__(*args, **kwargs)
        self.savedpost = []

    def createstimuli(self):
        """Creates the VisionEgg stimuli objects for this Experiment subclass"""
        super(WhiteNoise, self).createstimuli()
        
        position = (self.xorig+deg2pix(self.sweeptable.static.center[0]),self.yorig+deg2pix(self.sweeptable.static.center[1]))
        
        self.targetstimulus = Target2D(position = position,
                                       color = (0.0, 0.0, 0.0, 1.0),
                                       orientation = self.sweeptable.static.orientation,
                                       anchor = 'center',
                                       size = (deg2pix(self.sweeptable.static.widthDeg), deg2pix(self.sweeptable.static.heightDeg)),
                                       on = True)
        self.fixationspot = FixationSpot(position=(self.xorig, self.yorig),
                                                 anchor='center',
                                                 color=(1.0, 0.0, 0.0, 1.0),
                                                 size=(50, 50),
                                                 on = False)
        
        self.checkboard = CheckBoard(position = position,
                                     orientation = 0.0,
                                     anchor='center',
                                     size = (deg2pix(self.sweeptable.static.size[0]),deg2pix(self.sweeptable.static.size[1])),
                                     grid = self.sweeptable.static.griddim,
                                     drawline = False,
                                     cellcolor = self.sweeptable.static.cbcolormap,
                                     on = self.sweeptable.static.checkbdon)

        self.tsp = self.targetstimulus.parameters # synonym
        self.fsp = self.fixationspot.parameters
        self.cbp = self.checkboard.parameters
        # last entry will be topmost layer in viewport
        self.stimuli = (self.background, self.checkboard, self.targetstimulus, self.fixationspot)

    def add_controller(self):
        dt_controller = DTSweepStampController(sweeptable=self.sweeptable)
        position_controller = PositionController(sweeptable=self.sweeptable)
        contrast_controller = ContrastController(sweeptable=self.sweeptable)
        cbcolour_controller = CBColorController(cbp=self.cbp, sweeptable=self.sweeptable)
        self.presentation.add_controller(None,None,dt_controller)
        self.presentation.add_controller(self.targetstimulus,'position',position_controller)
        self.presentation.add_controller(self.targetstimulus,'color',contrast_controller)
        self.presentation.add_controller(None,None,cbcolour_controller)
        
    def saveparams(self):
        import time,os
        import pickle
        (year,month,day,hour24,min,sec) = time.localtime(time.time())[:6]
        trial_time_str = "%04d%02d%02d_%02d%02d%02d"%(year,month,day,hour24,min,sec)
        save_dir = os.path.abspath(os.curdir)+ os.path.sep + 'params'
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        file_name = save_dir + os.path.sep + 'whitenoise' + trial_time_str
        #pickle save
        pkl_output = open(file_name + '.pkl','wb')
        pickle.dump(self.savedpost, pkl_output)
        pkl_output.close()
        #text save
        txt_output = open(file_name + '.txt','w')
        txt_output.write("""Sparse White Noise parameters for every sweep.\n""")
        txt_output.write("""contrast xindex  yindex   postval\n""")
        for val in self.savedpost:
            txt_output.write('\t'+str(val>>12)+'\t\t'+str((val&0xFC0)>>6)+\
                             '\t\t'+str(val&0x3F)+'\t\t'+str(val)+'\n')
        txt_output.close()
        
