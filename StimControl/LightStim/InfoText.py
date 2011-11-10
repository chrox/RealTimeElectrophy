# 
#
# Copyright (C) 2010-2011 Huang Xin
#
#
# Distributed under the terms of the BSD License.
# See LICENSE.TXT that came with this file.

import VisionEgg.Core
import VisionEgg.ParameterTypes as ve_types

import VisionEgg.GL as gl # get all OpenGL stuff in one namespace

try:
    import OpenGL.GLUT as glut
    have_glut = True
except:
    have_glut = False

class GlutTextBase(VisionEgg.Core.Stimulus):
    """DEPRECATED. Base class: don't instantiate this class directly.

    Base class that defines the common interface between the
    other glut-based text stimuli.

    Parameters
    ==========
    color     -- (AnyOf(Sequence3 of Real or Sequence4 of Real))
                 Default: (1.0, 1.0, 1.0)
    lowerleft -- (Sequence2 of Real)
                 Default: (320, 240)
    on        -- (Boolean)
                 Default: True
    text      -- (String)
                 Default: the string to display
    """

    parameters_and_defaults = {
        'on':(True,
              ve_types.Boolean),
        'color':((1.0,1.0,1.0),
                 ve_types.AnyOf(ve_types.Sequence3(ve_types.Real),
                                ve_types.Sequence4(ve_types.Real))),
        'lowerleft':((320,240),
                     ve_types.Sequence2(ve_types.Real)),
        'text':('the string to display',
                ve_types.String)}

    def __init__(self,**kw):
        VisionEgg.Core.Stimulus.__init__(self,**kw)

class BitmapText(GlutTextBase):
    """DEPRECATED. Bitmap fonts from GLUT.

    Parameters
    ==========
    color     -- (AnyOf(Sequence3 of Real or Sequence4 of Real))
                 Inherited from GlutTextBase
                 Default: (1.0, 1.0, 1.0)
    font      -- (Integer)
                 Default: 5
    lowerleft -- (Sequence2 of Real)
                 Inherited from GlutTextBase
                 Default: (320, 240)
    on        -- (Boolean)
                 Inherited from GlutTextBase
                 Default: True
    text      -- (String)
                 Inherited from GlutTextBase
                 Default: the string to display
    """

#    parameters_and_defaults = {
#        'font':(glut.GLUT_BITMAP_TIMES_ROMAN_24,
#                ve_types.Integer),
#        }

    def __init__(self,**kw):
        GlutTextBase.__init__(self,**kw)
        glut.glutInit()
        
    def draw(self):
        if self.parameters.on:
            gl.glDisable(gl.GL_TEXTURE_2D)
            gl.glDisable(gl.GL_BLEND)
            gl.glDisable(gl.GL_DEPTH_TEST)

            gl.glMatrixMode(gl.GL_MODELVIEW)
            gl.glPushMatrix()
            gl.glTranslate(self.parameters.lowerleft[0],self.parameters.lowerleft[1],0.0)

            c = self.parameters.color

            if len(c)==3:
                gl.glColor3f(*c)
            elif len(c)==4:
                gl.glColor4f(*c)
            gl.glDisable(gl.GL_TEXTURE_2D)

            gl.glRasterPos3f(0.0,0.0,0.0)
            for char in self.parameters.text:
                glut.glutBitmapCharacter(glut.GLUT_BITMAP_8_BY_13,ord(char))
            gl.glPopMatrix()