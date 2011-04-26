from __future__ import division
from LightStim import StimParams
from LightStim.stimuli.WhiteNoise import WhiteNoise

static = StimParams.StaticParams()
dynamic = StimParams.DynamicParams()

"""Experiment settings"""
exp_times = 1
# for every grid cell
stim_times = 2
# pre-experiment duration to display blank screen (sec)
static.presweepSec = 1.0
# post-experiment duration to display blank screen (sec)
static.postsweepSec = 1.0
"""Screen settings"""
static.xorig = 0
static.yorig = 0
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
"""Mask settings"""
# mask, one of:  None, 'gaussian', or 'circle'
static.mask = None
# mask diameter (deg), ignored if mask is None
static.diameterDeg = 10
# screen gamma: None, or single value, or 3-tuple
static.gamma = None
"""CheckBoard settings"""
static.checkbdon = True
static.cbcolormap = 'ggr'

"""Dynamic parameters can potentially vary from one sweep to the next. 
If a dynamic parameter is assigned multiple values in a sequence, it's treated as a Variable, 
and has to be added to this Experiment's Variables object"""

"""Background settings"""
# background brightness (0-1)
dynamic.bgbrightness = 0.5
"""Fixation settings"""
dynamic.fixationspotOn = False
dynamic.fsxposDeg = 0.0
dynamic.fsyposDeg = 0.0
dynamic.fixationspotDeg = 0.5
"""Noise settings"""
# noise stimuli times for every grid cell(n)
dynamic.times = range(stim_times)
# sweep duration (sec)
dynamic.sweepSec = 1/75*4
# post-sweep duration to display blank screen (sec)
dynamic.postsweepSec = 0
# noise position index in stimulus grid
dynamic.posindex = [(i,j) for i in range(static.griddim[0]) for j in range(static.griddim[1])]
dynamic.contrast = [0,1]

runs = StimParams.Runs(n=2, reshuffle=True)

variable = StimParams.Variables()
variable.times    = StimParams.Variable(vals=dynamic.times,    dim=0, shuffle=True)
variable.posindex = StimParams.Variable(vals=dynamic.posindex, dim=1, shuffle=True)
variable.contrast = StimParams.Variable(vals=dynamic.contrast, dim=2, shuffle=True)

e = WhiteNoise(static=static, dynamic=dynamic, variables=variable, runs=runs) # create a WhiteNoise experiment
e.go()