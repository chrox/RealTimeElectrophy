#!/usr/bin/python
# SED is calaulated with LE and RE balance contrasts.
#
# Copyright (C) 2010-2013 Huang Xin
# 
# See LICENSE.TXT that came with this file.

import sys
import math
import random
import numpy as np

from StimControl.Experiments.SED import SED
from StimControl.Experiments.Quest import QuestObject
from StimControl.Utility.Logger import Logger

class Quest(object):
    def __init__(self, subject, pre_fix, contrast):
        self.logger = Logger(subject, pre_fix)
        self.control_contrast = contrast
        
        tGuess = math.log10(self.control_contrast)
        tGuessSd = 2.0 # sd of Gaussian before clipping to specified range
        pThreshold = 0.82
        #beta = 3.5
        beta = 4.0
        delta = 0.01
        gamma = 0.5
        grain = 0.01
        scope = 3
        
        self.quest_obj = QuestObject(tGuess=tGuess,tGuessSd=tGuessSd,pThreshold=pThreshold,
                                     beta=beta,delta=delta,gamma=gamma,grain=grain,scope=scope)
        self.trialsDesired = 50
        
        self.logger.write("QUEST for Sensory Eye Dominance(SED) measurement")
        self.logger.write("Quest object is initiated with "
                          "tGuess:%.2f "
                          "tGuessSd:%.2f "
                          "pThreshold:%.2f "
                          "beta:%.2f "
                          "delta:%.2f "
                          "gamma:%.2f "
                          "grain:%.2f "
                          "scope:%.2f "
                          %(tGuess,tGuessSd,pThreshold,beta,delta,gamma,grain,scope))
        self.logger.write("Quest trials is set to %d" %self.trialsDesired)
        
    def run(self, sed):
        self.logger.write("="*36)
        self.logger.write("QUEST for sensory eye dominance(SED)")
        self.logger.write("Control eye contrast: %.2f" %self.control_contrast)
        self.logger.write("Tested eye: %s" %sed.get_test_eye())
        self.logger.write("="*36)
        sed.update_control_contrast(self.control_contrast)
        for k in range(self.trialsDesired):
            # Get recommended level.  Choose your favorite algorithm.
            tTest = self.quest_obj.quantile()
            rand_contrast = 10**tTest + random.choice([-0.1,0,0.1])
            if rand_contrast <= 0:
                tTest = -4.0
            else:
                tTest = math.log10(rand_contrast)
            if tTest > 0: tTest = 0
            test_contrast = 10**tTest
            #tTest=q.mean()
            #tTest=q.mode()
            sed.update_orientation()
            sed.update_test_contrast(test_contrast)
            test_ori = sed.get_test_eye_orientation()
            self.logger.write("Trial %d :\n"
                  "\ttest eye %s, contrast %f\n"
                  "\ttest eye orientation %s"%(k, sed.get_test_eye(), test_contrast, test_ori))
            key_response = sed.run()
            response = key_response == test_ori
            if response:
                self.logger.write("\tobserver reports test eye")
            else:
                self.logger.write("\tobserver reports control eye")
            # Update the pdf
            self.quest_obj.update(tTest, int(response))
        
        # Get final estimate.
        t = self.quest_obj.mean()
        sd = self.quest_obj.sd()
        self.logger.write('\n%s eye balanced contrast is %4.2f +/- %.2f'%(sed.get_test_eye(), 10**t, sd))
        #t=QuestMode(q);
        #print 'Mode threshold estimate is %4.2f'%t
    
        self.logger.write('\nQuest beta analysis. Beta controls the steepness of the Weibull function.\n')
        self.quest_obj.beta_analysis(self.logger)
        self.logger.write_filestamp()
        
    
if __name__ == '__main__':
    subject = None
    contrast = None
    argv = list(sys.argv)
    if len(argv) >= 2:
        subject = argv[1]
    while subject is None:
        sys.stdout.write('Please input lowercase initials of subject name: ')
        subject = raw_input()
    
    if len(argv) >= 3:
        contrast = float(argv[2])
    if contrast is None:
        contrast = 0.5
        
    for eye in np.random.permutation(['left','right']):
        quest = Quest(subject, "sed_quest_", contrast)
        quest.run(SED(subject, eye))
        # try:
            # quest.run(SED(eye))
        # except Exception, e:
            # sys.stdout.write(str(e))
            # break
        
