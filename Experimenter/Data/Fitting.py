# Data fitting wrappers with optimized parameters.
#
# Copyright (C) 2010-2011 Huang Xin
# 
# See LICENSE.TXT that came with this file.

from __future__ import division
import math
import numpy as np
from gaussfitter import gaussfit
from gaborfitter import gaborfit

class GaussFit(object):
    def __init__(self):
        self.params = []
        
    def gaussfit2d(self,img,returnfitimage=True,return_all=False,**kwargs):
        """ 
            gaussian params=(height, amplitude, center_x, center_y, width_x, width_y, theta) 
        """
        x_dim,y_dim = img.shape
        limitedmin = [False,False,True,True,True,True,True]
        limitedmax = [False,False,True,True,True,True,True]
        minpars = [0.0, 0.0, -x_dim, -y_dim, 0.01, 0.01, 0.0]
        maxpars = [0.0, 0.0, x_dim, y_dim, x_dim, y_dim, 360.0]
        usemoment= np.array([True,True,True,True,True,True,True],dtype='bool')
        
        if returnfitimage:
            params,img = gaussfit(img,params=self.params,returnfitimage=True,limitedmin=limitedmin,\
                                  limitedmax=limitedmax,minpars=minpars,maxpars=maxpars,usemoment=usemoment)
            self.params = params
            return params,img
        elif return_all:
            params,errors = gaussfit(img,params=self.params,return_all=True,limitedmin=limitedmin,\
                                     limitedmax=limitedmax,minpars=minpars,maxpars=maxpars,usemoment=usemoment)
            self.params = params
            return params,errors

class GaborFit(object):
    def __init__(self):
        self.params = []
        
    def gaborfit2d(self,img,returnfitimage=True,return_all=False,**kwargs):
        """ 
            gabor params = (height,amplitude,center_x,center_y,width_x,width_y,theta,lambda,phi)
            These parameters determine the properties of the spatial receptive field. see Dayan etc., 2002
        """
        x_dim,y_dim = img.shape
        diag = math.sqrt(x_dim**2+y_dim**2)
        limitedmin=[False,False,True,True,True,True,True,True,True]
        limitedmax=[False,False,True,True,True,True,True,True,True]
        minpars=[0.0, 0.0, 0.01, 0.01, 0.01, 0.01, 0.0, 0.01, 0.0]
        maxpars=[0.0, 0.0, x_dim, y_dim, x_dim, y_dim, 360.0, diag, 360.0]
        
        if returnfitimage:
            params,img = gaborfit(img,params=self.params,returnfitimage=True,limitedmin=limitedmin,\
                                  limitedmax=limitedmax,minpars=minpars,maxpars=maxpars)
            self.params = params
            return params,img
        elif return_all:
            params,errors = gaborfit(img,params=self.params,return_all=True,limitedmin=limitedmin,\
                                     limitedmax=limitedmax,minpars=minpars,maxpars=maxpars)
            self.params = params
            return params,errors
