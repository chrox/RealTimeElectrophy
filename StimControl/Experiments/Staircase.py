# Modified from the PsychoPy library
#
# Copyright (C) 2011 Jonathan Peirce
#
# Distributed under the terms of the GNU General Public License (GPL).
#
# Copyright (C) 2013 Huang Xin
# 
# See LICENSE.TXT that came with this file.

import numpy as np

class StaircaseObject:
    
    """Measure threshold using staircase method."""
    
    def __init__(self,
                 startVal,
                 nReversals=None,
                 stepSizes=4,  #dB stepsize
                 nTrials=0,
                 nUp=1,
                 nDown=3, #correct responses before stim goes down
                 stepType='db',
                 minVal=None,
                 maxVal=None):
        """
        :Parameters:

            startVal:
                The initial value for the staircase.

            nReversals:
                The minimum number of reversals permitted. If stepSizes is a list then there must
                also be enough reversals to satisfy this list.

            stepSizes:
                The size of steps as a single value or a list (or array). For a single value the step
                size is fixed. For an array or list the step size will progress to the next entry
                at each reversal.

            nTrials:
                The minimum number of trials to be conducted. If the staircase has not reached the
                required number of reversals then it will continue.

            nUp:
                The number of 'incorrect' (or 0) responses before the staircase level increases.

            nDown:
                The number of 'correct' (or 1) responses before the staircase level decreases.

            stepType:
                specifies whether each step will be a jump of the given size in
                'db', 'log' or 'lin' units ('lin' means this intensity will be added/subtracted)

            stepType: *'db'*, 'lin', 'log'
                The type of steps that should be taken each time. 'lin' will simply add or subtract that
                amount each step, 'db' and 'log' will step by a certain number of decibels or log units
                (note that this will prevent your value ever reaching zero or less)

            minVal: *None*, or a number
                The smallest legal value for the staircase, which can be used to prevent it
                reaching impossible contrast values, for instance.

            maxVal: *None*, or a number
                The largest legal value for the staircase, which can be used to prevent it
                reaching impossible contrast values, for instance.

        """

        """
        trialList: a simple list (or flat array) of trials.

            """
        self.startVal=startVal
        self.nReversals=nReversals
        self.nUp=nUp
        self.nDown=nDown
        self.stepType=stepType

        self.stepSizes=stepSizes
        if type(stepSizes) in [int, float]:
            self.stepSizeCurrent=stepSizes
            self._variableStep=False
        else:#list, tuple or array
            self.stepSizeCurrent=stepSizes[0]
            self.nReversals= max(len(stepSizes),self.nReversals)
            self._variableStep=True

        self.nTrials = nTrials#to terminate the nTrials must be exceeded and either
        self.finished=False
        self.thisTrialN = -1
        self.data = []
        self.intensities=[]
        self.reversalPoints = []
        self.reversalIntensities=[]
        self.currentDirection='start' #initially it goes down but on every step
        self.correctCounter=0  #correct since last stim change (minus are incorrect)
        self._nextIntensity=self.startVal
        self._warnUseOfNext=True
        self.minVal = minVal
        self.maxVal = maxVal

    def __iter__(self):
        return self

    def update(self, result, intensity=None):
        """Add a 1 or 0 to signify a correct/detected or incorrect/missed trial

        This is essential to advance the staircase to a new intensity level!

        Supplying an `intensity` value here indicates that you did not use the
        recommended intensity in your last trial and the staircase will
        replace its recorded value with the one you supplied here.
        """
        self.data.append(result)

        #if needed replace the existing intensity with this custom one
        if intensity!=None:
            self.intensities.pop()
            self.intensities.append(intensity)

        #increment the counter of correct scores
        if result==1:
            if len(self.data)>1 and self.data[-2]==result:
                #increment if on a run
                self.correctCounter+=1
            else:
                #or reset
                self.correctCounter = 1

        else:
            if  len(self.data)>1 and self.data[-2]==result:
                #increment if on a run
                self.correctCounter-=1
            else:
                #or reset
                self.correctCounter = -1

        self.calculateNextIntensity()

    def calculateNextIntensity(self):
        """based on current intensity, counter of correct responses and current direction"""

        if len(self.reversalIntensities)<1:
            #always using a 1-down, 1-up rule initially
            if self.data[-1]==1:    #last answer correct
                #got it right
                self._intensityDec()
                if self.currentDirection=='up':
                    reversal=True
                else:#direction is 'down' or 'start'
                    reversal=False
                    self.currentDirection='down'
            else:
                #got it wrong
                self._intensityInc()
                if self.currentDirection=='down':
                    reversal=True
                else:#direction is 'up' or 'start'
                    reversal=False
                #now:
                self.currentDirection='up'

        elif self.correctCounter >= self.nDown: #n right, time to go down!
            #make it harder
            self._intensityDec()
            if self.currentDirection!='down':
                reversal=True
            else:
                reversal=False
            self.currentDirection='down'

        elif self.correctCounter <= -self.nUp: #n wrong, time to go up!
            #make it easier
            self._intensityInc()
            #note current direction
            if self.currentDirection!='up':
                reversal=True
            else:
                reversal=False
            self.currentDirection='up'

        else:
            #same as previous trial
            reversal=False


        #add reversal info
        if reversal:
            self.reversalPoints.append(self.thisTrialN)
            self.reversalIntensities.append(self.intensities[-1])
        #test if we're done
        if len(self.reversalIntensities)>=self.nReversals and \
            len(self.intensities)>=self.nTrials:
                self.finished=True
        #new step size if necessary
        if reversal and self._variableStep and self.finished==False:
            if len(self.reversalIntensities) >= len(self.stepSizes):
                #we've gone beyond the list of step sizes so just use the last one
                self.stepSizeCurrent = self.stepSizes[-1]
            else:
                self.stepSizeCurrent = self.stepSizes[len(self.reversalIntensities)]


    def next(self):
        """Advances to next trial and returns it.
        Updates attributes; `thisTrial`, `thisTrialN` and `thisIndex`.

        If the trials have ended, calling this method will raise a StopIteration error.
        This can be handled with code such as::

            staircase = StairHandler(.......)
            for eachTrial in staircase:#automatically stops when done
                #do stuff

        or::

            staircase = StairHandler(.......)
            while True: #ie forever
                try:
                    thisTrial = staircase.next()
                except StopIteration:#we got a StopIteration error
                    break #break out of the forever loop
                #do stuff here for the trial

        """
        if self.finished==False:
            #update pointer for next trial
            self.thisTrialN+=1
            self.intensities.append(self._nextIntensity)
            return self._nextIntensity
        else:
            raise StopIteration
    
    def mean(self, final=6):
        return np.average(self.reversalIntensities[-final:])
    
    def _intensityInc(self):
        """increment the current intensity and reset counter"""
        if self.stepType=='db':
            self._nextIntensity *= 10.0**(self.stepSizeCurrent/20.0)
        elif self.stepType=='log':
            self._nextIntensity *= 10.0**self.stepSizeCurrent
        elif self.stepType=='lin':
            self._nextIntensity += self.stepSizeCurrent
        #check we haven't gone out of the legal range
        if (self._nextIntensity > self.maxVal) and self.maxVal is not None:
            self._nextIntensity = self.maxVal
        self.correctCounter =0

    def _intensityDec(self):
        """decrement the current intensity and reset counter"""
        if self.stepType=='db':
            self._nextIntensity /= 10.0**(self.stepSizeCurrent/20.0)
        if self.stepType=='log':
            self._nextIntensity /= 10.0**self.stepSizeCurrent
        elif self.stepType=='lin':
            self._nextIntensity -= self.stepSizeCurrent
        self.correctCounter =0
        #check we haven't gone out of the legal range
        if (self._nextIntensity < self.minVal) and self.minVal is not None:
            self._nextIntensity = self.minVal
        
