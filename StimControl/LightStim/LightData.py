# Data structures.
#
# Copyright (C) 2010-2011 Huang Xin
# 
# See LICENSE.TXT that came with this file.
import numpy as np

class dictattr(dict):
    """ Dictionary with attribute access"""
    def __init__(self, *args, **kwargs):
        super(dictattr, self).__init__(*args, **kwargs)
        for k, v in kwargs.iteritems():
            self.__setitem__(k, v) # call our own __setitem__ so we get keys as attribs even on kwarg init
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError, '%r object has no attribute %r' % ('dictattr', key)
    def __setattr__(self, key, val):
        self[key] = val
    def __setitem__(self, key, val):
        super(dictattr, self).__setitem__(key, val)
        if key.__class__ == str and not key[0].isdigit(): # key isn't a number or a string starting with a number
            key = key.replace(' ', '_') # get rid of any spaces
            self.__dict__[key] = val # make the key show up as an attrib upon dir()

class IndexedParam(list):
    def __init__(self,parameter):
        if parameter == 'orientation':
            super(IndexedParam, self).__init__(np.linspace(0.0, 360.0, 16, endpoint=False))
        elif parameter == 'orientation_180':
            super(IndexedParam, self).__init__(np.linspace(0.0, 180.0, 16, endpoint=False))
        elif parameter == 'spatial_freq':
            super(IndexedParam, self).__init__(np.logspace(-1.0,0.5,16))
        elif parameter == 'phase_at_t0':
            super(IndexedParam, self).__init__(np.linspace(0.0, 360.0, 16, endpoint=False))
        elif parameter is None:
            super(IndexedParam, self).__init__([None])
        else:
            raise RuntimeError('Cannot understand parameter:%s' %str(parameter))