# 
#
# Copyright (C) 2010-2011 Huang Xin
#
#
# Distributed under the terms of the BSD License.
# See LICENSE.TXT that came with this file.

from StimControl.mangrating import FrameSweep
from VisionEgg.Gratings import SinGrating2D
grating = SinGrating2D()
import pickle
with open('test_pickle.pkl','w') as file:
    pickle.dump(grating,file,1)
with open('test_pickle.pkl','r') as file:
    unpckled_stim = pickle.load(file)
    
sweep = FrameSweep()
sweep.add_stimulus(unpckled_stim)

sweep.go()

