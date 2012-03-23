# This module contains the constants of SweepStamp.
#
# Copyright (C) 2010-2011 Huang Xin
#
# See LICENSE.TXT that came with this file.

from .. import LightStim

DTBOARDINSTALLED = LightStim.config.LIGHTSTIM_DTBOARD_INSTALLED

if DTBOARDINSTALLED:
    try:
        import DT # only importable if DT board is installed
    except ImportError:
        raise RuntimeError('Cannot import DT module.')
else:
    DT = None

# If DTboard pin C1 is connected to Omniplex pin A24, this post signal will trigger remote START recording.
RSTART_EVT = 0x00020000
# use single bit event to trigger START/STOP recording
START_REC = 1 << 14
STOP_REC = 1 << 15
# Maximum postable integer, 65535 for 16 digital lines. 
MAXPOSTABLEINT = 0x0000ffff