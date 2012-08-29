# Gabor function fitter.
#
# Copyright (C) 2010-2011 Huang Xin
# 
# See LICENSE.TXT that came with this file.
from __future__ import division
import math
import numpy as np
from mpfit import mpfit
from gaussfitter import gaussfit

def onedgabor(x,H,A,dx,w,l,p):
    """
    Returns a 1-dimensional gabor of form
    g = b + a * exp(-(x-dx)**2/(2*w**2)) * cos(2*pi*(x-dx)/lambda + phi)
    """
    p = np.pi/180 * p
    return H+A*np.exp(-(x-dx)**2/(2*w**2)) * np.cos(2*np.pi*(x-dx)/l+p)

def onedgaborfit(xax, data, err=None,
        params=[0,1,0,1,1,0],fixed=[False,False,False,False,False,False],
        limitedmin=[False,False,False,True,True,True],
        limitedmax=[False,False,False,False,False,True], minpars=[0,0,0,0,0,0],
        maxpars=[0,0,0,0,0,360], quiet=True, shh=True,
        veryverbose=False):
    """
    Inputs:
       xax - x axis
       data - y axis
       err - error corresponding to data

       params - Fit parameters: Height of background, Amplitude, Shift, Width, Wavelength, Phase
       fixed - Is parameter fixed?
       limitedmin/minpars - set lower limits on each parameter (default: width>0)
       limitedmax/maxpars - set upper limits on each parameter
       quiet - should MPFIT output each iteration?
       shh - output final parameters?

    Returns:
       Fit parameters
       Model
       Fit errors
       chi2
    """

    def mpfitfun(x,y,err):
        if err is None:
            def f(p,fjac=None): return [0,(y-onedgabor(x,*p))]
        else:
            def f(p,fjac=None): return [0,(y-onedgabor(x,*p))/err]
        return f

    if xax == None:
        xax = np.arange(len(data))

    parinfo = [ {'n':0,'value':params[0],'limits':[minpars[0],maxpars[0]],'limited':[limitedmin[0],limitedmax[0]],'fixed':fixed[0],'parname':"HEIGHT",'error':0} ,
                {'n':1,'value':params[1],'limits':[minpars[1],maxpars[1]],'limited':[limitedmin[1],limitedmax[1]],'fixed':fixed[1],'parname':"AMPLITUDE",'error':0},
                {'n':2,'value':params[2],'limits':[minpars[2],maxpars[2]],'limited':[limitedmin[2],limitedmax[2]],'fixed':fixed[2],'parname':"SHIFT",'error':0},
                {'n':3,'value':params[3],'limits':[minpars[3],maxpars[3]],'limited':[limitedmin[3],limitedmax[3]],'fixed':fixed[3],'parname':"WIDTH",'error':0},
                {'n':4,'value':params[4],'limits':[minpars[4],maxpars[4]],'limited':[limitedmin[4],limitedmax[4]],'fixed':fixed[4],'parname':"WAVELENGTH",'error':0},
                {'n':5,'value':params[5],'limits':[minpars[5],maxpars[5]],'limited':[limitedmin[5],limitedmax[5]],'fixed':fixed[5],'parname':"PHASE",'error':0}]

    mp = mpfit(mpfitfun(xax,data,err),parinfo=parinfo,quiet=quiet)
    mpp = mp.params
    mpperr = mp.perror
    chi2 = mp.fnorm

    if mp.status == 0:
        raise Exception(mp.errmsg)

    if (not shh) or veryverbose:
        print "Fit status: ",mp.status
        for i,p in enumerate(mpp):
            parinfo[i]['value'] = p
            print parinfo[i]['parname'],p," +/- ",mpperr[i]
        print "Chi2: ",mp.fnorm," Reduced Chi2: ",mp.fnorm/len(data)," DOF:",len(data)-len(mpp)

    return mpp,onedgabor(xax,*mpp),mpperr,chi2

def twodgabor(params, shape=None):
    """Returns a 2d gabor function of the form:
        x' = numpy.cos(theta) * x - numpy.sin(theta) * y
        y' = numpy.sin(theta) * x + numpy.cos(theta) * y
        g = b + a * exp(-(((x-x_0)/sigma_x)**2 + ((y-y_0)/sigma_y)**2 )/2) * cos(2*numpy.pi*(x-x_0)/lambda + phi)
        
        input params = [b,a,center_x,center_y,sigma_x,sigma_y,theta,lambda,phi]
                       (b is background height, a is peak amplitude)

        where x and y are the input parameters of the returned function,
        and all other parameters are specified by this function
        
        shape=None - if shape is set (to a 2-parameter list) then returns
            an image with the gaussian defined by params
        """
    height = float(params[0])
    amplitude, center_y, center_x = float(params[1]),float(params[2]),float(params[3])
    width_x, width_y = float(params[4]),float(params[5])
    theta = np.pi/180. * float(params[6])
    rcen_x = center_x * np.cos(theta) - center_y * np.sin(theta)
    rcen_y = center_x * np.sin(theta) + center_y * np.cos(theta)
    wavelength, phase= float(params[7]), np.pi/180. * float(params[8])
            
    def evalgabor(x,y):
        xp = x * np.cos(theta) - y * np.sin(theta)
        yp = x * np.sin(theta) + y * np.cos(theta)
        g = height+amplitude*np.exp(-(((rcen_x-xp)/width_x)**2+((rcen_y-yp)/width_y)**2)/2.) * \
            np.cos(2*np.pi*(rcen_x-xp)/wavelength + phase)
        return g
    if shape is not None:
        return evalgabor(*np.indices(shape))
    else:
        return evalgabor

def gaborfit(data,err=None,params=(),fixed=np.repeat(False,9),
             limitedmin=[False,False,False,False,True,True,True,True,True],
             limitedmax=[False,False,False,False,False,False,True,False,True],
             minpars=[0.0, 0.0, 0.0, 0.0, 0.01, 0.01, 0.0, 0.01, 0.0],
             maxpars=[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 360.0, 0.0, 360.0],
             quiet=True,returnmp=False,return_all=False,returnfitimage=False,**kwargs):
    """ gabor params = (height,amplitude,center_x,center_y,width_x,width_y,theta,lambda,phi) """

    """ gaussian params=(height, amplitude, center_x, center_y, width_x, width_y, theta) """
    if len(params) == 0:
        params,_errors = gaussfit(data,limitedmin=limitedmin[:7],limitedmax=limitedmax[:7],\
                                  minpars=minpars[:7],maxpars=maxpars[:7],return_all=True)
        spatial_freq = math.sqrt(params[2]**2+params[3]**2)
        phase = 0.0
    
        params = np.append(params, np.array([spatial_freq, phase],dtype='float'))

    def mpfitfun(data,err):
        if err is None:
            def f(p,fjac=None): return [0,np.ravel(data-twodgabor(p)\
                    (*np.indices(data.shape)))]
        else:
            def f(p,fjac=None): return [0,np.ravel((data-twodgabor(p)\
                    (*np.indices(data.shape)))/err)]
        return f
    
    parinfo = [ 
                {'n':0,'value':params[0],'limits':[minpars[0],maxpars[0]],'limited':[limitedmin[0],limitedmax[0]],'fixed':fixed[0],'parname':"HEIGHT",'error':0},
                {'n':1,'value':params[1],'limits':[minpars[1],maxpars[1]],'limited':[limitedmin[1],limitedmax[1]],'fixed':fixed[1],'parname':"AMPLITUDE",'error':0},
                {'n':2,'value':params[2],'limits':[minpars[2],maxpars[2]],'limited':[limitedmin[2],limitedmax[2]],'fixed':fixed[2],'parname':"XSHIFT",'error':0},
                {'n':3,'value':params[3],'limits':[minpars[3],maxpars[3]],'limited':[limitedmin[3],limitedmax[3]],'fixed':fixed[3],'parname':"YSHIFT",'error':0},
                {'n':4,'value':params[4],'limits':[minpars[4],maxpars[4]],'limited':[limitedmin[4],limitedmax[4]],'fixed':fixed[4],'parname':"XWIDTH",'error':0},
                {'n':5,'value':params[5],'limits':[minpars[5],maxpars[5]],'limited':[limitedmin[5],limitedmax[5]],'fixed':fixed[5],'parname':"YWIDTH",'error':0},
                {'n':6,'value':params[6],'limits':[minpars[6],maxpars[6]],'limited':[limitedmin[6],limitedmax[6]],'fixed':fixed[6],'parname':"ROTATION",'error':0},
                {'n':7,'value':params[7],'limits':[minpars[7],maxpars[7]],'limited':[limitedmin[7],limitedmax[7]],'fixed':fixed[7],'parname':"SPATIALFREQ",'error':0},
                {'n':8,'value':params[8],'limits':[minpars[8],maxpars[8]],'limited':[limitedmin[8],limitedmax[8]],'fixed':fixed[8],'parname':"PHASE",'error':0} ]
    
    mp = mpfit(mpfitfun(data,err),parinfo=parinfo,quiet=quiet)
        
    if returnmp:
        returns = (mp)
    elif return_all == 0:
        returns = mp.params
    elif return_all == 1:
        returns = mp.params,mp.perror
    if returnfitimage:
        fitimage = twodgabor(mp.params)(*np.indices(data.shape))
        returns = (returns,fitimage)
    return returns
    