#!/usr/bin/python
# Plotting staircase data from stereo threshold experiment log.
#
# Copyright (C) 2010-2012 Huang Xin
# 
# See LICENSE.TXT that came with this file.
import re
import sys
import matplotlib.pyplot as plt

from StimControl.Experiments.Staircase import StaircaseObject
from StimControl.Utility.Logger import ModLogger

class EmuStaircase(object):
    def __init__(self, logfile):
        self.logfile = logfile
        
        params_line = self.get_init_params()
        startVal = eval(re.compile(r'startVal:([0-9.]+) ').findall(params_line)[0])
        nReversals = eval(re.compile(r'nReversals:([0-9.]+) ').findall(params_line)[0])
        stepSizes = eval(re.compile(r'stepSizes:(\[.+\]) ').findall(params_line)[0])
        nTrials = eval(re.compile(r'nTrials:([0-9.]+) ').findall(params_line)[0])
        nUp = eval(re.compile(r'nUp:([0-9.]+) ').findall(params_line)[0])
        nDown = eval(re.compile(r'nDown:([0-9.]+) ').findall(params_line)[0])
        stepType = "lin"
        minVal = eval(re.compile(r'minVal:([0-9.]+) ').findall(params_line)[0])
        maxVal = eval(re.compile(r'maxVal:([0-9.]+)').findall(params_line)[0])
        
        self.logger = ModLogger(self.logfile, 'recomp')
        self.staircase_obj = StaircaseObject(
                startVal,
                nReversals,
                stepSizes,
                nTrials,
                nUp, 
                nDown,
                stepType, 
                minVal, 
                maxVal)
        
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
        
    def run(self):
        self.logger.write("="*36)
        self.logger.write("Staircase for Stereo Threshold measurement")
        self.logger.write("="*36)
        # disc demo
        data = self.collect_log_data()
        for i, trial_data in enumerate(data):
            disp, interval, response = trial_data
            try:
                self.staircase_obj.next()
            except:
                break
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

    def get_init_params(self):
        params_line_re = re.compile(r'^Staircase object is initiated with (.+)$')
        with open(self.logfile) as log:
            for line in log.readlines():
                params_str = params_line_re.findall(line)
                if params_str:
                    return params_str[0].strip()
            
    def collect_log_data(self):
        data = []
        disparity_re = re.compile(r'^\tdisparity (.+),')
        cross_at_re = re.compile(r'cross at interval ([1|2])')
        report_re = re.compile(r'\tobserver reports (.+)$')
        disparity, cross_at, report = None, None, None
        with open(self.logfile) as log:
            for line in log.readlines():
                disparity_str = disparity_re.findall(line)
                cross_at_str = cross_at_re.findall(line)
                report_str = report_re.findall(line)
                if disparity_str:
                    disparity = float(disparity_str[0].strip())
                if cross_at_str:
                    cross_at = int(cross_at_str[0].strip())
                if report_str:
                    report = True if report_str[0].strip() == 'True' else False
                    data.append((disparity, cross_at, report))
        return data

if __name__ == '__main__':
    plot_data = False
    argv = list(sys.argv)
    if '-p' in argv:
        plot_data = True
        argv.remove('-p')
    
    filename = argv[-1]
    stair = EmuStaircase(filename)
    stair.run()
    
    if plot_data:
        data = stair.collect_log_data()
        disp = [trail[0] for trail in data]
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.plot(xrange(len(disp)), disp)
        ax.grid(True)
        plt.show()
    