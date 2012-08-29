# Sinusoidal function fitter.
#
# Copyright (C) 2010-2011 Huang Xin
# 
# See LICENSE.TXT that came with this file.

from __future__ import division
import numpy as np
from mpfit import mpfit

def onedsinusoid(x,H,A,omega,phi):
    """
    Returns a 1-dimensional sinusoid of form
    H+A*np.sin(omega*x+phi)
    """
    phi = np.pi/180 * phi
    return H+A*np.sin(omega*x+phi)

def onedsinusoidfit(xax, data, err=None,
        params=[0,1,0,1],fixed=[False,False,False,False],
        limitedmin=[False,False,False,False],
        limitedmax=[False,False,False,False], minpars=[0,0,0,0],
        maxpars=[0,0,0,0], quiet=True, shh=True,
        veryverbose=False):
    """
    Inputs:
       xax - x axis
       data - y axis
       err - error corresponding to data

       params - Fit parameters: Height of background, Amplitude, Frequency, Phase
       fixed - Is parameter fixed?
       limitedmin/minpars - set lower limits on each parameter
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
            def f(p,fjac=None): return [0,(y-onedsinusoid(x,*p))]
        else:
            def f(p,fjac=None): return [0,(y-onedsinusoid(x,*p))/err]
        return f

    if xax == None:
        xax = np.arange(len(data))

    parinfo = [ {'n':0,'value':params[0],'limits':[minpars[0],maxpars[0]],'limited':[limitedmin[0],limitedmax[0]],'fixed':fixed[0],'parname':"HEIGHT",'error':0} ,
                {'n':1,'value':params[1],'limits':[minpars[1],maxpars[1]],'limited':[limitedmin[1],limitedmax[1]],'fixed':fixed[1],'parname':"AMPLITUDE",'error':0},
                {'n':2,'value':params[2],'limits':[minpars[2],maxpars[2]],'limited':[limitedmin[2],limitedmax[2]],'fixed':fixed[2],'parname':"FREQUENCY",'error':0},
                {'n':3,'value':params[3],'limits':[minpars[3],maxpars[3]],'limited':[limitedmin[3],limitedmax[3]],'fixed':fixed[3],'parname':"PHASE",'error':0}]

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

    return mpp,onedsinusoid(xax,*mpp),mpperr,chi2
