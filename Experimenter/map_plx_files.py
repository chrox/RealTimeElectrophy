# Mapping plx from experiment log.
#
# Copyright (C) 2010-2012 Huang Xin
# 
# See LICENSE.TXT that came with this file.

import os
import re
import sys
import shutil
from SpikeRecord.Plexon.PlexFile import PlexFile
from datetime import datetime

def collect_plx_timestamp(plx_dir):
    plx_timestamps = []
    for root, _dirs, files in os.walk(plx_dir):
        for filename in files:
            if filename[-4:] == '.plx':
                filepath = os.path.join(root,filename)
                time_stamp = PlexFile(filepath).get_datetime()
                plx_timestamps.append((filepath,time_stamp))
                print 'Found PLX file %s created at %s' %(filepath, time_stamp.strftime('%Y/%m/%d %H:%M:%S'))
    
    return sorted(plx_timestamps, key=lambda tup: tup[1])

def collect_log_timestamp(log_dir):
    log_timestamps = []
    name_re = re.compile(r'Experiment name is: (.+)\n')
    time_re = re.compile(r'Experiment time is: (.+)\n')
    for root, _dirs, files in os.walk(log_dir):
        log_file = os.path.basename(root) + '.log'
        if log_file in files:
            log_path = os.path.join(root,log_file)
            log = open(log_path).readlines()
            for linenum,line in enumerate(log):
                names = name_re.findall(line)
                if names:
                    exp_name = names[0].strip()
                    name_linenum = linenum
                times = time_re.findall(line)
                if times:
                    exp_time = times[0].strip()
                    time_linenum = linenum
                    if time_linenum != name_linenum + 1:
                        raise RuntimeError("Log file %s is corrupted at line %d." %(log_file, linenum))
                    time_stamp = datetime.strptime(exp_time,'%Y/%m/%d %H:%M:%S')
                    log_timestamps.append((root,exp_name,time_stamp))
                    print 'Found Experiment %s started at %s' %(exp_name, time_stamp.strftime('%Y/%m/%d %H:%M:%S'))
                    
    return sorted(log_timestamps, key=lambda tup: tup[2])

if __name__ == '__main__':
    update_file = False
    argv = list(sys.argv)
    if '-u' in argv:
        update_file = True
        argv.remove('-u')
        
    plx_timestamps = collect_plx_timestamp(argv[1])
    log_timestamps = collect_log_timestamp(argv[2])
    
    print 'Found %d PLX files and %d Experiments entries.' %(len(plx_timestamps),len(log_timestamps))
    for timestamp in plx_timestamps:
        try:
            while True:
                oldest_log = log_timestamps[0]
                elapse = (timestamp[1] - oldest_log[2]).total_seconds()
                print 'Elapse %f for experiment %s' %(elapse, oldest_log[1])
                if elapse >= 10.0: # skip experiments of ten secs ago
                    print 'Skip experiment %s' %(oldest_log[1])
                    log_timestamps.pop(0)
                elif elapse <= 0:
                    print "Skip PLX file %s" %timestamp[0]
                    break
                else:
                    log_timestamps.pop(0)
                    src_file = timestamp[0]
                    dst_file = os.path.join(oldest_log[0],oldest_log[1]+'.plx')
                    if update_file and os.path.exists(dst_file):
                        print "File %s exists" %dst_file
                    else:
                        shutil.copyfile(src_file, dst_file)
                        print "Created file %s" %dst_file
                    break
        except IndexError,e:
            print "No more entry in log file. " + str(e)
            break
         