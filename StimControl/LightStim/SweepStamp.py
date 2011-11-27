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

# Digital output status bits. These are found on Port D on the DataWave panel
DATA = 0x00010000 # data bit. Called datastrobe in Surf, needs to be toggled to signal new header or checksum related data on port
SWEEP = 0x00020000 # sweep bit. Called displaysweep in Surf, positive edge signals new stimulus sweep. When set to low, Surf detects this as a pause
RUN = 0x00040000 # run bit. Called displayrunning in Surf, needs to be high before Surf listens to any other digital line
REFRESH = 0x00080000 # refresh bit. Called frametoggle in Surf, needs to be toggled to signal new frame-related data on port, only read by Surf if a valid header was sent. Isn't used if the vsync signal from the video card has been wired as the refresh bit instead (in which case Surf looks for an up-down strobe instead of a toggle)

MAXPOSTABLEINT = 0x0000ffff # Maximum postable integer, 65535 for 16 digital lines. 