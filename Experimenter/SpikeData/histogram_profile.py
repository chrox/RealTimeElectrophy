# Test and profile TimeHistogram
#
# Copyright (C) 2010-2012 Huang Xin
# 
# See LICENSE.TXT that came with this file.
#import cProfile,pstats
from line_profiler import LineProfiler
import TimeHistogram

def run():
    psth = TimeHistogram.PSTHAverage('/home/chrox/dev/plexon_data/c04-stim-timing-8ms-rand-1.plx')
    psth.get_data()

if __name__ == '__main__':
    
    #cProfile.run('psth.get_data()','hist_profile')
    #p = pstats.Stats('hist_profile')
    #p.sort_stats('cumulative')
    #p.print_stats()
    
    profile = LineProfiler()
    profile.add_function(run)
    profile.add_function(TimeHistogram.PSTHAverage._process_unit)
    profile.run('run()')
    profile.print_stats()
    profile.dump_stats("hist_profile.lprof")