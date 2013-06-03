# -*- coding: utf-8 -*-
# Base class for grating stimulus.
#
# Copyright (C) 2010-2013 Huang Xin
#
# See LICENSE.TXT that came with this file.

from __future__ import division
import numpy as np
np.seterr(all='raise')
import logging

import os
import signal
import alsaaudio
from multiprocessing import Process
from pyffmpeg import FFMpegReader, PixelFormats

import pygame
from OpenGL.GL.shaders import compileProgram, compileShader

import VisionEgg.GL as gl
from VisionEgg.Textures import Texture, TextureObject, TextureStimulus
from VisionEgg.MoreStimuli import Target2D

from Core import Stimulus
from SweepController import StimulusController,SweepSequeStimulusController

class ShaderTexture(Texture):
    def __init__(self,contrast=1.0,*args,**kwargs):
        super(ShaderTexture, self).__init__(*args,**kwargs)
        """
        This contrast program comes from atduskgreg's shader example.
        See https://github.com/atduskgreg/Processing-Shader-Examples/
        """
        self.contrast_program = compileProgram(
            compileShader('''
                uniform sampler2D src_tex_unit0;
                uniform float contrast;
                void main() {
                    vec3 color = vec3(texture2D(src_tex_unit0, gl_TexCoord[0].st));
                    const vec3 LumCoeff = vec3(0.2125, 0.7154, 0.0721);
            
                    vec3 AvgLumin = vec3(0.5, 0.5, 0.5);
            
                    vec3 intensity = vec3(dot(color, LumCoeff));
            
                    // could substitute a uniform for this 1. and have variable saturation
                    vec3 satColor = mix(intensity, color, 1.);
                    vec3 conColor = mix(AvgLumin, satColor, contrast);
            
                    gl_FragColor = vec4(conColor, 1);
                }
            ''',gl.GL_FRAGMENT_SHADER))
        self.texture_loc = gl.glGetUniformLocation(self.contrast_program, "src_tex_unit0")
        self.contrast_loc = gl.glGetUniformLocation(self.contrast_program, "contrast")
        self.contrast = contrast
    
    def set_contrast(self, contrast):
        self.contrast = contrast
    
    def update(self):
        # install pixel shader for adjusting texture contrast
        gl.glUseProgram(self.contrast_program)
        gl.glUniform1i(self.texture_loc, 0)
        gl.glUniform1f(self.contrast_loc, self.contrast)

class SurfaceTextureObject(TextureObject):
    def __init__(self,*args,**kwargs):
        super(SurfaceTextureObject, self).__init__(*args,**kwargs)
        self.raw_data = None
        
    def update_sub_surface( self,
                            texel_data,
                            transfer_pixels,
                            sub_surface_size, # updated region size
                            unpack_offset = None, # crop offset 
                            update_offset = None, # update offset
                            mipmap_level = 0,
                            data_format = None, # automatic guess unless set explicitly
                            data_type = None, # automatic guess unless set explicitly
                            ):
        # make myself the active texture
        gl.glBindTexture(self.target, self.gl_id)

        if data_format is None: # guess the format of the data
            if isinstance(texel_data,pygame.surface.Surface):
                if texel_data.get_alpha():
                    data_format = gl.GL_RGBA
                else:
                    data_format = gl.GL_RGB

        data_type = gl.GL_UNSIGNED_BYTE
        target = gl.GL_TEXTURE_2D
        
        if unpack_offset is None:
            unpack_offset = (0, 0)
        if update_offset is None:
            update_offset = (0, 0)
            
        width, _height = texel_data.get_size()
        if transfer_pixels or self.raw_data is None:
            if texel_data.get_alpha():
                self.raw_data = pygame.image.tostring(texel_data,'RGBA',1)
            else:
                self.raw_data = pygame.image.tostring(texel_data,'RGB',1)

        gl.glPixelStorei( gl.GL_UNPACK_ROW_LENGTH, width)
        gl.glPixelStorei( gl.GL_UNPACK_SKIP_PIXELS, unpack_offset[0])
        gl.glPixelStorei( gl.GL_UNPACK_SKIP_ROWS, unpack_offset[1])
        gl.glTexSubImage2D(target,
                           mipmap_level,
                           update_offset[0],
                           update_offset[1],
                           sub_surface_size[0],
                           sub_surface_size[1],
                           data_format,
                           data_type,
                           self.raw_data)
        gl.glPixelStorei( gl.GL_UNPACK_ROW_LENGTH, 0)
        gl.glPixelStorei( gl.GL_UNPACK_SKIP_PIXELS, 0)
        gl.glPixelStorei( gl.GL_UNPACK_SKIP_ROWS, 0)

class BufferedTextureObject(TextureObject):
    def __init__(self,buffer_data,*args,**kwargs):
        super(BufferedTextureObject, self).__init__(*args,**kwargs)
        self.buffer_data = buffer_data
        
    def update_sub_surface( self,
                            texel_data,
                            transfer_pixels,
                            sub_surface_size, # updated region size
                            unpack_offset = None, # crop offset 
                            update_offset = None, # update offset
                            mipmap_level = 0,
                            data_format = None, # automatic guess unless set explicitly
                            data_type = None, # automatic guess unless set explicitly
                            ):
        # make myself the active texture
        gl.glBindTexture(self.target, self.gl_id)
        data_format = gl.GL_RGB
        data_type = gl.GL_UNSIGNED_BYTE
        target = gl.GL_TEXTURE_2D
        
        if unpack_offset is None:
            unpack_offset = (0, 0)
        if update_offset is None:
            update_offset = (0, 0)
            
        width, _height = texel_data.get_size()
        raw_data = np.frombuffer(self.buffer_data, 'B')

        gl.glPixelStorei( gl.GL_UNPACK_ROW_LENGTH, width)
        gl.glPixelStorei( gl.GL_UNPACK_SKIP_PIXELS, unpack_offset[0])
        gl.glPixelStorei( gl.GL_UNPACK_SKIP_ROWS, unpack_offset[1])
        gl.glTexSubImage2D(target,
                           mipmap_level,
                           update_offset[0],
                           update_offset[1],
                           sub_surface_size[0],
                           sub_surface_size[1],
                           data_format,
                           data_type,
                           raw_data)
        gl.glPixelStorei( gl.GL_UNPACK_ROW_LENGTH, 0)
        gl.glPixelStorei( gl.GL_UNPACK_SKIP_PIXELS, 0)
        gl.glPixelStorei( gl.GL_UNPACK_SKIP_ROWS, 0)

class ShaderTextureStimulus(TextureStimulus):
    def __init__(self,shared_texture,*args,**kwargs):
        super(ShaderTextureStimulus, self).__init__(*args,**kwargs)
        # Recreate an OpenGL texture object this instance "owns"
        self.texture_object = shared_texture
        self.parameters.texture.load(self.texture_object,
                                     internal_format=gl.GL_RGB,
                                     build_mipmaps=False)
        
    def draw(self):
        super(ShaderTextureStimulus, self).draw()
        # uninstall shader program
        gl.glUseProgram(0)
                
class MovieController(StimulusController):
    """ update movie from pygame surface """
    def __init__(self,*args,**kwargs):
        super(MovieController, self).__init__(*args,**kwargs)
        
        self.surface = self.stimulus.surface
        self.texture = self.stimulus.texture
        self.texture_obj = self.texture.get_texture_object()
        
        width, height = self.surface.get_size()
        viewport = self.viewport.get_name()
        if self.p.layout == "2D":
            self.crop_offset = (0, 0)
            self.size = (width, height)
            self.update_offset = (0, 0)
        elif self.p.layout == "LR":
            if viewport == "left":
                self.crop_offset = (0, 0)
            elif viewport == "right":
                self.crop_offset = (width//2, 0)
            self.size = (width//2, height)
            self.update_offset = (width//4, 0)
        elif self.p.layout == "RL":
            if viewport == "left":
                self.crop_offset = (width//2, 0)
            elif viewport == "right":
                self.crop_offset = (0, 0)
            self.size = (width//2, height)
            self.update_offset = (width//4, 0)
        elif self.p.layout == "TB":
            if viewport == "left":
                self.crop_offset = (0, 0)
            elif viewport == "right":
                self.crop_offset = (0, height//2)
            self.size = (width, height//2)
            self.update_offset = (0, height//4)
        elif self.p.layout == "BT":
            if viewport == "left":
                self.crop_offset = (0, height//2)
            elif viewport == "right":
                self.crop_offset = (0, 0)
            self.size = (width, height//2)
            self.update_offset = (0, height//4)
        else:
            self.logger.error("Cannot support layout: %s" %self.p.layout)
        
    def during_go_eval(self):
        transfer_pixels = True if self.viewport.get_name() == "left" else False
        self.texture.set_contrast(self.p.contrast)
        self.texture_obj.update_sub_surface(self.surface,
                                            transfer_pixels=transfer_pixels,
                                            sub_surface_size=self.size,
                                            unpack_offset=self.crop_offset,
                                            update_offset=self.update_offset)

class Movie(Stimulus):
    def __init__(self, params, surface, texture_obj, subject=None, sweepseq=None, trigger=True, **kwargs):
        super(Movie, self).__init__(subject=subject, params=params, **kwargs)
        self.name = 'timingmovie'
        self.logger = logging.getLogger('LightStim.Movie')
        self.param_names = ['on','xorigDeg','yorigDeg','widthDeg','heightDeg']
        self.defalut_parameters = {'xorigDeg':0.0,
                                   'yorigDeg':0.0,
                                   'bgbrightness':0.0,}
        """ load parameters from stimulus_params file """
        self.load_params()
        """ override params from script """
        self.set_parameters(self.parameters, params)
        self.parameters.on = False
    
        self.sweepseq = sweepseq
        self.trigger = trigger
        
        self.surface = surface
        self.texure_obj = texture_obj
        
        self.make_stimuli()
        self.register_controllers()

    def make_stimuli(self):
        size = self.viewport.get_size()
        self.background = Target2D(position=(size[0]/2, size[1]/2),
                                   anchor='center',
                                   size=size,
                                   on=True)

        self.bgp = self.background.parameters
        #set background color before real sweep
        bgb = self.parameters.bgbrightness
        self.bgp.color = bgb, bgb, bgb, 1.0
        
        contrast = self.parameters.contrast
        self.texture = ShaderTexture(contrast, self.surface)
        self.texture_stim = ShaderTextureStimulus(texture=self.texture,
                                                   shared_texture=self.texure_obj,
                                                   position=(size[0]/2, size[1]/2),
                                                   anchor='center',
                                                   mipmaps_enabled=0,
                                                   texture_min_filter=gl.GL_LINEAR)
        self.tp = self.texture_stim.parameters
        
        self.stimuli = (self.background, self.texture_stim)
    
    def register_controllers(self):
        self.controllers.append(MovieController(self))
        
class TimingController(SweepSequeStimulusController):
    def __init__(self,*args,**kwargs):
        super(TimingController, self).__init__(*args,**kwargs)
        self.tp = self.stimulus.tp
    def during_go_eval(self):
        stimulus_on = self.next_param()
        if stimulus_on:
            self.tp.on = True
        else:
            self.tp.on = False
            
class TimingSetMovie(Movie):
    def register_controllers(self):
        super(TimingSetMovie, self).register_controllers()
        self.logger.info('Register TimingController.')
        self.controllers.append(TimingController(self))
        
class AlsaSoundLazyPlayer:
    def __init__(self,rate=44100,channels=2,fps=25):
        self._rate=rate
        self._channels=channels
        self._d = alsaaudio.PCM()
        self._d.setchannels(channels)
        self._d.setformat(alsaaudio.PCM_FORMAT_S16_LE)
        self._d.setperiodsize(int((rate*channels)//fps//2))
        self._d.setrate(rate)
    def push_nowait(self,stamped_buffer):
        self._d.write(stamped_buffer[0].data)

class MoviePlayer(Process):
    def __init__(self, filename, *args,**kwargs):
        super(MoviePlayer, self).__init__(*args,**kwargs)        
        TS_VIDEO_RGB24={ 'video1':(0, -1, {'pixel_format':PixelFormats.PIX_FMT_RGB24}), 'audio1':(1,-1,{})}
        ## create the reader object
        self.mp = FFMpegReader(seek_before=0)
        ## open an audio-video file
        self.mp.open(filename,TS_VIDEO_RGB24,buf_size=4096)
            
    def get_size(self):
        tracks = self.mp.get_tracks()
        return tracks[0].get_size()
    
    def set_buffer(self, buffer_data):
        self.buffer_data = buffer_data
        
    def render_to_buffer(self, frame):
        buffer_array = np.frombuffer(self.buffer_data, 'B')
        frame = np.flipud(frame)
        frame = frame.reshape((1, -1))
        buffer_array[:] = frame
        
    def run(self):
        tracks = self.mp.get_tracks()
        tracks[0].set_observer(self.render_to_buffer)
        rate = tracks[1].get_samplerate()
        channels = tracks[1].get_channels()
        fps = tracks[0].get_fps()
        ap = AlsaSoundLazyPlayer(rate, channels, fps)
        tracks[1].set_observer(ap.push_nowait)
        self.mp.run()
    
    def seek(self, pos=0):
        self.mp.seek_to_seconds(pos)
    
    def stop(self):
        self.mp.close()
        os.kill(self.pid, signal.SIGKILL)
        