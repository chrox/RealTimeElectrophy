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
import logging  # available in Python 2.3
import logging.handlers
import Configuration

############# Get config defaults #################
config = Configuration.Config()

############# Logging #############
logger = logging.getLogger('Lightstim')
logger.setLevel( logging.INFO )
log_formatter = logging.Formatter('%(asctime)s (%(process)d) %(levelname)s: %(message)s')
