"""Modified from dimstim Movie experiment"""

from __future__ import division

import numpy as np
np.seterr(all='raise') # raise all numpy errors (like 1/0), don't just warn
import pygame
import OpenGL.GL as gl

import VisionEgg
from VisionEgg.MoreStimuli import Target2D
from VisionEgg.Core import FixationSpot

from LightStim import deg2pix,sec2intvsync
from LightStim.FrameControl import FrameControl,DT
from LightStim.SweepStamp import DTBOARDINSTALLED,MAXPOSTABLEINT,SWEEP
from LightStim.stimuli.CheckBoard import CheckBoard


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

class WhiteNoise(FrameControl):
    """WhiteNoise experiment"""
    def __init__(self, *args, **kwargs):
        super(WhiteNoise, self).__init__(*args, **kwargs)
        if 'fixationspotDeg' not in self.dynamic.keys(): # most WhiteNoise scripts won't bother specifying it
            self.dynamic.fixationspotDeg = False # default to off
        self.receptive_field = RFModel()
        self.savedpost = []

    def createstimuli(self):
        """Creates the VisionEgg stimuli objects for this Experiment subclass"""
        super(WhiteNoise, self).createstimuli()
        
        position = (self.xorig+deg2pix(self.static.center[0]),self.yorig+deg2pix(self.static.center[1]))
        
        self.targetstimulus = Target2D(position = position, # init to orig
                                       color = (0.0, 0.0, 0.0, 1.0),
                                       orientation = self.static.orientation,
                                       anchor = 'center',
                                       size = (deg2pix(self.static.widthDeg), deg2pix(self.static.heightDeg)),
                                       on = False)
        self.fixationspot = FixationSpot(position=(self.xorig, self.yorig),
                                                 anchor='center',
                                                 color=(1.0, 0.0, 0.0, 1.0),
                                                 size=(50, 50),
                                                 on = False)
        
        self.checkboard = CheckBoard(position = position,
                                     orientation = 0.0,
                                     anchor='center',
                                     size = (deg2pix(self.static.size[0]),deg2pix(self.static.size[1])),
                                     grid = self.static.griddim,
                                     drawline = False,
                                     cellcolor = self.static.cbcolormap,
                                     on = self.static.checkbdon)

        self.tsp = self.targetstimulus.parameters # synonym
        self.fsp = self.fixationspot.parameters
        self.cbp = self.checkboard.parameters
        # last entry will be topmost layer in viewport
        self.stimuli = (self.background, self.checkboard, self.targetstimulus, self.fixationspot)

    def updateparams(self, i):
        """Updates stimulus parameters, given sweep table index i"""
        if i == None: # do a blank sweep
            self.tsp.on = False # turn off the stimulus, leave all other parameters unchanged
            self.postval = MAXPOSTABLEINT # posted to DT port to indicate a blank sweep
            self.nvsyncs = sec2intvsync(self.blanksweeps.sec) # this many vsyncs for this sweep
            self.npostvsyncs = 0 # this many post-sweep vsyncs for this sweep, blank sweeps have no post-sweep delay
        else: # not a blank sweep
            self.tsp.on = True # ensure texture stimulus is on
            """ 
            16-bits stimuli representation code will be posted to DT port
                000 1 111111 111111
                 |  |    |      |-----y index  
                 |  |    |------------x index
                 |  |-----------------contrast
                 |--------------------reserved 
            """
            self.postval = (self.st.contrast[i]<<12) + (self.st.posindex[i][0]<<6) + self.st.posindex[i][1]
            self.nvsyncs = sec2intvsync(self.st.sweepSec[i]) # vsyncs for one sweep
            self.npostvsyncs = sec2intvsync(self.st.postsweepSec[i]) # post-sweep vsyncs for one sweep

            # Update targetstimulus position
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
            #print self.st.posindex[i][0], self.st.posindex[i][1]
            xposdeg = self.static.center[0]-self.static.size[0]/2 + \
                        self.st.posindex[i][1]*self.static.gridcell[0]+self.static.widthDeg/2
            yposdeg = self.static.center[1]+self.static.size[1]/2 - \
                        self.st.posindex[i][0]*self.static.gridcell[1]-self.static.heightDeg/2
            self.tsp.position = self.xorig+deg2pix(xposdeg),self.yorig+deg2pix(yposdeg)
            if self.st.contrast[i] == 0:
                self.tsp.color = (0.0, 0.0, 0.0, 1.0)
            else:
                self.tsp.color = (1.0, 1.0, 1.0, 1.0)
            # Update background parameters
            self.bgp.color = self.st.bgbrightness[i], self.st.bgbrightness[i], self.st.bgbrightness[i], 1.0

            # Update fixationspot
            self.fsp.position = self.xorig+deg2pix(self.st.fsxposDeg[i]), self.yorig+deg2pix(self.st.fsyposDeg[i])
            self.fsp.on = bool(self.st.fixationspotOn[i])
            self.fsp.size = deg2pix(self.st.fixationspotDeg[i]), deg2pix(self.st.fixationspotDeg[i])
            
            # update checkboard color index
            xindex, yindex = self.st.posindex[i][0], self.st.posindex[i][1]
            m, n = self.static.griddim[0], self.static.griddim[1]
            xpos = xindex/m*8 - 4
            ypos = 4 - yindex/n*8
#            if self.st.contrast[i] == 0:
#                contrast = -1
#            else:
#                contrast = 1
            color_increment = self.receptive_field.response(xpos,ypos,self.st.contrast[i])
            self.cbp.colorindex[self.st.posindex[i][0],self.st.posindex[i][1]] += color_increment
            # hopefully, calcs didn't take much time. If so, then sync up to the next vsync before starting the sweep
    
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
            
    def sweep(self):
        """Run the main stimulus loop for this Experiment subclass
        make screen.get_framebuffer_as_array for all Experiment classes more easily
        available from outside of dimstim (for analysis in neuropy) so you can
        grab the frame buffer data at any timepoint (and use for, say, revcorr)
        """
        for ii, i in enumerate(self.sweeptable.i):
            self.updateparams(i)
            # Set sweep bit high, do the sweep
            if DTBOARDINSTALLED: DT.setBitsNoDelay(SWEEP) # set sweep bit high, no delay
            for dummy_vsynci in xrange(self.nvsyncs): # nvsyncs depends on if this is a blank sweep or not
                for event in pygame.event.get(): # for all events in the event queue
                    if event.type == pygame.locals.KEYDOWN:
                        if event.key == pygame.locals.K_ESCAPE:
                            self.quit = True
                        if event.key == pygame.locals.K_PAUSE:
                            self.pause = not self.pause # toggle pause
                            self.paused = True # remember that a pause happened
                if self.quit:
                    break # out of vsync loop
                if DTBOARDINSTALLED: DT.postInt16NoDelay(self.postval) # post value to port, no delay
                self.savedpost.append(self.postval)
                self.screen.clear()
                self.viewport.draw()
                VisionEgg.Core.swap_buffers() # returns immediately
                gl.glFlush() # waits for next vsync pulse from video card
                #self.vsynctimer.tick()
                #self.nvsyncsdisplayed += 1 # increment

            # Sweep's done, turn off the texture stimulus, do the postsweep delay, clear sweep bit low
            self.tsp.on = False
            self.staticscreen(nvsyncs=self.npostvsyncs) # clears sweep bit low when done

            if self.quit:
                self.ii = ii + 1 - 1 # dec for accurate count of nsweeps successfully displayed
                break # out of sweep loop

        self.ii = ii + 1 # nsweeps successfully displayed
        self.checkboard.save()
        
