#!/usr/bin/env python

import VisionEgg
VisionEgg.start_default_logging(); VisionEgg.watch_exceptions()

import numpy as np
import VisionEgg.GL as gl # get all OpenGL stuff in one namespace
from VisionEgg.FlowControl import Presentation
from VisionEgg.Gratings import SinGrating2D

from VisionEgg.Core import Viewport
class HorizontalMirrorView(VisionEgg.Core.ModelView):
    def __init__(self,viewport_with=800):
        gl.glMatrixMode(gl.GL_MODELVIEW) # Set OpenGL matrix state to modify the modelview matrix
        gl.glPushMatrix()
        gl.glLoadIdentity() # Clear the modelview matrix
        gl.glTranslate(viewport_with,0,0)
        gl.glRotate(180, 0, 1, 0)
        matrix = gl.glGetFloatv(gl.GL_MODELVIEW_MATRIX)
        gl.glPopMatrix()
        if matrix is None:
            # OpenGL wasn't started
            raise RuntimeError("OpenGL matrix operations can only take place once OpenGL context started.")
        matrix = np.asarray(matrix) # make sure it's numpy array
        VisionEgg.Core.ModelView.__init__(self,**{'matrix':matrix})

# Normal stuff (from grating demo):
screen = VisionEgg.Core.get_default_screen()
grating = SinGrating2D(position         = ( screen.size[0]/2.0, screen.size[1]/2.0 ),
                        anchor           = 'center',
                        size             = ( 400.0 , 300.0 ),
                        spatial_freq     = 10.0 / screen.size[0], # units of cycles/pixel
                        temporal_freq_hz = 5.0,
                        orientation      = 45.0 )

viewport = Viewport( screen=screen, stimuli=[grating])
viewport.parameters.camera_matrix = HorizontalMirrorView(offset=screen.size[0])
p = Presentation(go_duration=(5.0,'seconds'),viewports=[viewport])

# Go!
p.go()
