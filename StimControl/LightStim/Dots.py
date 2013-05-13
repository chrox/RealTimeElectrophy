# The Vision Egg: Dots
#
# Copyright (C) 2001-2003 Andrew Straw.
# Copyright (C) 2005,2008 California Institute of Technology
#
# URL: <http://www.visionegg.org/>
#
# Distributed under the terms of the GNU Lesser General Public License
# (LGPL). See LICENSE.TXT that came with this file.

"""
Random dot stimuli.

"""

####################################################################
#
#        Import all the necessary packages
#
####################################################################
from __future__ import division
import numpy as np
import Image, ImageDraw

import VisionEgg.ParameterTypes as ve_types
from VisionEgg.Textures import TextureStimulusBaseClass, TextureStimulus, Texture, Mask2D

import VisionEgg.GL as gl # get all OpenGL stuff in one namespace

class DiscMask(Mask2D):
    # All of these parameters are constant -- if you need a new mask, create a new instance
    parameters_and_defaults = {
        'shift':((50,50),
                    ve_types.Sequence2(ve_types.Real)),
        'texture':(None,
                   ve_types.Instance(Texture),
                   "source of texture data"),
        }

    def draw_masked_quad(self,lt,rt,bt,tt,le,re,be,te,depth):
        # The *t parameters are the texture coordinates. The *e
        # parameters are the eye coordinates for the vertices of the
        # quad.
        shift = self.parameters.shift
        texture = self.parameters.texture
        delta_lr = shift[0]/texture.size[0]*(rt-lt)
        delta_bt = shift[0]/texture.size[0]*(tt-bt)
        lt = lt + delta_lr
        rt = rt + delta_lr
        bt = bt + delta_bt
        tt = tt + delta_bt
        le = le + shift[0]
        re = re + shift[0]
        be = be + shift[1]
        te = te + shift[1]
        v1 = (le,be,depth)
        v2 = (re,be,depth)
        v3 = (re,te,depth)
        v4 = (le,te,depth)
        self.draw_masked_quad_3d(lt,rt,bt,tt,v1,v2,v3,v4)

class TextureDots(TextureStimulusBaseClass):
    """Random Dots drawn on Texture."""

    parameters_and_defaults = {
        'on':(True,
              ve_types.Boolean),
        'position':((320,240),
                    ve_types.Sequence2(ve_types.Real)),
        'mask_on':(False,
              ve_types.Boolean),
        'mask_position':((0,0),
                    ve_types.Sequence2(ve_types.Real)),
        }
    constant_parameters_and_defaults = {
        'size' : ((256,256),
                ve_types.Sequence2(ve_types.Real)),
        'mask_diameter' : (50,
                       ve_types.Real),
        'bgcolor' : ((0.5,0.5,0.5),
                   ve_types.Sequence3(ve_types.Real)),
        'seed' : ( 0,
                       ve_types.Integer ),
        'num_dots' : ( 500,
                       ve_types.UnsignedInteger ),
        'dot_size' : (4.0, # pixels
                      ve_types.Real),
        'dot_color' : ((1.0,1.0,1.0),
                   ve_types.Sequence3(ve_types.Real)),
        }

    __slots__ = (
        'texture_stimulus',
        )

    def __init__(self,**kw):
        TextureStimulusBaseClass.__init__(self,**kw)
        size = self.constant_parameters.size
        bgcolor = self.constant_parameters.bgcolor
        img_color = (int(255*bgcolor[0]),int(255*bgcolor[1]),int(255*bgcolor[2]))
        texels = Image.new("RGBX",size,img_color)
        texels_draw = ImageDraw.Draw(texels)
        
        num_dots = self.constant_parameters.num_dots
        dot_size = self.constant_parameters.dot_size
        dot_color = self.constant_parameters.dot_color
        fill_color = (int(255*dot_color[0]),int(255*dot_color[1]),int(255*dot_color[2]))
        np.random.seed(self.constant_parameters.seed)
        xs = np.random.uniform(0, 1, num_dots) * size[0]
        np.random.seed(self.constant_parameters.seed+1)
        ys = np.random.uniform(0, 1, num_dots) * size[1]
        for i in xrange(num_dots):
            texels_draw.rectangle((xs[i], ys[i], 
                                   xs[i]+dot_size, ys[i]+dot_size), 
                                   fill=fill_color)
        self.texture = Texture(texels)
        nmasksamples = 256
        radius = self.constant_parameters.mask_diameter / 2
        samplesperpix = nmasksamples / self.texture.size[0]
        self.mask = DiscMask(function="circle",
                             texture = self.texture,
                             radius_parameter=radius*samplesperpix,
                             num_samples=(256,256))
        self.texture_stimulus = TextureStimulus( texture = self.texture,
                                                 position = self.parameters.position,
                                                 mask = self.mask,
                                                 anchor = 'center',
                                                 size = size,
                                                 internal_format = gl.GL_RGBA,
                                                 mipmaps_enabled = False,
                                                 texture_min_filter = gl.GL_NEAREST,
                                                 texture_mag_filter = gl.GL_NEAREST,
                                                 )
    def draw(self):
        contained = self.texture_stimulus.parameters #shorthand
        my = self.parameters #shorthand
        contained.position = my.position
        contained.size = self.constant_parameters.size
        contained.on = my.on
        if my.mask_on:
            contained.mask = self.mask
        else:
            contained.mask = None
        self.mask.parameters.shift = my.mask_position
        self.texture_stimulus.draw()
        