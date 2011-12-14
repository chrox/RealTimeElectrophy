# Data fitting wrappers with optimized parameters.
#
# Copyright (C) 2010-2011 Huang Xin
# 
# See LICENSE.TXT that came with this file.

from __future__ import division
import math
import numpy as np
from sinusoidfitter import onedsinusoidfit,onedsinusoid
from gaussfitter import gaussfit,onedgaussfit,onedgaussian
from gaborfitter import gaborfit,onedgaborfit,onedgabor

class SinusoidFit(object):
    def sinusoid1d(self,xax,data,modelx=None,returnfitcurve=True,return_all=False,**kwargs):
        """
            1d sinusoidal params: (height, amplitude, frequency, phase)
        """
        frequency = 2*np.pi/(xax.max()-xax.min())
        params=[(data.max()+data.min())/2,(data.max()-data.min())/2,frequency,0]
        fixed=[False,False,True,False]
        limitedmin=[True,False,True,True]
        limitedmax=[True,False,True,True]
        minpars=[data.min(),0,0.8*frequency,0]
        maxpars=[data.max(),0,1.2*frequency,360]
        params,_model,errs,chi2 = onedsinusoidfit(xax,data,params=params,fixed=fixed,\
                                                  limitedmin=limitedmin,limitedmax=limitedmax,\
                                                  minpars=minpars,maxpars=maxpars,**kwargs)
        if modelx == None:
            modelx = xax
        model = onedsinusoid(modelx,*params)
        if return_all:
            return params,model,errs,chi2
        elif returnfitcurve:
            return model

class GaussFit(object):
    def __init__(self):
        self.params = []
    
    def gaussfit1d(self,xax,data,modelx=None,returnfitcurve=True,return_all=False,**kwargs):
        """
            1d gaussian params: (height, amplitude, shift, width) 
        """
        width = xax.max()-xax.min()
        params=[(data.max()+data.min())/2,(data.max()-data.min())/2,width*0.5,width*0.2]
        fixed=[False,False,False,False]
        limitedmin=[True,False,True,True]
        limitedmax=[True,False,True,True]
        minpars=[data.min(),0,xax.min()-3*width,width*0.05]
        maxpars=[data.max(),0,xax.max()+3*width,width*3.0]
        params,_model,errs,chi2 = onedgaussfit(xax,data,params=params,fixed=fixed,\
                                               limitedmin=limitedmin,limitedmax=limitedmax,\
                                               minpars=minpars,maxpars=maxpars,**kwargs)
        if modelx == None:
            modelx = xax
        model = onedgaussian(modelx,*params)
        if return_all:
            return params,model,errs,chi2
        elif returnfitcurve:
            return model

    def gaussfit2d(self,img,returnfitimage=True,return_all=False,**kwargs):
        """ 
            2d gaussian params: (height, amplitude, center_x, center_y, width_x, width_y, theta) 
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
        
    def gaborfit1d(self,xax,data,modelx=None,returnfitcurve=True,return_all=False,**kwargs):
        """
            1d gabor params: (height,amplitude,shift,width,wavelength,phase)
        """
        wavelength = xax.max()-xax.min()
        width = xax.max()-xax.min()
        params=[(data.max()+data.min())/2,(data.max()-data.min())/2,width*0.5,width*0.2,wavelength,0]
        fixed=[False,False,False,False,True,False]
        limitedmin=[True,False,True,True,False,True]
        limitedmax=[True,False,True,True,False,True]
        minpars=[data.min(),0,xax.min()-3*width,width*0.05,0,0]
        maxpars=[data.max(),0,xax.max()+3*width,width*3.00,0,360]
        params,_model,errs,chi2 = onedgaborfit(xax,data,params=params,fixed=fixed,\
                                               limitedmin=limitedmin,limitedmax=limitedmax,\
                                               minpars=minpars,maxpars=maxpars,**kwargs)
        if modelx == None:
            modelx = xax
        model = onedgabor(modelx,*params)
        if return_all:
            return params,model,errs,chi2
        elif returnfitcurve:
            return model
        
    def gaborfit2d(self,img,returnfitimage=True,return_all=False,**kwargs):
        """ 
            2d gabor params: (height,amplitude,center_x,center_y,width_x,width_y,theta,frequency,phase)
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
