# CheckBoard stimulus
#
# Copyright (C) 2010-2011 Huang Xin
# 
#
# Distributed under the terms of the GNU Lesser General Public License
# (LGPL). See LICENSE.TXT that came with this file.

from __future__ import division

import VisionEgg
import VisionEgg.GL as gl # get all OpenGL stuff in one namespace
from VisionEgg.Core import Stimulus
import VisionEgg.ParameterTypes as ve_types
import numpy as np

def colormap(value, color='jet'):
    def clamp(x): return max(0.0, min(x, 1.0))
    if color == 'jet':
        #code from Matt Stine's Blog
        fourValue = 4 * value;
        red   = min(fourValue - 1.5, -fourValue + 4.5)
        green = min(fourValue - 0.5, -fourValue + 3.5)
        blue  = min(fourValue + 0.5, -fourValue + 2.5)
        return map(clamp,(red,green,blue))
    if color == 'gbr':
        #green black red
        red   = 2 * value - 1
        green = 1 - 2 * value
        blue  = 0.0
        return map(clamp,(red,green,blue))
        #return map(lambda x: max(0.0,min(x, 1.0)),(red,green,blue))
    if color == 'bbr':
        #blue black red
        red   = 2 * value - 1
        green = 0.0
        blue  = 1 - 2 * value
        return map(clamp,(red,green,blue))
    if color == 'ggr':
        #green gray red
        red   = max(0.5,value)
        green = max(0.5,1 - value)
        blue  = 1 - (red + green)/2.0
        red   = red + 0.5 - green
        green = green + 0.5 - red
        return map(clamp,(red,green,blue))
    else:
        return (0.0,0.0,0.0)
    
class CheckBoard(Stimulus):
    """A checkboard stimulus, typically used as a aux stimulus for whitenoise.

    Parameters
    ==========
    anchor   -- how position parameter is used (String)
                Default: center
    color    -- color (256 jet colormap )
                Default: 0(gray)
    on       -- draw? (Boolean)
                Default: True
    position -- position in eye coordinates (AnyOf(Sequence2 of Real or Sequence3 of Real or Sequence4 of Real))
                Default: (320.0, 240.0)
    size     -- size in eye coordinates (Sequence2 of Real)
                Default: (4.0, 4.0)
    """

    parameters_and_defaults = VisionEgg.ParameterDefinition({
        'on':(True,
              ve_types.Boolean,
              'draw?'),
        'bgcolor':((0.5,0.5,0.5),
                 ve_types.AnyOf(ve_types.Sequence3(ve_types.Real),
                                ve_types.Sequence4(ve_types.Real)),
                 'backgroud color'),
        'linecolor':((0.5,0.0,0.0),
                 ve_types.AnyOf(ve_types.Sequence3(ve_types.Real),
                                ve_types.Sequence4(ve_types.Real)),
                 'grid line color'),
        'cellcolor':('gbr',
                     ve_types.String,
                     'color map for the range [0.0,1.0]'),
        'colorindex':(None,
                 ve_types.Sequence(ve_types.Integer),
                 'color index in jet colormap'),
        'drawline':(False,
                    ve_types.Boolean,
                    'draw line?'),
        'orientation':(0.0,
                       ve_types.Real),
        'position' : ( ( 320.0, 240.0 ), # in eye coordinates
                       ve_types.AnyOf(ve_types.Sequence2(ve_types.Real),
                                      ve_types.Sequence3(ve_types.Real),
                                      ve_types.Sequence4(ve_types.Real)),
                       'position in eye coordinates'),
        'anchor' : ('center',
                    ve_types.String,
                    'how position parameter is used'),
        'size':((100.0,100.0), # horiz and vertical size
                ve_types.Sequence2(ve_types.Real),
                'size in eye coordinates'),
        'grid':((8,8),# grid dimension of the checkboard
                ve_types.Sequence2(ve_types.Integer),
                'grid dimension'),
        'center' : (None,  # DEPRECATED -- don't use
                    ve_types.Sequence2(ve_types.Real),
                    'position in eye coordinates',
                    VisionEgg.ParameterDefinition.DEPRECATED),
        })

    def __init__(self,**kw):
        Stimulus.__init__(self,**kw)
        self.parameters.colorindex = np.zeros(self.parameters.grid)
        self.parameters.colorindex.fill(0.5)
    def draw(self):
        p = self.parameters # shorthand
        if p.center is not None:
            p.anchor = 'center'
            p.position = p.center[0], p.center[1] # copy values (don't copy ref to tuple)
        if p.on:
            # calculate center
            center = VisionEgg._get_center(p.position,p.anchor,p.size)
            gl.glMatrixMode(gl.GL_MODELVIEW)
            gl.glPushMatrix()
            gl.glTranslate(center[0],center[1],0.0)
            gl.glRotate(p.orientation,0.0,0.0,1.0)

            if len(p.bgcolor)==3:
                gl.glColor3f(*p.bgcolor)
            elif len(p.bgcolor)==4:
                gl.glColor4f(*p.bgcolor)
            gl.glDisable(gl.GL_DEPTH_TEST)
            gl.glDisable(gl.GL_TEXTURE_2D)
            gl.glBlendFunc(gl.GL_SRC_ALPHA,gl.GL_ONE_MINUS_SRC_ALPHA)
            gl.glEnable(gl.GL_BLEND)

            w = p.size[0]/2.0 #grid half-size
            h = p.size[1]/2.0
            m = p.size[0]/p.grid[0] #cell size
            n = p.size[1]/p.grid[1]
            i = range(p.grid[0]) #grid index
            j = range(p.grid[1])
            #draw colorful cell
#           vertices_list = [((-w+column*m, h-(row+1)*n, 0.0),(-w+column*m, h-row*n, 0.0),\
#                         (-w+(column+1)*m, h-row*n, 0.0),(-w+(column+1)*m, h-row*n, 0.0))\
#                         for column in j for row in i]
            vertices_list = [((-w+column*m, h-(row+1)*n, 0.0),(-w+column*m, h-row*n, 0.0),\
                              (-w+(column+1)*m, h-row*n, 0.0),(-w+(column+1)*m, h-(row+1)*n, 0.0))\
                         for column in j for row in i]
            colors_list = [colormap(p.colorindex[row,column],color=p.cellcolor)*4 for column in j for row in i]
            #flattening the vertices and colors
            vertices_flat = [num for tuple in vertices_list for vertex in tuple for num in vertex]
            colors_flat = [num for tuple in colors_list for num in tuple]
            vertices = np.array(vertices_flat)
            colors = np.array(colors_flat)
            vertices.shape = (-1, 3)
            colors.shape   = (-1, 3)
            gl.glVertexPointerd(vertices)
            gl.glColorPointerd(colors)
            gl.glEnableClientState(gl.GL_VERTEX_ARRAY)
            gl.glEnableClientState(gl.GL_COLOR_ARRAY)
            gl.glDisable(gl.GL_LIGHTING)
            gl.glDrawArrays(gl.GL_QUADS,0,p.grid[0]*p.grid[1]*4)
                        
            #draw grid lines
            if p.drawline:
                if len(p.linecolor) == 3:
                    gl.glColor3f(*p.linecolor)
                elif len(p.linecolor) == 4:
                    gl.glColor4f(*p.linecolor)
                
                row_list = [((-w, h - i * n),(w, h - i * n)) for i in range(p.grid[1] + 1)]
                col_list = [((-w + i * m, h),(-w + i * m, -h)) for i in range(p.grid[0] + 1)]
                ver_row_flat = [num for tuple in row_list for vertex in tuple for num in vertex]
                ver_col_flat = [num for tuple in col_list for vertex in tuple for num in vertex]
                vertices_row = np.array(ver_row_flat)
                vertices_col = np.array(ver_col_flat)
                vertices_row.shape = (-1,2)
                vertices_col.shape = (-1,2)
                
                gl.glEnableClientState(gl.GL_VERTEX_ARRAY)
                gl.glDisableClientState(gl.GL_COLOR_ARRAY)
                gl.glVertexPointerd(vertices_row)
                gl.glDrawArrays(gl.GL_LINES,0,(p.grid[1] + 1)*2)
                gl.glVertexPointerd(vertices_col)
                gl.glDrawArrays(gl.GL_LINES,0,(p.grid[0] + 1)*2)
                
#                gl.glBegin(gl.GL_LINES);
#                for i in range(p.grid[1] + 1):
#                    gl.glVertex2f(-w, h - i * n)
#                    gl.glVertex2f(w, h - i * n)
#                for i in range(p.grid[0] + 1):
#                    gl.glVertex2f(-w + i * m, h)
#                    gl.glVertex2f(-w + i * m, -h)
#                gl.glEnd();
            gl.glPopMatrix()
        
    #save checkboard to file
    def save(self):
        import time,os
        (year,month,day,hour24,min,sec) = time.localtime(time.time())[:6]
        trial_time_str = "%04d%02d%02d_%02d%02d%02d"%(year,month,day,hour24,min,sec)
        dummy_filename = os.path.abspath(os.curdir)+ os.path.sep + 'screenshoot' + \
                   os.path.sep + 'checkboard' + trial_time_str + '.jpg'
        
