# LightStim.SweepTable: the core class for frame-by-frame stimulus control.
#
# Copyright (C) 2010-2011 Huang Xin
# 
#
# Distributed under the terms of the GNU Lesser General Public License
# (LGPL). See LICENSE.TXT that came with this file.

"""

This module contains the SweepTable class. 

"""
from copy import copy
import cStringIO
import numpy as np
from SweepStamp import MAXPOSTABLEINT

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

class Dimension(object):
    """An experiment dimension, all of whose Variables co-vary"""
    def __init__(self, variables, dim, shuffle=False, random=False):
        self.variables = variables
        self.dim = dim
        self.shuffle = shuffle
        self.random = random
        self.check()
    def keys(self):
        return self.variables.keys()
    def values(self):
        return self.variables.values()
    def items(self):
        return self.variables.items()
    def __len__(self):
        """Number of conditions in this Dimension"""
        return len(self.variables.values()[0]) # assumes all vars in this dim have the same number of conditions
    '''
    def __getitem__(self, key):
        """Allows dictionary-like access to Variable objects in this Dimension"""
        return self.variables[key]
    '''
    def check(self):
        """Check that all is well with this Dimension"""
        assert self.shuffle * self.random == 0, 'Dimension %d shuffle and random flags cannot both be set' % self.dim
        for var in self.variables:
            assert iterable(var), 'all Variables in Dimension %d must be iterable' % self.dim
            assert len(var) == len(self), 'all Variables in Dimension %d must have the same number of conditions' % self.dim
            assert var.dim == self.dim, 'all Variables in Dimension %d must have the same dimension value' % self.dim
            assert var.shuffle == self.shuffle, 'all variables in Dimension %d must have the same shuffle flag' % self.dim
            assert var.random == self.random, 'all variables in Dimension %d must have the same random flag' % self.dim

class SweepTable(object):
    """A SweepTable holds all unique combinations of Experiment Variables, as well as indices
    into these combinations, based on shuffle/random flags for each Dimension, the number of runs,
    whether each run is reshuffled, with optional BlankSweeps inserted at the (potentially shuffled)
    intervals requested"""
    def __init__(self, static, dynamic, variables, runs=None, blanksweeps=None):
        self.static = static # StaticParams object
        self.dynamic = dynamic # DynamicParams object
        self.variables = variables # Variables object
        self.runs = runs # Runs object
        self.blanksweeps = blanksweeps # BlankSweeps object
        """Build the sweep table.

        A Variable's dim value relative to the dim values of all the other
        Variables determines its order in the nested for loops that generate
        the combinations of values for each sweep: the Variable with the lowest
        dim value becomes the outermost for loop and changes least often;
        the Variable with the highest dim value becomes the innermost for loop
        and changes on every sweep. dim must be an integer. Variables with the
        same dim value are part of the same Dimension, are shuffled/randomized
        together, and must therefore be of the same length and have the same
        shuffle and random flags"""

        # Build the dimensions
        self.builddimensions()

        # Build the dimension index table
        self.builddimitable()

        # Now use dimitable to build the sweep table
        self.data = dictattr() # holds the actual sweep table, a dict with attribute access
        for dim in self.dimensions:
            for var in dim.variables:
                dimi = self.dimitable[:, dim.dim] # get the entire column of indices into the values of this dimension
                vals = np.asarray(var.vals)[dimi] # convert to array so you can select multiple values with a sequence of indices
                self.data[var.name] = vals # store it as an array

        # Check to make sure that all the variables in self.data have the same number of vals
        try:
            nvals = len(self.data.values()[0])
        except IndexError: # there aren't any variables at all
            nvals = 0
        for varname in self.data:
            assert len(self.data[varname]) == nvals, '%s length in sweep table does not match expected length %d' % (varname, nvals)

        # For convenience in the main stimulus loop, add the non-varying dynamic params to self.data
        nvals = max(nvals, 1) # make sure the sweep table has at least one entry
        for paramname, paramval in self.dynamic.iteritems():
            if paramname not in self.data:
                self.data[paramname] = np.tile(paramval, nvals) # paramval was already checked to be a scalar in Experiment.check()

        # Do the Dimension shuffling/randomizing by generating appropriate sweep table indices
        self.i = self.geti() # get 1 Run's worth of sweep table indices, shuffling/randomizing variables that need it
        if self.runs:
            if self.runs.reshuffle:
                for dummy in range(1, self.runs.n):
                    self.i = np.append(self.i, self.geti()) # add another Run's worth of indices, reshuffling/rerandomizing Dimensions that need it
            else:
                self.i = np.tile(self.i, self.runs.n) # create n identical Runs worth of indices

        # Add BlankSweeps to the sweep table indices
        if self.blanksweeps:
            nsweeps = len(self.i)
            insertioni = range(self.blanksweeps.T-1, nsweeps, self.blanksweeps.T-1) # where to insert each blank sweep, not quite right
            for ii, ipoint in enumerate(insertioni):
                insertioni[ii] += ii # fix it by incrementing each insertion point by its position in insertioni to account for all the preceding blank sweeps

            if self.blanksweeps.shuffle:
                samplespace = range(nsweeps + len(insertioni)) # range of possible indices to insert at
                np.random.shuffle(samplespace) # shuffle them in place
                insertioni = samplespace[:len(insertioni)] # pick the fist len(insertioni) entries in samplespace
                insertioni.sort() # make sure we insert in order, don't try inserting at indices that don't exist yet

            i = list(self.i)
            for ipoint in insertioni:
                i.insert(ipoint, None) # do the insertion, None sweep table index value indicates a blank sweep
            self.i = np.asarray(i) # save the results back to self

    def builddimensions(self):
        """Build the Dimension objects from the Experiment Variables"""

        # find unique dimension values across variables. Dim values could be 0, 5, 5, 5, 2, 666, -74,...
        dims = list(np.unique([ var.dim for var in self.variables ])) # np.unique returns sorted values

        # renumber dimension values to be consecutive 0-based
        newdims = range(len(dims)) # 0-based consecutive dim values
        old2new = dict(zip(dims, newdims)) # maps from old dim values to new ones
        for var in self.variables:
            var.dim = old2new[var.dim] # overwrite each Variable's old dim value with the new one

        # use newdims to init a list of Dimensions, each with an empty Variables object
        self.dimensions = []
        for dim in newdims:
            d = Dimension(variables=Variables(), dim=dim)
            self.dimensions.append(d)

        # now assign each Variable object to the appropriate Dimension object
        for var in self.variables:
            d = self.dimensions[var.dim] # get the Dimension object
            d.variables[var.name] = var # assign the Variable to the Dimension's Variables
            d.shuffle = var.shuffle # set the Dimension's shuffle and random flags according to this Variable
            d.random = var.random
            d.check() # make sure everything is consistent in this Dimension

    def builddimitable(self):
        """Build the dimension index table"""
        # Can't figure out how to use a recursive generator/function to do this, see Apress Beginning Python p192
        # HACK!!: generate and exec the appropriate Python code to build the ordered (unshuffled/unrandomized) dimension index table
        dummy_dimi = [None]*len(self.dimensions) # stores the index we're currently on in each dimension
        self.dimitable = [] # ordered dimension index table, these are indices into the values in dimensions, dimensions are in columns, sweeps are in rows
        # generate code with the right number of nested for loops
        code = ''
        tabs = ''
        for dimension in self.dimensions: # generate ndim nested for loops...
            i = str(dimension.dim)
            code += tabs+'for dummy_dimi['+i+'] in range(len(self.dimensions['+i+'])):\n'
            tabs += '    ' # add a tab to tabs in preparation for the next for loop, or the innermost part of the last one
        code += tabs+'self.dimitable.append(copy(dummy_dimi))\n' # innermost part of the nested for loops, copying dummy_dimi is important
        exec(code) # run the generated code, this builds the ordered dimitable with all the permutations
        '''
        # example of what the generated code looks like for 3 dimensions:
        for dummy_dimi[0] in range(len(self.dimensions[0])):
            for dummy_dimi[1] in range(len(self.dimensions[1])):
                for dummy_dimi[2] in range(len(self.dimensions[2])):
                    self.dimitable.append(copy(dummy_dimi))
        '''
        self.dimitable = np.asarray(self.dimitable)
        self.checkdimitable()

    def checkdimitable(self):
        """Check the length of the dimitable"""
        nsweeps = len(self.dimitable)
        if nsweeps > MAXPOSTABLEINT:
            raise ValueError, 'sweep table has %d sweeps, with indices exceeding \
            the maximum index %d that can be sent to Surf (index %d is reserved to signify a blank sweep). \
            Reduce the number of dimensions or conditions' % (nsweeps, MAXPOSTABLEINT-1, MAXPOSTABLEINT)

    def geti(self):
        """Return one Run's worth of sweep table indices, in a numpy array.
        Takes into account the state of each Dimension's shuffle and random flags"""
        i = np.arange(len(self.dimitable)) # set of indices into the sweep table, stores in what order and the # of times and we'll be stepping through the sweeptable during the experiment

        # check if all dims are set to be shuffled/randomized, if so, do it the fast way
        if np.all([ dim.shuffle for dim in self.dimensions ]): # all dimensions are set to be shuffled
            i = shuffle(i) # shuffle all of the indices at once
        elif np.all([ dim.random for dim in self.dimensions ]): # all dimensions are set to be randomized
            i = randomize(i) # randomize all of the indices at once
        else: # shuffle/randomize each dim individually (slower)
            for dim in self.dimensions:
                if dim.shuffle or dim.random: # if flag is set to shuffle or randomize
                    dimi = self.dimitable[:, dim.dim] # get the entire column of indices into the values of this dimension
                    sortis = np.argsort(dimi, kind='mergesort') # indices into dimi that would give you dimi sorted. mergesort is a stable sort, which is an absolute necessity in this case!
                    sortedi = i[sortis] # sweep table indices sorted in order of dimi
                    offset = np.prod([ len(d) for d in self.dimensions if d != dim ]) # offset is the product of the lengths of all the dimensions other than this one
                    if len(i) % len(dim) != 0: # check before doing int division
                        raise ValueError, 'Somehow, number of sweeps is not an integer multiple of length of dim %d' % dim.dim
                    nsegments = len(i) // len(dim) # number of segments of the sweep table indices within which this dimension's values vary consecutively?? - i guess it's possible that some segments will butt up against each other, making effectively longer consecutively-varying segments - long dimensions will be split into many segments, short dimensions into few
                    # maybe np.split() would be useful here??
                    for segmenti in range(nsegments):
                        # j is a collection of indices to shuffle over, made up of every offset'th index, starting from segmenti
                        j = np.asarray([ j for j in range(segmenti, offset*len(dim), offset) ])
                        if dim.shuffle:
                            newj = shuffle(j)
                        elif dim.random:
                            newj = randomize(j)
                        i[sortis[j]] = sortedi[newj] # update sweep table indices appropriately, this is the trickiest bit
        return i

    def pprint(self, i=None):
        """Print out the sweep table at sweep table indices i,
        formatted as an actual table instead of just a dict.
        Only Variables are included (non-varying dynamic params are left out).
        If i is left as None, prints the basic sorted sweep table"""
        print self._pprint(i)

    def _pprint(self, i=None):
        """Return a string representation of the sweep table at sweep table indices i,
        formatted as an actual table instead of just a dict.
        Only Variables are included (non-varying dynamic params are left out).
        If i is left as None, prints the basic sorted sweep table"""
        f = cStringIO.StringIO() # create a string file-like object, implemented in C, fast
        f.write('i\t') # sweep table index label
        for dim in self.dimensions:
            for var in dim.variables:
                f.write('%s\t' % var.name) # column label
        if i == None:
            # sweep table will always have at least one value per dynamic parameter, see self.build()
            i = range(len(self.data.values()[0])) # default to printing one Run's worth of the table in sorted order
        for ival in i:
            f.write('\n')
            f.write('%s\t' % ival) # sweep table index
            for dim in self.dimensions:
                for var in dim.variables:
                    if ival == None: # blank sweep
                        f.write('%s\t' % None)
                    else:
                        f.write('%s\t' % self.data[var.name][ival]) # variable value at sweep table index
        return f.getvalue()
    
def shuffle(seq):
    """Take a sequence and return a shuffled (without replacement) copy.
    Its only benefit over np.random.shuffle is that it returns a copy instead of shuffling in-place"""
    result = copy(seq)
    np.random.shuffle(result) # shuffles in-place, doesn't convert to an array
    return result
'''
def randomize(seq):
    """Take an input sequence and return a randomized (with replacement) output sequence
    of the same length, sampled from the input sequence"""
    result = []
    for i in range(len(seq)):
        result.append(random.choice(seq))
    return result
'''
def randomize(seq):
    """Return a randomized (with replacement) output sequence sampled from
    (and of the same length as) the input sequence"""
    n = len(seq)
    i = np.random.randint(n, size=n) # returns random ints from 0 to len(seq)-1
    if seq.__class__ == np.ndarray:
        return np.asarray(seq)[i] # use i as random indices into seq, return as an array
    else:
        return list(np.asarray(seq)[i]) # return as a list
