# WhiteNoise stimulus
#
# Copyright (C) 2010-2011 Huang Xin
#
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
from LightData import dictattr
from SweepController import SweepSequeStimulusController,SaveParamsController,DTSweepSequeController
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

class WhiteNoiseSweepStampController(DTSweepSequeController):
    """Digital output for triggering and frame timing verification 
    """
    def __init__(self,*args,**kwargs):
        super(WhiteNoiseSweepStampController, self).__init__(*args,**kwargs)
    def during_go_eval(self):
        param = self.next_param()
        if param == None: return
        """ 
            16-bits stimuli representation code will be posted to DT port
                001 1 111111 111111
                 |  |    |      |-----x index  
                 |  |    |------------y index
                 |  |-----------------contrast
                 |--------------------reserved 
        """
        x_index, y_index, contrast = param
        postval = (1<<13) + (contrast<<12) + (y_index<<6) + x_index
        self.post_stamp(postval)
        
class TargetController(SweepSequeStimulusController):
    """Target noise in the white noise stimulus"""
    def __init__(self,*args,**kwargs):
        super(TargetController, self).__init__(*args,**kwargs)
        self.tsp = self.stimulus.tsp
    def during_go_eval(self):
        param = self.next_param()
        """Whether draw the target""" 
        if param == None:
            self.tsp.on = False
            return
        else:
            self.tsp.on = True
        """Update target position, given sweep Seque index index"""
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
        x_index, y_index, contrast = param
        xposdeg = self.stimulus.parameters.xorigDeg - self.stimulus.parameters.gridsize/2 + \
                    y_index*self.stimulus.gridcell[0]+self.stimulus.barsize[0]/2
        yposdeg = self.stimulus.parameters.yorigDeg + self.stimulus.parameters.gridsize/2 - \
                    x_index*self.stimulus.gridcell[1]-self.stimulus.barsize[1]/2
        """Update target contrast, given sweep Seque index index"""
        if contrast == 0:
            self.tsp.color = (0.0, 0.0, 0.0, 1.0)
        else:
            self.tsp.color = (1.0, 1.0, 1.0, 1.0)
        self.tsp.position = (self.viewport.xorig + self.viewport.deg2pix(xposdeg),
                             self.viewport.yorig + self.viewport.deg2pix(yposdeg))

class CheckBoardController(SweepSequeStimulusController):
    def __init__(self,*args,**kwargs):
        super(CheckBoardController, self).__init__(*args,**kwargs)
        self.cbp = self.stimulus.cbp
        self.receptive_field = RFModel()
    def during_go_eval(self): 
        """update checkboard color index"""
        param = self.next_param()
        if param == None: return
        x_index, y_index, contrast = param
        m, n = self.stimulus.parameters.griddim[0], self.stimulus.parameters.griddim[1]
        xpos = x_index/m*8 - 4
        ypos = 4 - y_index/n*8
        color_increment = self.receptive_field.response(xpos,ypos,contrast)
        self.cbp.colorindex[x_index,y_index] += color_increment

class SavePosParamsController(SaveParamsController):
    """ Use Every_Frame evaluation controller in case of real time sweep Seque modification
    """
    def __init__(self,stimulus):
        super(SavePosParamsController, self).__init__(stimulus,file_prefix='whitenoise')
        self.file_header = 'Sparse White Noise parameters for every sweep.\n contrast xindex  yindex   postval\n'
        self.file_saved = False
    def during_go_eval(self):
        param = self.next_param()
        if param == None: return
        x_index, y_index, contrast = param
        postval = (contrast<<12) + (x_index<<6) + y_index
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
    def __init__(self, params, sweepseq, trigger=True, **kwargs):
        super(WhiteNoise, self).__init__(**kwargs)
        self.name = 'whitenoise'
        self.savedpost = []
        self.parameters = dictattr()
        self.load_params(self.parameters)
        self.set_parameters(self.parameters, params)
        self.sweepseq = sweepseq
        self.trigger = trigger
        
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
        bgb = self.parameters.bgbrightness # get it for sweep Seque index 0
        self.bgp.color = bgb, bgb, bgb, 1.0 # set bg colour, do this now so it's correct for the pre-exp delay
        
        position = (self.viewport.xorig+self.viewport.deg2pix(self.parameters.xorigDeg), \
                    self.viewport.yorig+self.viewport.deg2pix(self.parameters.yorigDeg))
        
        self.gridcell = (self.parameters.gridsize/self.parameters.griddim[0],
                         self.parameters.gridsize/self.parameters.griddim[1])
        
        self.barsize = (self.gridcell[0]*self.parameters.widthmag,
                        self.gridcell[1]*self.parameters.heightmag)
        
        self.targetstimulus = Target2D(position = position,
                                       color = (0.0, 0.0, 0.0, 1.0),
                                       orientation = self.parameters.ori,
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
                                     size = (self.viewport.deg2pix(self.parameters.gridsize), \
                                             self.viewport.deg2pix(self.parameters.gridsize)),
                                     grid = self.parameters.griddim,
                                     drawline = False,
                                     cellcolor = self.parameters.cbcolormap,
                                     on = self.parameters.checkbdon)

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
        if isinstance(self.controllers[-1],SweepSequeStimulusController):
            controller = self.controllers[-1]
            estimated_duration = controller.get_estimated_duration()
            sweep_num = controller.get_sweeps_num()
            logger.info('Estimated stimulus duration: %s for %d sweeps.' %(str(TimeFormat(estimated_duration)), sweep_num))
        
    def load_params(self, parameters, index=0):
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
            with open('stimulus_params.pkl','rb') as pkl_input:
                preferences_dict = pickle.load(pkl_input)
                self.defalut_preference.update(preferences_dict[name][index])
                self.preference = self.defalut_preference
        except:
            if self.viewport.get_name() != 'control':
                logger.warning('Cannot load preference for ' + info + ' Use the default preference.')
            self.preference = self.defalut_preference

        parameters.xorigDeg = self.preference['xorigDeg']
        parameters.yorigDeg = self.preference['yorigDeg']
        parameters.gridsize = self.preference['widthDeg']
        parameters.ori = self.preference['ori']