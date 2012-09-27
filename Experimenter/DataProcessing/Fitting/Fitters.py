# Data fitting wrappers with optimized parameters.
#
# Copyright (C) 2010-2011 Huang Xin
# 
# See LICENSE.TXT that came with this file.

from __future__ import division
import math
import numpy as np
import scipy.ndimage as nd
from sinusoidfitter import onedsinusoidfit,onedsinusoid
from gaussfitter import gaussfit,onedgaussfit,onedgaussian,onedloggaussfit,onedloggaussian
from gaborfitter import gaborfit,onedgaborfit,onedgabor

class SinusoidFit(object):
    def sinusoid1d(self,xax,data,modelx=None,return_models=True,return_all=False,**kwargs):
        """
            1d sinusoidal params: (height, amplitude, frequency, phase)
        """
        frequency = 2*np.pi/(xax.max()-xax.min())
        amplitude = (data.max()-data.min())/2
        params=[(data.max()+data.min())/2,amplitude,frequency,0]
        fixed=[False,False,True,False]
        limitedmin=[True,True,True,True]
        limitedmax=[True,True,True,True]
        minpars=[data.min(),0.8*amplitude,0.8*frequency,-180]
        maxpars=[data.max(),1.2*amplitude,1.2*frequency,540]
        params,_model,errs,chi2 = onedsinusoidfit(xax,data,params=params,fixed=fixed,\
                                                  limitedmin=limitedmin,limitedmax=limitedmax,\
                                                  minpars=minpars,maxpars=maxpars,**kwargs)
        if modelx == None:
            modelx = xax
        model_xdata = onedsinusoid(xax,*params)
        model_fitting = onedsinusoid(modelx,*params)
        if return_all:
            return params,model_xdata,model_fitting,errs,chi2
        elif return_models:
            return (model_xdata, model_fitting)

class GaussFit(object):
    def gaussfit1d(self,xax,data,modelx=None,return_models=True,return_all=False,**kwargs):
        """
            1d gaussian params: (height, amplitude, shift, width) 
        """
        width = xax.max()-xax.min()
        lower_bound = np.sort(data)[:3].mean()
        params=[0,(data.max()-data.min())*0.5,0,width*0.2]
        fixed=[False,False,False,False]
        limitedmin=[False,True,True,True]
        limitedmax=[True,True,True,True]
        minpars=[0,(data.max()-data.min())*0.5,xax.min()-width,width*0.05]
        maxpars=[lower_bound*1.5,data.max()-data.min(),xax.max(),width*3.0]
        params,_model,errs,chi2 = onedgaussfit(xax,data,params=params,fixed=fixed,\
                                               limitedmin=limitedmin,limitedmax=limitedmax,\
                                               minpars=minpars,maxpars=maxpars,**kwargs)
        if modelx == None:
            modelx = xax
        model_xdata = onedgaussian(xax,*params)
        model_fitting = onedgaussian(modelx,*params)
        if return_all:
            return params,model_xdata,model_fitting,errs,chi2
        elif return_models:
            return (model_xdata, model_fitting)

    def loggaussfit1d(self,xax,data,modelx=None,return_models=True,return_all=False,**kwargs):
        """
            1d gaussian params: (height, amplitude, shift, width) 
        """
        width = xax.max()-xax.min()
        lower_bound = np.sort(data)[:3].mean()
        params=[0,(data.max()-data.min())*0.5,0,width*0.2]
        fixed=[False,False,False,False]
        limitedmin=[False,True,True,True]
        limitedmax=[True,True,True,True]
        minpars=[0,(data.max()-data.min())*0.5,xax.min()-width,width*0.05]
        maxpars=[lower_bound*1.5,data.max()-data.min(),xax.max(),width*3.0]
        params,_model,errs,chi2 = onedloggaussfit(xax,data,params=params,fixed=fixed,\
                                                  limitedmin=limitedmin,limitedmax=limitedmax,\
                                                  minpars=minpars,maxpars=maxpars,**kwargs)
        if modelx == None:
            modelx = xax
        model_xdata = onedloggaussian(xax,*params)
        model_fitting = onedloggaussian(modelx,*params)
        if return_all:
            return params,model_xdata,model_fitting,errs,chi2
        elif return_models:
            return (model_xdata, model_fitting)
    
    def gaussfit2d(self,img,returnfitimage=True,return_all=False):
        """ 
            2d gaussian params: (height, amplitude, center_x, center_y, width_x, width_y, theta) 
        """
        x_dim,y_dim = img.shape
        limitedmin = [False,False,True,True,True,True,True]
        limitedmax = [False,False,True,True,True,True,True]
        minpars = [0.0, 0.0, 0, 0, x_dim*0.1, y_dim*0.1, 0.0]
        maxpars = [0.0, 0.0, x_dim, y_dim, x_dim*0.8, y_dim*0.8, 360.0]
        usemoment= np.array([True,True,False,False,False,False,True],dtype='bool')
        #usemoment=np.array([],dtype='bool')
        params = [0.0, 0.0, x_dim/2, y_dim/2, x_dim/3, y_dim/3, 0.0]
        img = nd.filters.gaussian_filter(img,0.2)
        
        if returnfitimage:
            params,img = gaussfit(img,params=params,returnfitimage=True,limitedmin=limitedmin,\
                                  limitedmax=limitedmax,minpars=minpars,maxpars=maxpars,usemoment=usemoment)
            return params,img
        elif return_all:
            params,errors = gaussfit(img,params=params,return_all=True,limitedmin=limitedmin,\
                                     limitedmax=limitedmax,minpars=minpars,maxpars=maxpars,usemoment=usemoment)
            return params,errors

class GaborFit(object):
    def gaborfit1d(self,xax,data,modelx=None,return_models=True,return_all=False,**kwargs):
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
        model_xdata = onedgabor(xax,*params)
        model_fitting = onedgabor(modelx,*params)
        if return_all:
            return params,model_xdata,model_fitting,errs,chi2
        elif return_models:
            return (model_xdata, model_fitting)
        
    def gaborfit2d(self,img,returnfitimage=True,return_all=False):
        """ 
            2d gabor params: (height,amplitude,center_x,center_y,width_x,width_y,theta,frequency,phase)
            These parameters determine the properties of the spatial receptive field. see Dayan etc., 2002
        """
        x_dim,y_dim = img.shape
        diag = math.sqrt(x_dim**2+y_dim**2)
        limitedmin=[False,False,True,True,True,True,True,True,True]
        limitedmax=[False,False,True,True,True,True,True,True,True]
        minpars=[0.0, 0.0, 0.0, 0.0, x_dim*0.2, y_dim*0.2, 0.0, diag, 0.0]
        maxpars=[0.0, 0.0, x_dim, y_dim, x_dim*0.5, y_dim*0.5, 360.0, diag*2, 180.0]
        params = [0.0, 0.0, x_dim/2, y_dim/2, x_dim/3, y_dim/3, 0.0, diag, 0.0]
        img = nd.filters.gaussian_filter(img,0.2)
        
        if returnfitimage:
            params,img = gaborfit(img,params=params,returnfitimage=True,limitedmin=limitedmin,\
                                  limitedmax=limitedmax,minpars=minpars,maxpars=maxpars)
            return params,img
        elif return_all:
            params,errors = gaborfit(img,params=params,return_all=True,limitedmin=limitedmin,\
                                     limitedmax=limitedmax,minpars=minpars,maxpars=maxpars)
            return params,errors
