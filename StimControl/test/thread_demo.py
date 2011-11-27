# 
#
# Copyright (C) 2010-2011 Huang Xin
#
# See LICENSE.TXT that came with this file.

import threading
import time
from StimControl.mangrating import FrameSweep,stimulus_control,stimulus_left,stimulus_right

sweep = FrameSweep()
def stimcontrol(sweep):
    sweep.add_stimulus(stimulus_control)
    sweep.add_stimulus(stimulus_left)
    sweep.add_stimulus(stimulus_right)
    sweep.add_controllers()
    while True:
        time.sleep(1)
    
control = threading.Thread(target = stimcontrol, args=[sweep], name = "StimControl")
control.setDaemon(1)
control.start()

sweep.go()

