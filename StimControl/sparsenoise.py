# 
#
# Copyright (C) 2010-2011 Huang Xin
# 
#
# Distributed under the terms of the GNU Lesser General Public License
# (LGPL). See LICENSE.TXT that came with this file.
from __future__ import division

from LightStim.SweepTable import StaticParams,DynamicParams,Runs,Variable,Variables
from LightStim.WhiteNoise import WhiteNoise

static = StaticParams()
dynamic = DynamicParams()

"""Experiment settings"""
exp_times = 1
# for every grid cell
stim_times = 2
# pre-experiment duration to display blank screen (sec)
static.presweepSec = 3.0
# post-experiment duration to display blank screen (sec)
static.postsweepSec = 1.0
"""Screen settings"""
static.origDeg = (0, 0)
"""Grid settings"""
static.center = (6, 6)
static.size = (10, 10)
# grid dimension (x, y)
static.griddim = (20, 20)
# pre-calculated grid cell size (increment)
static.gridcell = (static.size[0]/static.griddim[0], static.size[1]/static.griddim[1])
# stimuli orientation offset (deg)
static.orientation = 0.0
# noise width (deg)
static.widthDeg = static.size[0]/static.griddim[0]
# noise height (deg)
static.heightDeg = static.size[1]/static.griddim[1]
"""Background settings"""
# background brightness (0-1)
static.bgbrightness = 0.5
"""Fixation settings"""
static.fixationspotOn = False
static.fsxposDeg = 0.0
static.fsyposDeg = 0.0
static.fixationspotDeg = 0.5
"""Mask settings"""
# mask, one of:  None, 'gaussian', or 'circle'
static.mask = None
# mask diameter (deg), ignored if mask is None
static.diameterDeg = 10
# screen gamma: None, or single value, or 3-tuple
static.gamma = None
"""CheckBoard settings"""
static.checkbdon = False
static.cbcolormap = 'ggr'

"""Dynamic parameters can potentially vary from one sweep to the next. 
If a dynamic parameter is assigned multiple values in a sequence, it's treated as a Variable, 
and has to be added to this Experiment's Variables object"""


"""Noise settings"""
# noise stimuli times for every grid cell(n)
dynamic.times = range(stim_times)
# sweep duration (sec)
static.sweepSec = 0.04
# post-sweep duration to display blank screen (sec)
static.postsweepSec = 0
# noise position index in stimulus grid
dynamic.posindex = [(i,j) for i in range(static.griddim[0]) for j in range(static.griddim[1])]
dynamic.contrast = [0,1]

runs = Runs(n=2, reshuffle=True)

variable = Variables()
variable.times    = Variable(vals=dynamic.times,    dim=0, shuffle=True)
variable.posindex = Variable(vals=dynamic.posindex, dim=1, shuffle=True)
variable.contrast = Variable(vals=dynamic.contrast, dim=2, shuffle=True)

e = WhiteNoise(static=static, dynamic=dynamic, variables=variable, runs=runs) # create a WhiteNoise experiment
e.go()