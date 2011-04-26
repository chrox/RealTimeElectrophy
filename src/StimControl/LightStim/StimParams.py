#!/usr/bin/env python
"""  """
# Copyright (c) 2010-2011 HuangXin.  Distributed under the terms
# of the GNU Lesser General Public License (LGPL).

from __future__ import division
#from LightStim import *

############# parameter structure #############
class dictattr(dict):
    """Dictionary with attribute access"""
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

class StaticParams(dictattr):
    """Stores static experiment parameters, attributed by their name.
    Exactly which attributes are stored here depends on the type of experiment"""
    def __init__(self, *args, **kwargs):
        """Common static params for all Experiments. Init for documentation's sake"""
        super(StaticParams, self).__init__(*args, **kwargs)
        # x coordinates of center anchor from screen center (deg)
        self.xorigDeg = None
        # y coordinates of center anchor from screen center (deg)
        self.yorigDeg = None
        # pre-experiment duration to display blank screen (sec)
        self.preexpSec = None
        # post-experiment duration to display blank screen (sec)
        self.postexpSec = None
        # stimulus ori offset (deg)
        self.orioff = None
    def check(self):
        for name, val in self.items():
            assert not iterable(val) or val.__class__ in (str, tuple), \
            'static parameter must be a scalar: %s = %r' % (name, val) 
            # can't be an iterable object, unless it's a string or a tuple


class DynamicParams(dictattr):
    """Stores potentially dynamic experiment parameters, attributed by their name.
    Exactly which attributes are stored here depends on the type of experiment"""
    pass


class Variable(object):
    """A dynamic experiment parameter that varies over sweeps"""
    def __init__(self, vals, dim=0, shuffle=False, random=False):
        """Bind the dynamic parameter values, its dim, and its shuffle and random flags to this experiment Variable"""
        self.vals = vals
        self.dim = dim
        self.shuffle = shuffle
        self.random = random
    def __iter__(self):
        return iter(self.vals)
    def __len__(self):
        return len(self.vals)
    def check(self):
        """Check that all is well with this Variable, run this after being assigned to Variables object,
        which gives self a .name"""
        assert iterable(self.vals), '%s Variable values must be in a sequence' % self.name
        assert len(self.vals) > 0, '%s Variable values must be in a sequence of non-zero length' % self.name
        for val in self.vals:
            assert val != None, '%s Variable values cannot be left as None' % self.name
        assert not (self.shuffle and self.random), '%s Variable shuffle and random flags cannot both be set' % self.name


class Variables(dictattr):
    """A collection of Variable objects, attributed by their name.
    Exactly which attributes are stored here depends on the Variable objects themselves.
    Each of the Variable objects stored here can have different dims and shuffle and random flags,
    unlike those stored in a Dimension"""
    def __init__(self, *args, **kwargs):
        super(Variables, self).__init__(*args, **kwargs)
    def __setattr__(self, varname, variable):
        """Every attribute assigned to Variables must be a Variable"""
        assert variable.__class__ == Variable
        try:
            variable.name
        except AttributeError:
            variable.name = varname # store the Variable's name in its own .name field
        variable.check()
        super(Variables, self).__setattr__(varname, variable)
    def __iter__(self):
        """Iterates over all Variable objects stored here"""
        return self.itervalues() # inconsistent with dict behaviour

class Runs(object):
    """Stores info about experiment runs"""
    def __init__(self, n=1, reshuffle=False):
        self.n = n # number of runs
        self.reshuffle = reshuffle # reshuffle/rerandomize on every run those variables with their shuffle/random flags set?
        self.check()
    def check(self):
        """Check that all is well with these Runs"""
        assert self.n.__class__ == int and self.n > 0, 'number of runs must be a positive integer'

def iterable(x):
    """Check if the input is iterable, stolen from numpy.iterable()"""
    try:
        iter(x)
        return True
    except:
        return False
    
