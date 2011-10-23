# Utilities used in LightStim.
#
# Copyright (C) 2010-2011 Huang Xin
# 
#
# Distributed under the terms of the GNU Lesser General Public License
# (LGPL). See LICENSE.TXT that came with this file.

class TimeFormat(object):
    """Convert from sec to ISO HH:MM:SS[.mmmmmm] format"""
    def __init__(self,sec):
        h = int(sec // 3600)
        m = int(sec % 3600 // 60)
        s = int(sec % 3600 % 60)
        dec = '%.6f' % (sec % 1)
        self.str = '%d:%02d:%02d' % (h, m, s) + dec[1:]
    def __str__(self):
        return self.str
    def __repr__(self):
        return self.__str__()