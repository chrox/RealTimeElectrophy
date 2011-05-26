# Profile the sweep
#
# Copyright (C) 2010-2011 Huang Xin
# 
#
# Distributed under the terms of the GNU Lesser General Public License
# (LGPL). See LICENSE.TXT that came with this file.
import cProfile,pstats
from StimControl.mangrating import *

sweep = FrameSweep()
sweep.add_stimulus(stimulus_control)
sweep.add_stimulus(stimulus_primary)
sweep.add_stimulus(stimulus_left)
sweep.add_stimulus(stimulus_right)

cProfile.run('sweep.go()','mangrating_profile')
p = pstats.Stats('mangrating_profile')
p.sort_stats('cumulative')
p.print_stats()