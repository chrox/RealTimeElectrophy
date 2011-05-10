#!/usr/bin/env python

import VisionEgg
VisionEgg.start_default_logging(); VisionEgg.watch_exceptions()

import numpy as np
import VisionEgg.GL as gl # get all OpenGL stuff in one namespace
from VisionEgg.Core import ModelView,Viewport
from VisionEgg.FlowControl import Presentation
from VisionEgg.Gratings import SinGrating2D


class MirrorView(ModelView):
    def __init__(self):
        # XXX right now this is done in OpenGL, we should do it ourselves
        gl.glMatrixMode(gl.GL_MODELVIEW) # Set OpenGL matrix state to modify the projection matrix
        gl.glPushMatrix()
        gl.glLoadIdentity() # Clear the projection matrix
        gl.glScalef (1., 0.5, 1.)
        matrix = gl.glGetFloatv(gl.GL_MODELVIEW_MATRIX)
        gl.glPopMatrix()
        if matrix is None:
            # OpenGL wasn't started
            raise RuntimeError("OpenGL matrix operations can only take place once OpenGL context started.")
        matrix = np.asarray(matrix) # make sure it's numpy array
        ModelView.__init__(self,**{'matrix':matrix})

# Normal stuff (from grating demo):
screen = VisionEgg.Core.get_default_screen()
grating = SinGrating2D(position         = ( screen.size[0]/2.0, screen.size[1]/2.0 ),
                        anchor           = 'center',
                        size             = ( 300.0 , 300.0 ),
                        spatial_freq     = 10.0 / screen.size[0], # units of cycles/pixel
                        temporal_freq_hz = 5.0,
                        orientation      = 45.0 )

mirror_view = MirrorView()
viewport = Viewport( screen=screen, camera_matrix=mirror_view, stimuli=[grating] )
p = Presentation(go_duration=(5.0,'seconds'),viewports=[viewport])

# Go!
p.go()
