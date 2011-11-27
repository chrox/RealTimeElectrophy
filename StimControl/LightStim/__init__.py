# The LightStim Visual Stimulus Generator
#
# Copyright (C) 2010-2011 Huang Xin
#
# See LICENSE.TXT that came with this file.

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
import VisionEgg
VisionEgg.start_default_logging(); VisionEgg.watch_exceptions()
import Configuration

############# Logging #############
logger = logging.getLogger('LightStim')
logger.setLevel( logging.INFO )
log_formatter = logging.Formatter('%(asctime)s (%(process)d) %(levelname)s: %(message)s')
log_handler_stderr = logging.StreamHandler()
log_handler_stderr.setFormatter(log_formatter)
logger.addHandler(log_handler_stderr)

############# Get config defaults #################
config = Configuration.Config()
config.check_configuration()