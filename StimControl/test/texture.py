#!/usr/bin/env python
"""Load a texture from a file."""

import os

from VisionEgg.Core import *
from VisionEgg.Textures import Mask2D

from StimControl.LightStim.RandomDots import RandomDots

screen = get_default_screen()

dots = RandomDots(num_dots=3000,
                  seed=2,
                  dot_size=3)

viewport = Viewport(screen=screen,
                    stimuli=[dots])

p = Presentation(go_duration=(5.0,'seconds'),viewports=[viewport])
p.go()
