# Print and log to file
#
# Copyright (C) 2010-2013 Huang Xin
# 
# See LICENSE.TXT that came with this file.

import time,os

class Logger(object):
    def __init__(self, sub_dir, file_prefix):
        self.file_prefix = file_prefix
        (year,month,day,hour24,_min,sec) = time.localtime(time.time())[:6]
        self.trial_time_str = "%04d%02d%02d_%02d%02d%02d"%(year,month,day,hour24,_min,sec)
        save_dir = os.path.abspath(os.curdir) + os.path.sep + 'data' + os.path.sep + sub_dir
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        self.file_name = save_dir + os.path.sep + self.file_prefix + self.trial_time_str
        
    def write(self, line):
        with open(self.file_name + '.txt','a') as output:
            output.write(line+"\n")
        print(line)
        
    def write_filestamp(self):
        self.write("Writen into file: " + self.file_name + "\n")
        
        