# WhiteNoise stimulus
#
# Copyright (C) 2010-2011 Huang Xin
#
#
# Distributed under the terms of the BSD License.
# See LICENSE.TXT that came with this file.

from __future__ import division
import numpy as np
np.seterr(all='raise') # raise all numpy errors (like 1/0), don't just warn

import pickle
import logging
from VisionEgg.MoreStimuli import Target2D
from VisionEgg.Core import FixationSpot

from Core import Stimulus
from LightUtil import TimeFormat
from SweepController import SweepTableStimulusController,SaveParamsController,DTSweepTableController
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

class WhiteNoiseSweepStampController(DTSweepTableController):
    """Digital output for triggering and frame timing verification 
    """
    def __init__(self,*args,**kwargs):
        super(WhiteNoiseSweepStampController, self).__init__(*args,**kwargs)
    def during_go_eval(self):
        index = self.next_index()
        if index == None: return
        """ 
            16-bits stimuli representation code will be posted to DT port
                001 1 111111 111111
                 |  |    |      |-----x index  
                 |  |    |------------y index
                 |  |-----------------contrast
                 |--------------------reserved 
        """
        postval = (1<<13) + (self.st.contrast[index]<<12) + (self.st.posindex[index][1]<<6) + self.st.posindex[index][0]
        self.post_stamp(postval)
        
class TargetController(SweepTableStimulusController):
    """Target noise in the white noise stimulus"""
    def __init__(self,*args,**kwargs):
        super(TargetController, self).__init__(*args,**kwargs)
        self.tsp = self.stimulus.tsp
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
        xposdeg = self.stimulus.xorigDeg - self.stimulus.gridsize/2 + \
                    self.st.posindex[index][1]*self.stimulus.gridcell[0]+self.stimulus.barsize[0]/2
        yposdeg = self.stimulus.yorigDeg + self.stimulus.gridsize/2 - \
                    self.st.posindex[index][0]*self.stimulus.gridcell[1]-self.stimulus.barsize[1]/2
        """Update target contrast, given sweep table index index"""
        if self.st.contrast[index] == 0:
            self.tsp.color = (0.0, 0.0, 0.0, 1.0)
        else:
            self.tsp.color = (1.0, 1.0, 1.0, 1.0)
        self.tsp.position = (self.viewport.xorig + self.viewport.deg2pix(xposdeg),
                             self.viewport.yorig + self.viewport.deg2pix(yposdeg))

class CheckBoardController(SweepTableStimulusController):
    def __init__(self,*args,**kwargs):
        super(CheckBoardController, self).__init__(*args,**kwargs)
        self.cbp = self.stimulus.cbp
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
    def __init__(self,stimulus):
        super(SavePosParamsController, self).__init__(stimulus,file_prefix='whitenoise')
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

class WhiteNoise(Stimulus):
    """WhiteNoise stimulus"""
    def __init__(self, **kwargs):
        super(WhiteNoise, self).__init__(**kwargs)
        self.name = 'whitenoise'
        self.savedpost = []

        self.load_preference(0)
        self.make_stimuli()
        self.register_controllers()
        
    def make_stimuli(self):
        size = self.viewport.get_size()
        self.background = Target2D(position=(size[0]/2, size[1]/2),
                                   anchor='center',
                                   size=size,
                                   on=True)

        self.bgp = self.background.parameters # synonym
        #set background color before real sweep
        bgb = self.sweeptable.static.bgbrightness # get it for sweep table index 0
        self.bgp.color = bgb, bgb, bgb, 1.0 # set bg colour, do this now so it's correct for the pre-exp delay
        
        position = (self.viewport.xorig+self.viewport.deg2pix(self.xorigDeg), \
                    self.viewport.yorig+self.viewport.deg2pix(self.yorigDeg))
        
        self.gridcell = (self.gridsize/self.sweeptable.static.griddim[0],
                         self.gridsize/self.sweeptable.static.griddim[1])
        
        self.barsize = (self.gridcell[0]*self.sweeptable.static.widthmag,
                        self.gridcell[1]*self.sweeptable.static.heightmag)
        
        self.targetstimulus = Target2D(position = position,
                                       color = (0.0, 0.0, 0.0, 1.0),
                                       orientation = self.ori,
                                       anchor = 'center',
                                       size = (self.viewport.deg2pix(self.barsize[0]), 
                                               self.viewport.deg2pix(self.barsize[1])),
                                       on = False)
        self.fixationspot = FixationSpot(position=(self.viewport.xorig, self.viewport.yorig),
                                                 anchor='center',
                                                 color=(1.0, 0.0, 0.0, 1.0),
                                                 size=(50, 50),
                                                 on = False)
        
        self.checkboard = CheckBoard(position = position,
                                     orientation = 0.0,
                                     anchor='center',
                                     size = (self.viewport.deg2pix(self.gridsize), \
                                             self.viewport.deg2pix(self.gridsize)),
                                     grid = self.sweeptable.static.griddim,
                                     drawline = False,
                                     cellcolor = self.sweeptable.static.cbcolormap,
                                     on = self.sweeptable.static.checkbdon)

        self.tsp = self.targetstimulus.parameters # synonym
        self.fsp = self.fixationspot.parameters
        self.cbp = self.checkboard.parameters
        # last entry will be topmost layer in viewport
        self.stimuli = (self.background, self.checkboard, self.targetstimulus, self.fixationspot)
    
    def register_controllers(self):
        logger = logging.getLogger('LightStim.WhiteNoise')
        self.controllers.append(WhiteNoiseSweepStampController(self))
        self.controllers.append(SavePosParamsController(self))
        self.controllers.append(TargetController(self))
        self.controllers.append(CheckBoardController(self))
        if isinstance(self.controllers[-1],SweepTableStimulusController):
            controller = self.controllers[-1]
            estimated_duration = controller.get_estimated_duration()
            sweep_num = controller.get_sweeps_num()
            logger.info('Estimated stimulus duration: %s for %d sweeps.' %(str(TimeFormat(estimated_duration)), sweep_num))
        
    def load_preference(self, index):
        name = self.viewport.name
        info = self.name + str(index) + ' in ' + name + ' viewport.'
        logger = logging.getLogger('LightStim.WhiteNoise')
        if self.viewport.get_name() != 'control':   # make control viewport like a passive viewport
            logger.info('Load preference for ' + info)
        self.defalut_preference = {'xorigDeg':0.0,
                                   'yorigDeg':0.0,
                                   'widthDeg':3.0,
                                   'barheightDeg':1.0,
                                   'ori': 0.0}
        try:
            with open('Manbar_preference.pkl','rb') as pkl_input:
                preferences_dict = pickle.load(pkl_input)
                self.defalut_preference.update(preferences_dict[name][index])
                self.preference = self.defalut_preference
        except:
            if self.viewport.get_name() != 'control':
                logger.warning('Cannot load preference for ' + info + ' Use the default preference.')
            self.preference = self.defalut_preference

        self.xorigDeg = self.preference['xorigDeg']
        self.yorigDeg = self.preference['yorigDeg']
        self.gridsize = self.preference['widthDeg']
        self.ori = self.preference['ori']