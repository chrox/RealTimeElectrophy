# 
#
# Copyright (C) 2010-2011 Huang Xin
# 
#
# Distributed under the terms of the GNU Lesser General Public License
# (LGPL). See LICENSE.TXT that came with this file.
import threading
import time
from StimControl.mangrating import *

sweep = FrameSweep()
def stimcontrol(sweep):
    sweep.add_stimulus(stimulus_control)
    sweep.add_stimulus(stimulus_primary)
    sweep.add_stimulus(stimulus_left)
    sweep.add_stimulus(stimulus_right)
    sweep.add_controllers()
    while True:
        time.sleep(1)
    
control = threading.Thread(target = stimcontrol, args=[sweep], name = "StimControl")
control.setDaemon(1)
control.start()

sweep.go()

