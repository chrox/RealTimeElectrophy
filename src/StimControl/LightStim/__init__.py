# The LightStim Visual Stimulus Generator
#
# Distributed under the terms of the GNU Lesser General Public License
# (LGPL). See LICENSE.TXT that came with this file.
#

"""
The LightStim package.

The LightStim is a light-weight visual stimulus generator that
uses VisionEgg as the drawing back-end. The main feature of LightStim
is the by-frame control of the generated stimuli which is modified from 
Martin Spacek's Dimstim. For more information about Dimstim please refer to 
http://swindale.ecc.ubc.ca  

"""
from __future__ import division
import math
import VisionEgg
import Configuration

############# Get config defaults #################
config = Configuration.Config()
            
############# Some spatial utilities #############
SCREENWIDTH = VisionEgg.config.VISIONEGG_SCREEN_W
SCREENHEIGHT = VisionEgg.config.VISIONEGG_SCREEN_H
SCREENWIDTHCM = config.LIGHTSTIM_SCREEN_WIDTH
SCREENHEIGHTCM = config.LIGHTSTIM_SCREEN_HEIGHT
SCREENDISTANCECM = config.LIGHTSTIM_SCREEN_DISTANCE
PIXPERCM = (SCREENWIDTH/SCREENWIDTHCM + SCREENHEIGHT/SCREENHEIGHTCM)/2
def deg2pix(deg):
    """Convert from degrees of visual space to pixels"""
    # shouldn't I be using opp = 2.0 * distance * tan(deg/2), ie trig instead of solid angle of a circle ???!!
    # make it a one-liner, break it up into multiple lines in the docstring
    if deg == None:
        deg = 0 # convert to an int
    rad = deg * math.pi / 180 # float, angle in radians
    s = SCREENDISTANCECM * rad # arc length in cm
    return s * PIXPERCM # float, arc length in pixels

def deg2truepix(deg):
    return 2.0 * SCREENDISTANCECM * PIXPERCM * math.tan(deg*math.pi/90)

def pix2deg(pix):
    """Convert from pixels to degrees of visual space"""
    # shouldn't we be using arctan?????!!!!!!!
    if pix == None:
        pix = 0 # convert to an int
    s = pix / PIXPERCM # arc length in cm
    rad = s / SCREENDISTANCECM # angle in radians
    return rad * 180 / math.pi # float, angle in degrees

############# Some temporal utilities #############
REFRESHRATE = VisionEgg.config.VISIONEGG_MONITOR_REFRESH_HZ # Hz

def intround(n):
    """Round to the nearest integer, return an integer"""
    return int(round(n))

def sec2vsync(sec):
    """Convert from sec to number of vsyncs"""
    return sec * REFRESHRATE # float

def msec2vsync(msec):
    """Convert from msec to number of vsyncs"""
    return sec2vsync(msec / 1000) # float

def sec2intvsync(sec):
    """Convert from sec to an integer number of vsyncs"""
    vsync = intround(sec2vsync(sec))
    # prevent rounding down to 0 vsyncs. This way, even the shortest time interval in sec will get you at least 1 vsync
    if vsync == 0 and sec != 0:
        vsync = 1
    return vsync # int

def msec2intvsync(msec):
    """Convert from msec to an integer number of vsyncs"""
    vsync = intround(msec2vsync(msec))
    # prevent rounding down to 0 vsyncs. This way, even the shortest time interval in msec will get you at least 1 vsync
    if vsync == 0 and msec != 0:
        vsync = 1
    return vsync # int

def vsync2sec(vsync):
    """Convert from number of vsyncs to sec"""
    return vsync / REFRESHRATE # float

def vsync2msec(vsync):
    """Convert from number of vsyncs to msec"""
    return vsync2sec(vsync) * 1000.0 # float

############# Some spatial-temporal utilities #############
def degSec2pixVsync(degSec):
    """Convert speed from degress of visual space per sec to pixels per vsync"""
    try:
        pixSec = deg2pix(degSec)
        secPix = 1 / pixSec
        vsyncPix = sec2vsync(secPix) # float
        return 1 / vsyncPix # float
    except (ZeroDivisionError, FloatingPointError):
        return 0.0 # float

def cycSec2cycVsync(cycSec):
    """Convert temporal frequency from cycles per sec to cycles per vsync"""
    try:
        secCyc = 1 / cycSec
        vsyncCyc = sec2vsync(secCyc) # float
        return 1 / vsyncCyc # float
    except (ZeroDivisionError, FloatingPointError):
        return 0.0 # float

def cycDeg2cycPix(cycDeg):
    """Convert spatial frequency from cycles per degree of visual space to cycles per pixel"""
    try:
        degCyc = 1 / cycDeg
        pixCyc = deg2pix(degCyc) # float
        return 1 / pixCyc # float
    except (ZeroDivisionError, FloatingPointError):
        return 0.0 # float