#!/usr/bin/python
# SED is calaulated with LE and RE balance contrasts.
#
# Copyright (C) 2010-2013 Huang Xin
# 
# See LICENSE.TXT that came with this file.

import sys

from StimControl.Experiments.Disparity import Disparity
from StimControl.Experiments.Staircase import StaircaseObject
from StimControl.Utility.Logger import Logger

class Staircase(object):
    def __init__(self, subject, pre_fix):
        self.logger = Logger(subject, pre_fix)
        
        self.trialsDesired = 50
        startVal = 0.5
        nReversals = 10
        stepSizes = [0.03, 0.01, 0.01, 0.005, 0.005, 0.002, 0.001]
        nTrials = 50
        nUp = 1
        nDown = 3
        stepType = "lin"
        minVal = 0
        maxVal = 0.5
        
        self.staircase_obj = StaircaseObject(
                startVal, nReversals, stepSizes,
                nTrials, nUp, nDown,
                stepType, minVal, maxVal)
        
        self.logger.write("Staircase for Stereo Threshold measurement")
        self.logger.write("Staircase object is initiated with "
                          "startVal:%.2f "
                          "nReversals:%.2f "
                          "stepSizes:%s "
                          "nTrials:%.2f "
                          "nUp:%.2f "
                          "nDown:%.2f "
                          "minVal:%.2f "
                          "maxVal:%.2f "
                          %(startVal,nReversals,stepSizes,nTrials,nUp,nDown,minVal,maxVal))
        self.logger.write("Staircase trials is set to %d" %nTrials)
        
    def run(self, disparity):
        self.logger.write("="*36)
        self.logger.write("Staircase for Stereo Threshold measurement")
        self.logger.write("="*36)
        # disc demo
        disparity.set_disparity(0.1)
        disparity.demo()
        for i, disp in enumerate(self.staircase_obj):
            disparity.set_disparity(disp)
            response = disparity.run()
            
            interval = disparity.get_cross_interval()  # [1,2]
            self.logger.write("Trial %d :\n"
                  "\tdisparity %.2f,"
                  "\tcross at interval %d" %(i, disp, interval))
            
            self.logger.write("\tobserver reports %s" %response)
            # Update the pdf
            self.staircase_obj.update(int(response))
        
        # Get final estimate.
        t = self.staircase_obj.mean(final=6)
        self.logger.write('\nmean of final 6 reversals = %.3f\n' %t)
        self.logger.write_filestamp()
    
if __name__ == '__main__':
    subject = None
    argv = list(sys.argv)
    if len(argv) >= 2:
        subject = argv[1]
    while subject is None:
        sys.stdout.write('Please input lowercase initials of subject name: ')
        subject = raw_input()
        
    stair = Staircase(subject, "stereo_stair_")
    stair.run(Disparity(subject))
        
