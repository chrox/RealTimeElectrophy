# WhiteNoise stimulus
#
# Copyright (C) 2010-2011 Huang Xin
# 
#
# Distributed under the terms of the GNU Lesser General Public License
# (LGPL). See LICENSE.TXT that came with this file.

from __future__ import division

import numpy as np
np.seterr(all='raise') # raise all numpy errors (like 1/0), don't just warn

import pickle

from VisionEgg.MoreStimuli import Target2D
from VisionEgg.Core import FixationSpot

import FrameControl
from SweepStamp import DT,DTBOARDINSTALLED,SWEEP
from SweepController import SweepTableController,SaveParamsController
from LightStim import SCREENWIDTH,SCREENHEIGHT,deg2pix

from CheckBoard import CheckBoard


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

class DTSweepStampController(SweepTableController):
    """Digital output for triggering and frame timing verification 
    """
    def __init__(self,*args,**kwargs):
        super(DTSweepStampController, self).__init__(*args,**kwargs)
        if DTBOARDINSTALLED: DT.initBoard()
    def during_go_eval(self):
        index = self.next_index()
        if index == None: return
        """ 
            16-bits stimuli representation code will be posted to DT port
                000 1 111111 111111
                 |  |    |      |-----y index  
                 |  |    |------------x index
                 |  |-----------------contrast
                 |--------------------reserved 
        """
        if DTBOARDINSTALLED: DT.setBitsNoDelay(SWEEP)
        postval = (self.st.contrast[index]<<12) + (self.st.posindex[index][0]<<6) + self.st.posindex[index][1]
        if DTBOARDINSTALLED: DT.postInt16NoDelay(postval) # post value to port, no delay
        
class TargetController(SweepTableController):
    """Target noise in the white noise stimulus"""
    def __init__(self,tsp,*args,**kwargs):
        super(TargetController, self).__init__(*args,**kwargs)
        self.tsp = tsp
    def during_go_eval(self):
        index = self.next_index()
        """Whether draw the target""" 
        if index == None:
            self.tsp.on = False
            return
        else:
            self.tsp.on = True
        """Update target position, given sweep table index index"""
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
        xposdeg = self.static.center[0]-self.static.size[0]/2 + \
                    self.st.posindex[index][1]*self.static.gridcell[0]+self.static.widthDeg/2
        yposdeg = self.static.center[1]+self.static.size[1]/2 - \
                    self.st.posindex[index][0]*self.static.gridcell[1]-self.static.heightDeg/2
        xorig = deg2pix(self.static.origDeg[0]) + SCREENWIDTH / 2 
        yorig = deg2pix(self.static.origDeg[1]) + SCREENHEIGHT / 2
        
        """Update target contrast, given sweep table index index"""
        if self.st.contrast[index] == 0:
            self.tsp.color = (0.0, 0.0, 0.0, 1.0)
        else:
            self.tsp.color = (1.0, 1.0, 1.0, 1.0)
        self.tsp.position = (xorig+deg2pix(xposdeg),yorig+deg2pix(yposdeg))

class CheckBoardController(SweepTableController):
    def __init__(self,cbp,*args,**kwargs):
        super(CheckBoardController, self).__init__(*args,**kwargs)
        self.cbp = cbp
        self.receptive_field = RFModel()
    def during_go_eval(self): 
        """update checkboard color index"""
        index = self.next_index()
        if index == None: return
        xindex, yindex = self.st.posindex[index][0], self.st.posindex[index][1]
        m, n = self.static.griddim[0], self.static.griddim[1]
        xpos = xindex/m*8 - 4
        ypos = 4 - yindex/n*8
        color_increment = self.receptive_field.response(xpos,ypos,self.st.contrast[index])
        self.cbp.colorindex[self.st.posindex[index][0],self.st.posindex[index][1]] += color_increment

class SavePosParamsController(SaveParamsController):
    """ Use Every_Frame evaluation controller in case of real time sweep table modification
    """
    def __init__(self,file_prefix='whitenoise',*args,**kwargs):
        super(SavePosParamsController, self).__init__(file_prefix='whitenoise',*args,**kwargs)
        self.file_header = 'Sparse White Noise parameters for every sweep.\n contrast xindex  yindex   postval\n'
        self.file_saved = False
    def during_go_eval(self):
        index = self.next_index()
        if index == None: return
        postval = (self.st.contrast[index]<<12) + (self.st.posindex[index][0]<<6) + self.st.posindex[index][1]
        self.savedpost.append(postval)
    def between_go_eval(self):
        if self.file_saved:
            return
        #pickle save
        pkl_output = open(self.file_name + '.pkl','wb')
        pickle.dump(self.savedpost, pkl_output)
        pkl_output.close()
        #text save
        txt_output = open(self.file_name + '.txt','w')
        txt_output.write(self.file_header)
        for val in self.savedpost:
            txt_output.write('\t'+str(val>>12)+'\t\t'+str((val&0xFC0)>>6)+\
                             '\t\t'+str(val&0x3F)+'\t\t'+str(val)+'\n')
        txt_output.close()
        self.file_saved = True
        

class WhiteNoise(FrameControl.FrameSweep):
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
                                       on = False)
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

    def add_stimulus_controllers(self):
        dt_controller = DTSweepStampController(sweeptable=self.sweeptable)
        save_params_controller = SavePosParamsController(sweeptable=self.sweeptable)
        target_controller = TargetController(tsp=self.tsp, sweeptable=self.sweeptable)
        checkboard_controller = CheckBoardController(cbp=self.cbp, sweeptable=self.sweeptable)
        self.add_controller(None,None,dt_controller)
        self.add_controller(None,None,save_params_controller)
        self.add_controller(None,None,target_controller)
        self.add_controller(None,None,checkboard_controller)
    
    def remove_stimulus_controllers(self):
        pass
